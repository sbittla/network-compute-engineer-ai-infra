# W1 — Staged upgrade for ORION-XL

Inputs (prompt): 512 HX8 nodes, 128 racks × 4 nodes; canary 4 nodes in 4 racks, 72 h bake; waves
≤ 32 nodes and ≤ 1 node per rack; 3 h per wave; 6 h bake between waves. Method from Section 16.8.

**(a) Waves after the canary.** Remaining = 512 − 4 = 508 nodes.
Per-wave cap: ⌈508 / 32⌉ = ⌈15.875⌉ = 16. Per-rack cap: the largest rack remainder is 4 (124 racks
had no canary node), and at most 1 node per rack per wave → ≥ 4 waves.
Waves = max(16, 4) = **16** (15 × 32 + 1 × 28). Feasible: a 32-node wave needs 32 distinct racks
and 128 exist. `[MODELED]`

**(b) Calendar time.** Canary (3 h + 72 h) + 16 × (3 h + 6 h) = 75 + 144 = **219 h ≈ 9.1 days**.
(This counts a bake after the last wave as part of the campaign, as in Section 16.8.)

**(c) Capacity out of service.** Every node, canary included, is out once for 3 h:
512 × 3 h = **1,536 node-hours** = 1,536 × 8 = **12,288 GPU-hours**. Fraction of campaign capacity:
1,536 / (512 × 219) ≈ 1.4 %.

**(d) Canary detection probability**, Poisson model P = 1 − e^(−λNT), NT = 4 × 72 = 288 node-hours:
- λ = 1/100 node-hours: 1 − e^(−2.88) = 1 − 0.0561 = **94.4 %**
- λ = 1/1,000 node-hours: 1 − e^(−0.288) = 1 − 0.750 = **25.0 %** `[MODELED]`

**(e) Canary size for 90 % at λ = 1/1,000.** e^(−λNT) ≤ 0.10 → λNT ≥ ln 10 = 2.303 →
NT ≥ **2,303 node-hours** (for example 32 nodes × 72 h = 2,304, a full wave baked for three days).

*Conclusion:* canaries are a cost-effective net for *common* regressions, but faults that appear
once per thousands of node-hours need a canary as large as a full wave, which defeats its purpose.
Rare faults must be caught by fleet-wide telemetry that compares upgraded and not-yet-upgraded
cohorts during and after the campaign, backed by a fast per-component rollback.

**Common mistakes:** using 512 instead of 508 in (a); forgetting the canary nodes in (c);
confusing node-hours with GPU-hours; using λT instead of λNT.

`solve.py` reproduces every number and asserts the key values.
