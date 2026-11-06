# Exercise 5.9 — Modeled cost of one bad path

★★ · Tier L1 · worked problem · kind: `computed`

<!-- prompt:start -->
**5.9** ★★ L1 — *Modeled cost of one bad path.* Using the Section 5.9 formula with *S* = 1 GiB,
*n* = 256, *R* = 8, α = 0.2 ms and no variance: (a) busbw when every path is PIX (48 GB/s); (b) busbw when
one node has one NIC at PCIe Gen5 x8 (assume 27 GB/s achievable); (c) busbw when one node lacks GPUDirect RDMA on all
NICs (18 GB/s cap); (d) explain why (c) is worse than one would guess from "one node out of 32". (This
exercise models a 256-rank `all_reduce_perf` health check across all 32 nodes, unlike the 16-node worked
example.)
*Evidence required:* three results with arithmetic; one-paragraph explanation; label `[MODELED]`.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 5.4 model parameters.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/5.9-one-bad-path-cost/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
