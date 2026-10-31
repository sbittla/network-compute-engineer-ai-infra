# W2 — Capping in a tighter hall: worked solution

Source: manuscript Section 21.8 (Table 21.4 method). Cap curve from `lab/data/power_cap_curve.csv`
`[ILLUSTRATIVE]`; 30 kW rack limit from the prompt (declared variation); results `[MODELED]` and
reproduced by `solve.py`.

**Setup.** Planned budget per rack = 30 × (1 − 0.10) = **27.0 kW** (one side carries the rack). Node
peak = 4.6 kW + 8 × cap. Nodes per rack = min(4 slots, ⌊27.0 / node peak⌋). Deployable = min(64,
racks × nodes per rack). Throughput = deployable × relative throughput, in node-equivalents where an
uncapped HX8 node = 1.0.

**(a) The three caps, 16 racks.**

| Cap | Node peak | Nodes/rack | Deployable | Throughput | Unused budget/rack |
|---|---|---|---|---|---|
| 650 W | 4.6 + 5.2 = 9.8 kW | ⌊27 / 9.8⌋ = 2 | 32 | 32 × 0.990 = **31.7** | 7.4 kW |
| 550 W | 4.6 + 4.4 = 9.0 kW | ⌊27 / 9.0⌋ = 3 | 48 | 48 × 0.945 = **45.4** | 0.0 kW |
| 350 W | 4.6 + 2.8 = 7.4 kW | ⌊27 / 7.4⌋ = 3 | 48 | 48 × 0.700 = **33.6** | 4.8 kW |

For reference, the full curve on 16 racks: 700 W 32.0; 600 W 31.1; 500 W 43.4; 450 W 41.0; 400 W 37.9.

**(b) Best cap and why "deeper" is wrong.** 550 W is best: it is the *lightest* cap that fits a third
node, because 9.0 × 3 = 27.0 kW lands exactly on the budget. The 600 W cap gives 9.4 kW nodes, and
three need 28.2 kW, which does not fit. Going deeper than 550 W adds no node. A fourth node needs node
peak ≤ 27 / 4 = 6.75 kW, i.e. cap ≤ (6.75 − 4.6) / 8 ≈ 269 W, below the curve's useful range. So 350 W
keeps 48 nodes and throws away 26 % of each GPU's throughput. The binding constraint is a discrete one
(whole nodes per rack), so the optimum sits at the step, not at the best throughput per kW (≈ 500 W).
Caution: 550 W leaves 0.0 kW planned headroom, so the 4.6 kW base must be measured on these nodes.
A base 1 % higher pushes the choice to 500 W (3 × 8.65 ≈ 25.9 kW, throughput 43.4).

**(c) 22 racks.** With 550 W, 22 × 3 = 66 slots ≥ 64, so all 64 nodes deploy: 64 × 0.945 = **60.5**.
At 650 W or uncapped only 2 per rack fit: 44 nodes → 43.6 or 44.0. Running all 64 uncapped would need
⌈64 / 2⌉ = 32 racks. **Recommend 550 W on 22 racks**: +37 % over uncapped 44 nodes, with 20 more nodes
in service. Apply the cap uniformly to every node of each job (Section 21.8, "Cap jobs, not
racks"), and alarm at 80 % / 90 % of the per-side limit (Table 21.5).

**Common wrong answers:** using the old 3.6 kW base; planning against 30 kW without the margin
(30 / 9.8 = 3.06 → 3 nodes at 650 W, which is unsafe); assuming the deepest cap is best.
