# Exercise 5.13 — Rank placement and its validation

★★ · Tier L1 · outline-mandated · kind: `written`

<!-- prompt:start -->
**5.13** ★★ L1 (L2/L3 to validate) — *Rank placement and its validation.* For a 2-node, 16-rank job on HX8
nodes with TP = 8 inside each node and DP = 2 across nodes, propose the rank→GPU→NIC→CPU mapping
(including `CUDA_VISIBLE_DEVICES`, CPU binding and NIC selection) and a validation plan that proves the
placement on hardware. *Evidence required:* mapping table, launcher settings, a validation checklist with
pass criteria and the commands/log lines used.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
