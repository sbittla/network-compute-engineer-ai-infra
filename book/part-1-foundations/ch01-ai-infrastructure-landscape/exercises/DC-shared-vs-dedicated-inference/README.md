# Exercise DC — Shared versus dedicated inference capacity

**Difficulty:** ★★★ · **Tier:** L1 · **Type:** design-challenge · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
Halcyon needs inference capacity for W-INFER equivalent to eight `HX8` nodes. Option A: carve eight
nodes out of ORION's training partition and share them (training jobs may use them when inference
load is low). Option B: buy a dedicated eight-node inference pool on the frontend network only (no
backend RDMA NICs). Using the chapter's trade-off criteria, recommend one option. Address: SLO risk,
utilization and cost (use $2.50/GPU-hour `[ILLUSTRATIVE]`), what the backend fabric is and is not
needed for in inference, scheduler implications (Slurm vs Kubernetes), failure domains, and what
evidence would make you change your recommendation.

**Evidence required:** a one-page recommendation with a criteria × option table, at least one
quantified argument, explicit assumptions, and a "would change my mind if…" section.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/recommendation.md`: one-page recommendation with criteria x option table, quantified argument, assumptions and a would-change-my-mind section

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
