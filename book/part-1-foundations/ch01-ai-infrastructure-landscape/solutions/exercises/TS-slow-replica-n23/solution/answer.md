# TS — Slow inference replica `orion-n23`: model answer

Method: the diagnostic loop of manuscript Section 1.11 and the decode analysis of Section 1.9 Step 5.
Evidence in the prompt is `[ILLUSTRATIVE]`; arithmetic is `[MODELED]` and reproduced by `solve.py`.

## Consistency check first

If a replica reads the same HBM bytes per step but each step takes longer, DRAM activity should fall in
proportion: 0.63 × 12 / 19 = **0.40**, against 0.41 observed. Tensor activity: 0.08 × 12 / 19 = 0.05,
exactly as observed. So the GPUs do the same work, spread over a longer step: they are *waiting*, not
throttled (no clock-event reasons, normal temperature).

## 1. Ranked hypotheses

| Rank | Hypothesis | For | Against |
|---|---|---|---|
| 1 | **GPU 5 has lost its NVLinks** (scale-up) | All 18 links `inactive` on GPU 5 only; activity ratios fit "waiting"; clocks and temperature normal | None yet |
| 2 | Host-side overhead (CPU governor, IRQ placement, noisy process; Chapter 3) | Decode is launch-latency sensitive | Does not explain the link state |
| 3 | Orchestration/config drift (other image, CUDA graphs off, other TP layout) | One replica differs | Same model version reported; check pod spec |
| 4 | Scale-out fabric | — | TP = 8 decode does not use the backend NICs |

**Watch item, not a cause:** GPU 2's replay counter at ≈ 1/s. Even at 5 µs per replay that is ≈ 5 µs per
second, ≈ 0.06 µs per 12 ms step, against a 7 ms gap. Trend it and add it to the Fleet ticket as an
early sign of a marginal link.

## 2. Mechanism

Each decode step performs 2 × 80 = **160 TP all-reduces** in sequence, ≈ 13,300 per second at a 12 ms
step. Every all-reduce completes only when all eight GPUs have exchanged their data, so the slowest path
sets its latency. With GPU 5's NVLinks inactive, NCCL has no NVLink path to it, and its channels fall
back to PCIe peer-to-peer or host-staged shared memory: tens of µs per hop instead of a few. Decode is
especially sensitive because each all-reduce is small (32 × 8,192 × 2 B = 524 KB) and latency-bound. The
gap needs (19 − 12) ms / 160 = **≈ 44 µs extra per all-reduce**, which a host-staged fallback can supply
`[ILLUSTRATIVE]`. By contrast, a *partial* link loss (a third of 450 GB/s) adds only ≈ 1 µs per
all-reduce (≈ 0.16 ms per step): a watch-and-schedule item, not this incident. Note that the fallback is
not guaranteed: depending on the Fabric Manager degraded-mode policy and driver, a GPU that has lost all
NVLinks may instead be excluded or block the job `[VENDOR-SPEC, 2026-10 — verify]`.

## 3. Discriminating tests (read-only, safe in production)

1. `nvidia-smi nvlink --status` and `nvidia-smi nvlink --errorcounters` (or DCGM NVLink fields) on the
   node. Expected under H1: GPU 5's links inactive, all others nominal.
2. The replica's NCCL initialization log (`NCCL_DEBUG=INFO`, captured at pod start). Expected: channels
   touching GPU 5 use a non-NVLink transport (`via SHM`, or `P2P` over PCIe) where healthy replicas show
   NVLink `P2P/CUMEM` (`P2P/IPC` before NCCL 2.19).
3. `kubectl get pod <pod> -o yaml` and the image digest against a healthy replica. Expected: identical,
   which weakens H3.

After draining only: `dcgmi diag -r 3` and an intra-node `all_reduce_perf` on this node and a healthy
one. Expected: lower bus bandwidth and NVLink failures in the diagnostic.

## 4. Remediation and validation

Remove the replica from the router and confirm that the other 11 absorb the load: 12 / 11 = **+9.1 %**
per replica, inside SLO headroom (TPOT p95 12 ms against 50 ms). Then `kubectl cordon` and
`kubectl drain` the node, and hand it to Fleet with the evidence bundle for diagnostics and repair
(reseat or replace per vendor process). **Validation:** after return, all 18 links per GPU active at
nominal speed, replay counters flat for ≥ 24 h, and replica TPOT p95 within 5 % of the fleet median over
≥ 1 h at normal load.

**Proven versus correlated:** the inactive links are *correlated* with the slowdown. Causation is shown
only when the NCCL transport lines confirm the fallback path, the drained-node diagnostics reproduce the
loss, and the repaired node returns to fleet-median TPOT. The GPU 2 replay rate is not shown to
contribute.

**Common wrong answers:** blaming the replay counter; restarting the pod and declaring victory; running
diagnostics on a node still serving traffic; blaming the backend fabric.
