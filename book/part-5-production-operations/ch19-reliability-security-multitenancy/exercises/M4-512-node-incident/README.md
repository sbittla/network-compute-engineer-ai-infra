# M4 — 512-node incident (Section 20.1) (★★★, L1)

Type: Outline-mandated · Kind: `lab` · Points: 30

## Prompt

<!-- prompt:start -->
**M4 ★★★ L1 — 512-node incident (Section 20.1).** Given the synthetic 512-node training incident with
one flaky HCA, one GPU ECC fault, and an NCCL timeout (Lab 19), correlate logs and telemetry, identify
the smallest failure domain, quarantine the suspect component, and produce a safe restart plan.
Distinguish proven cause from correlation. Submit the failure timeline, rank-to-hardware mapping, health
decision, checkpoint/restore validation, recovery metrics, and a postmortem (Chapter 18 template).
*Evidence required:* checker PASS; the six artifacts.
<!-- prompt:end -->

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
python check.py            # your starter/incident_toolkit.py > ../exercises/M4-512-node-incident/outputs/check_output.txt
```
