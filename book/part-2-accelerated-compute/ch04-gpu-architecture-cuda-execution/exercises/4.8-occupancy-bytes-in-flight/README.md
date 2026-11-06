# Exercise 4.8 — Occupancy and bytes in flight

★★ · Tier L1 · worked problem · kind: `computed`

<!-- prompt:start -->
**4.8** ★★ L1 — *Occupancy and bytes in flight.* A memory-bound kernel uses 128 threads per block,
80 registers per thread and 48 KB (49,152 B) of shared memory per block. Each warp keeps two independent
128-byte loads in flight.
(a) Compute theoretical occupancy and the limiter using the Section 4.7 rules.
(b) Using Little's law with 600 ns latency and 3.35 TB/s, estimate the bytes in flight needed per SM and
the fraction of HBM bandwidth this kernel can reach at that occupancy `[MODELED]`.
(c) Shared memory per block is reduced to 32 KB (32,768 B). Recompute (a) and (b).
*Evidence required:* every limit computed, limiter named, bandwidth bound with arithmetic.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/4.8-occupancy-bytes-in-flight/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
