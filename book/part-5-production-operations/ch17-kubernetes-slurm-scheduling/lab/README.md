# Lab 17 — ORION Gang Scheduler Simulator and Pending-Job Diagnoser

**Progressive Lab 7, part 2.** In part 1 ([Chapter 16 lab](../../ch16-bare-metal-fleet-lifecycle/lab/)) you
built the node lifecycle state machine (`discovered → imaged → validated → schedulable → draining →
drained → repair → retired`) and the acceptance evaluator that decides when a node may enter
`schedulable`. In this part you consume that state: only `schedulable` nodes are eligible, and you
decide *which* jobs land *where* — and explain, from evidence, why a job is not running.

## 1. Goal and the real-world task it mirrors

Platform engineers on Halcyon AI's **Platform** team do two things every week that this lab
reproduces:

1. **Policy review before a scheduler change.** Before changing priorities, quotas, or placement
   rules on a production cluster, you replay the current queue against a snapshot of the cluster
   in a simulator and check that the outcome is what the policy intends. You will implement a
   small but faithful policy simulator: gang (all-or-nothing) placement, node lifecycle and health
   filters, pools, node selectors, taints/tolerations, MIG, rail completeness, tenant GPU quotas,
   priority, dynamic fair share, socket-aware GPU selection, and rack-compact gang placement.
2. **"My job is pending but the dashboard shows free GPUs."** This is the single most common
   ticket a GPU platform team receives. You will implement a diagnoser that takes an evidence
   bundle (job spec, node snapshots, quota object, scheduler events) and returns the *set* of
   causes that explain why the apparently free GPUs are not usable.

## 2. Tier and realism boundary

**Tier L1** — laptop, Python ≥ 3.10, standard library only, < 5 s.

> **Realism boundary:** the simulator is a single-pass policy evaluator over a snapshot. It does
> not model time (no job completions, no scheduling cycles), backfill with reservations,
> preemption, Kueue cohort borrowing, Slurm multifactor decay, or any real kubelet/device-plugin/
> slurmctld behaviour. All outputs are `[SIMULATED]`. It can show that a *policy* produces the
> placements you intend; it cannot show how long jobs wait or how fast a real scheduler is.

## 3. Setup

```bash
cd book/part-5-production-operations/ch17-kubernetes-slurm-scheduling/lab
python --version                      # 3.10 or newer
python check.py                       # progress meter on starter/orion_sched.py
```

## 4. Background you need

| Topic | Manuscript section |
|---|---|
| Extended resources, device plugin, allocatable vs physical GPUs | 17.2 |
| Labels, selectors, taints/tolerations, MIG | 17.2, 17.3 |
| Gang scheduling, quotas, priority, fair share | 17.4 |
| Slurm partitions, QOS, gres, node states | 17.5 |
| Topology-aware placement on HX8 and ORION | 17.6 |
| Pending-job diagnostic loop | 17.11 |

## 5. Specification (implement exactly this)

Data files (all `[SIMULATED]`, committed; the seeded generator `tools/generate_data.py` is an
instructor copy only and is not part of the student release):

| File | Contents |
|---|---|
| `data/cluster_state.json` | 32 nodes with `lifecycle_state`, `health`, `labels`, `taints`, `mig_enabled`, `rails_up`, `gpus_allocated`; `running` jobs; `tenants` with `gpu_quota` |
| `data/job_queue.json` | 15 queued jobs: `job_id`, `tenant`, `pool`, `gpus`, `priority`, `submit_time` (s), `node_selector`, `tolerations` |
| `data/pending_cases.json` | 12 evidence bundles (independent incidents on different days, so node states differ from the snapshot): `job`, `nodes` (allocatable/allocated/physical GPUs, state, labels, taints), `quota`, `events` |

### 5.1 `tolerates(taints, tolerations)` (Task 1)
Every taint with effect `NoSchedule` or `NoExecute` must be matched by some toleration: same `key`;
operator `Exists` **or** equal `value` (operator defaults to `Equal`); toleration `effect` empty or
equal. `PreferNoSchedule` never blocks.

### 5.2 `node_filter(node, job, multi_node)` (Task 2)
Return the first failing code in this order, else `None`: `NotSchedulable` (lifecycle ≠
`schedulable`) → `Unhealthy` (health `failed`) → `PoolMismatch` (label `halcyon.ai/pool`) →
`SelectorMismatch` → `UntoleratedTaint` → `MIGEnabled` → `RailIncomplete` (only when
`multi_node`, fewer than 8 rails up). A `degraded` node is still eligible. On a real cluster a single
dead rail is an *attribute*, not a drain: label `halcyon.ai/rails-complete=false` (present in the data)
with required node affinity for gang workers in Kubernetes, or Slurm feature `rails7` + lower `Weight`
with `--constraint=rails8` on multi-node jobs. DRAIN/cordon is reserved for GPU faults, fatal Xids,
and all-rails-down (manuscript Sections 17.5.5 and 17.6).

### 5.3 `select_gpus(free, n)` (Task 3)
HX8 sockets: GPUs 0–3 (NUMA 0) and 4–7 (NUMA 1). `n == 8` → all eight. `n ≤ 4` → among sockets with
≥ n free GPUs choose the one with the **fewest** free (tie → socket 0) and take its lowest n
indices, `aligned=True`; if none fits, lowest n free indices, `aligned=False`. `5 ≤ n ≤ 7` → lowest
n free, `aligned=True`. Return `None` if fewer than n free.

### 5.4 `place_job(state, job)` (Task 4)
1. `InvalidRequest` if `gpus < 1`, or `gpus > 8` and not a multiple of 8.
2. `QuotaExceeded` if tenant `used + gpus > quota`.
3. Eligible nodes = `node_filter(...) is None` (with `multi_node = gpus > 8`). None → `NoEligibleNodes`.
4. **Multi-node:** needs `gpus/8` eligible nodes with all 8 GPUs free. If not enough:
   `Fragmentation` if the eligible nodes' total free GPUs ≥ `gpus`, else `InsufficientCapacity`.
   Otherwise choose **rack-compact**: group whole-free nodes by rack, order racks by (most
   whole-free nodes first, then rack number), take nodes by name within each rack until enough.
5. **Single-node:** candidate = eligible node where `select_gpus` succeeds. Score =
   (`0` if aligned else `1`, free GPUs left after placement, `1` if the node has all 8 rails else `0`,
   node name); lowest wins. No candidate → `Fragmentation` / `InsufficientCapacity` as above.
6. Commit only on success (all-or-nothing): remove GPUs from `free`, add to tenant `used`.
   Return `{"status": "placed", "nodes": {name: [idx…]}, "socket_aligned": bool}` or
   `{"status": "pending", "reason": code}`.

### 5.5 `schedule(cluster, jobs)` (Task 5)
Build state with the provided `build_state`. Repeatedly pick, among jobs not yet attempted, the
minimum of `(-priority, round(used/quota of its tenant, 6), submit_time, job_id)`, attempt it once,
record the result. Shares change after every placement (dynamic fair share). Return
`{"order": [...], "results": {job_id: result}, "tenant_used": {tenant: gpus}}`.

### 5.6 `diagnose_pending(case)` (Task 6)
Let `total = gpus_per_node × nodes`, `apparent_free = physical_gpus − allocated[resource]` (what
`nvidia-smi` and a naive dashboard show).
- `QUOTA_EXHAUSTED` if `quota.used + total > quota.hard`. Only the Kueue `ClusterQueue` and Slurm QOS
  bundles can show this, because those objects *hold* a job. The six `ResourceQuota` bundles are all
  below their limit: a plain `ResourceQuota` never produces a Pending pod (admission rejects the pod
  and the controller logs `FailedCreate`).
- For each node, the first failing check: `NODE_DRAINED` (`schedulable` false, or Slurm state in
  DRAIN/DRAINING/DRAINED/DOWN/FAIL/MAINT, ignoring trailing `*~#` flags, or lifecycle ≠ schedulable) →
  if `allocatable[resource] == 0` while `physical_gpus > 0`: `MIG_PROFILE_MISMATCH` when any
  `nvidia.com/mig-*` resource is allocatable, else `DEVICE_PLUGIN_NOT_ADVERTISING` →
  `SELECTOR_MISMATCH` → `UNTOLERATED_TAINT`. Report that code only if the node's
  `apparent_free ≥ gpus_per_node` (it is one of the "free GPUs" the user is pointing at).
- Nodes with no failing check are eligible with `free = allocatable − allocated`.
  `FRAGMENTATION` if the eligible nodes' total free ≥ `total` but fewer than `nodes` eligible nodes
  have `free ≥ gpus_per_node`.
- Return the sorted codes, or `["NONE_FOUND"]`.

## 6. Tasks and acceptance criteria

| # | Task | Acceptance (checker line) | Points |
|---|---|---|---|
| 1 | Implement `tolerates` | `T1` passes | 8 |
| 2 | Implement `node_filter` | `T2` passes | 10 |
| 3 | Implement `select_gpus` | `T3` passes | 10 |
| 4 | Implement `place_job` | both `T4` lines pass | 17 |
| 5 | Implement `schedule`; run it on the dataset | `T5` invariants, exact match, order pass | 20 |
| 6 | Implement `diagnose_pending` | `T6` passes (12/12 cases) | 15 |
| 7 | Write `placement-report.md` (≤ 1 page): for every pending job, the reason and the policy change (if any) that would let it run; identify which jobs were affected by fair share, by rail health, and by lifecycle state | instructor review | 10 |
| 8 | Write `pending-guide.md`: a one-page troubleshooting guide mapping each diagnoser code to the `kubectl`/Slurm command that shows it on a real cluster and the safe fix | instructor review | 10 |
| | **Total** | | **100** |

Expected run (solution): `9/9 checks passed (solution)`; 10 of 15 jobs placed.

## 7. Running the checker

```bash
python check.py                    # starter: TODO lines until you implement each task; exit 1
python check.py --impl solution    # instructor copy only; exit 0
```
Expected answers for the supplied datasets are stored as hashes, so `FAIL` lines tell you *which*
job or case differs without revealing the answer. Use `python starter/orion_sched.py` to print your
schedule and diagnoses once all tasks are implemented.

## 8. Extensions (L2 / L3)

> **Safety:** run these only on a dedicated lab cluster you control. Do not cordon, drain, taint,
> or change quotas on shared or production clusters.

**L2 — one GPU host (kind/k3s + GPU Operator, or single-node Slurm).**

```bash
# Kubernetes: what the scheduler sees vs what the hardware has
nvidia-smi -L                                                  # physical GPUs
kubectl get nodes -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
kubectl describe node <node> | sed -n '/Capacity/,/Allocated resources/p'
kubectl get pods -n gpu-operator -o wide                      # device-plugin / GFD / DCGM pods
kubectl get node <node> --show-labels | tr ',' '\n' | grep nvidia.com/
# Reproduce three planted causes on YOUR lab node, one at a time, and capture the events:
kubectl taint nodes <node> halcyon.ai/dedicated=search:NoSchedule       # then remove with a trailing '-'
kubectl create quota gpu-quota --hard=requests.nvidia.com/gpu=1 -n lab   # then create a 2-GPU Job
kubectl get events -n lab --field-selector reason=FailedCreate     # quota rejection: no Pending pod
kubectl get events -n lab --field-selector reason=FailedScheduling # taint/selector causes

# Slurm (single node with gres/gpu configured)
sinfo -N -o '%N %T %G %E'
scontrol update NodeName=<node> State=DRAIN Reason="lab drain test"     # then State=RESUME
squeue -o '%.10i %.9P %.20j %.2t %.6D %R'
```
Record in a copy of `manifest.yaml`: Kubernetes, GPU Operator, device-plugin and driver versions,
MIG strategy, Slurm version and `gres.conf`, the allocatable snapshot, and the exact event text for
each reproduced cause. Compare the real event strings with those in `pending_cases.json`.

**L3 — two or more multi-GPU nodes with RDMA.** Submit the same 2-node job under two placements
(nodes in the same rack/leaf block vs. different blocks if your fabric has blocks; rail-complete vs.
a node with one rail administratively down) and measure NCCL `all_reduce_perf` bus bandwidth:

```bash
srun -N2 --ntasks-per-node=8 --gpus-per-node=8 ./build/all_reduce_perf -b 1G -e 8G -f 2 -g 1
```
Record ≥ 5 repetitions per placement (median, p95, min/max), warm-up policy, `scontrol show topology`
(or the topology labels you used), NIC firmware and driver versions, and time-to-start (p50/p95) for
gang jobs with and without topology constraints.

## 9. Intentionally flawed inputs

The datasets contain planted traps and anomalies that teach diagnosis. They are documented for
instructors in `../solutions/exercises-key.md` (Lab section). Do not look there before finishing.
