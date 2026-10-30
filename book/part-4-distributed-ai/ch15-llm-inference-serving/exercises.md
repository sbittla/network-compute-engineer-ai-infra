# Chapter 15 — Exercises

Tags: difficulty ★ foundational, ★★ intermediate, ★★★ advanced. Tier: L1 laptop/simulation,
L2 single GPU host, L3 multi-node with RDMA. Use the ORION/W-INFER values from
`docs/REFERENCE_CLUSTER.md` unless an exercise changes one explicitly. Label every number you
produce `[MODELED]`, `[SIMULATED]`, `[MEASURED]` or `[ILLUSTRATIVE]`.

---

## A. Knowledge checks

**K1. ★ L1 — Why decode is memory-bound.** In three or four sentences, explain why a decode step
for W-INFER at batch 32 is HBM-bandwidth-bound while a 2,048-token prefill is compute-bound.
Use arithmetic intensity and the H100-class BF16 ridge point.
*Evidence required:* both intensities (approximate is fine) compared with the ridge in FLOP/B.

**K2. ★ L1 — Latency metrics.** Define TTFT, TPOT and ITL. Give one failure that is visible in
ITL p99 but almost invisible in mean TPOT.
*Evidence required:* the three definitions as formulas over request timestamps, plus the failure
and the reason it averages away.

**K3. ★ L1 — Paged KV cache.** What problem does PagedAttention solve, and what new failure mode
does on-demand block allocation introduce?
*Evidence required:* the fragmentation/over-reservation mechanism, and preemption (recompute or
swap) with its cost.

**K4. ★ L1 — Batching.** Contrast static, dynamic and continuous batching for generation. Why
does continuous batching create prefill-decode interference?
*Evidence required:* one sentence per strategy, plus the interference mechanism in terms of
iterations.

**K5. ★ L1 — Goodput.** Define goodput as DistServe uses it, and as an operational per-trace
metric. Why can goodput fall while throughput rises?
*Evidence required:* both definitions and a concrete scenario.

**K6. ★ L1 — GQA.** W-INFER has 64 query heads and 8 KV heads. Compute the KV bytes per token
with and without GQA, and explain the effect on maximum concurrency.
*Evidence required:* both byte counts with the formula.

**K7. ★★ L1 — GPU utilization.** Why does `nvidia-smi` utilization at 100 % not show that a
decode replica is saturated? Name two better signals.
*Evidence required:* what the utilization counter measures, and two alternative signals with the
reason each is better.

**K8. ★★ L1 — Recompute vs swap.** For a preempted 10k-token sequence on a TP = 2 FP8 replica,
estimate the cost of recompute vs swap.
*Evidence required:* both estimates with stated assumptions (prefill µs/token; PCIe GB/s).

---

## B. Worked problems

**W1. ★★ L1 — Capacity of an alternative layout.** Halcyon AI considers a long-context tier: one
TP = 8 replica per HX8 with **FP8 weights (70 GB) and FP8 KV cache**, `memory_fraction` 0.90,
2 GB reserve per GPU, 16-token blocks.
(a) Compute the KV budget, the number of blocks, and the maximum number of concurrent 8,192-token
sequences. (b) Repeat with BF16 KV. (c) Compute the decode-step lower bound and the planning value
(efficiency 0.70, overhead 3 ms) at B = 64 with an average context of 6,000 tokens (FP8 KV), and
the resulting tokens/s.
*Evidence required:* every formula, substituted values and results with units. Lab Part A
functions may be used to check your arithmetic.

**W2. ★★ L1 — Sizing a shared pool with Little's law.** A document-QA product sends 25 req/s with
4,096-token prompts and 512-token outputs to T-tp4-fp8 replicas (same assumptions as Section 15.12). The
SLOs are TTFT p95 ≤ 800 ms and TPOT p95 ≤ 50 ms; plan for mean TPOT ≤ 35 ms.
(a) Compute prefill time and prefill demand in replica-seconds per second. (b) For 6, 8, 10 and 12
shared replicas, compute ρ_prefill, mean TTFT, mean TPOT and decode batch. Identify any
configuration that is unstable. (c) Pick a pool size and state the worst-case ITL. (d) Check KV
capacity at full sequence length.
*Evidence required:* a table for (b), the fixed-point derivation for one row, and the choice with
justification.

---

## C. Hands-on lab

**L1. ★★ L1 — Lab 15: capacity model, serving-trace analyzer, disaggregation model.** Complete
[lab/README.md](lab/README.md) Tasks 1–10.
*Evidence required:* `python check.py` output with 18/18 PASS, and the two-page report described
in lab Section 8.

---

## D. Troubleshooting case

**T1. ★★★ L1 (tabletop) — Token-2 stall in the disaggregated pool.** Halcyon AI runs W-INFER
disaggregated (6 prefill + 2 decode TP = 4 replicas; the decode replicas are on GPUs 0–3 of
`orion-n27` and `orion-n28`, nodes of the Kubernetes inference partition orion-n25–n32, so W-TRAIN is not
running at full size), with KV transfer over RoCEv2 on the backend rails. Every weekday
from about 14:00 to 15:30, the second-token latency (the first ITL gap) p99 climbs from 24 ms to
180 ms. TTFT and mean TPOT barely move, and the decode pool's KV usage is
normal. You have the following evidence `[ILLUSTRATIVE]`:

| Signal (decode-node rail ports) | 13:00–14:00 | 14:00–15:30 |
|---|---|---|
| RX throughput per decode node, sum of its rails 0–3 (Gb/s, 1 min avg) | 108 | 330 |
| ECN-marked packets/s (`orion-be-leaf-r0`–`r3` egress to decode NICs) | 40 | 31,000 |
| PFC pause frames received by decode NICs (per s) | 0 | 1,900 |
| KV transfer time p99 | 4.3 ms | 160 ms |
| Inference request rate | 39 req/s | 41 req/s |

The Slurm calendar shows a recurring 64-GPU fine-tuning job from 14:00 to 15:30. You do not know
which nodes it runs on.
(a) Walk the diagnostic loop: list ranked hypotheses, the discriminating test for each, and the
evidence you would still need. (b) Propose a safe immediate mitigation and a structural fix.
(c) State how you would validate the fix.
*Evidence required:* ranked hypotheses with for/against evidence, at least two discriminating
tests with real commands or data sources, a mitigation that touches no shared fabric
configuration without change control, and a validation criterion with numbers.

---

## E. Design challenge

**D1. ★★★ L1 — RAG serving tier.** Design the serving tier for a retrieval-augmented assistant.
It must handle 20 req/s at peak with 8,192-token prompts (retrieved context) and 300-token
outputs. The SLOs are TTFT p95 ≤ 1.5 s and TPOT p95 ≤ 40 ms. Use T-tp4-fp8 replicas, and include
the quadratic attention term in prefill.
Decide between a shared pool (with or without chunked prefill) and disaggregated serving. Size
the pools and choose a transport. Give the KV-transfer network budget, the QoS and isolation
design, and the failure behaviour (what happens when a decode replica dies). State three
measurements you would take at L2/L3 before committing.
*Evidence required:* a sizing table with ρ, TTFT, TPOT and batch per pool, the network budget in
Gb/s with the arithmetic, a transport decision with numbers, a failure table, and an explicit
MODELED/MEASURED labelling of every number.

---

## F. Outline-mandated exercises

**O1. ★★ L1 — Memory demand vs batch, sequence length and concurrency.** Using Lab Part A, fill
in a table of total memory demand (weights + KV) for T-tp4-fp8 at batch 16, 64 and 128 and
sequence lengths 1k, 4k and 16k. Mark every cell that exceeds the 288 GB usable HBM, and state
the maximum concurrent sequences per sequence length. Explain in two sentences which variable
dominates as context grows.
*Evidence required:* the 3 × 3 table, the max-sequence row, and the explanation.

**O2. ★★ L1 — Analyze a serving trace.** Using Lab Part B on `lab/data/`, report TTFT, ITL,
throughput (req/s and output tokens/s), queue time, and GPU utilization (`gpu_busy_pct`) for the
baseline (< 230 s) and for each detected episode. Explain why GPU utilization is the least
informative of these.
*Evidence required:* a table with each metric for the baseline and each episode, and the
explanation.

**O3. ★★ L1 — Compare two serving configurations.** Using Lab Part A's `compare_serving_configs`,
recommend one configuration for a latency-sensitive objective and another for a
throughput-oriented objective. Then name the operating condition (load, context length, or SLO)
under which each recommendation would flip.
*Evidence required:* the comparison table, both recommendations with numbers, and the flip
conditions.

**O4. ★★★ L1 — Prompt workload split across prefill and decode pools (Section 20.2).** Change the
disaggregation workload to **10 req/s with 8,192-token prompts** (256-token outputs). Estimate the
KV bytes per request, the aggregate transfer bandwidth at that rate, and the per-request transfer
time over RDMA and TCP (lab assumptions). Compare a shared-pool design with disaggregated serving
over RDMA and TCP. Then discuss per-layer streaming overlap: can TCP hide the transfer if its
link is uncontended? Repeat the bandwidth estimate with FP8 KV.
*Evidence required:* KV bytes, Gb/s, transfer times, a three-row comparison, the overlap
calculation per layer, and a statement of which values are modeled and which would need L3
measurement.

**O5. ★★ L1 — Speculative decoding trade-off.** For α ∈ {0.6, 0.8, 0.9} and k ∈ {2, 4, 8}, with a
draft cost of 0.05, compute expected tokens per step and speedup. First assume memory-bound
verification (cost 1). Then derive the verification cost at B = 128 on T-tp4-fp8 from the
roofline for each k (compute time of B × (k + 1) tokens vs the 20.2 ms decode step) and repeat. Recommend k for
an interactive tier and decide whether to enable speculation on the throughput tier.
*Evidence required:* two 3 × 3 tables and the recommendation with its reasoning.

---

## G. Reflection and review

**R1. ★ L1.** Which three assumptions in the lab's capacity model would you most want to measure
on real hardware, and why those three?
*Evidence required:* three named parameters, the output each one drives, and the L2/L3
measurement that would replace it.

**R2. ★★ L1.** The lab trace's ITL percentiles come from a 5 % sample of requests. What can and
cannot be concluded from that sample's p99.9?
*Evidence required:* the sample size in requests and gaps, the correlation argument, and one
better instrument.

**R3. ★★ L1.** The worked example recommends a shared pool with chunked prefill over
disaggregation. Which observed change in production traffic should trigger re-evaluation, and
what metric would show it first?
*Evidence required:* the traffic change, the leading metric, and the threshold you would set.

**R4. ★★ L1.** What evidence would you need before claiming that FP8 KV caching is safe for the
long-context tenant?
*Evidence required:* at least three distinct pieces of evidence (offline evaluation at real
context length, canary signal, engine support), each with its acceptance criterion.

---

## H. Chapter deliverable

**DEL. ★★★ L1 (L2 optional) — Inference capacity model and tuning recommendation.** Submit the
completed lab module (Parts A–C) and a recommendation memo of at most two pages for W-INFER on
ORION. The memo must cover: the chosen replica layout and pool size for the 40 req/s launch, the
latency and throughput tiers, a disaggregation decision with network budget, phase-specific SLOs
and alert thresholds, and a validation plan listing the L2/L3 measurements and the manifest fields
to record.
*Evidence required:* the checker at 18/18, every number labelled, and the validation plan with
the commands from lab Section 9.
