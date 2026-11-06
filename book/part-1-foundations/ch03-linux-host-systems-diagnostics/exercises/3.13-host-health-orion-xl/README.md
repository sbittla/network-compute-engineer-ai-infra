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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/3.13-host-health-orion-xl/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/design_note.md`: design note of at most two pages: decision table, snapshot-volume arithmetic, two rejected alternatives

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
