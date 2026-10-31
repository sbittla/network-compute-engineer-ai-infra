# 17-M3 — Pending-despite-free-GPUs troubleshooting guide

**Decision order** (stop at the first class that explains the pending state, but finish the list:
P08 shows two independent causes):

| # | Evidence class | Kubernetes | Slurm | What it proves |
|---|---|---|---|---|
| 1 | Scheduler verdict | `kubectl describe pod` events; `kubectl get workloads` conditions (Kueue) | `squeue -j <id> -o %R`, `scontrol show job` | Which filter failed, per node count |
| 2 | Policy: quota, priority | `kubectl get resourcequota`; ClusterQueue usage; `FailedCreate` events | `sacctmgr show qos`, `sshare`, `sprio` | Whether policy, not capacity, holds the job (`>` not `≥`) |
| 3 | Node state | `kubectl get nodes` (SchedulingDisabled), `kubectl describe node` taints | `sinfo -R`, `scontrol show node` | Drained/cordoned/down nodes counted as "free" |
| 4 | Device plugin | `kubectl get pods -n gpu-operator -o wide`; allocatable vs `nvidia-smi -L`; `nvidia.com/mig-*` | `scontrol show node` `Gres=` vs `nvidia-smi -L` | GPUs not advertised, or advertised as MIG slices |
| 5 | Placement constraints | `kubectl get node --show-labels` vs selector/affinity; tolerations | `--constraint` vs node `Features` | Selector typos, dedication taints |
| 6 | Topology / shape | per-node allocatable − requested | `sinfo -N -O NodeList,GresUsed`; `--switches` | Free GPUs exist but not in the gang's shape |

**Applied diagnoses** `[SIMULATED]`, `lab/data/pending_cases.json`:

- **P03 (Slurm, 4-node pt-ablation):** evidence line `squeue: 48211 train pt-ablation PD 0:00 4
  (Resources)`. Policy: quota 96 + 32 = 128 ≤ 160 → not quota. Node state: all `MIXED`/`IDLE`, none
  drained. Shape: free per node n13–n20 = 4, 3, 6, 2, 8, 1, 5, 5 = **34 ≥ 32**, but only **one** whole
  node (n17) for a 4-node gang → **FRAGMENTATION**. Fix: a reservation/backfill for the gang or
  confining small jobs; do not preempt blindly.
- **P11 (Kubernetes, 2-node distill gang):** evidence lines `pod distill-2node-worker-0: Scheduled to
  orion-n30 (gang not complete; waiting)` and `worker-1: 0/3 nodes are available: 1 node(s) had
  untolerated taint {halcyon.ai/dedicated: search}, 2 Insufficient nvidia.com/gpu`. Quota: 24 + 16
  = 40 ≤ 48. The second whole-free node is orion-n31 (dedicated to search); eligible free = n30 8 +
  n26 4 = **12 < 16**, so it is *not* fragmentation → **UNTOLERATED_TAINT**. Fix is a capacity or
  policy decision (wait, or borrow capacity), never tolerating search's taint.

`solve.py` recomputes both diagnoses from the evidence bundles with the diagnoser's rules and
asserts the codes and arithmetic.
