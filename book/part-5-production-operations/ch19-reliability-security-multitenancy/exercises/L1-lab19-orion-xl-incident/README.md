# L1 — Lab 19: ORION-XL incident (★★★, L1)

Type: Hands-on lab · Kind: `lab` · Points: 100

## Prompt

<!-- prompt:start -->
**L1 ★★★ L1 — Lab 19: ORION-XL incident** ([lab/README.md](../../lab/README.md)). Implement
`lab/starter/incident_toolkit.py`, pass `python check.py`, and submit the incident packet.
*Evidence required:* 12/12 PASS; `incident_packet.md` per lab README Section 8.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/check_output.txt` (the `python check.py` report)
- `outputs/incident_packet.md`

Run:

```bash
cd ../../lab
python check.py > ../exercises/L1-lab19-orion-xl-incident/outputs/check_output.txt   # checks your starter/incident_toolkit.py
```
