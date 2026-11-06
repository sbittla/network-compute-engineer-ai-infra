# T1 — The contaminated 4-node benchmark

**Source:** manuscript Section 23.7 (benchmark table format, "Benchmark discipline, condensed") and
Section 23.12 (the same diagnostic loop); Chapter 22 method; key Section D. Run values `[ILLUSTRATIVE]`.

## 1. What is wrong

Sorted runs: 194.4, 208.8, 318.4, 324.0, 329.6 GB/s.
- **Mean** = 1,375.2 / 5 = **275.04 GB/s** (34.4 GB/s per rail). **Median** = **318.4 GB/s**.
- The sample is bimodal: runs 2 and 4 (194.4, 208.8) coincide with the other team's job and with PFC
  pause counters rising by ≈ 10⁶ frames versus < 10³ in runs 1, 3, 5 — a ≈ 1,000× difference.
- The team reported the **mean of a bimodal sample** as one `[MEASURED]` value, did not state that the
  fabric was shared (Section 23.7 requires it), and used contaminated data for a design change.
- The "23 % loss" is 1 − 275.04 / 356 = 22.7 %: a contaminated mean compared with a clean 2-node median.
  The clean runs (1, 3, 5) have median **324.0 GB/s** (40.5 GB/s per rail), only 1 − 324.0 / 356 =
  **9.0 %** below B-02 — consistent with added 4-node latency terms — and *above* A-06's 320 GB/s node
  busbw (40 GB/s per rail). Lowering A-06 to 34 GB/s per rail is not supported.

## 2. Ranked hypotheses for the low runs

| Rank | Hypothesis | Why this rank | Discriminating test |
|---|---|---|---|
| H1 | Interference from the other team's traffic on the shared fabric | Time correlation with their job; ≈ 10³× PFC pause increase only in runs 2 and 4 | Rerun ≥ 5 times in an isolated or reserved window, recording PFC/ECN counters per run: H1 predicts all runs ≈ 320–330 GB/s with flat pause counters |
| H2 | A flapping or erroring link on one rail | Would also give intermittent low runs, but does not explain the job correlation | Per-port FEC/symbol-error and link-flap counters for runs 2 and 4 versus 1, 3, 5: H2 predicts errors on one port, H1 predicts none |
| H3 | A straggling node (thermal throttling, CPU frequency) | Possible, but straggling would not raise PFC pauses on rail-leaf ports | Per-rank timings and `nvidia-smi --query-gpu=clocks.sm,temperature.gpu --format=csv -l 1` during runs |
| H4 | Genuine 4-node scaling loss | Contradicted by the three clean runs within 9 % of B-02 | Compare isolated 2-node and 4-node medians on the same image |

## 3. Corrected benchmark row and register

Mark the series invalid for design use, keeping all five runs visible:

| ID | Metric | Value | Label | Tier | Manifest |
|---|---|---|---|---|---|
| B-07 | `all_reduce_perf` busbw, 8 GiB, 4 × 8 GPUs, **shared fabric, contaminated** (runs 2, 4 coincide with foreign traffic) | median 318.4 GB/s (min 194.4, max 329.6); not used for design | `[MEASURED]` | L3 | `manifests/l3-4node-shared.yaml` |

Optionally an indicative row for runs 1, 3, 5 (median 324.0 GB/s, n = 3, same label and manifest), noted
as too few runs. **No change to A-06** until an isolated rerun exists; add a backlog item for it.

**Common wrong answers.** Silently deleting runs 2 and 4 (survivorship bias, Chapter 22); reporting the
mean; lowering A-06; blaming the fabric design rather than the shared environment.
