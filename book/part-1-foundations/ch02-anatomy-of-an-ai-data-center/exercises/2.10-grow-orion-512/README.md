# Exercise 2.10 — Growing ORION to 512 GPUs in the same hall

**Difficulty:** ★★★ · **Tier:** L1 · **Type:** design-challenge · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
Halcyon wants to double ORION to 64 HX8 nodes in the same row space, adding at most 6 racks. The
hall can supply up to 800 kW of IT load to the row, one additional 300 kW CDU, and no structural
work this year.

Choose and defend a design: rack count and nodes per rack (air-cooled HX8 or the DLC variant of
Exercise 2.6), CDU topology, backend fabric change (the current spines have no free ports), and how
you will remove the SPOFs found in the lab. Present a one-page decision record: options considered
(at least three), criteria, the decision, what you gave up, and the evidence you would collect before
committing.

**Evidence required:** decision record; power, cooling, CDU, and floor arithmetic for the chosen
option; the fabric change with switch and link counts.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/decision_record.md`: one-page decision record with power, cooling, CDU, floor and fabric arithmetic

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
