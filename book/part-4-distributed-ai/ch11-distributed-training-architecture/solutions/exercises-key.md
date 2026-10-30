# Chapter 11 — Exercises Answer Key (INSTRUCTOR ONLY)

All numbers are `[MODELED]` from the chapter's formulas and the `[ILLUSTRATIVE]` assumptions of
Table 11.4 unless stated. Every value below was computed twice: by hand and with
`solutions/lab/stepmodel.py`. Accept answers within ±2 % when learners round intermediate values.

Shared constants: N = 70e9, L = 80, h = 8192, s = 4096, B = 1024 sequences, tokens/step D = 4,194,304,
6ND = 1.7616e18 FLOP, ideal step on 256 GPUs = 6.958 s, compute at 50 % efficiency = 13.916 s,
M = s·b·h·2 B = 67.1e6 B for b = 1.

---

## 11.1 Collectives per strategy

| Strategy | Collective(s) | Frequency |
|---|---|---|
| DDP | all-reduce of gradient buckets | once per step (per bucket), overlapped with backward; with `no_sync()` only on the last micro-batch |
| ZeRO-1 (distributed optimizer) | reduce-scatter of gradients + all-gather of updated weights | once per step |
| ZeRO-3 / FSDP full shard | all-gather weights (fwd), all-gather weights (bwd), reduce-scatter grads | per layer/unit, per micro-batch |
| Megatron TP + SP | all-gather + reduce-scatter (2 all-reduce-equivalents fwd, 2 bwd) | per layer per micro-batch |
| Pipeline | point-to-point send/recv of activations (fwd) and activation gradients (bwd) | per micro-batch per stage boundary |
| Expert parallel | all-to-all dispatch + combine (2 fwd, 2 bwd) | per MoE layer per micro-batch |

Marking (6 pts): 1 per row. Common mistake: saying ZeRO-1 uses all-reduce "plus" extra traffic — it
uses the *same* bytes split into reduce-scatter and all-gather.

## 11.2 Bytes per parameter

2 B BF16 weights (used in forward/backward), 2 B BF16 gradients, 12 B FP32 optimizer state (4 B master
weights, 4 B Adam first moment, 4 B second moment). With DP = 8:
ZeRO-1 = 2 + 2 + 12/8 = **5.5 B**; ZeRO-2 = 2 + (2 + 12)/8 = **3.75 B**; ZeRO-3 = 16/8 = **2.0 B**
(plus transient gather buffers). Accept 20 B/param variants only if the learner explicitly adds FP32
gradient accumulation buffers and states it.

## 11.3 Bubble

(p − 1)/(m + p − 1): p = 4, m = 8 → 3/11 = **27.3 %**; m = 32 → 3/35 = **8.6 %**; m = 128 → 3/131 =
**2.3 %**; p = 8, m = 32 → 7/39 = **17.9 %**. If the learner uses (p − 1)/m (relative to ideal compute)
they get 37.5 %, 9.4 %, 2.3 %, 21.9 %: accept only if the form is named.

## 11.4 Sequence parallelism

It reduces **activation memory**, not wire bytes: activations outside the tensor-parallel matmuls
(LayerNorm and dropout inputs/outputs, ≈ 10·s·b·h bytes per layer) were replicated on every TP rank;
SP splits them along the sequence. Per-layer activations go from s·b·h·(10 + 24/t) to s·b·h·34/t
(attention-score term removed by selective recompute). For t = 8: 13 vs 4.25 → **≈ 3.1× less**. The
wire bytes are unchanged because each all-reduce becomes a reduce-scatter + all-gather of the same
total.

## 11.5 Rail locality

Global rank r = tp + 8·dp + 64·pp (TP fastest, then DP, then PP; TP = 8, DP = 8). Rank 19 → tp = 19
mod 8 = 3, dp = ⌊19/8⌋ mod 8 = 2, pp = ⌊19/64⌋ = 0. Its DP group is {3 + 8k : k = 0..7} =
{3, 11, 19, 27, 35, 43, 51, 59}. With `--nproc-per-node=8`, rank r lives on node ⌊r/8⌋ as local rank
r mod 8 = 3 for every member. Local rank 3 ↔ GPU 3 ↔ NIC 3 ↔ rail leaf 3 (assuming
`CUDA_VISIBLE_DEVICES` is not reordered and GPU i uses NIC i). Same argument for PP peers 19 + 64j.
Marking: 2 pts arithmetic, 1 pt for stating the two assumptions.

## 11.6 Timeout victim

Every rank blocks in the collective the faulty rank never joins; all healthy ranks time out at
roughly the same time, and whichever watchdog fires first logs first. The faulty rank may be dead (no
log), stuck elsewhere (its own collective has a *lower* sequence number), or in a different
collective (mismatch). Artifacts: (1) NCCL flight-recorder dumps per rank — find the rank whose last
`SeqNum` is lowest or whose op type differs; (2) `py-spy dump` stacks of all ranks; also accepted:
host kernel logs (Xid), scheduler/node events, the missing rank in the launcher's exit summary.

## 11.7 MFU vs recompute

No. MFU = 6ND/(GPUs × peak × step time) counts only model FLOPs. Full recompute adds ≈ 2ND of extra
forward FLOPs, so hardware FLOP/s utilization (HFU) can rise while the step gets longer. In the lab
model, K (full recompute) takes 22.17 s vs 17.45 s: MFU falls from 39.9 % to 31.4 %. Recompute is
worth it only if the memory it frees buys a faster layout (e.g., smaller TP or fewer pipeline stages).

## 11.8 Memory audit (TP 4, PP 4, DP 16, b = 2, ZeRO-1, selective)

```text
P = 70e9/(4×4) = 4.375e9
weights 2P = 8.75 GB; grads 2P = 8.75 GB; optimizer 12P/16 = 3.281 GB → states 20.78 GB
m = 1024/(16×2) = 32; in-flight on stage 0 = min(4, 32) = 4
activation/layer = 4096 × 2 × 8192 × 34 / 4 = 570.4 MB; layers/stage = 20
activations = 570.4 MB × 20 × 4 = 45.63 GB
total = 20.78 + 45.63 + 4.0 = 70.4 GB → fits 80 GB but EXCEEDS the 68 GB planning limit
```

Fix suggestions: b = 1 (activations 22.8 GB → total 47.6 GB), or full recompute, or PP = 8.
Common mistake: forgetting the in-flight factor (gives 11.4 GB activations and a false "comfortable").

## 11.9 Communication budget (baseline)

```text
TP: 4 × 2(7/8) × 67.1e6 × 20 × 128 = 1.2026e12 B; 10,240 × (391.5 µs + 10 µs) = 4.11 s (exposed 3.08 s)
DP: 2(7/8) × 4.375e9 = 7.656e9 B; /45e9 = 0.170 s (window 13.916/128 × 2/3 = 0.072 s → exposed 0.098 s)
PP: 2 × 128 × 67.1e6/8 = 2.147e9 B; /45e9 + 256 × 30 µs = 0.055 s (exposed 0.028 s)
```

Attack TP first: it is 18 % of the step and > 95 % of exposed communication. TP = 2:
V = 8 × (t − 1) × M × L × B/(W × b) = 8 × 1 × 67.1e6 × 80 × 1024/256 = **171.8 GB** (= 1.2026e12/7).
Identity: (L/p) × m = L × B/(p × d × b) = L × B × t/(W × b), so 2(t − 1)/t × t = 2(t − 1).

## 11.10 (O1) Three workloads

Model answers (accept others with correct memory proof and traffic accounting):

**(a) 1.3B, s = 2,048, B = 512, 64 GPUs → pure DP (DDP, or ZeRO-1), DP = 64.** Model state
16 × 1.3e9 = 20.8 GB per GPU fits. Assuming h ≈ 2,048 and 24 layers, activations ≈ 2048 × b × 2048 × 34
× 24 = 3.4 GB per sequence; 8 sequences per GPU per step as b = 4 with 2 accumulation steps → 13.7 GB;
total ≈ 38 GB. Traffic: one gradient all-reduce of 2.6 GB per GPU per step (2 × 63/64 × 2.6 GB ≈ 5.1 GB
sent), bucketed and overlapped; NCCL uses NVLink inside the node and all 8 rails between nodes.
Hierarchical model: 2(7/8) × 2.6/300 + 2(7/8) × (2.6/8)/45 ≈ 0.015 + 0.013 = 0.028 s against ≈ 0.26 s of
compute (6 × 1.3e9 × 1,048,576 / 64 / 4.945e14). TP or PP would add critical-path traffic for no memory
benefit.

**(b) W-TRAIN on 64 GPUs, B = 256 → TP = 8, PP = 4, DP = 2, ZeRO-1** (or TP 8/PP 8/DP 1, or TP 4/PP 8/DP 2).
P = 70e9/32 = 2.1875e9; states (2 + 2 + 12/2) × P = 21.9 GB; activations 11.4 GB (m = 128); total
37.3 GB. Traffic: TP 1.2 TB per GPU per step on NVLink (same per-GPU work as the baseline, compute
13.9 s); DP 2 × 1/2 × 4.375 GB = 4.4 GB over the GPU's rail (0.10 s); PP 2.15 GB on the same rail.
TP 4/PP 8/DP 2 variant: states 21.9 GB + 22.8 GB activations = 48.7 GB, TP bytes 515 GB.

**(c) 70B fine-tune, s = 65,536, B = 32, 32 GPUs → TP = 8, PP = 4, DP = 1 with full recompute** (or
TP 8 + CP 2–4 with distributed optimizer over CP and full recompute). Selective recompute is
impossible: s·h·34/8 = 65,536 × 8192 × 34/8 = 2.28 GB per layer per sequence × 20 layers × 4 in flight
= 182 GB. Full recompute stores 2·s·h/t = 134 MB per layer → 134 MB × 20 × 4 = 10.7 GB; states
2.1875e9 × 16 = 35 GB (DP = 1, nothing to shard over); total ≈ 50 GB. Traffic: M = 65,536 × 8192 × 2 =
1.07 GB per TP collective; 4 × 1.75 × 1.07 GB × 20 layers × 32 micro-batches = 4.8 TB per GPU per step on
NVLink, ≈ 7.2 TB with the recomputed forward's collectives (×1.5) — about 24 s at 300 GB/s. PP sends
2 × 32 × 134 MB = 8.6 GB per GPU per step over the rail. Bubble 3/35 = 8.6 %. Learners should also note
that attention FLOPs (≈ 12·L·h·s per token for the score/value matmuls) are comparable to 6N at this
length and are not in the 6ND estimate.

Marking (per case 5 pts): layout 1, memory proof 2, dominant traffic with bytes 1, link placement 1.

## 11.11 (O2) Step-time sensitivity

Ideal step 6.958 s; MFU = 6.958/step.

| Case | Arithmetic | Step (s) | MFU |
|---|---|---|---|
| Baseline | 13.916 + 0.326 + 3.083 + 0.098 + 0.028 | 17.45 | 39.9 % |
| (a) efficiency 0.55 | compute 13.916 × 0.50/0.55 = 12.651; bubble 0.297; DP window shrinks to 0.066 s → exposed DP 0.104; + 3.083 + 0.028 | 16.16 | 43.1 % |
| (b) TP overlap 60 % | exposed TP 4.111 × 0.40 = 1.644; 13.916 + 0.326 + 1.644 + 0.098 + 0.028 | 16.01 | 43.5 % |
| (c) one rank 8 % slower | everyone waits: + 0.08 × (13.916 + 0.326) = + 1.139 | 18.59 | 37.4 % |
| (d) DP time × 3 | exposed DP = 0.511 − 0.072 = 0.438 (+0.341) | 17.79 | 39.1 % |
| (e) (b) and (c) | 16.012 + 1.139 | 17.15 | 40.6 % |

Ranking of levers: TP overlap (−1.44 s) ≈ kernel efficiency (−1.29 s) > eliminating stragglers
(+1.14 s avoided; a *single* rank costs all 256 GPUs) > fabric congestion on DP (+0.34 s, because
almost all of the extra DP time is exposed). Expert answers note why (d) matters more than the DP share suggests: the overlap window is
fixed at ≈ 72 ms, so every extra millisecond of DP time beyond it lands on the critical path.

## 11.12 (O3) Failure-aware workflow

From `reliability_table` (verified by hand, e.g. √(2 × 45 × 172,800) = 3,944 s). MTBF = 1,536 node-h /
nodes (REFERENCE_CLUSTER canonical values):

| Scenario | τ_opt | Waste at τ_opt | Waste at 4 h | Failures/day | Lost s/failure | Lost GPU-h/failure | Lost GPU-h/day (failures only) |
|---|---|---|---|---|---|---|---|
| ORION-256 sync (C 45 s, R 900 s, MTBF 48 h) | 3,944 s (65.7 min) | 2.80 % | 5.0 % | 0.5 | 2,872 | 204 | 102 |
| ORION-256 async (C 5 s) | 1,315 s (21.9 min) | 1.28 % | 4.7 % | 0.5 | 1,557 | 111 | 55 |
| ORION-XL sync (C 45 s, R 900 s, MTBF 3 h) | 986 s (16.4 min) | 17.5 % | invalid (τ > MTBF) | 8 | 1,393 | 1,585 | 12,679 |
| ORION-XL async (C 5 s) | 329 s (5.5 min) | 11.4 % | invalid | 8 | 1,064 | 1,211 | 9,688 |

(For the XL 4-h case the tool returns NaN with `valid_at_4h = False`: the first-order formula assumes
τ ≪ MTBF, and only e^(−4/3) ≈ 26 % of 4-h intervals would finish without a failure.)

Waste at XL async decomposes as C/τ = 1.52 %, τ/(2·MTBF) = 1.52 %, R/MTBF = 8.33 %: **restart time
dominates**, so invest in R (a declared spare pool — a variation, since ORION has none — pre-pulled containers,
faster NCCL bootstrap, parallel sharded restore) and in MTBF (burn-in, proactive health checks that
drain suspect nodes before they fail). At 256 GPUs waste is 2.8 % (sync) vs 1.3 % (async): asynchronous
checkpointing roughly halves it and is worth doing; at XL scale it is necessary but not sufficient. Procedure: detect (watchdog timeout, rank exit,
step-time SLO), isolate (rank → host/GPU/NIC map; smallest failure domain), replace (drain; wait for repair or
restart at DP = 7 on ORION-256, which has no spares), restore (latest checkpoint whose metadata is durable and that passed a restore test),
validate (loss continuity within noise, step time within 2 % of baseline, no per-rank outliers),
with a retry policy: same node fails twice → quarantine; > 3 restarts/hour → stop and page.
Marking: numbers 8 pts, procedure 6, policy 3, investment argument 3.

## 11.13 Lab

See `solutions/lab/stepmodel.py` and the lab README rubric. Expected recommendation:
`D_tp4_pp8_dp8` (16.07 s, 43.3 % MFU, 38.8 GB).

## 11.14 Troubleshooting: the quiet 8 %

Ranks 96–103 = node index ⌊96/8⌋ = 12, i.e. `orion-n13` (one TP group; with r = tp + 8·dp + 64·pp, it is PP stage 1, DP
replica 4). Ranked hypotheses: (1) node-level power/thermal limit on `orion-n13` — all 8 GPUs equally
slow, compute only; (2) data imbalance — plausible, because all 8 TP ranks of a group process the same
micro-batches, so test it with per-rank token counts; (3) degraded NVLink on node
12 — would raise TP comm, which is unchanged, so rejected; (4) host CPU contention slowing kernel
launch — check CPU utilization. Discriminating tests: `nvidia-smi -q -d PERFORMANCE` (clock event
reasons: `SW Power Cap: Active`), `nvidia-smi -q -d POWER` (power limit, e.g. 500 W vs 700 W default),
`nvidia-smi --query-gpu=clocks.sm,power.draw,power.limit,temperature.gpu --format=csv` versus a peer
node; per-rank token counts identical to peers (rejects 2). Root cause: a power limit left in place
by the maintenance procedure on `orion-n13`. Safe fix: checkpoint, drain `orion-n13`, and either wait
for Fleet (fast if only a power limit) or restart at DP = 7 (224 GPUs, batch/LR adjusted) — ORION-256 has
no spares, and draining alone does not move a running job; the training job is not the place to change power policy; Fleet
restores the default power policy under change control and runs acceptance tests before returning
the node. Validation: step p50 back to 17.45 s, ranks 96–103 compute within 1 % of median, power
limit = default on the returned node. Expected step: 17.45 + 1.3 × 131/128 = 18.78 s (stem: 18.8 s).
Loss: 1 − 17.45/18.78 = 7.1 % of 256 GPUs × 24 h = **≈ 435 GPU-h per day**. Common mistake: blaming the fabric because "everyone is waiting in collectives".

## 11.15 Design challenge: 8k sequences

With `seq_len: 8192`, `global_batch_seqs: 512` in `model_wtrain.yaml` (tool output, `[MODELED]`):

| Layout (b = 1, ZeRO-1, selective) | Mem stage 0 | Bubble | Step | MFU |
|---|---|---|---|---|
| TP 8 / PP 4 / DP 8 | 38.8 GB | 4.5 % | 17.66 s | 39.4 % |
| TP 8 / PP 2 / DP 16 | 47.6 GB | 3.0 % | 17.48 s | 39.8 % |
| TP 4 / PP 8 / DP 8 | 61.7 GB | 9.9 % | 16.79 s | 41.4 % |
| TP 8 / PP 8 / DP 4 | 34.5 GB | 5.2 % | 17.77 s | 39.1 % |

A strong answer picks TP 4/PP 8 only if it also argues that 6 GB of headroom is acceptable (with an
allocator-statistics test) — or picks TP 8/PP 2 as the safer choice, giving up ≈ 4 % throughput for
20 GB more headroom. Either is acceptable with the trade-off stated. Bonus: noting that attention
FLOPs grow with s and are not in 6ND, so all step times are optimistic by a similar factor.

## 11.16–11.19 Reflection (marking guidance)

- 11.16: kernel efficiency (profile a step: achieved TFLOP/s of the GEMMs), TP overlap fraction
  (Nsight Systems trace: NCCL kernels concurrent with compute), effective NVLink/rail busbw at the real
  message sizes (nccl-tests, Chapter 12).
- 11.17: the overlap window for DP is only the last micro-batch's backward (see 11.11 d); stragglers
  and jitter make the all-reduce wait for the slowest rank; FP32 gradient reduction doubles bytes;
  congestion from other jobs sharing spines.
- 11.18: peak (not steady) allocation, fragmentation, longer sequences or batch-size changes later,
  checkpoint/eval code paths with extra buffers; require allocator peak stats over ≥ 200 steps plus
  an eval and a checkpoint, and ≥ 15 % headroom.
- 11.19: infant mortality after maintenance, correlated failures (a rack PDU, a spine), or
  wear-out; failure rates are bursty → shorten τ after maintenance and around known-risky events;
  use per-period MTBF.

## 11.20 Fault-isolation tabletop

Rank map: `orionxl-n312` GPU 5 → rank 8 × (312 − 1) + 5 = **2493** (node ranks 2488–2495); `orionxl-n141` NIC 2 → GPU 2
→ rank 8 × 140 + 2 = **1122** (node ranks 1120–1127), rail 2. Timeline: 01:00 NIC 2 flaps begin → 01:05 step +6 %
(straggler on rank 1122's DP/PP paths) → 02:58 uncorrectable ECC on `orionxl-n312` GPU 5 → ≈ 03:02–03:08
process on rank 2493 dies or wedges → 03:12 watchdog timeout (≈ 10 min default) on healthy ranks.
Most likely cause of the timeout: the ECC fault (fatal to the process; a timeout follows one timeout
period later). The flapping NIC is **correlated but separate**: the job ran 2 h with it (degraded,
not hung). Health decisions: drain `orionxl-n312` (smallest *schedulable* domain for a TP = 8 job is the node;
the GPU itself goes to Fleet for reset/row-remap/RMA triage); drain `orionxl-n141` and open a Fabric ticket
for NIC 2's port/optic/cable (Chapter 10). Restart: last checkpoint whose write completed and was
validated before 02:58 (conservative; ECC events can precede the crash), two nodes from a declared ORION-XL spare pool (a variation from the reference cluster) or a
shrunken DP, same rank map. Validation: loss within noise of pre-incident trend, step time back to pre-01:05 baseline,
no per-rank outliers, NIC counters clean on the replacement. Proof (vs correlation): flight-recorder dumps
show rank 2493 missing from / behind in the collective that timed out, and the Xid timestamp precedes
it; the NIC flaps cannot explain a missing rank.
