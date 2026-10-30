# Editorial Review — Capstone H: Disaggregated LLM Serving

**Independent score history:** 8.68 → 9.28 → 9.50 (iterations 1 → 2 → 3; PASS at iteration 3, 2026-10-30).

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Author self-review, iteration 1 | 2026-10-29 | Author | 8.95 | FAIL |
| Author self-review, iteration 2 | 2026-10-29 | Author | 9.48 | FAIL (marginal: 0.02 below gate) |

## Scores by dimension (latest — iteration 2)

| Dim | Weight | Score | Justification |
|---|---|---|---|
| D1 Technical accuracy | 20 % | 9.5 | KV arithmetic from GQA dimensions; roofline with attention term; transfer exposure; path-MTU and GDR-evidence statements aligned with docs/VERIFIED_FACTS.md; perftest/iperf3 flags checked. |
| D2 Depth and production realism | 15 % | 9.5 | Burst shedding, long-context head-of-line blocking, chunked-prefill trade-off, compute-bounded KV emission, QoS interaction with training's lossless class, N+1 decode. |
| D3 Pedagogy and clarity | 15 % | 9.5 | Figures H.1/H.2; worked numbers with every step; "facts you must get right". |
| D4 Hands-on lab quality | 15 % | 9.5 | Given simulator + 11 checks incl. model-vs-simulation agreement and admission under burst; ≈ 4 s; generator SKIP rule honoured. |
| D5 Assessment assets | 10 % | 9.5 | Templates for all eight outline outputs plus the nine common sections; full expected-results table. |
| D6 Evidence labelling | 10 % | 9.5 | MODELED vs SIMULATED separated in every table; hypothetical hardware flagged. |
| D7 Cross-layer integration | 5 % | 9.5 | GPU roofline, PCIe/NIC path, fabric QoS, scheduler admission and cost joined. |
| D8 Operational realism and safety | 5 % | 9.5 | Lab-only floods; QoS risk to training called out. |
| D9 Editorial polish | 5 % | 9.0 | Dense tables. |

Weighted: 0.95 × 9.5 + 0.05 × 9.0 = **9.475** (reported 9.48). Lowest: D9 9.0. Not rounded up: the internal gate needs ≥ 9.5, so an editorial polish pass on table density (D9) is the outstanding item.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| H-01 | major | README §9 | Network share of backend line rate mis-stated (2.6 %). | Recomputed: 74 / 3,200 Gb/s = 2.3 %. |
| H-02 | major | sim | Initial colocated loop could stall when instances drifted apart in time. | Rewritten as per-instance simulation after join-shortest-queue dispatch. |
| H-03 | major | analysis | RDMA vs TCP looked identical in means. | Added `layer_pipelined` switch and `kv_exposed_s` distribution; documented as P5. |
| H-04 | minor | check.py | Generator check must SKIP in student release. | Implemented. |
| H-05 | minor | README | Inference partition size vs candidate deployments. | Declared ORION variation (up to 8 nodes). |

## Release-gate items outstanding

- L2 calibration of MFU/HBM efficiency and L3 per-rail GDR measurements not executed.
- Verify serving-stack disaggregation features and perftest `--use_cuda` syntax against current releases.
- External review by an inference-infrastructure engineer.

## Independent review iteration 1 + author fixes (2026-10-30)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Independent review, iteration 1 | 2026-10-30 | Independent reviewer | 8.68 | FAIL (major findings) |
| Author fixes, iteration 3 | 2026-10-30 | Author | 9.50 (self-assessed; awaiting re-review) | PASS (internal, pending) |

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R-01 | major | `utilizations`, docs | Network load was sized on the sender side only. | Returns `network_out` and `network_in` (fan-in = KV ÷ D) and gates on the maximum. 5P2D TCP fan-in is 0.40; 5P1D TCP is 0.79 (network-bound). The checker asserts both. |
| R-02 | major | README §9 | Not reconciled with Chapter 15. | Added a "Relation to Chapter 15" box (workload, TP/precision, link efficiency) and the Chapter 15 TCP profile `tcp-200g-x1-ch15`. Its fan-in of 0.95 reproduces the chapter's "TCP infeasible" verdict; the burst and 32k tail are explained. |
| R-03 | major | simulator, verdict | Chunked prefill was modelled serially. | A fused iteration now costs max(chunk compute, decode memory) + overhead. Chunked colocation meets TPOT (23–38 ms). The verdict is softened: its TTFT failure comes from the burst and from an admission policy built for dedicated prefill. Admission is now supported in colocated mode. |
| R-04 | major | speculative decoding | 2.40× is wrong at B ≈ 491. | Added `speculative_gain_at_batch` (max(compute, memory)). At the operating point it gives 1.25× (k = 4) and 1.64× (k = 1); it is checked, and it reduces to the simple model at batch 1. |
| R-05 | major | exemplar QoS | The KV class did not say whether it is lossless or lossy. | Specified a lossy ECN class with DWRR share, marking thresholds, DCQCN, go-back-N cost per VERIFIED_FACTS and a short QP ACK timeout; the lossless alternative was costed and rejected. |
| R-06 | minor | README §9 | "218 GB" was ambiguous. | Now stated as 218 GB of KV out of 358 GB total per step. |
| R-07 | minor | exemplar | "Below ≈ 10 req/s" was unsupported. | Dropped; only the 2-node, 5.8 req/s evidence is claimed, and a sweep is listed as next work. |
| R-08 | minor | checker | Model and simulation were compared over different windows. | The simulator reports `prefill_window`; the comparison is 0.551 vs 0.554 over the same 115 s, with a 5 % tolerance. |

Validation after fixes: `python scripts/validate_labs.py capstone-h` — solution pass, starter fails gracefully, no-generator pass, docs ok.

## Independent review iteration 2 + author fixes (2026-10-30)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| Independent review, iteration 2 | 2026-10-30 | Independent reviewer | 9.28 (FAIL, one major) | FAIL |
| Author fixes, iteration 4 | 2026-10-30 | Author | 9.50 (self-assessed; awaiting re-review) | PASS (internal, pending) |

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R-09 | major | simulator, checker, README, guide, exemplar | No ITL reported; TPOT means hide stalls and second-token gaps. | The simulator records per-token gaps (decode steps weighted by batch, fused or stretched colocated iterations, and second-token gaps) and `summarize()` reports ITL p50/p95/p99 plus second-token gap p95/max. Added an ITL p99 ≤ 100 ms SLO, checked in T5. Verdict table re-run with an ITL column: unchunked colocation fails ITL (257 ms; at low load 157 ms although TPOT passes); fused chunks meet ITL (31–58 ms); Chapter 15 TCP second-token gap p95 is 162 ms, beyond the budget. Text relabelled (TPOT vs ITL). |
| R-10 | minor | README §2 | Didn't follow the canonical split. | Rewritten: inference is n25–n32 (rack-07–08); 5P2D uses 7 of its 8 nodes, 5P1D 6, colocated × 7 uses 7; colocated × 10 is flagged as exceeding the partition. |
| R-11 | minor | README §7, guide, exemplar | Decode MFU 0.6 was unjustified. | Labelled `[ILLUSTRATIVE]` with a rationale (large-batch GEMM vs long-sequence attention) and speedups at 0.5 shown: k = 4 1.08×, k = 2 1.30×, k = 1 1.43×. |
| Rec | — | exemplar | Recommendation framing. | Kept 5P2D + admission as the recommendation; chunked colocation presented as co-finalist ($6.49 vs $6.96 per M tokens), with the flip condition: chunk-aware admission reaching TTFT p95 ≤ 0.8 s under the burst with ITL p99 ≤ 100 ms and ≤ 10 % shed. |

Validation after fixes: `python scripts/validate_labs.py capstone-h`: solution pass, starter fails gracefully, no-generator pass, docs ok.

## Independent review iteration 3 (2026-10-30): PASS 9.50

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| R-12 | minor | README §2 SLO line | Second-token gap was described as part of ITL p99, which dilutes it. | Listed second-token gap p95 ≤ 100 ms as its own SLI, explained why, aligned the template and starter README with the checker (which already gates on it). |
