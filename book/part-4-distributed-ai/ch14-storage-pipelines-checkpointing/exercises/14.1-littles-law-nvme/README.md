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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/14.1-littles-law-nvme/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
