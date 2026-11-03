# 20-W2 — Wave plan for ORION-XL (★★★, L1)

Type: Worked problem · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
ORION-XL has 512 HX8 nodes in 128 racks (4 nodes per rack). You are rolling out a NIC firmware
bundle. Constraints: at most one node per rack per wave; each wave costs 75 min (apply + verify +
60 min bake); nodes are drained for their wave.

a. A latent defect affects nodes with one board revision: 2 % of the fleet. With a random 8-node
   canary, what is the probability that the canary contains at least one affected node? How many
   randomly chosen nodes would you need for a 90 % probability?
b. The inventory identifies the 10 nodes with that revision. If you put 2 of them in the canary,
   and the defect manifests on an affected node during bake with probability 0.8, what is the
   detection probability?
c. Propose a wave plan (list of wave sizes) that respects the per-rack constraint and finishes in
   at most 8 waves. Compute total duration, peak fraction of GPUs out of service, and GPU-hours
   consumed.
d. After your first three waves, what is the probability that the 2 % defect has appeared at least
   once under *random* selection? What does that tell you about relying on wave size alone?

**Evidence required:** all arithmetic shown; a wave-size list that sums to 512 with the per-wave
maximum justified.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md` (working for a-d)
- `outputs/wave_plan.csv` (wave, size, cumulative nodes)
