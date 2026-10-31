# T1 — The contaminated 4-node benchmark (★★★, L1)

Troubleshooting case · difficulty ★★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**T1 ★★★ L1 (analysis) / L3 (rerun).** Kestrel's L3 extension ran `all_reduce_perf` (8 GiB, 4 nodes ×
8 GPUs) five times on a lab fabric that it shares with another team. Results `[ILLUSTRATIVE]` (node busbw over 8 rails): 329.6,
194.4, 318.4, 208.8, 324.0 GB/s. Their draft benchmark table reports "275.0 GB/s `[MEASURED]`" and
their design text concludes "the fabric loses 23 % at 4 nodes versus B-02's 356 GB/s; we lower A-06 to
34 GB/s per rail". Additional
evidence: the other team's job log shows it running during runs 2 and 4, and the switch's PFC pause
counters on rail-leaf ports for those two runs rose by ≈ 10⁶ frames versus < 10³ for runs 1, 3, 5.

1. What is wrong with the reported number and the conclusion?
2. Rank at least three hypotheses for the low runs and name a discriminating test for each.
3. Write the corrected benchmark-table row(s) and the assumptions-register change, if any.

*Evidence required:* median and mean computed; ranked hypotheses with tests; corrected rows with
labels.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solve.py --out outputs   # optional: script your arithmetic
```
