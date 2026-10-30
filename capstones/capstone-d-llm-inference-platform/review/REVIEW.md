# Editorial Review — Capstone D

**Independent score history:** iteration 1 = 9.23 (fail) → iteration 2 = 9.50 (pass). Author iteration 3 fixes
(below) address the iteration-2 findings; awaiting independent re-review.


| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.025 | Not met (findings open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.475 | Not met: weighted score just under 9.5 (see note) |

Scored against [docs/EDITORIAL_RUBRIC.md](../../../docs/EDITORIAL_RUBRIC.md), reading D5 as "templates,
milestones and grading assets" for a capstone. The checker was validated with
`python scripts/validate_labs.py capstone-d`: the solution passes, the starter fails gracefully, and the data
regenerates byte-identically.

## Scores by dimension (latest)

| Dim | Weight | Iteration 1 | Iteration 2 |
|---|---|---|---|
| D1 | 20% | 9.0 | 9.5 |
| D2 | 15% | 9.0 | 9.5 |
| D3 | 15% | 9.0 | 9.5 |
| D4 | 15% | 9.0 | 9.5 |
| D5 | 10% | 9.0 | 9.5 |
| D6 | 10% | 9.0 | 9.5 |
| D7 | 5% | 9.0 | 9.0 |
| D8 | 5% | 9.5 | 9.5 |
| D9 | 5% | 9.0 | 9.5 |

Note: D7 stays at 9.0. The ties to ORION and to Chapters 15, 18, 20 and 21 are explicit, but the network leg of the request path (frontend fabric) is only named in the templates, not quantified.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| D-1 | blocker | trace, configs | The first trace (14 req/s) and 8,192-token chunks saturated every configuration, so the comparisons meant nothing | Trace at ~5 req/s per node; 2,048-token chunk budget; load sweeps document the knee |
| D-2 | major | check 05 | The preemption test config left no room for the weights | gpu_memory_utilization 0.2693 leaves ~1,074 KV tokens, so preemption is exercised |
| D-3 | major | README, GRADING | The planted 'better throughput, TTFT violated' trap had to exist in the data | Shown by c3 at 2.0x (2,766 tok/s per node, TTFT p95 1.01 s) and by c2 vs c1 at 2.0x (equal throughput, TPOT 181 ms) |
| D-4 | minor | EXEMPLAR | Fleet-sizing arithmetic | Re-derived: 40/(4.9 x 2.5) = 3.3 -> 4 + 1; RAG 0.8 x 1.1 s ~ 0.9 replica; 48 GPUs = $105.6/h, $162/h after 0.65 utilization |

All findings above are resolved. No blocker or major finding is open.

## Release-gate items outstanding

- The L2/L3 procedures in `starter-kit/README.md` have not been run on hardware. Every hardware-facing
  number remains `[MODELED]`, `[SIMULATED]` or `[VENDOR-SPEC, 2026-10]`.
- External review by a practising GPU-cluster/network engineer (and, for Capstone A, a facilities
  specialist), per docs/RELEASE_GATES.md.
- Re-verify vendor flags, counter names and NCCL log formats against the releases current at publication.


## Independent review iteration 1 + author fixes (2026-10-30)

Independent reviewer score: **9.23**, gate not met. The reviewer's findings differed from the gaps the
author had named in iteration 2. The author re-read docs/VERIFIED_FACTS.md (distributed-training
operations, FEC alerting, alert scoring, ITL vs TPOT) and docs/REFERENCE_CLUSTER.md (24 + 8 default
split, no spares) before fixing.

| ID | Severity | Finding | Fix |
|---|---|---|---|
| D-01 | major | No ITL distribution | simulate() records every inter-token gap (res.attrs['itl_s']); summarize reports ITL p95/p99; slo-sli-spec separates TPOT (per-request mean) from ITL (per-token tail); ITL p99 ≤ 100 ms [ILLUSTRATIVE] added; c1's chunk stalls breach ITL p99 while TPOT p95 is 39 ms |
| D-02 | major | Single-trace percentiles | Five independent 15-minute traces; 60 s warm-up and cool-down exclusion; replicate()/aggregate() report the median and range across seeds; overloaded runs are flagged unstable (TTFT trend) and get no p95; the c3 knee was re-judged on 5 seeds |
| D-03 | minor | No frontend budget | 30 ms [ILLUSTRATIVE] frontend budget (gateway, auth, tokenization, network) subtracted: engine TTFT target 0.77 s |
| D-04 | minor | Prefill attention FLOPs omitted | attention_flops() = 2·L·d·((p+c)² − p²) per chunk, included in the iteration cost (≈ +30 % at 32k) |
| D-05 | minor | Cost headline on output tokens | Headline is $/M total tokens; output-loaded figure kept as an upper bound |
| D-06 | minor | simulate() could loop forever | Requests larger than the replica's KV capacity are rejected on arrival; checker 05 tests it |

### Author self-review, iteration 3 (after fixes)

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 3 | 2026-10-30 | Author self-review after independent review 1 | 9.50 | Met, pending independent re-review |

Scores: D1 9.5 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.5. `python scripts/validate_labs.py` passes for this package (solution, graceful starter,
no-generator release check, docs). Every number changed by these fixes was recomputed from the reference
implementation, not edited by hand.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent score: **9.50 (pass)**.

| ID | Severity | Finding | Fix |
|---|---|---|---|
| D2-01 | minor | Over-length rejections given as a point value | Now a range across seeds: 0–3 per trace window, 0–0.08 % (0–0.8× burn) |
| D2-02 | minor | Attention FLOPs: which n? | Stated: 1.34e15 for n = 32,000; 1.41e15 for n = 32,768 (guide, exemplar, checker message) |

`python scripts/validate_labs.py capstone-a capstone-b capstone-c capstone-d`: 4/4 OK on every column
(solution, starter fails gracefully, no-generator, docs). Data regenerates byte-identically.
