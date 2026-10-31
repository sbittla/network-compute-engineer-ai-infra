# 12.14 — Latency doubled, bandwidth fine (★★★, L1)

**Type:** Troubleshooting case · **Kind:** written · **Points:** 15

## Prompt

<!-- prompt:start -->
**12.14 ★★★ L1 — Latency doubled, bandwidth fine.** After a container image update, the nightly
8-node run shows: 8 B all-reduce time 95 µs (baseline 47 µs); 1 MiB time 118 µs (baseline 53 µs);
plateau busbw 344 GB/s (baseline 345). `#wrong` = 0. No node changes. Rank hypotheses, name
discriminating tests (with commands and the log lines you expect), give the most likely root cause, the
safe fix, and the validation evidence.
*Evidence required:* ≥ 3 ranked hypotheses, tests with expected outcomes, root cause, fix, and
validation criteria.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Show every formula, substitution and result with units, and label each number with its evidence label.
