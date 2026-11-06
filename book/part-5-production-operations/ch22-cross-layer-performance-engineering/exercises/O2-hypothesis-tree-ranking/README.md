# O2 — Hypothesis tree and test ranking (★★, L1)

Outline-mandated · difficulty ★★ · tier L1 · kind `lab` · [exercise index](../README.md)

<!-- prompt:start -->
**O2 ★★ (L1) — Build a hypothesis tree and rank tests by information value, cost, and risk.**
a. Draw the hypothesis tree for the lab regression (Mermaid or drawn), rooted in the step-time equation,
   with every change, alert, and anomaly attached to a term and a predicted fingerprint.
b. Complete lab task 8 and add two tests of your own with justified information value, cost, risk, and
   environment; place them in the ranking.
*Evidence required:* tree; ranked table including your two tests with scores; the list of rejected
tests and the rule applied.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Numbers in prompts are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/tree.md`
- `outputs/ranking.md`

Run:

```bash
python ../../lab/check.py   # rank_tests must PASS
```
