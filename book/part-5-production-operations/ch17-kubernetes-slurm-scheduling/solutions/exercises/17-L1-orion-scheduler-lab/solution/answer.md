# 17-L1 — Lab 17 reference results

**Checker:** `9/9 checks passed (solution)`; 10 of 15 jobs placed; final tenant usage pretrain 112,
research 34, finetune 24, inference 42, search 8 (= 220 of 256 GPUs allocated) `[SIMULATED]`.

**Reference schedule** (attempt order): J10 n26 [4–7] · J05 n22 + n24 · J12 n31 · J02 n14 · J03
QuotaExceeded · J04 InvalidRequest · J08 n13 + n18 · J07 n20 [4–7] · J11 n29 [0,1] · J13 n30 · J01
InsufficientCapacity · J15 n29 [2] · J06 Fragmentation · J14 QuotaExceeded · J09 n20 [2,3].

**placement-report.md must explain the five pending jobs:**
- J01 — InsufficientCapacity: dynamic fair share (pretrain 0.700 after J05) ranked it after
  research's J08 and inference's J13; J05 and J08 took the four whole rail-complete nodes; fix:
  head-of-queue gang reservation or wait for R-pt-002 (n09–n12).
- J03 — QuotaExceeded: research 18 + 32 = 50 > 48; fix: quota borrowing in a cohort or resize.
- J04 — InvalidRequest: 12 GPUs is > 8 and not a multiple of 8; fix: request 8 or 16.
- J06 — Fragmentation: exactly 8 eligible free GPUs (n20 2 + n21 6) but no node with 8.
- J14 — QuotaExceeded: inference 42 + 8 = 50 > 48 after higher-priority inference jobs.
- Rail effect: J02 lands on rail-degraded n14 (preferred for single-node 8-GPU work), keeping n13
  whole for gangs. Lifecycle effect: n19 (`repair`, GPU5 uncorrectable ECC) and n23 (`drained` for
  firmware wave 2) hold 16 "free" GPUs that are not schedulable.

**pending-guide.md (reference mapping):**

| Code | Command that shows it | Safe fix / do not |
|---|---|---|
| `QUOTA_EXHAUSTED` | `kubectl get resourcequota` + `FailedCreate` events (plain ResourceQuota rejects at admission); `kubectl get workloads` (Kueue); `sacctmgr show qos`, `squeue -o %R` | Borrow within cohort / wait; do not raise quota ad hoc |
| `NODE_DRAINED` | `kubectl get nodes` (SchedulingDisabled); `sinfo -R` | Follow the lifecycle; do not uncordon a fault-drained node |
| `DEVICE_PLUGIN_NOT_ADVERTISING` | `kubectl get pods -n gpu-operator -o wide`; allocatable vs `nvidia-smi -L` | Fix plugin/driver compatibility; do not restart blindly on a canary node |
| `MIG_PROFILE_MISMATCH` | node allocatable `nvidia.com/mig-*`; `nvidia-smi mig -lgi` | Request the MIG resource; do not reconfigure MIG live |
| `SELECTOR_MISMATCH` | `kubectl get node --show-labels` vs pod spec | Fix the selector value; do not relabel nodes to match a typo |
| `UNTOLERATED_TAINT` | `kubectl describe node | grep Taints` | Wait/borrow; do not add another tenant's toleration |
| `FRAGMENTATION` | `sinfo -N -O NodeList,GresUsed`; allocatable − requested per node | Reservation/backfill or confine small jobs; do not preempt blindly |

**Planted traps the report should mention:** n30's `PreferNoSchedule` taint is not blocking; n28 is
MIG-only; quota checks use `>` not `≥` (P07 at 47 + 1 = 48 is allowed); P12's cordoned node is
`NODE_DRAINED`, not `UNTOLERATED_TAINT`.
