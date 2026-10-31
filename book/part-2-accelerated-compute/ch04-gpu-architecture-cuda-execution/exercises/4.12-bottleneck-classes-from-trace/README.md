# Exercise 4.12 — Identify the bottleneck class from a trace

★★ · Tier L1 · outline-mandated · kind: `computed`

<!-- prompt:start -->
**4.12** ★★ L1 (L2 to verify) — *Identify the bottleneck class from a trace.* Using the lab capture (or a
CUDA sample such as `bandwidthTest`/a vector-add run on an L2 host), identify one instance each of launch
overhead, memory-transfer cost, an occupancy constraint and a memory-bandwidth bottleneck, quoting the
rows or metrics that prove each.
*Evidence required:* four findings, each with quoted evidence (row IDs, durations, bytes, metric values).
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/
```
