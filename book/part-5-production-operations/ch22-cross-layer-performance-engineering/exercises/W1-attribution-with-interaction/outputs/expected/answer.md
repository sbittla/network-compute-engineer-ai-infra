# W1 — Attribution with an interaction (solution)

All values `[ILLUSTRATIVE]` (prompt inputs). Method: cell-mean effects and exposure-weighted contributions
(manuscript Sections 22.4.2 and 22.10.2). `solve.py` reproduces every number.

**(a) After-period mean.**

```text
mean_after = (4 × 17.6 + 3 × 24.8 + 2 × 19.4 + 1 × 28.2) / 10 = (70.4 + 74.4 + 38.8 + 28.2) / 10
           = 211.8 / 10 = 21.18 s
Δ = 21.18 − 17.40 = 3.78 s ;  3.78 / 17.40 = +21.7 %
```

**(b) Effects from cell means.**

```text
period shift      = mean(P=0,S=0) − before = 17.6 − 17.40 = 0.20 s
effect P (S = 0)  = 24.8 − 17.6 = 7.20 s
effect S (P = 0)  = 19.4 − 17.6 = 1.80 s
interaction P×S   = 28.2 − 17.6 − 7.20 − 1.80 = 1.60 s
```

**(c) Attribution.** Exposures after (all zero before): P = (3 + 1)/10 = 0.4; S = (2 + 1)/10 = 0.3;
P×S = 1/10 = 0.1; period = 1.

| Term | Effect (s) | Δ exposure | Contribution (s) | Share |
|---|---|---|---|---|
| Period shift | 0.20 | 1.0 | 0.20 | 5.3 % |
| P | 7.20 | 0.4 | 2.88 | 76.2 % |
| S | 1.80 | 0.3 | 0.54 | 14.3 % |
| P × S | 1.60 | 0.1 | 0.16 | 4.2 % |
| **Total** | | | **3.78** | **100 %** |

Check: 0.20 + 2.88 + 0.54 + 0.16 = 3.78 s = Δ. The table balances because the four cells are saturated
by the four terms.

**(d) Naive within-after differences.**

```text
mean(P=1) = (3 × 24.8 + 28.2)/4 = 102.6/4 = 25.65 s ; mean(P=0) = (4 × 17.6 + 2 × 19.4)/6 = 109.2/6 = 18.20 s
naive P = 25.65 − 18.20 = 7.45 s   (vs 7.20 s)
mean(S=1) = (2 × 19.4 + 28.2)/3 = 67.0/3 = 22.33 s ; mean(S=0) = (4 × 17.6 + 3 × 24.8)/7 = 144.8/7 = 20.69 s
naive S = 22.33 − 20.69 = 1.65 s   (vs 1.80 s)
```

They differ because each naive difference averages over an unbalanced mix of the other factor and folds
in part of the interaction. P is present in 3/7 = 43 % of S = 0 jobs but only 1/3 = 33 % of S = 1 jobs,
which pulls naive S down; the positive interaction pulls both naive values up. Here the biases partly
cancel; in the lab bundle they do not (naive storage difference ≈ −0.55 s, Section 22.4.3).

**(e) Mechanism for a positive interaction.** Note first that the simple dataloader-slack model
(Section 22.10.4) predicts a *negative* interaction: a longer TP-split step gives the loader more slack
and hides recalls, which is what the lab bundle shows (−1.31 s). A positive interaction needs another
mechanism. Example: CPU contention. TP-split jobs move TP traffic onto the NICs, so NCCL's network proxy
threads consume more host CPU on the same NUMA node as the dataloader workers; batch production time
rises, and capacity-tier recalls are exposed *more*. Evidence to check: per-thread CPU of proxy threads
and loader workers (`pidstat -u -t 1`), NUMA placement (`numastat -p`), and producer time per batch on
P = 1, S = 1 jobs versus P = 0, S = 1.

**Common wrong answers.** Using job counts instead of exposure fractions in (c); reporting the naive
differences as effects; dropping the interaction so shares sum to more than 100 %.
