# Exercise 3.13 — Host health at ORION-XL scale

**Difficulty:** ★★★ · **Tier:** L1 · **Type:** design-challenge · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
ORION-XL has 512 `HX8` nodes. Design the host-diagnostics strategy that Fleet, SRE and Training Infra
will share. Decide and defend: (a) what runs continuously (agents, metrics, intervals) and what runs
on demand (the collector), with the trigger for each; (b) privilege model (root or not, where, audited
how); (c) which analyzer findings drain a node automatically and which only page a human, with the
rationale in terms of false-positive cost and lost GPU-hours; (d) storage and retention of snapshots
(estimate the volume of one full-fleet sweep using the size of the supplied snapshots); (e) how the
baseline YAML is versioned and changed safely.
*Evidence required:* a design note of no more than two pages with a decision table, the
snapshot-volume arithmetic, and at least two explicitly rejected alternatives with reasons.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/design_note.md`: design note of at most two pages: decision table, snapshot-volume arithmetic, two rejected alternatives

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
