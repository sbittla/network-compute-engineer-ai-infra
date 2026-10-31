# 14.1 — Little's law on NVMe (★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**14.1 Little's law on NVMe** ★ · L1
A drive serves 4 KiB random reads with a mean latency of 95 µs. (a) What IOPS and MB/s does it
deliver at queue depth 1? (b) `iostat -x` shows `r/s` = 330,000 and `r_await` = 0.097 ms. What is
the average queue depth? (c) Why is `%util` = 100 % not evidence that the drive is saturated?
*Evidence required:* the formula, substituted values, and results with units.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
