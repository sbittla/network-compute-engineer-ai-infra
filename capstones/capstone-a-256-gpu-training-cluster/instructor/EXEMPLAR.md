# Capstone A — Exemplar Design Summary (abridged, distinction level)

INSTRUCTOR ONLY. This is an abridged summary of what a 90+ submission contains, written as the
learner would write it. Every number is `[MODELED]` from the `[ILLUSTRATIVE]` starter-kit inputs unless
labelled otherwise. A real submission includes the full templates. This shows the substance and the
level of reasoning we expect.

## 1. Executive summary

We recommend **option A (rail-optimized, 1:1)** for ORION-256, at $12.62 M capex versus $12.08 M for
option B `[MODELED, ILLUSTRATIVE prices]`. Option B is 4.3 % cheaper and wins on $/M training tokens
under the model's perfect-ECMP assumption. Its advantage depends on two things the platform does not
control: the launcher's rank order and ECMP hash placement of a few elephant flows. When we model
hash collisions, option B loses for the fully sharded scenario. Option A's backend uplinks carry
almost no W-TRAIN traffic under any rank order. The facility cannot host the design as drawn. Rack rack-05
violates 2N at maximum load, and row D cannot cool rack-08 with N+1. Both have owned mitigations, and
energizing rack-05 and rack-08 for production is gated on them.

## 2. Architecture highlights

- 32 × HX8, 8 rails; 8 rail leaves (32 down / 32 up) and 4 spines, each leaf with 8 × 400G to every spine.
  Option A: 256 host links + 256 leaf–spine links, 768 transceivers (224 MM + 32 SM host links;
  128 MM + 128 DAC fabric links).
- Leaves 0–3 and spines 0–1 in net-01; leaves 4–7 and spines 2–3 in net-02. Half the fabric links stay in-rack
  on 2 m DAC.
- eBGP underlay per REFERENCE_CLUSTER (spines AS 65100, leaves 65101–65108). Host /31 per rail, MTU
  9216/9000/4096, RoCEv2 DSCP 26 → TC3 lossless with ECN, CNP DSCP 48 → TC6.
- Data paths: GPU*i* → PCIe switch → NIC*i* (PIX) → rail-*i* leaf → same-rail peer for DP and PP traffic.
  The spine is touched only by cross-rail traffic, which NCCL normally avoids by moving data over
  NVLink to the GPU on the right rail first (PXN-style).

## 3. Facility findings and mitigations

| Finding | Arithmetic | Mitigation | Owner | Gate |
|---|---|---|---|---|
| rack-05 (A07) fails 2N at max | √3 × 415 V × 63 A = 45.29 kVA × 0.95 × 0.80 = 34.42 kW < 40.8 kW | Re-feed A07 at 80 A (43.70 kW usable). Interim: rack-05 nodes run in the dev/eval partition with GPU power capped at 500 W: (34.42/4 − 4.6) kW / 8 ≈ 500 W. They are excluded from W-TRAIN, because a capped node becomes a straggler for the whole synchronous job | Facilities | rack-05 joins W-TRAIN after re-feed |
| Row D fails N+1 | (2 − 1) × 30 = 30 kW < 40.8 kW | Add a third 30 kW unit (N+1 usable 60 kW). Interim operation at N needs a signed risk acceptance, an inlet-temperature alarm and automated drain of rack-08 if a cooling unit fails | Facilities + SRE | rack-08 production after third unit |
| rack-08 links exceed MM reach | (36.0 + 10.8 + 4.0) m × 1.1 = 55.9 m → 70 m stock > 50 m | 32 SM host links (64 SM optics), a separate spares SKU, and rack-08 flagged in the cable plan | Fabric | Acceptance P-01 |

## 4. Communication model and the oversubscription comparison

| Option | Scenario | Rank order | DP / PP contention | Step (s) | $/M tokens |
|---|---|---|---|---|---|
| A | baseline_3d | any | 1.0 / 1.0 | 17.516 | 0.4645 |
| B | baseline_3d | sorted, dp-contiguous | 1.0 / 2.0 | 17.516 | 0.4459 |
| B | baseline_3d | launcher hostfile | 2.0 / 2.0 | 17.707 | 0.4508 |
| A | fsdp_dp32 | any | 1.0 | 17.776 | 0.4714 |
| B | fsdp_dp32 | sorted | 1.0 | 17.776 | 0.4526 |
| B | fsdp_dp32 | launcher hostfile | 2.0 | 18.157 | 0.4623 |

Break-even: option B FSDP matches option A's $0.4714 when step time reaches
$0.4714 × 1.50995e10 tokens/h ÷ $384.42/h ÷ 1e6 ≈ 18.51 s. That corresponds to an effective DP contention of
(18.51 − 17.394) / (0.30 × 1.2715) ≈ **2.94**.

Exposure model (docs/VERIFIED_FACTS.md): with PP = 4 only the last micro-batch's backward (≈ 70 ms) can hide
the DP all-reduce, so exposed = max(0, T_DP − 0.07 s). That is 0.191 − 0.07 = 0.121 s on option A and
0.383 − 0.07 = 0.313 s on option B with the launcher order (+1.1 % step time). The FSDP rows (PP = 1) use a
30 % exposed fraction for per-layer prefetch, which we label as a variation `[ILLUSTRATIVE]`.

**ECMP attack (our extension, `[MODELED]` Monte Carlo, seed 7, 20,000 trials).** The model assumes perfect
ECMP. A synchronous ring runs at the speed of its most contended hop, so effective contention is the
maximum flow count on any uplink.

| Flows from one leaf | Sub-flows per flow (distinct UDP source ports) | Expected max flows per uplink | p95 |
|---|---|---|---|
| 32 (hostfile order) | 1 | 4.83 | 6 |
| 32 | 4 | 3.34 | 4 |
| 8 (sorted order) | 1 | 2.06 | 3 |
| 8 | 4 | 1.21 | 1.75 |
| 32 | 2 | 3.94 | 5 |
| 8 | 2 | 1.54 | 2 |

Sub-flows model NCCL using several QPs per connection (`NCCL_IB_QPS_PER_CONNECTION`, default 1) and several channels per hop, each with its own UDP source port `[VENDOR-SPEC, 2026-10]`. Even with 2–4 sub-flows, the hostfile order stays above the 2.94 break-even (3.94 and 3.34). At an effective contention of about 5, option B FSDP with the launcher order runs at about 19.30 s and
costs $0.4914 per million tokens, 4.2 % worse than option A. Even with four sub-flows (3.34) it is
slightly worse ($0.4744). Option A is immune because W-TRAIN's DP and PP traffic never leaves the rail leaf.

**What would change our mind:** an L3 measurement on option-B-like hardware showing that effective
contention stays below about 2.5 under the real launcher order (for example, because adaptive routing
or packet spraying is available and validated), together with a commitment from the Platform team to
topology-sorted rank ordering.

## 5. Acceptance plan (summary)

Physical (512 links, 768 optics DDM via `ethtool -m` with SM (DR4-class) Rx warn at ≈ −4 dBm and critical at ≈ −5.9 dBm, 24 h soak with zero uncorrectable FEC) → node (32
nodes: `nvidia-smi topo -m` golden diff, burn-in, 30-minute power log) → rail (256 ring-neighbour
`ib_write_bw` tests, each ≥ 90 % of line rate, spread ≤ 5 % `[ILLUSTRATIVE threshold]`) → cluster
(`all_reduce_perf -b 8 -e 8G -f 2 -g 1`, ≥ 5 runs after warm-up, median bus bandwidth ≥ 350 GB/s for
large messages, i.e. ≈ 44 GB/s per rail; our model's 0.80 efficiency is deliberately more conservative) → workload (W-TRAIN pilot step time within 5 % of the model, with an nsys
capture). Each stage has a named owner and blocks the next.

## 6. Failure analysis (excerpt)

| Domain | Option A blast radius | Option B blast radius |
|---|---|---|
| Leaf | One rail lost on all 32 nodes; the job stalls or NCCL runs degraded on 7 rails, every node affected | All 8 rails of 4 nodes; the job loses 32 GPUs and must restart smaller or wait |
| Spine | 25 % of fabric capacity, near-zero W-TRAIN impact | 50 % of fabric capacity; contention doubles for cross-rack traffic |

Option A turns a leaf failure into a cluster-wide degradation with no node lost, so a DP shrink does not
help. Runbook RB-1a chooses between waiting for repair, a checkpointed restart on 7 rails (failed HCA
excluded, ≈ 12.5 % less inter-node bandwidth, PXN cross-rail paths validated first), and taking the job
down. Option B's ToR failure (RB-1b) removes one replica, and the choice is a DP = 7 restart or waiting.

## 7. Security considerations (excerpt)

The backend fabric is not routed to the frontend or the internet. BMCs sit on an isolated OOB network
with per-node credentials rotated by the provisioning system. Switch management uses AAA with
role-based access, and PFC/ECN/QoS changes need a two-person review. Firmware images are verified
against vendor signatures before staging. Checkpoints on the parallel FS are access-controlled per
project.

## 8. Next-step backlog (top 3)

1. **P0:** L3 pilot on two racks: `all_reduce_perf` with sorted and hostfile rank orders, plus switch
   uplink counters, to measure the effective contention behind the decision.
2. **P0:** Facilities change requests for the A07 re-feed and the row D third cooling unit, with dates.
3. **P1:** Platform: make topology-sorted rank ordering the launcher default (Slurm topology-aware
   placement plus a sorted hostfile), whichever fabric is chosen.
