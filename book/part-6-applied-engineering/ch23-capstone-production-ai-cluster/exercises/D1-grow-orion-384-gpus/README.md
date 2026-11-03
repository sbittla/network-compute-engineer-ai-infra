# D1 — Growing ORION to 48 nodes (★★★, L1)

Design challenge · difficulty ★★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**D1 ★★★ L1.** Halcyon wants to grow ORION to 48 HX8 nodes (384 GPUs) for W-TRAIN, while the
inference team plans to run disaggregated serving with cross-rail KV cache transfer on the same
backend next year. Rail-leaf ASICs are 51.2 Tb/s class, deployed either as 64 × 800G cages each run at 400G
(radix 64 at 400G) or broken out to 128 × 400G (radix 128). Compare at least three backend options:
(A) keep one radix-64 leaf per rail (64 × 800G cages at 400G) with 48 down / 16 up; (B) two such radix-64
leaves per rail at 1:1; (C) one 128 × 400G leaf per rail at 1:1. For each, compute leaf and spine counts and port usage,
oversubscription, backend cable count, and state which traffic crosses the spines. Recommend one
in an ADR with a revisit trigger. Include rack count and GPU-node power at 45 kW planned per rack
(50 kW limit, 10 % transient margin).
*Evidence required:* the arithmetic per option; an ADR (context, options, decision, evidence,
consequences, revisit trigger).
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`
- `outputs/adr.md`

Run:

```bash
python solve.py --out outputs   # optional: script your arithmetic
```
