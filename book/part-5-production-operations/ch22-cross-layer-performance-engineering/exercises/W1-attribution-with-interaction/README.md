# W1 — Attribution with an interaction (★★, L1)

Worked problem · difficulty ★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**W1 ★★ (L1) — Attribution with an interaction.** Before a change window, 10 W-TRAIN ablation jobs had a
job-weighted mean step time of 17.40 s. After the window, 10 jobs ran with the exposures below
(P = TP group split across nodes, S = dataset on capacity tier):

| Cell | Jobs | Mean step (s) |
|---|---|---|
| P = 0, S = 0 | 4 | 17.6 |
| P = 1, S = 0 | 3 | 24.8 |
| P = 0, S = 1 | 2 | 19.4 |
| P = 1, S = 1 | 1 | 28.2 |

a. Compute the after-period mean, the delta in seconds, and the percentage regression.
b. Using cell means, compute the period shift, the effect of P (at S = 0), the effect of S (at P = 0),
   and the P × S interaction.
c. Attribute the delta to period shift, P, S, and the interaction (contribution in s and share in %).
   Show that the contributions sum to the delta.
d. Compute the naive within-after differences "mean(P=1) − mean(P=0)" and "mean(S=1) − mean(S=0)".
   Why do they differ from (b)?
e. The interaction is positive. Propose a mechanism that would make S hurt more when P = 1.

*Evidence required:* all arithmetic; a balanced attribution table; one-paragraph mechanism.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python work.py   # optional: script your arithmetic; save the working in outputs/answer.md
```
