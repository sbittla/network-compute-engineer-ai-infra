# Chapter 17 — Answer Key (INSTRUCTOR ONLY)

Remove this folder before distributing to learners (`scripts/make_student_release.py`). Numbers are
`[SIMULATED]` (lab snapshot, seed 17), `[MODELED]` (formula shown), or `[ILLUSTRATIVE]`. Every
calculation below was checked twice, and the lab results were cross-checked against the reference
simulator output.

---

## Knowledge checks

**17-K1.** The NVIDIA device plugin marked one GPU `Unhealthy` (it watches NVML for critical events
such as Xid 79 "fallen off the bus" or uncorrectable ECC) and reports 7 healthy devices to the
kubelet through `ListAndWatch`; the kubelet sets `allocatable` to 7. The scheduler trusts
`allocatable`, so an 8-GPU pod is never placed there (`Insufficient nvidia.com/gpu`) even though
the node is `Ready` and `nvidia-smi` lists eight GPUs. Correct follow-up: Chapter 16 repair flow,
not a plugin restart.
*Marking:* 2 pts component (device plugin → kubelet allocatable), 2 pts mechanism (per-device
health), 1 pt outcome. *Common mistake:* blaming the scheduler or a quota.

**17-K2.** Selector/affinity *attracts* (pod may run only where labels match); taint *repels*
(node refuses pods without a matching toleration). A toleration permits, never sends.
```yaml
spec:
  nodeSelector: {halcyon.ai/dedicated: search}
  tolerations:
  - {key: halcyon.ai/dedicated, operator: Equal, value: search, effect: NoSchedule}
```
*Marking:* both pieces required for full credit; toleration alone = half credit.

**17-K3.** `NoSchedule` — new pods without a toleration are not scheduled; running pods stay.
`PreferNoSchedule` — soft; the scheduler avoids the node but may use it; never blocks.
`NoExecute` — blocks new pods *and* evicts running pods that do not tolerate it (optionally after
`tolerationSeconds`). Blocking: NoSchedule, NoExecute. Evicting: NoExecute only.

**17-K4.** `mixed`: the node advertises `nvidia.com/mig-1g.10gb: 56` (8 GPUs × 7) and
`nvidia.com/gpu: 0`; a pod requesting `nvidia.com/gpu: 1` stays Pending (`Insufficient
nvidia.com/gpu`) — lab case P07. `single`: the slices are advertised as `nvidia.com/gpu: 56`; the pod
schedules and receives one `1g.10gb` instance (≈ 10 GB), which will likely fail with out-of-memory
if the workload expected a full 80 GB GPU. *Common mistake:* saying `single` exposes 8 GPUs.

**17-K5.** `Resources` — the job is at the head of the queue (for its partition) and the requested
resources are not available now. `Priority` — higher-priority pending jobs are ahead of it.
`QOSGrpGRES` — the QOS group limit on a GRES (here GPUs) is reached. `ReqNodeNotAvail` — nodes the
job requires (or all candidate nodes) are down, drained, or reserved.

**17-K6.** The scheduler filters and binds on node-level resource counts; it does not evaluate NUMA
alignment. The kubelet's Topology Manager evaluates hints at **pod admission on the node, after
binding**. Under `single-numa-node` (or `restricted`) an unalignable pod is rejected: the pod ends in
phase `Failed` with reason `TopologyAffinityError` — it is not retried in place. If a controller
(Deployment/Job) owns it, a replacement pod is created and the scheduler, seeing free counts, can bind
it to the same node again, producing a reject/recreate loop. Mitigations: replica sizes that always
fit one socket (1/2/4 GPUs on HX8); scheduler-visible topology (DRA device attributes, or node labels
consumed by affinity); or `best-effort` during migration (the only policy that admits misaligned
pods — `restricted` rejects too).
*Marking:* 2 pts "decision after binding, on the kubelet", 2 pts Failed/`TopologyAffinityError` +
controller loop, 1 pt a valid mitigation. *Common mistake:* claiming `restricted` avoids rejection.

**17-K7.** `F = 2^(−U/S)`: U = S → 2^(−1) = 0.5; U = S/2 → 2^(−0.5) = 0.707; U = 2S → 2^(−2) = 0.25.

---

## Worked problems

**17-W1.**
1. Naive panel = 8 + 8 + 0 + 4 + 6 + 2 + 8 + 3 + 5 + 8 + 1 + 7 = **60 GPUs**. p07 (8 free) is
   `draining`, so eligible = 60 − 8 = **52 GPUs**.
2. Whole-free eligible nodes: p01, p02, p10 (p07 excluded) = 3 → largest gang = 3 × 8 = **24 GPUs**.
3. 4-node gang = 32 GPUs. Eligible free 52 ≥ 32, whole nodes 3 < 4 → **Fragmentation**.
4. Candidates with ≥ 6 free: p01 (8), p02 (8), p05 (6), p10 (8), p12 (7). Free left after placement:
   2, 2, 0, 2, 1 → best fit **p05** (0 left). For 5–7 GPUs socket alignment is not a criterion.
5. Interleaved: A gets 2 nodes, B gets 2 nodes; each waits for a third → **all 4 × 8 = 32 GPUs
   stranded**. Cost = 32 GPUs × 5 h = 160 GPU-hours; 160 × $2.50 = **$400** `[ILLUSTRATIVE price]`.
6. Lost = GPUs × (interval/2 + restart) = 128 × (45/2 min + 15 min) = 128 × (0.375 h + 0.25 h) =
   128 × 0.625 h = **80 GPU-hours** per preemption `[MODELED]`.
*Marking:* 1 pt per part except part 5 (2 pts) and part 6 (2 pts). *Common mistakes:* including the
draining node; computing the largest gang as floor(52/8) = 6 nodes; using the full interval instead
of half.

**17-W2.** Submit times in the dataset (after seeded jitter): J01 108 s, J05 304 s.
1. With J01 at priority 100, J01 and J05 are both pretrain/priority 100 with identical share
   (0.600 at the time), so **submit time** decides: J01 (108) before J05 (304). Order begins J10
   (inference, 0.5625) → J01 → J05 → … Predicted/verified placements `[SIMULATED]`:

   | Job | Result | Reason |
   |---|---|---|
   | J01 (32) | n22, n24, n13, n18 | Rack-compact: rack-06 (2 whole) first, then rack-04 (n13), rack-05 (n18) |
   | J05 (16) | Pending — InsufficientCapacity | No whole rail-complete node left; n20 6 + n21 6 = 12 < 16 |
   | J08 (16) | Pending — InsufficientCapacity | Same 12 < 16 |

   All other jobs are unchanged (J10, J12, J02, J07, J11, J13, J15, J09 placed; J03, J14 quota; J04
   invalid; J06 fragmentation).
2. GPUs placed: baseline 69; variant 4 + 32 + 8 + 8 + 4 + 2 + 8 + 1 + 2 = **69** — identical. Per
   tenant (new GPUs): baseline pretrain 16, research 16, finetune 14, inference 15, search 8;
   variant pretrain 32, research 0, finetune 14, inference 15, search 8. Final usage variant:
   pretrain 128/160, research 18/48.
3. Unintended consequences: the *urgent* release-candidate evaluation J05 is now blocked by an
   ablation, because both share priority 100 and age breaks the tie; research gets nothing despite
   being furthest below entitlement. Utilization does not improve (69 = 69). Better policy (any
   well-argued one earns full credit), e.g.: (a) a dedicated `urgent-eval` QOS at priority above 100
   with a small cap (`GrpTRES=gres/gpu=16`) so urgent work always wins but cannot monopolize; (b) a
   gang **reservation** for the head-of-queue multi-node job at priority 50 so J01 is guaranteed the
   next four whole nodes (R-pt-002's 32 GPUs on n09–n12 when it ends) and small/other jobs only
   backfill if they do not delay it; (c) keep fair share for research.
4. Simulator output must match the table above.
*Marking:* 4 pts prediction, 2 pts comparison arithmetic, 3 pts policy with numbers, 1 pt
verification. *Common mistake:* assuming J05 still runs first because it is "urgent".

---

## Hands-on lab (17-L1)

### Expected checker output (solution)
`9/9 checks passed (solution)`; 10 of 15 jobs placed; final tenant usage pretrain 112, research 34,
finetune 24, inference 42, search 8 (= 220 of 256 GPUs allocated).

### Reference schedule `[SIMULATED]`
| Order | Job | Result |
|---|---|---|
| 1 | J10 | n26 [4,5,6,7] |
| 2 | J05 | n22 + n24 (all GPUs) |
| 3 | J12 | n31 (all GPUs) |
| 4 | J02 | n14 (all GPUs) |
| 5 | J03 | QuotaExceeded |
| 6 | J04 | InvalidRequest |
| 7 | J08 | n13 + n18 |
| 8 | J07 | n20 [4,5,6,7] |
| 9 | J11 | n29 [0,1] |
| 10 | J13 | n30 (all GPUs) |
| 11 | J01 | InsufficientCapacity |
| 12 | J15 | n29 [2] |
| 13 | J06 | Fragmentation |
| 14 | J14 | QuotaExceeded |
| 15 | J09 | n20 [2,3] |

### Reference diagnoses
| Case | Causes | Teaching point |
|---|---|---|
| P01 | QUOTA_EXHAUSTED | Kueue `QuotaReserved=False`; 44 + 8 = 52 > 48 while n30 has 8 free |
| P02 | UNTOLERATED_TAINT | Dedicated n31 is the only node with 8 free; n26/n27 have 2 + 5 = 7 < 8 (no fragmentation) |
| P03 | FRAGMENTATION | Slurm `Resources`; 34 free over 8 nodes, only n17 whole; needs 4 |
| P04 | DEVICE_PLUGIN_NOT_ADVERTISING | `allocatable 0`, physical 8, plugin CrashLoopBackOff |
| P05 | NODE_DRAINED | n18 DRAIN (Xid 79); eligible 4 + 2 = 6 < 8, so *not* fragmentation |
| P06 | SELECTOR_MISMATCH | `NVIDIA-H100-SXM5-80GB` vs label `NVIDIA-H100-80GB-HBM3` |
| P07 | MIG_PROFILE_MISMATCH | Quota 47 + 1 = 48 is **not** exceeded (boundary trap: `>` not `≥`) |
| P08 | QUOTA_EXHAUSTED, UNTOLERATED_TAINT | Two independent causes; fixing one is not enough |
| P09 | NONE_FOUND | Control: PreferNoSchedule taint is not blocking; pod is 3 s old |
| P10 | FRAGMENTATION, NODE_DRAINED | Manuscript Section 17.11 scenario; 18 eligible ≥ 16, one whole node |
| P11 | UNTOLERATED_TAINT | Gang of 2; second whole-free node is dedicated; eligible 8 + 4 = 12 < 16 |
| P12 | NODE_DRAINED | Cordoned node also carries the `unschedulable` taint; first-failing order reports NODE_DRAINED, not UNTOLERATED_TAINT |

### Planted anomalies and traps (do not distribute)
Cluster snapshot (`cluster_state.json`):
1. **orion-n14** — `health: degraded`, rail 3 down, label `halcyon.ai/rails-complete=false`; *not*
   drained (DRAIN is reserved for GPU faults, fatal Xids, all-rails-down). Eligible for single-node work
   only; the policy *prefers* it for 8-GPU single-node jobs (J02 must land here, not on n13). Real-cluster
   expression: Slurm feature `rails7` + low `Weight`, `--constraint=rails8` for gangs; Kubernetes
   required node affinity `rails-complete=true` for gang workers.
2. **orion-n19** — `repair`/`failed` (GPU5 uncorrectable ECC). 8 apparently free GPUs.
3. **orion-n23** — `drained` for firmware wave 2 (0 GPUs allocated, firmware not yet applied): the classic "free but not
   schedulable" trap from Chapter 16.
4. **orion-n28** — MIG `all-1g.10gb`; ineligible for whole-GPU jobs; J13/J14 must not land there.
5. **orion-n31** — dedicated taint **and** label; J12 has both selector and toleration and must land
   here. A learner who implements toleration without the selector still gets n31 here only because
   J12 carries the selector — the report should explain why both are needed.
6. **orion-n30** — `PreferNoSchedule` taint (red herring). It must stay eligible; J13 lands there.
7. **Partial allocations** n20 [0,1], n21 [4,5], n26 [0–3], n27 [0,1,4], n29 [4–7] create socket
   best-fit decisions (J10, J07, J11, J15, J09) and the fragmentation for J06.
8. **Rack layout**: whole-free rail-complete nodes n13 (rack-04), n18 (rack-05), n22 + n24 (rack-06) —
   J05 must choose rack-06 (rack-compact); a learner who picks by name chooses n13 + n18 and fails T5.

Job queue (`job_queue.json`):
9. **J04** asks for 12 GPUs (invalid shape). **J03** exceeds research quota (18 + 32 = 50 > 48).
10. **J14** (priority 10) exceeds inference quota after higher-priority inference jobs (42 + 8 = 50).
11. **J06** (priority 10, 8 GPUs) sees exactly 8 eligible free GPUs (n20 2 + n21 6) → Fragmentation,
    not InsufficientCapacity.
12. **J01** is starved by dynamic fair share (earliest priority-50 submission at t = 108 s — J06 at
    t = 42 s is earlier but priority 10; pretrain share highest) → the
    discussion in manuscript Section 17.9 Step 7 and 17-W2.
13. **J09** priority 5 ensures it is attempted after J06, so J06 sees the fragments.

Evidence bundles (`pending_cases.json`): file order is shuffled; P07 quota boundary; P09 control;
P12 order-of-checks trap; P05 vs P10 contrast (drain alone vs drain + fragmentation). The evidence
bundles are independent incidents (different days), so their node states need not match the
Monday snapshot.

### Common learner errors the checker catches
`>=` instead of `>` in quota checks (P07, T4); treating `PreferNoSchedule` as blocking (T1, P09);
spread instead of best-fit (T4, J11); forgetting rail preference (J02 on n13); static instead of
dynamic shares (order hash: J07 before J11, J13 before J01); mutating state when a gang fails (T4
gang); not stripping Slurm state suffixes; reporting UNTOLERATED_TAINT for a cordoned node (P12).

### Marking guidance for Tasks 7–8 (20 points)
- `placement-report.md` (10): all five pending jobs with correct reason (5); identifies fair-share
  effect on J01, rail effect on J02/n14, lifecycle effect of n19/n23 (3); one concrete policy change
  with expected effect (2).
- `pending-guide.md` (10): each of the 7 codes mapped to a real command — e.g. QUOTA →
  `kubectl get resourcequota` + `FailedCreate` events (plain ResourceQuota: the pod is rejected at
  admission, never Pending) / `kubectl get workloads` (Kueue) / `sacctmgr show qos` + `squeue %R`;
  NODE_DRAINED → `kubectl get nodes` (SchedulingDisabled) / `sinfo -R`; DEVICE_PLUGIN →
  `kubectl get pods -n gpu-operator`, node `allocatable` vs `nvidia-smi -L`; MIG → node allocatable
  `nvidia.com/mig-*`, `nvidia-smi mig -lgi`; SELECTOR → `kubectl get node --show-labels` vs pod spec;
  TAINT → `kubectl describe node | grep Taints`; FRAGMENTATION → per-node free GPUs
  (`sinfo -N -O NodeList,GresUsed`, allocatable minus requested) (7); safe fix per code with an
  explicit "do not" (3).

---

## Troubleshooting case (17-T1)

1. **Reconciliation.** Allocated: n25 8 + n26 4 + n27 3 + n29 4 + n32 8 = 27 (matches quota 27/48).
   The panel's 21 = Σ(allocatable − allocated) = n26 4 + n27 5 + n29 4 + n31 8 = 21 (n25, n32 full;
   n28 and n30 advertise 0 `nvidia.com/gpu`). Physically idle GPUs are 64 − 27 = 37: the extra 16 are
   n28 (MIG slices, by design) and n30 (device plugin down). Of the 21, n31's 8 are dedicated to
   search (by design), leaving 13 scattered as 4/5/4 — no node can take 8.
2. **Hypotheses** (ranked, with discriminating evidence):
   | # | Hypothesis | Test | Verdict |
   |---|---|---|---|
   | H1 | Device plugin down on n30 | `kubectl get pods -n gpu-operator -o wide`, `kubectl logs` of the plugin; allocatable 0 vs `nvidia-smi -L` on the node | **Confirmed — actionable** |
   | H2 | Fragmentation in general pool | Per-node allocatable − allocated: 4/5/4 | True, by design |
   | H3 | Dedicated taint on n31 | Event text; `kubectl describe node orion-n31` | True, by design |
   | H4 | MIG on n28 | allocatable `mig-1g.10gb: 56`, `gpu: 0` | True, by design |
   | H5 | Quota | 27 + 8 = 35 ≤ 48; a quota block would prevent pod creation | Rejected |
   | H6 | Selector mismatch | Event lacks "didn't match Pod's node affinity/selector" | Rejected |
3. **Actionable root cause:** the device plugin on n30 is in CrashLoopBackOff since the driver canary
   (49 min ago) — most likely a driver/toolkit/plugin incompatibility or the plugin failing NVML
   initialization against the new driver. By design: n31 dedication, n28 MIG, packing fragments.
4. **Safe fix:** treat n30 as a failed canary under Chapter 20: keep it out of service (`draining`
   via the lifecycle system — it has no GPU pods, so nothing is evicted), collect plugin logs and
   `nvidia-smi` output as evidence, roll the canary back to the last known-good driver or fix the
   component version per the compatibility matrix (Chapter 16), let the GPU Operator validator pass,
   confirm `allocatable nvidia.com/gpu: 8`, then return n30 to `schedulable`. **Validation:** the
   replica schedules onto n30; a 1-GPU validation pod runs `nvidia-smi`; the canary is marked failed
   and the wave halted. **Do not:** remove n31's dedication taint or add a search toleration to the
   inference replica (violates tenant isolation); do not reconfigure MIG on n28 while it serves MIG
   workloads; do not roll the new driver to more nodes.
*Marking:* reconciliation 3, hypotheses 3, root cause 2, fix + validation + prohibition 2.

---

## Design challenge (17-D1) — reference answer

(a) Sixteen blocks of 32 nodes: `SwitchName=blk01 Nodes=orionxl-n[001-032]` … `blk16`, grouped under
pod/spine switches (manuscript Section 17.5.6). Kubernetes equivalent: Kueue Topology-Aware
Scheduling (TAS) — label nodes with their pod, block, and hostname; define a `Topology` object whose
`levels` list those label keys from widest to narrowest; reference it from the `ResourceFlavor`
(`spec.topologyName`); and request placement per pod set with the annotation
`kueue.x-k8s.io/podset-required-topology: <block-label>` (all pods within one block) or
`kueue.x-k8s.io/podset-preferred-topology` (best effort, may span). TAS admits the workload only when
the requested domain has capacity, giving gang + topology in one admission decision. TAS has moved
from alpha toward beta across recent Kueue releases; API version and annotation names are
`[VENDOR-SPEC, 2026-10]` — verify.
(b) Minimum blocks for 64 nodes = 64 / 32 = 2. Model the exposure as the fraction of ring hops that
cross a block boundary for a rail ring ordered block-contiguously `[MODELED]`: 2 blocks → 2/64 =
3.1 %; 3 blocks → 3/64 = 4.7 %; random spread over 16 blocks → probability the next node is in a
different block ≈ 1 − 3/63 ≈ 95 % (each block holds ≈ 4 of the 64 nodes). Per-block uplink at 2:1:
32 × 8 × 400 Gb/s / 2 = 51.2 Tb/s; contiguous placement keeps job cross-block traffic to a few node
links, while spread placement puts nearly every rail hop on the oversubscribed spine, shared with
other jobs. Recommendation: require ≤ 2 blocks, allow 3 after a timeout, never spread.
(c) Waiting cost vs slowdown cost: waiting *w* hours idles 512 GPUs → 512·*w* GPU-h. A 3 % step
slowdown `[ILLUSTRATIVE]` on a 240 h run costs 0.03 × 240 × 512 ≈ 3,686 GPU-h. Break-even wait
*w* = 3,686 / 512 ≈ 7.2 h. A `--switches=2@04:00:00` (4 h) bound is defensible; any value with
consistent arithmetic earns credit.
*Marking:* config 3, model 4, wait trade-off 3.

---

## Outline-mandated exercises

**17-M1 (reference table).** Use manuscript Table 17.5 extended with: rollout/upgrade model
(Deployments rolling update vs drain-and-requeue); autoscaling (HPA/cluster autoscaler vs static
partitions/power saving); quota/fair share (ResourceQuota/Kueue vs QOS + multifactor); accounting
(external vs `slurmdbd`); user interface (YAML + containers vs `sbatch`/`srun`). Recommendations:
inference → Kubernetes (service abstraction, rolling updates, autoscaling); single-node batch →
either (Slurm if colocated with training, Kubernetes + Kueue if platform is K8s-first); tightly
coupled multi-node → Slurm (atomic gang allocation, `srun`, topology, requeue) or Kubernetes only with
gang admission + topology + training operator. Hybrid rule: the lifecycle system owns node state; one
scheduler per node; pool moves are lifecycle transitions.
*Marking:* table 4 (≥ 8 criteria), recommendations 4, hybrid rule 2.

**17-M2 (model policy outline).** Filters in order: lifecycle `schedulable` → health → pool → GPU
type (`nvidia.com/gpu.product` / Slurm `Feature`) → dedication (taint + selector) → MIG vs whole →
rail completeness for multi-node (expressed as Slurm feature/constraint + `Weight`, or K8s
label + required affinity — never as a drain). Topology: 1/2/4-GPU jobs socket-aligned best fit; >8 GPUs whole
nodes only, multiple of 8; prefer rail-degraded nodes for single-node 8-GPU; rack-compact gangs
(blocks on ORION-XL). Quota: nominal per tenant, ≤ 1.2× overcommit with borrowing only into idle
capacity; preemption asymmetric (serving may preempt best-effort; training preemptible only in a
`requeue` QOS). Fairness: priority class first, then share, then age; head-of-queue gang reservation.
Small jobs confined to shared nodes in the training pool. Metrics: gang time-to-start p95, largest
placeable gang, allocation %, fragmentation (free GPUs not in whole nodes), quota-blocked job-hours.
Replay evidence: e.g. confining ≤ 4-GPU jobs in the training pool to n14 (and a debug/shared set)
on the Monday queue — learners must show simulator output before/after.
*Marking:* completeness of the nine elements (9), metrics (3), replay evidence (3); scale to 15 and
normalize.

**17-M3 (guide skeleton + applications).** Decision order: (1) does the object exist and what does
the scheduler say (`kubectl describe pod` events / `squeue %R`, Kueue Workload conditions); (2)
policy — quota (`kubectl get resourcequota`, ClusterQueue usage; `sacctmgr show qos`, `sshare`),
priority (`sprio`, PriorityClass); (3) node state (`kubectl get nodes`, cordon/taints; `sinfo -R`,
`scontrol show node`); (4) device plugin (`kubectl get pods -n gpu-operator`, allocatable vs
`nvidia-smi -L`, MIG resources); (5) placement constraints (labels/selectors/affinity, features);
(6) topology/shape (per-node free GPUs vs gang shape; topology constraints such as `--switches`).
- **P03:** `squeue` reason `Resources`; quota 96 + 32 = 128 ≤ 160 (rules out policy); `sinfo` shows
  n13–n20 with free 4, 3, 6, 2, 8, 1, 5, 5 = 34 ≥ 32, one whole node (n17) < 4 → FRAGMENTATION.
- **P11:** quota 24 + 16 = 40 ≤ 48; worker-0 bound to n30 (gang waiting); worker-1 event: untolerated
  taint on n31; n26 has only 4 free; eligible 8 + 4 = 12 < 16 so not fragmentation →
  UNTOLERATED_TAINT. Fix is a capacity/policy decision (wait or borrow), not tolerating search's taint.
*Marking:* guide coverage of five evidence classes (5), commands correct (3), two applications (2).

---

## Reflection

**17-R1.** Hidden behaviours: (a) **backfill with reservations** — Slurm would reserve whole nodes
for J01 at the head of the queue and let J08 start only if it did not delay J01, potentially
changing J08's result; (b) **preemption** — J10 (priority 100) could preempt best-effort work; (c)
**time** — R-pt-002 finishing frees n09–n12 and J01 starts; (d) Kueue **borrowing** — J14 could
borrow idle quota within its cohort instead of `QuotaExceeded`. Any two with a concrete job effect.

**17-R2.** Decayed usage remembers the last ~7 days, not the instant: a tenant that just finished a
large run keeps a low fair-share factor even with nothing running, and a tenant idle all week gets a
high one. On Monday, pretrain (96 GPUs running for days) would have high decayed usage and rank even
lower; research or finetune — typically bursty and recently light — benefit most. Accept any answer
reasoning from decayed usage.

**17-R3.** Rack events are correlated: a shared CDU loop or PDU feeding several racks, a frontend
leaf pair serving several racks, or a Chapter 16 upgrade wave defined over several racks at once.
Modified rule: compact within a *shared-infrastructure domain* boundary, and spread replicas of a
*service* across domains (the opposite rule for inference availability).

**17-R4.** Metric: multi-node job queue wait (Submit→Start) p50/p95, and fraction of time largest
placeable gang ≥ next queued gang. Window: ≥ 2 weeks before and after (weekly cycles). Comparison:
same job-size mix; report job counts. Confounders: queue mix change, drains/firmware waves, quota
changes, capacity additions. Record the policy version in the scheduler manifest.

---

## Chapter deliverable (17-DEL)
Grade with the M2 and M3 rubrics plus 10 % for the lab appendix and checker output. Distinction:
replay evidence for at least two policy changes and a measured (L2) reproduction of at least two
pending causes with the real event text.
