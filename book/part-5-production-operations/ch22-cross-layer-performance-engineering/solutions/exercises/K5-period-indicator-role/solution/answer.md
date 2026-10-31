# K5 — Why the model needs a period indicator (solution)

**Role of the term (Section 22.4.1).** `after = 1` for every job after the change window. It soaks up any
shift common to *all* after-period jobs: in the lab, CHG-7802 (the rebuilt base container), plus any
environmental drift over the window. With an intercept and `after` in the model, the OLS contributions
sum exactly to the observed delta, and the common shift is reported as its own row instead of being
silently assigned to a named change.

**What goes wrong without it.** The common shift must still go somewhere. OLS pushes it onto the
factors whose exposure is highest in the after period, because those columns are the best stand-in for
"after". Refitting the lab model without `after` (`solve.py`, reference bundle seed 2214, `[SIMULATED]`):

| Term | With `after` (s/step) | Without `after` (s/step) | Change |
|---|---|---|---|
| `after` | +0.34 ± 0.09 | (dropped) | |
| `tp_split` | +8.96 | +9.18 | +0.22 |
| `driver_new` | +0.90 | +1.07 | +0.17 |
| `storage_new` | +1.40 | +1.57 | +0.17 |
| `alert_node` | −0.05 | +0.16 | +0.21 |
| `tp_x_storage` | −1.31 | −1.59 | −0.28 |

**The concrete misattribution.** The driver team (CHG-7781) and the storage team (CHG-7795) would each be
charged ≈ 0.17 s per step more than their change caused, and the orion-n13 ECC alert would acquire a
positive "effect" (+0.16 s) that does not exist in the generator (true effect 0). The container rebuild,
which is the most plausible source of the common shift, would disappear from the report entirely.

**Common wrong answers.** "It improves R²" (it barely does: 0.998 either way); "it controls for the
number of jobs" (it controls for the period, not sample size).

`solve.py` refits the model on the lab bundle with and without the indicator and asserts the key's values
(driver 1.07 s, storage 1.57 s, TP 9.18 s; tolerance ± 0.01 s).
