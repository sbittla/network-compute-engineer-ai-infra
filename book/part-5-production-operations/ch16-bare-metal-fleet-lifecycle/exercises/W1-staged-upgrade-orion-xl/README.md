# W1 · Staged upgrade for ORION-XL (★★ · L1)

Type: worked-problem · Kind: computed · Points: 15

<!-- prompt:start -->
**W1 ★★ (L1) — Staged upgrade for ORION-XL.** ORION-XL has 512 HX8 nodes in 128 racks of 4. You must
move it to a new bundle. Policy: canary of 4 nodes in 4 different racks with a 72 h bake; waves of at
most 32 nodes and at most 1 node per rack; each wave takes 3 h; 6 h bake between waves.
(a) How many waves after the canary? (b) Calendar time for the campaign? (c) Node-hours and
GPU-hours out of service? (d) Probability the canary catches a regression with an intermittent fault
rate of λ = 1 per 100 node-hours, and of λ = 1 per 1,000 node-hours. (e) How many canary node-hours
would give 90 % detection at λ = 1 per 1,000 node-hours, and what does that imply about canaries for
rare faults?
*Evidence required:* every formula, substituted values, and result with units; a two-sentence
conclusion for (e).
<!-- prompt:end -->

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, plus the evidence label. If you check the arithmetic with a script, save it as
`outputs/work.py` and run it from this folder with `python outputs/work.py`.
