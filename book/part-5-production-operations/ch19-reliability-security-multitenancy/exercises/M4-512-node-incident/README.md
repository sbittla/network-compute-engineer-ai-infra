# M4 — 512-node incident (★★★, L1)

Type: Outline-mandated · Kind: `lab` · Points: 30

## Prompt

<!-- prompt:start -->
**M4 ★★★ L1 — 512-node incident.** Given the synthetic 512-node training incident with
one flaky HCA, one GPU ECC fault, and an NCCL timeout (Lab 19), correlate logs and telemetry, identify
the smallest failure domain, quarantine the suspect component, and produce a safe restart plan.
Distinguish proven cause from correlation. Submit the failure timeline, rank-to-hardware mapping, health
decision, checkpoint/restore validation, recovery metrics, and a postmortem (Chapter 18 template).
*Evidence required:* checker PASS; the six artifacts.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/check_output.txt`
- `outputs/timeline.md`
- `outputs/rank_map_excerpt.md`
- `outputs/health_decision.md`
- `outputs/restore_validation.md`
- `outputs/recovery_metrics.md`
- `outputs/postmortem.md`

Run:

```bash
cd ../../lab
python check.py > ../exercises/M4-512-node-incident/outputs/check_output.txt   # checks your starter/incident_toolkit.py
```
