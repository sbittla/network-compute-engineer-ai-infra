# M3 — Present evidence, failure exercise and backlog (grading guide)

**Source:** manuscript Section 23.8 (failure exercise, Figure 23.5), Section 23.9 (Table 23.9 talk
structure, Table 23.10 backlog); key G (M3).

**Slides (Table 23.9, 20 minutes).** Problem and the one success number (2 min); architecture and data
paths (3); three decision-critical assumptions with sensitivity (3); key ADRs with revisit triggers (3);
failure domains (3); evidence table with labels (3); failure exercise (2); top three backlog items (1).
Every claim shows its label on the slide: if a reviewer must ask "is that measured?", the slide is wrong.

**Failure-exercise report.** A one-page plan and result: hypothesis (e.g. "when `orion-be-leaf-r3` fails
the job is detected as hung within 2 min and restarts from the last checkpoint"), expected signals in
order, measurements, abort criteria and rollback. Labels by tier: a tabletop's estimated times are
`[ILLUSTRATIVE]`, an injected synthetic stream is `[SIMULATED]`, a lab injection is `[MEASURED]`.
Lost GPU-hours must be computed, e.g. for a 256-GPU job with τ = 4,554 s and R = 900 s:
(τ/2 + R) × 256 / 3,600 = (2,277 + 900) × 256 / 3,600 ≈ 225.9 GPU-hours `[MODELED]` per failure
(Section 23.10). The "Validate" step (loss curve continuous, step time back to baseline) must appear.

**Backlog.** Score = (impact × confidence) ÷ effort, impact and effort 1–5, confidence a fraction; safety
and blocker-class risks first regardless of score. Example from Table 23.10: measure MFU on a 64-GPU slice
(5 × 0.9 / 2 = 2.25) first; leaf–spine ADR (2 × 1.0 / 1 = 2.00) second because it is cheap. A rationale
column the reviewers could dispute is mandatory.

**Deduct** for unlabelled claims, a tabletop reported as `[MEASURED]`, missing TTD/TTM/TTR, or a backlog
with no stated criteria.
