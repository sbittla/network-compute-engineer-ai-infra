# Chapter 1 — Exercise Answer Key (INSTRUCTOR ONLY)

All arithmetic below was computed twice (by hand and with a Python check). Values are `[MODELED]`
from ORION `[ILLUSTRATIVE]`/`[VENDOR-SPEC, 2026-10]`-class ceilings unless marked otherwise.
ORION per-GPU ceilings: 989 TFLOP/s BF16 dense (≈ 1,979 FP8), 3,350 GB/s HBM, 450 GB/s NVLink per
direction, 50 GB/s per 400G NIC.

---

## Exercise 1.1 — Reference architectures

**Model answer.** Figures 1.1–1.4 of the manuscript are the reference. A full-credit answer contains:

*Training (W-TRAIN):* object store → PFS → frontend NICs → host data loaders → PCIe → GPUs; NVLink
domain per node (TP traffic ≈ 1,203 GB per GPU per step); 8 backend rails (DP ≈ 7.66 GB + PP
≈ 2.15 GB per GPU per step); checkpoint path GPUs → host → frontend → PFS (≈ 980 GB, ≥ 12.25 s at
80 GB/s); Slurm controller (gang scheduling, rank placement); telemetry from DCGM exporter, node
exporter, switch counters, job step-time logs. Failure domain: the whole job (all 256 GPUs) for any
component fault.

*Inference (W-INFER):* clients → gateway/LB → router with admission control → replica (one `HX8`,
TP = 8) with KV cache in HBM; model registry → local NVMe → HBM at replica start (≈ 140 GB); per-
request data is small (≈ 2,048 prompt tokens in, streamed tokens out); Kubernetes control plane;
TTFT/TPOT histograms, queue depth, KV-cache occupancy. Failure domain: one replica (eight GPUs);
requests in flight are lost/retried; fleet capacity drops by 1/n.

Dependency tables should resemble Tables 1.3 and 1.4. Accept different but defensible first signals.

**Marking (20 pts):** diagrams with ≥ 6 components and ≥ 4 data paths each (6); volumes on paths,
correct within 2× (4); dependency tables covering all six layers (6); failure-domain contrast (4).

**Common mistakes:** drawing TP traffic on the backend fabric; omitting checkpoint flow; treating the
dataset as the dominant training I/O for text LLMs; forgetting the OOB/BMC network; no observability
layer at all.

---

## Exercise 1.2 — Scale-up versus scale-out

| Bound | Workload A (decode) | Workload B (MoE training) |
|---|---|---|
| Compute | 0.56 / 989 = 0.566 ms | 400 / 989 = 0.404 s |
| Memory | 20.18 / 3,350 = 6.02 ms | 500 / 3,350 = 0.149 s |
| Scale-up | 0.147 / 450 = 0.327 ms | 40 / 450 = 0.089 s |
| Scale-out | 0 / 50 = 0 | 30 / 50 = 0.600 s |
| Dominant | Memory (HBM) | Scale-out (NIC) |
| Ceiling fraction | 6.02 / 9.5 = 0.63 | 0.600 / 1.5 = 0.40 |

*A* is memory-bound; the communication that matters is on the **scale-up** domain (160 small TP
all-reduces per step), and it is latency- rather than bandwidth-dominated. Confirming telemetry:
`DCGM_FI_PROF_DRAM_ACTIVE` high (≈ 0.6 or more), `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` low (< 0.1); TPOT
grows roughly linearly with KV bytes (batch × context); NIC counters ≈ 0.

*B* is communication-bound on **scale-out**: expert-parallel all-to-all across nodes. Confirming
telemetry: an Nsight Systems timeline in which all-to-all (NCCL send/recv) kernels occupy ≥ 40 % of
the step; NIC TX rates near line rate (tens of GB/s) during those phases; rising ECN marks/CNPs on the
rail leaves; step time that scales with tokens routed off-node.

*Placement for B:* constrain expert-parallel groups to one node (EP ≤ 8) or use hierarchical
all-to-all so most token exchanges ride NVLink. If all 30 GB moved to NVLink: 30 / 450 = 0.067 s,
making B compute-bound (0.404 s). Limit: the NVLink domain is 8 GPUs, so experts must fit in 8 × 80 GB
of HBM per group, and any cross-node data-parallel or expert replication traffic remains on the NIC.

**Marking (20 pts):** eight bounds correct with units (8); dominant resource and network for each (4);
telemetry with expected direction (4); placement proposal with ORION limit (4).

**Common mistakes:** dividing NIC bytes by 400 (forgetting bits → bytes); reporting A as
communication-bound because "TP is communication"; summing bounds and calling it the prediction.

---

## Exercise 1.3 — Role-to-skill matrix

Model answer: Table 1.10 of the manuscript. Accept variations of ±1 per cell when justified. Look for:
AI Network Engineer at 3 on L2/L3/BGP, RDMA/congestion, physical layer; GPU Cluster Engineer at 3 on
host/PCIe/NUMA, NVLink/topology, NCCL, provisioning/firmware; SRE at 3 on observability and
automation/safe change. Every role should be ≥ 2 on observability. The personal column and gap list
must point at specific chapters (e.g., gap in RDMA → Chapters 8–9 and the Chapter 9 telemetry lab).

**Marking (10 pts):** ≥ 12 domains, three roles (3); justifications for highs and lows (3); personal
column and gap list with chapter + artifact (4). **Common mistakes:** rating everything 3; listing
tools rather than skill domains; claiming market data without a dated register.

---

## Knowledge checks

**K1.** Coupling (step = max over 256 ranks, 17.4 s modeled step); bandwidth per server (3.2 Tb/s
backend + 400 Gb/s frontend vs 25–100 Gb/s); traffic (east-west synchronized collectives, low
entropy); power density (≈ 41 kW per rack); failure semantics (one fault stops the job; MTBF_job =
MTBF_node / n). Also accept: goodput economics (≈ $56k/year per 1 %).

**K2.** Synchronous steps end only when the slowest rank finishes; every other rank waits in the
collective. The job runs at the speed of its slowest member, so the loss ≈ 10 % of all 256 GPUs
(≈ 25.6 GPU-equivalents).

**K3.** (a) 400 / 8 = 50 GB/s. (b) 900 GB/s total bidirectional = 450 GB/s per direction.
(c) 8 × 400 Gb/s = 3,200 Gb/s = 400 GB/s per direction.

**K4.** Prefill: all prompt tokens through every layer at once → large matrix multiplies →
compute-bound. Decode: one token per sequence per step; all weights + KV cache read each step →
HBM-bandwidth-bound unless batch is very large.

**K5.** 2(p − 1)/p × S. p = 4: 1.5; p = 8: 1.75.

**K6.** > 1.0: the profile claims faster-than-peak work → data error (units, bidirectional counter,
double count, wrong observed time). 0.1: no throughput ceiling explains the time; latency, launch
overhead, synchronization, queueing, or stragglers dominate.

**K7.** It measures the fraction of time any kernel runs, including communication kernels waiting on
peers. Better: `DCGM_FI_PROF_SM_ACTIVE` and `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`.

**Marking:** 2 pts each (14). Half credit for correct idea without numbers in K1/K3.

---

## WP1 — Re-partitioning W-TRAIN (TP = 4, PP = 8, DP = 8)

Tokens per DP replica: 4,194,304 / 8 = 524,288. Layers per stage: 80 / 8 = 10.
Per-all-reduce payload: 524,288 × 8,192 × 2 B = 8.59 GB.

(a) S_TP = 4 × 10 × 8.59 GB = 343.6 GB. Sent per GPU = 2(4 − 1)/4 × 343.6 = 1.5 × 343.6 = 515.4 GB.
T_scaleup = 515.4 / 450 = **1.145 s**.

(b) Parameters per GPU = 70 × 10⁹ / (4 × 8) = 2.1875 × 10⁹ (unchanged, since TP × PP = 32 either way).
Gradient shard = 4.375 GB; sent = 1.75 × 4.375 = 7.66 GB; T = 7.66 / 50 = **0.153 s**.

(c) Boundary volume 8.59 GB split over 4 TP ranks = 2.15 GB per GPU per direction; a middle-stage GPU
sends ≈ 4.30 GB → 4.30 / 50 = **0.086 s** if both boundaries cross nodes. With two stages per node,
every other boundary is intra-node and can use NVLink, so the NIC share is ≈ 2.15 GB for most GPUs.
Worst-case NIC total ≈ 7.66 + 4.30 ≈ 11.95 GB → 0.239 s.

(d)

| | TP 8 / PP 4 | TP 4 / PP 8 |
|---|---|---|
| TP bytes, NVLink bound | 1,202.6 GB, 2.67 s | 515.4 GB, 1.145 s |
| NIC bytes (worst case), bound | 9.8 GB, 0.196 s | 11.95 GB, 0.239 s |
| Compute per GPU | 6.95 s | 6.95 s |

Unmodeled cost: the **pipeline bubble**. With *m* micro-batches the idle fraction of a 1F1B schedule
is ≈ (p − 1)/(m + p − 1); for m = 64 `[ILLUSTRATIVE]`: PP 4 → 3/67 = 4.5 %, PP 8 → 7/71 = 9.9 %.
Also acceptable: more activation memory in flight for deeper pipelines, more point-to-point latency.

**Marking (15 pts):** (a) 4, (b) 3, (c) 4 (full credit requires noting intra-node boundaries or
stating the worst-case assumption), (d) 4. **Common mistakes:** using 1.75 for p = 4; dividing
parameters by TP only; forgetting that per-all-reduce payload does not shrink with TP degree.

---

## WP2 — FP8 serving on half a node

(a) Weights per GPU = 70 GB / 4 = 17.5 GB. KV per replica = 32 × 2,048 × 327,680 B = 21.47 GB; per GPU
= 21.47 / 4 = 5.37 GB (two of eight KV heads per GPU). Total = 22.87 GB per GPU per step.

(b) T_memory = 22.87 / 3,350 = **6.83 ms**. FLOP per GPU = 2 × 70 × 10⁹ × 32 / 4 = 1.12 × 10¹² →
T_compute = 1.12 / 1,979 = **0.566 ms**.

(c) Step ≈ 6.83 / 0.63 = 10.84 ms. Per replica: 32 / 0.01084 = 2,952 tokens/s. Per node (2 replicas):
**≈ 5,900 tokens/s**, ≈ 1.75× the BF16 TP = 8 figure of ≈ 3,370 tokens/s per node.

| | BF16, TP 8 | FP8, TP 4 |
|---|---|---|
| HBM bytes per GPU per step | 20.18 GB | 22.87 GB |
| T_memory | 6.02 ms | 6.83 ms |
| Replicas per node | 1 | 2 |
| Tokens/s per node (fraction 0.63) | ≈ 3,370 | ≈ 5,900 |

(d) Weights-only intensity = 2 FLOP × 32 / 1 B = **64 FLOP/B**; FP8 machine balance = 1,979 / 3.35 ≈
**591 FLOP/B**, so decode remains ≈ 9× below balance: still memory-bound.

To trust (c), measure TPOT distributions (p50/p95) at FP8 TP = 4 under the target load: FP8 kernel
efficiency and the different all-reduce latency at p = 4 change the ceiling fraction; also validate
model quality at FP8.

**Marking (15 pts):** (a) 4, (b) 4, (c) 4, (d) 3. **Common mistakes:** halving KV bytes too (the KV
cache is still BF16); forgetting the second replica; using the BF16 peak for FP8 compute.

---

## Lab

See `solutions/lab/README.md` for planted flaws and the reference output. Grade using the rubric in
`lab/README.md`. The data-quality note must identify: W13 missing HBM bytes; second W05 (duplicate,
keep first); W15 negative read volume; W18 `Gbps` is a rate, not a volume; W11 `Gb` must be divided by
8 (otherwise it appears impossible); W12 impossible (40 GB in 0.49 s ≈ 81 GB/s > 50 GB/s line rate →
likely TX + RX summed, or a counter covering two NICs); W16 latency/overhead-dominated (eager-mode
batch-1 decode); W05 and W09 mislabeled (communication-bound, declared compute).

---

## Troubleshooting case — slow replica `orion-n23`

**Ranked hypotheses.**
1. *Degraded NVLink state on GPU 5 (scale-up network).* For: all 18 of GPU 5's links report `inactive`
   while every other GPU shows 18 links at 26.562 GB/s; lower DRAM activity (GPUs waiting, not
   streaming weights); clocks and temperature normal. Against: none yet.
2. *Host-side overhead on this node* (CPU frequency governor, IRQ placement, noisy process; Chapter 3).
   For: decode is sensitive to launch latency. Against: does not explain the link state.
3. *Orchestration/config drift* (different image, CUDA graphs disabled, different TP layout). For:
   one replica differs. Against: same model version reported; check the pod spec.
4. Scale-out fabric: unlikely, because TP = 8 decode does not use the backend NICs.

*Watch item, not a cause:* GPU 2's replay counter rising at ≈ 1/s. Each replay costs on the order of a
link round trip (well under a microsecond to a few µs), so ≈ 1 replay per second adds microseconds per
second, far too little to explain a 7 ms TPOT gap across ≈ 13,000 all-reduces per second (160 per
12 ms step). Record it and trend it. A rising rate is an early sign of a marginal link, which belongs
on the Fleet ticket.

**Mechanism.** Each decode step performs 160 TP all-reduces in sequence. Every all-reduce completes
only when all eight GPUs have exchanged data, so the slowest path in the group sets its latency. With
GPU 5's NVLinks inactive, NCCL has no NVLink path to that GPU. Its channels fall back to a slower path:
PCIe peer-to-peer, or host-staged shared memory where P2P is not permitted. That path costs tens of µs
per hop instead of a few. Decode is especially sensitive because each all-reduce is small (≈ 524 KB at
batch 32) and latency-bound. Example: ≈ 44 µs extra per all-reduce × 160 ≈ 7 ms, the observed gap
`[ILLUSTRATIVE]`. A link running at *reduced width* (some links inactive) would mostly cost bandwidth. Note that this PCIe fallback is not guaranteed: depending on the Fabric Manager degraded-mode policy and driver version, a GPU that has lost all its NVLinks may instead be excluded from use (or block the job from starting) `[VENDOR-SPEC, 2026-10 — verify]`.
At 524 KB per all-reduce, losing a third of 450 GB/s adds only ≈ 1 µs, so a partial loss produces a
much smaller TPOT gap and is a watch-and-schedule item, not an emergency.

**Discriminating tests (read-only).** (1) Inspect per-link state and error counters on the node with
`nvidia-smi nvlink --status` and `nvidia-smi nvlink --errorcounters`, or the DCGM NVLink fields. Expect
GPU 5's links inactive or missing and every other GPU's links nominal. (2) Read the replica's NCCL
initialization log (`NCCL_DEBUG=INFO`, captured at pod start). Expect channels touching GPU 5 to use a
non-NVLink transport (for example `via SHM`, or `P2P` over PCIe) where healthy replicas show
NVLink `P2P/IPC` everywhere. (3) Compare the pod spec and image digest with a healthy replica using
`kubectl get pod <pod> -o yaml`. Expect them to be identical, which weakens H3. A further test, after
draining: run `dcgmi diag -r 3` and an intra-node `all_reduce_perf` on the drained node and on a
healthy node. Expect lower bus bandwidth and NVLink failures in the diag.

**Remediation.** Remove the replica from the router. Confirm that the remaining 11 replicas absorb the
load (load rises by 12/11 ≈ 9 %) while staying within SLO. Run `kubectl cordon`, then `kubectl drain`
on the node, and hand it to Fleet with the evidence bundle for diagnostics and repair (reseat or
replace per vendor process). Return it to service only after acceptance tests pass. **Validation:**
after return, all 18 links per GPU active at nominal speed, replay counters flat for ≥ 24 h, and
replica TPOT p95 within 5 % of the fleet median over ≥ 1 h at normal load.

**Proven vs correlated:** the inactive links on GPU 5 are correlated with the slowdown. Causation is
shown only when the NCCL transport lines confirm the fallback path, the drained-node diagnostics
reproduce the degraded bandwidth and latency, and the repaired node returns to fleet-median TPOT. The
GPU 2 replay rate is not shown to contribute.

**Marking (15 pts):** hypotheses with evidence (4); mechanism (4); safe tests with expected results
(4); remediation + validation + proven/correlated (3). **Common mistakes:** blaming the ≈ 1/s replay counter (too small to matter); restarting the pod and
declaring victory; running diagnostics on a node still serving traffic; blaming the backend fabric.

---

## Design challenge — shared vs dedicated inference capacity

**Model recommendation: Option B (dedicated pool), with a stated condition for revisiting.**

| Criterion | A: share ORION nodes | B: dedicated frontend-only pool |
|---|---|---|
| SLO risk | Higher: preemption/handover latency; training jobs on same rails/power envelope | Lower: isolated scheduling and capacity |
| Hardware cost | Uses existing 400G backend NICs/ports that inference does not need | No backend NICs, no rail ports: 64 fewer 400G ports and optics |
| Utilization | Higher if training can absorb idle inference capacity | Idle off-peak capacity is wasted |
| Scheduler | Slurm and Kubernetes must coordinate ownership of the same nodes | Kubernetes only |
| Failure domain | Shared with training partition | Separate |

Quantified argument: 8 nodes = 64 GPUs; at $2.50/GPU-hour `[ILLUSTRATIVE]` the pool costs 64 × 2.50 ×
8,760 = $1,401,600/year. If inference averages 60 % of the pool, sharing could reclaim at most
0.40 × 64 × 8,760 × $2.50 = $560,640/year of training capacity, and only if training jobs can use
preemptible 1–8-node fragments, which large synchronous jobs generally cannot. Backend fabric:
TP = 8 inference stays inside one node and needs no RDMA; it would be needed for multi-node model
parallelism or disaggregated prefill/decode with KV transfer over RDMA (Chapter 15).

*Would change my mind if:* inference demand is strongly diurnal and Halcyon has many small,
preemptible training/eval jobs; or a disaggregated-serving design needs RDMA KV transfer; or the
facility cannot host a separate pool.

**Marking (15 pts):** recommendation with table (5); quantified argument (4); fabric need correctly
analysed (3); assumptions + "change my mind" (3). Either option earns full credit if well argued.

---

## Reflection

**R1.** Examples: achievable vs peak rates (measure with microbenchmarks: GEMM, `all_reduce_perf`,
storage `fio`); overlap of communication and compute (Nsight Systems timeline); latency/launch overhead
and stragglers (per-rank timing, small-message collective latency); contention from other jobs
(shared PFS and fabric counters).

**R2.** Can conclude: which skills recur in the sampled postings on a date. Cannot conclude: market
share, demand trends, or completeness; postings change weekly, titles differ, duplicates abound.
Dating is required because a claim without a date cannot be verified or refreshed.

**R3.** MODELED: FLOP counts, lower bounds, KV sizes, TP/DP volumes. ILLUSTRATIVE: observed step times
(17.4 s is modeled from an assumed 40 % MFU; 9.5 ms, 75 ms), HBM traffic of 2.1 TB, all-reduce
latency of 10 µs. To make MEASURED: actual step time and MFU, decode TPOT distribution, NVLink/NIC byte
rates, all-reduce latency at the relevant sizes, HBM activity.

**R4.** Example: "GPU utilization counts any running kernel, including NCCL kernels waiting on peers.
For compute efficiency use SM active / tensor active panels below. A drop in tensor activity with
flat utilization usually means communication or waiting."

**Quick self-check.** Q1: see K7. Q2: 40 GB / 0.5 s = 80 GB/s > 50 GB/s line rate: impossible; likely
TX + RX summed, bits/bytes confusion elsewhere in the pipeline, wrong time window, or two NICs'
counters aggregated. Q3: DP groups are same-local-index GPUs, which share a rail; rail leaf *r*
connects NIC *r* of all 32 nodes, so the traffic stays on one leaf.
