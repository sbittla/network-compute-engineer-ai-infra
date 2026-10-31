# 20.3 — Wave plan for ORION-XL: worked solution

**Relies on:** manuscript Section 20.7.2 (detection probability, slot-major waves, Table 20.7) and
Section 20.11, Step 5 (duration, peak capacity, GPU-hours). All results `[MODELED]`; inputs from the prompt.
Reference computation: `solve.py`, which also writes `wave_plan.csv`.

## a. Random 8-node canary

Binomial approximation (independent selection), p = 0.02, k = 8:
P = 1 − 0.98⁸ = 1 − 0.851 = **0.149**.

Exact (10 affected nodes of 512, 8 drawn without replacement):
P = 1 − C(502, 8) / C(512, 8) ≈ **0.147**. Either is accepted with the method stated.

For 90 %: 1 − 0.98ᵏ ≥ 0.9 → k ≥ ln 0.1 / ln 0.98 = −2.3026 / −0.0202 = 113.97 → **k = 114 nodes**,
22 % of the fleet. A "canary" that large is not a canary.

## b. Stratified canary with 2 known-affected nodes

Each affected node manifests during bake with probability 0.8, independently:
P = 1 − (1 − 0.8)² = 1 − 0.04 = **0.96**. Two deliberately chosen nodes beat 114 random ones: stratify by
the attribute the change interacts with (board revision), as Section 20.7.2 recommends.

## c. Wave plan

Constraint: at most one node per rack per wave, and there are 128 racks, so **no wave can exceed 128 nodes**.
Each rack has 4 nodes, so at least 4 waves are needed; the 8-wave limit leaves room for small early waves.

Reference plan: **2, 6, 24, 96, 128, 128, 128** = 512 nodes in 7 waves (taken slot-major: the first
node of every rack, then the second, and so on). The canary (2) includes the two board-revision nodes in
different racks; sizes grow roughly 3–4× once detection probability is high.

- Duration = 7 × 75 min = 525 min = **8.75 h** (plus drain lead time).
- Peak out of service = 128 / 512 = **25 %** of GPUs, and never more than 1 of 4 nodes (25 %) of any rack.
- GPU-hours consumed = 512 nodes × 8 GPUs × 1.25 h = **5,120 GPU-h**. This is independent of the plan shape,
  because every node is drained for exactly one 75-minute wave.

Any plan of ≤ 8 waves that sums to 512, keeps every wave ≤ 128 and starts with a canary of ≤ 4 nodes earns
full marks; for example 4, 12, 40, 72, 128, 128, 128 (7 waves).

## d. Detection after the first three waves (random selection)

Waves 0–2 = 2 + 6 + 24 = 32 nodes: P = 1 − 0.98³² = 1 − 0.524 = **0.476** (exact hypergeometric 0.479).

After 32 nodes, a 2 % minority defect has appeared with roughly coin-flip probability, and wave 3 then takes
96 more nodes. Wave size alone is not a detection strategy: put the known minority populations (board
revision, firmware lot, optics vendor) into the canary deliberately, and keep the early waves for detection,
not throughput.

## Marking (10 points)

a 3 · b 2 · c 3 · d 2.

**Common wrong answers.** Computing k with mixed log bases or solving 0.98ᵏ = 0.9 (gives 5). Allowing a
wave larger than 128. Computing GPU-hours from the wall-clock duration (512 × 8 × 8.75 h): each node is out
for one wave, not for the whole rollout. Assuming independence when the affected nodes share racks.
