# 17-T1 — "21 free GPUs and my 8-GPU replica is pending"

**1. Reconciliation** `[ILLUSTRATIVE evidence]`.
Allocated = n25 8 + n26 4 + n27 3 + n29 4 + n32 8 = **27**, matching the quota's 27/48.
Dashboard "free" = Σ(allocatable − allocated) = n26 (8 − 4) + n27 (8 − 3) + n29 (8 − 4) + n31 8 =
4 + 5 + 4 + 8 = **21** (n25 and n32 are full; n28 and n30 advertise 0 `nvidia.com/gpu`).
Physically idle GPUs = 8 nodes × 8 − 27 = **37**; the extra 37 − 21 = 16 are n28 (MIG slices, by
design) and n30 (device plugin down).
Of the 21, n31's 8 are dedicated to search (by design), leaving **13** scattered as 4 / 5 / 4; no
node can host 8 → the event "1 untolerated taint, 7 Insufficient nvidia.com/gpu".

**2. Ranked hypotheses**

| # | Hypothesis | Discriminating command | Verdict |
|---|---|---|---|
| H1 | Device plugin down on n30 | `kubectl get pods -n gpu-operator -o wide`, `kubectl logs` of the plugin pod; `allocatable` 0 vs `nvidia-smi -L` on the node | **Confirmed, actionable** |
| H2 | Fragmentation in the general pool | per-node allocatable − allocated: 4 / 5 / 4 | True, by design |
| H3 | Dedicated taint on n31 | event text; `kubectl describe node orion-n31` | True, by design |
| H4 | MIG on n28 | allocatable `nvidia.com/mig-1g.10gb: 56`, `nvidia.com/gpu: 0` | True, by design |
| H5 | Quota | 27 + 8 = 35 ≤ 48; a ResourceQuota block would prevent pod creation | Rejected |
| H6 | Selector mismatch | event lacks "didn't match Pod's node affinity/selector" | Rejected |

**3. Root cause.** The device plugin on n30 has been in CrashLoopBackOff (14 restarts, 47 min)
since the driver canary (driver pod 49 min old): most likely a driver/toolkit/plugin
incompatibility or NVML initialization failing against the new driver. That removes the one
whole-free general node. By design: n31 dedication, n28 MIG, packing fragments.

**4. Safe fix and validation.** Treat n30 as a failed canary (Chapter 20): keep it out of service
(drain via the lifecycle system; it has no GPU pods, so nothing is evicted); collect plugin logs and
`nvidia-smi` output; roll the canary back to the last known-good driver, or fix the component
version per the compatibility matrix (Chapter 16); let the GPU Operator validator pass; confirm
`allocatable nvidia.com/gpu: 8`; return n30 to `schedulable`. *Validation:* the replica schedules
onto n30; a 1-GPU validation pod runs `nvidia-smi`; the canary is marked failed and the wave halted.
*Do not:* remove n31's dedication taint or add a search toleration to the inference replica
(breaks tenant isolation); do not reconfigure MIG on n28 while it serves MIG workloads; do not roll
the new driver to more nodes.

`solve.py` reproduces the reconciliation arithmetic from the evidence.
