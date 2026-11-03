# 12.20 — All-to-all and PXN on ORION (★★, L1)

**Type:** Worked problem · **Kind:** computed · **Points:** 8

## Prompt

<!-- prompt:start -->
**12.20 ★★ L1 — All-to-all and PXN on ORION.** An expert-parallel group spans two ORION nodes
(n = 16, one rank per GPU) and runs `alltoall_perf` with S = 1 GiB per rank on an otherwise idle fabric.
Assume an effective 45 GB/s per NIC and that NVLink is never the bottleneck. (a) Split the bytes each
rank sends into intra-node, inter-node same-rail, and inter-node cross-rail. (b) With PXN enabled,
compute the expected time, algbw, and busbw. (c) Repeat (b) with `NCCL_PXN_DISABLE=1`, and give the
fraction of all bytes sent that crosses the spines in each case. (d) Repeat the busbw and spine
fraction for a 256-rank all-to-all over all 32 nodes. (e) Explain why the benchmark in (b) and (c) can
hide the PXN setting, and what changes in production.
*Evidence required:* formula → substitution → result for (a)–(d), and two sentences for (e).
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units and evidence labels
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
