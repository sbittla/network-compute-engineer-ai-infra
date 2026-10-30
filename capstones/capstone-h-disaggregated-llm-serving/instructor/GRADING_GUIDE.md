# Capstone H — Instructor Grading Guide (INSTRUCTOR ONLY)

Removed from student releases. Reference: [reference/serve.py](reference/serve.py). Exemplar:
[EXEMPLAR.md](EXEMPLAR.md).

## 1. Verifying the kit

```bash
cd capstones/capstone-h-disaggregated-llm-serving/starter-kit
python check.py --impl solution     # 11/11 PASS, exit 0, ≈ 4 s
python check.py                     # 1/11 PASS (dataset), 10 TODO, exit 1
python ../../../scripts/validate_labs.py capstone-h
```

## 2. Planted features

| # | Planted | Correct handling | Teaches |
|---|---|---|---|
| P1 | Burst: 2.5× rate for 120–150 s | Without admission TTFT p95 = 9.49 s for every candidate; admission sheds ≈ 7 % and restores 0.57 s | Capacity for the mean is not capacity for the burst; shedding is part of the design |
| P2 | 1 % of prompts are 32,768 tokens | Prefill 1.52 s each; attention is 23 % of their FLOPs; separate TTFT SLO; head-of-line blocking at small P | Long-context tail drives TTFT and transfer max |
| P3 | `rdma-400g-x8-vendor-sheet` row in GB/s | Reject: 3,200 Gb/s per NIC exceeds PCIe Gen5 x16 (504 Gb/s) | Unit hygiene; sanity bounds from the host side |
| P4 | QoS proposal maps KV to DSCP 26 / TC 3 (training's lossless class) and sends KV unencrypted across a tenant boundary | Three findings; KV gets its own DSCP and TC (with ECN), encryption or a separate trust domain | A bulk new flow in the training lossless class can trigger PFC pauses that slow training |
| P5 | TCP looks identical to RDMA in mean metrics | Second-token gap with TCP (30 GB/s), not pipelined: p95 81 ms, max 393 ms; with Chapter 15's TCP profile (12.5 GB/s): p95 162 ms, max 894 ms — beyond the 100 ms ITL budget, while TPOT and ITL p99 barely move (one gap per request) | Compare gap distributions against the ITL budget, not means |
| P7 | Decode-side fan-in | Each decode instance receives KV ÷ D: at 5P2D 95 Gb/s = 40 % of the TCP pair; at 5P1D 79 % (network becomes the bottleneck); with the Chapter 15 profile 95 % | Size the receiver; the simulator does not model link contention, so this comes from the model |
| P6 | Hypothetical accelerator classes | Accept as a sensitivity analysis only; say so | Don't launder made-up hardware into a recommendation |

## 3. Expected numbers (reference solution)

| Item | Value | Class |
|---|---|---|
| KV per token / 2k / 32k | 327,680 B / 0.671 GB / 10.7 GB | MODELED |
| Prefill 2k / 32k | 73.9 ms / 1.52 s | MODELED |
| Decode step B = 256, ctx 2,600 | 23.1 ms | MODELED |
| KV capacity per instance | 1,330,566 tokens | MODELED |
| Mean prefill per request (trace) | 0.0910 s | MODELED |
| Sizing at 30 req/s (H100, ρ 0.7) | P = 4, D = 1 (40 GPUs); B = 491 at 33.5 ms/step; 14,675 tok/s per decode instance; KV 23.8 GB/s | MODELED |
| Utilisation, 5P2D at 30 req/s | prefill 0.55, decode 0.29; network egress per prefill 0.013 (RDMA) / 0.16 (TCP); **fan-in per decode 0.033 (RDMA) / 0.40 (TCP)** → **prefill-bound**. 5P1D over TCP: fan-in 0.79 → **network-bound**. Chapter 15 TCP profile at 5P2D: fan-in 0.95 → network-bound | MODELED |
| Model vs simulation (first 115 s, same window on both sides) | 0.551 vs 0.554 (< 1 %) | MODELED vs SIMULATED |
| Speculative α 0.8, k 4, c 0.1 | Memory-bound (small batch) model: 3.36 tokens/step, 2.40×; best k 6 (α 0.8), 3 (α 0.6), 8 (α 0.9, c 0.05). **At the operating point B = 491** (decode MFU 0.6 `[ILLUSTRATIVE]`): plain step 33.5 ms, verification 76.4 ms (compute-bound: 2 × 70 × 10⁹ × 491 × 5 = 3.44 × 10¹⁴ FLOP) → **1.25×**; k = 1 gives 1.64×, k = 6 only 1.05×. At decode MFU 0.5 (same as prefill): k = 4 → 1.08×, k = 2 → 1.30×, k = 1 → 1.43× | MODELED |

Simulation results `[SIMULATED]` on the full trace. TPOT is the per-request mean (p95 across
requests); ITL is the per-token gap distribution (p99 across tokens, including disaggregated
second-token gaps). SLOs: TTFT p95 ≤ 0.8 s, TPOT p95 ≤ 50 ms, ITL p99 ≤ 100 ms, ≤ 10 % shed.

| Candidate | GPUs | TTFT p95 | TPOT p95 | ITL p99 | Rejected | Output tok/s | $/M tokens | Verdict |
|---|---|---|---|---|---|---|---|---|
| Colocated × 7 | 56 | 4.87 s | 119 ms | 257 ms | 0 | 9,526 | — | fails TTFT, TPOT, ITL |
| Colocated × 7, chunk 512 (fused) | 56 | 6.04 s | 23.0 ms | 31 ms | 0 | 9,641 | — | fails TTFT (burst, no admission) |
| Colocated × 7, chunk 512 + reference admission | 56 | 5.52 s | 23.0 ms | 31 ms | 0.4 % | 9,597 | 6.48 | fails TTFT |
| Colocated × 7, chunk 1,024 + reference admission | 56 | 2.50 s | 37.7 ms | 58 ms | 0.4 % | 9,586 | 6.49 | TPOT and ITL pass; TTFT fails — the policy assumes dedicated prefill and under-predicts shared queueing |
| Colocated × 10 | 80 | 0.89 s | 110 ms | 238 ms | 0 | 9,538 | — | fails TPOT, ITL |
| 5P2D RDMA, no admission | 56 | 9.49 s | 18.3 ms | 19 ms | 0 | 9,625 | — | fails TTFT |
| **5P2D RDMA + admission** | 56 | 0.57 s | 17.6 ms | 18 ms | 7.1 % | 8,940 | 6.96 | **passes all** |
| 5P1D RDMA + admission | 48 | 0.57 s | 32.8 ms | 35 ms | 7.1 % | 8,905 | 5.99 | passes; no decode N+1 |
| 4P1D RDMA + admission | 40 | 0.60 s | 25.0 ms | 26 ms | 11.6 % | 8,476 | 5.24 | fails shedding |
| 4P1D hypothetical hetero + admission | 40 | 0.55 s | 20.6 ms | 21 ms | 4.4 % | 9,241 | 4.16 | passes (hypothetical hardware) |
| Low load (≈ 5.8 req/s): colocated × 2 | 16 | 0.15 s | 42 ms | 157 ms | 0 | 1,623 | — | **fails ITL** although TPOT passes |
| Low load: colocated × 2, chunk 1,024 | 16 | 0.16 s | 25 ms | 50 ms | 0 | 1,627 | — | passes |
| Low load: 1P1D | 16 | 1.50 s | 13.5 ms | 14 ms | 0 | 1,630 | — | fails TTFT (head-of-line behind 32k prompts) |

Second-token gap (exposed KV + decode-slot wait + first decode step), 5P2D + admission: RDMA p95
30 ms (max 37 ms); TCP pair, not pipelined, p95 81 ms (max 393 ms); Chapter 15 TCP profile, not
pipelined, p95 162 ms (max 894 ms) — beyond the 100 ms ITL budget. These gaps are one per request
(≈ 0.35 % of tokens), so they do not move ITL p99; report them separately.

Cost arithmetic (5P2D): 56 × $4.00 = $224/h; 224 / (8,940 × 3,600) × 10⁶ = $6.96 per million
output tokens `[MODELED from SIMULATED throughput, ILLUSTRATIVE prices]`.

## 4. Rubric interpretation

| Dimension | Weight | 9–10 | 7–8 | 5–6 | < 5 |
|---|---|---|---|---|---|
| Problem framing and assumptions | 10 | Efficiencies, prompt mix, burst, SLOs, hypothetical hardware all stated | Most | Implicit | — |
| Architecture and technical correctness | 20 | Correct KV/roofline arithmetic, pipelining, QoS mechanism, GDR prerequisites | One slip | KV size wrong by GQA factor (×8) | Multiple errors |
| Implementation / reproducibility | 15 | 11/11, scripted comparisons | 11/11 | 8–10 | < 8 |
| Measurement and analysis | 20 | Bottleneck with all utilisations; model vs sim; two loads; ITL p95/p99 reported separately from TPOT; second-token gaps vs the ITL budget | Bottleneck only | Means only | Unlabelled |
| Reliability, security and operations | 15 | Failure table, N+1 decode, shedding policy, KV encryption/isolation | Partial | Generic | — |
| Troubleshooting and engineering judgment | 10 | "When it hurts" with evidence; rejects 5P1D on availability or justifies it | Qualitative | Pro-disaggregation by default | — |
| Communication and portfolio quality | 10 | Memo approvable as written | Clear | Long | — |

## 5. Common failure patterns

1. KV size computed with 64 query heads instead of 8 KV heads (8× too large).
2. Using 400 Gb/s as 400 GB/s (P3) — or not noticing the vendor-sheet row.
3. Sizing the network on the prefill (sender) side only. Fan-in at the decode side is 2.5× higher at 5P2D and decides TCP feasibility.
4. Comparing RDMA and TCP by mean TPOT and concluding "no difference" (P5).
5. Dismissing chunked-prefill colocation. With a fused iteration it meets TPOT; its TTFT failure here comes from the burst and from an admission policy built for dedicated prefill. Credit students who design chunk-aware admission or argue it as Chapter 15 does.
6. Recommending 5P1D purely on cost without addressing a single decode instance as a failure domain
   for 99.9 % availability.
7. Treating hypothetical accelerator results as a purchase recommendation.
8. Proposing to put KV in TC 3 "because RoCE needs lossless".
9. Speculative decoding speedup applied at large batch without discussing that verification is no
   longer nearly free when decode is no longer purely memory-bound.

## 6. Oral questions

1. Why is the KV emission rate of a prefill node bounded by its compute? Derive the 74 Gb/s.
2. Your decode pool loses one of two instances. What happens to the sequences it held?
3. At what prompt length and rate would TCP become the bottleneck in this design?
4. Where does chunked prefill sit between colocated and disaggregated, and why did it fail here?
5. What would you measure first on real hardware to de-risk the recommendation?
