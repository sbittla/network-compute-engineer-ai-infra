# Exercise 2.6 — What liquid cooling does to node power and rack density

**Difficulty:** ★★ · **Tier:** L1 · **Type:** worked-problem · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
The DLC variant of HX8 replaces most fan power with pumps in the CDU. Assume `[ILLUSTRATIVE]`: peak
fan power falls from 1,350 W to 350 W; all other DC loads and the 94 % PSU efficiency are unchanged;
the liquid capture fraction becomes 80 % of rack IT load (nodes plus rack auxiliaries); node weight
is unchanged (135 kg); the non-node rack mass is 280 kg. Use ORION's facility envelope (Section 2.10).

1. What is the DLC node's AC maximum? How much does a 4-node rack save?
2. Does a **fifth** node per rack fit electrically (per side, with 10 % transient margin)?
3. For a 5-node rack: coolant flow (PG25, ΔT 10 K), residual airflow (ΔT 15 K), and the load on a
   single 300 kW CDU serving 8 such racks.
4. Does the 5-node rack pass the 1,200 kg/m² floor rating?
5. Does the DLC node still have the feed-loss problem of Section 2.2?
6. Verdict: 4 or 5 nodes per rack? Name the binding constraint.

**Evidence required:** all arithmetic shown; a five-row check table (electrical, liquid, CDU, floor,
feed loss) with ✓/✗.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: all arithmetic and the five-row check table with pass/fail marks

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
