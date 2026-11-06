# Exercise DC — Shared versus dedicated inference capacity

**Difficulty:** ★★★ · **Tier:** L1 · **Type:** design-challenge · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
Halcyon needs a *second* eight-node W-INFER pool, in addition to ORION's default inference pool
(`orion-n25`–`n32`). Option A: take eight nodes from ORION's 24-node Slurm training partition
(leaving 16) and share them (training jobs may use them when inference load is low). Option B: buy a
dedicated eight-node inference pool on the frontend network only (no backend RDMA NICs). Using the
chapter's trade-off criteria, recommend one option. Address: SLO risk, utilization and cost (use
$3.00/GPU-hour, Chapter 21's rate), what the backend fabric is and is not needed for in inference,
scheduler implications (Slurm vs Kubernetes), failure domains, and what evidence would make you
change your recommendation.

**Evidence required:** a one-page recommendation with a criteria × option table, at least one
quantified argument, explicit assumptions, and a "would change my mind if…" section.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/recommendation.md`: one-page recommendation with criteria x option table, quantified
  argument, assumptions and a would-change-my-mind section

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show
formula, substitution and result with units.
