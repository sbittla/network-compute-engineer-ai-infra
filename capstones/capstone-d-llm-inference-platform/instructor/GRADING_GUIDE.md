# Capstone D — Instructor Grading Guide

INSTRUCTOR ONLY. Removed from the student edition by `scripts/make_student_release.py`, together with
`starter-kit/tools/`.

## 1. Reference numbers

**Capacity `[MODELED]`.** KV = 327,680 B/token.

- **TP8 BF16:** usable 576 GB − 140 GB weights − 32 GB reserve = 404 GB, which is 1,232,910 tokens
  (301 sequences at 4k).
- **TP4 FP8:** 288 − 70 − 16 = 202 GB, which is 616,455 tokens per replica.
- **Iteration costs:** a 2,048-token prefill iteration on TP8 BF16 takes ≈ 75.5 ms (compute-bound,
  before attention). A 64-sequence × 2k-context decode iteration takes ≈ 12.7 ms (HBM-bound).
- **Causal attention:** 2·L·d·n², which is ≈ 1.34 × 10¹⁵ FLOP for n = 32,000 tokens (≈ 1.41 × 10¹⁵ for
  n = 32,768), +30 % on top of
  2·N·n.

**Simulation `[SIMULATED]`.** Five independent 15-minute traces, with a steady-state window excluding
the first and last 60 s.

- **Load:** node load 1.0 ≈ 5 req/s per node. c3 runs two replicas per node at half the traffic each.
- **SLO targets:** the engine-side TTFT target is 0.77 s (0.8 s minus a 30 ms `[ILLUSTRATIVE]` frontend
  budget). ITL p99 ≤ 100 ms `[ILLUSTRATIVE]`.
- **Table format:** median [min–max] across seeds.

| Config | Node load | Mix | TTFT p95 (s) | TPOT p95 (ms) | ITL p99 (ms) | Output tok/s per node | SLO met (seeds) |
|---|---|---|---|---|---|---|---|
| c1 BF16 TP8 chunked | 1.0 | mixed | 1.39 [1.25–1.53] | 35.0 | 103 [99–104] | 1,376 | 0/5 (TTFT, ITL) |
| c1 | 1.25 | mixed | 1.74 [1.47–2.18] | 48.3 (max 53.9) | 108 | 1,709 | 0/5 |
| c1 | 2.0 | mixed | **unstable**: TTFT grows 0.029 s per s of arrival (seed 1: "p95" 13.8 s) | — | — | 2,784 (highest of all) | 0 |
| c2 BF16 TP8 big batch, no chunking | 1.0 | mixed | 1.53 [1.44–1.72] | 40.0 | 150 [140–154] | 1,376 | 0/5 |
| c3 FP8 TP4 × 2 | 1.0 | mixed | 0.62 [0.51–0.86] | 19.2 | 79 | 1,378 | **4/5**: not robust |
| c3 | 1.25 | mixed | 0.91 [0.78–1.09] | 23.0 | 87 | 1,716 | 0/5 |
| c4 BF16 TP8, 8k max length | 1.0 | mixed | 0.19 [0.19–0.21] | 18.2 | 77 | 1,349 | latency 5/5, but 2.1 % rejected |
| c1 | 2.0 | chat only | 0.40 [0.39–0.45] | 37.2 | 79 | 2,703 | 5/5 |
| c2 | 2.0 | chat only | 0.45 [0.40–0.48] | 41.3 | **241 [221–257]** | 2,703 | 0/5: ITL only |
| c3 | 2.5 | chat only | 0.23 [0.22–0.24] | 21.8 | 77 | 3,356 | 5/5 |
| c3 | 3.0 | chat only | 0.27 [0.25–0.28] | 26.4 | 78 | 4,040 | 5/5 |

Seed 1 values used by the checker: c1 at 1.0, TTFT 1.530 s, TPOT 38.6 ms, ITL p99 103.7 ms; c3 at 1.0,
TTFT 0.742 s; c4, 82 rejections (2.1 %, ≈ 21× burn).

Cost, as $/M **total** tokens (the headline: the mix is input-dominated, ≈ 8 input tokens per output token):
$0.60 at node load 1.0 for c1 or c3 alike, $0.32 at 2.5× chat-only on c3, and $0.27 at 3.0×. A c3
replica costs 4 × $2.20 / 0.65 = $13.54 per hour. The output-loaded figures ($5.46 → $1.86 per M output
tokens) are upper bounds for output pricing only.

## 2. Planted issues

| Issue | Where | Strong handling |
|---|---|---|
| Units trap | `vendor_sizing_sheet.csv`: "320 KB" per token | Uses 327,680 B (320 KiB). The 2.4 % error compounds into KV token counts |
| Head-of-line blocking from 32k prompts | `rag-long` tenant (2 %) | Diagnoses c1's TTFT miss at load 1.0 as long prefills (≈ 1.4 s each with attention) occupying the token budget, and fixes it by isolation or routing, not more nodes |
| Mean TPOT hides stalls | c2 (and c1) | c2 chat-only at 2.0×: TPOT p95 41 ms passes but ITL p99 241 ms fails. Unchunked prefills stall every decoder in the iteration (docs/VERIFIED_FACTS.md: ITL vs TPOT) |
| Throughput looks best, system is unstable | c1 at 2.0× mixed: 2,784 tok/s per node | Flags instability (TTFT trend) and refuses to quote a p95 or a cost there |
| Single-seed knee | c3 at 1.0× mixed: 4 of 5 seeds pass | Calls the mixed-traffic knee "not robust at 1.0×" rather than quoting one seed |
| "Meets SLO" by rejecting | c4 | Rejected requests count against availability; ≈ 21× burn; the rollback gate fires |
| Over-length requests | c1–c3 reject 0–3 requests per trace in the steady-state window (prompt + output > 32,768) | Notes the 0–0.08 % error rate (0–0.8× burn) and the product decision it implies |
| FP8 quality | c3 | Makes the offline evaluation a release gate |
| Idle capacity | economics | Cost divides by utilization; per-token cost at peak load is not the fleet cost |

## 3. Dimension expectations

| Dimension | Exemplary | Proficient | Developing | Insufficient |
|---|---|---|---|---|
| Framing (10) | Forecast, mix, quality status and frontend budget as assumptions with validation | Mostly | Implicit | None |
| Correctness (20) | Memory plan, roofline with attention, request path complete; TPOT vs ITL defined correctly | Minor slip | KV unit or TP arithmetic wrong | Weights/KV do not add up |
| Implementation (15) | 11/11; sweeps scripted across seeds | 11/11 | 7–10 | < 7 |
| Measurement (20) | ≥ 5 seeds, median and range, unstable points flagged, knee per config, ITL tails, goodput + errors, labels | Multi-seed without instability handling | Single trace, single load | Simulated presented as measured: cap at 40 % |
| Reliability/security/ops (15) | Gates (SLO incl. ITL, regression, burn), TP-group failure, KV exhaustion, tenant isolation | Gates only | Generic | None |
| Judgment (10) | Architectural fix for long-context traffic; FP8 gate; ignores unstable throughput | Picks c3 without routing | Picks by throughput | Picks c4 |
| Communication (10) | One-page decision with evidence and cost | Clear | Dense | Disorganized |

## 4. Common failure patterns

1. Quoting $/M tokens at 2× mixed load, where the system is unstable.
2. Dropping rejected requests from the denominators and declaring c4 the winner.
3. Using the vendor's 320 KB per token.
4. Reporting TPOT p95 only and missing the c2 stall tail.
5. Calling c3 compliant at 1.0× mixed from one seed.
6. Sizing for mean load rather than peak plus failure headroom.
7. Treating TTFT p95 over all prompts (including 32k) as the SLI.

## 5. Viva questions

1. Why is decode memory-bound and prefill compute-bound on the same GPU? Show the bytes-per-FLOP argument.
2. What chunk size keeps every mixed iteration, and so every ITL gap, under 50 ms on TP8 BF16? Why does
   c1 still show an ITL p99 of ≈ 103 ms with 2,048-token chunks?
3. Why can a configuration show the highest throughput while it is failing? How did you detect it?
4. FP8 TP4 beats BF16 TP8 here. Name two things that could reverse that on real hardware.
5. How would disaggregated prefill/decode (Capstone H) change the long-context problem, and what new
   cost does it add?
