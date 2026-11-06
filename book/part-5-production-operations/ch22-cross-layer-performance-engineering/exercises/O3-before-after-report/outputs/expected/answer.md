# O3 — Before/after report for the change owners (solution)

A model report (Section 22.9 structure). All lab numbers `[SIMULATED]`; predictions `[MODELED]`.

```markdown
# W-TRAIN 64-GPU sweep regression after CW-2026-10-12 — before/after report
Scope: all 48 jobs launched (24 before, 24 after), post-warm-up step time, job-weighted mean and median
of per-job means. Evidence class: SIMULATED.
Hygiene: 44 replayed rows removed (job 41105); 480 warm-up rows removed (steps 0–9); 0 jobs removed
(failed job 41114 kept, 60 usable steps); driver and alert flags joined as of job start.

## Measured facts
- Mean 17.38 → 21.42 s (+4.04 s, +23.2 %); median 17.42 → 19.70 s (+13.1 %); step-weighted +22.3 %.
- Exposure: 7 TP-split jobs; 12 on R570 nodes after the window; 14 capacity-tier; 6 on orion-n13 after
  the alert start; 3 TP-split capacity-tier.
- Backend tx per node 6.06 GB/s (packed) vs 95.93 GB/s (split); SM active 0.57 vs 0.40.
- Data wait, TP-packed jobs: capacity minus hot +1.46 s per step; iowait 1.52 % vs 6.03 %.
- Host bounce copy on orion-n17..n32: 0.40 GB/s before, 9.50 GB/s after; NET channel lines lack /GDRDMA.
- orion-n13: SBE 140–160 per job-node (≈ 1 h jobs, i.e. the alert's 140–160/h), no DBE, no row remap; temperature 67.4 vs 68.1 °C.

## Inferred causes (share of +4.04 s; ± classical SE)
| Cause | Effect (s/step) | Share |
| TP groups split across nodes (CHG-7790) | +8.96 ± 0.10 | 64.7 % ± 0.7 pp |
| Capacity storage tier (CHG-7795) | +1.40 ± 0.07 | 20.2 % ± 1.1 pp |
| R570 driver, GDR host-staged (CHG-7781) | +0.90 ± 0.07 | 11.2 % ± 0.9 pp |
| Common shift (period; container CHG-7802 most likely) | +0.34 ± 0.09 | 8.3 % ± 2.2 pp |
| TP split × capacity tier interaction | −1.31 ± 0.15 | −4.0 % ± 0.5 pp |
| ECC alert on orion-n13 — ruled out | −0.05 ± 0.09 | −0.3 % ± 0.6 pp |
Equal-split alternative for the interaction: TP 62.7 %, storage 18.1 %. Each named cause is corroborated
by a direct measurement above.

## Remaining uncertainty
- Common shift 8.3 % ± 1.7 pp (HC3); a repeat sweep with another job mix: 4–14 % (bootstrap).
- Assumes additivity apart from one interaction, and no selection in exposure (natural experiment).
- Not measured: GDR bandwidth loss on hardware (needs L3 test T6); container diff.

## Recommended changes and validation
1. Restore TP-packed placement: predicted −8.8 to −9.2 s on affected jobs; canary one job; n = 5 per
   arm, MDE 0.19 s; abort if any TP group spans nodes in placement records.
2. Load the peer-memory module on R570 nodes (drained, Chapter 16): predicted −0.8 to −1.0 s on affected
   jobs; validate /GDRDMA on channel lines and L3 busbw; abort if busbw below fleet baseline.
3. Four dataloader workers (or move hot datasets back): predicted −1.2 to −1.4 s on TP-packed
   capacity-tier jobs; n = 5, MDE 0.19 s; abort if host memory pressure or p99 does not fall.
```

**Why this earns full marks.** Measured facts contain only observations with method and n, no causal
words ("because", "caused by"); the attribution shows all six rows summing to 100 % with intervals; the
alert verdict is evidence-based; each fix has a predicted range (effect ± 2 SE), scope, MDE at n = 5
(2.8 × 0.11 × √(2/5) = 0.19 s) and an abort condition. L3 learners add the placement A/B results labelled
`[MEASURED]` with a manifest.

**Deductions.** Causal language in Measured facts; unlabelled numbers; dropping the interaction row
(shares exceed 100 %); a recommendation without predicted effect or abort condition.

## Hardware run

`python scripts/hw_labs.py run ch22 --device gpu` writes a before/after report in this exercise's shape, on
regressions whose ground truth is known. The measured facts are the copy bandwidths, the interleaved A/B and the
per-job step times. The inferred causes are the lab's OLS attribution of the injected pageable-copy and
micro-batch changes, with a placebo ruled out. The remaining uncertainty is the common-shift term and the MDE
from the before-period spread. Use it to check your report's structure against real numbers before the L3
canary. With `--device cpu` the same design runs on the host (strided-gather data path, per-job medians).
