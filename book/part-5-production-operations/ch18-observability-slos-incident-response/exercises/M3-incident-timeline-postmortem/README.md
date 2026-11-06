# M3 · INC-2291 timeline and blameless postmortem (★★★ · L1)

Type: outline-mandated · Kind: lab · Points: 25

<!-- prompt:start -->
**M3 ★★★ L1 — Incident timeline and postmortem for a cluster-wide throughput regression.** Using the
Lab 18 bundle, write the incident timeline (onset, detection, declaration, mitigation, resolution with
TTD/TTM/TTR) and a blameless postmortem from the template, including impact with evidence labels,
rejected hypotheses with the evidence that rejected them, and ≥ 5 action items typed detect /
mitigate / prevent with owners. *(Deliverable: `postmortem.md`.)*
*Evidence required:* timeline table; postmortem; checker PASS on T5.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put these files in `outputs/`:

- `postmortem.md` — rendered from `lab/data/postmortem_template.md` with `render_postmortem()`, then
  edited into prose, including the timeline table
- `check_output.txt` — `cd lab && python check.py` (T5 must PASS)
