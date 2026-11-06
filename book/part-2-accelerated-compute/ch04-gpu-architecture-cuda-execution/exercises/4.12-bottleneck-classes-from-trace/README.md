# Exercise 4.12 — Identify the bottleneck class from a trace

★★ · Tier L1 · outline-mandated · kind: `computed`

<!-- prompt:start -->
**4.12** ★★ L1 (L2 to verify) — *Identify the bottleneck class from a trace.* Using the lab capture (`lab/data/`: `gpu_trace.csv`, `cuda_api_trace.csv`, `nvtx_ranges.csv`,
`device.json`) (or a
CUDA sample such as `bandwidthTest`/a vector-add run on an L2 host), identify one instance each of launch
overhead, memory-transfer cost, an occupancy constraint and a memory-bandwidth bottleneck, quoting the
rows or metrics that prove each.
*Evidence required:* four findings, each with quoted evidence (row IDs, durations, bytes, metric values).
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
