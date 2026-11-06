# O3 — Design a controlled congestion experiment (★★★, L1)

Type: Outline-mandated · kind: `written` · 20 points

## Prompt

<!-- prompt:start -->
**O3 ★★★ L1 (L3 to execute) — Controlled experiment.** Design a controlled experiment comparing
congestion behaviour under two documented configurations (choose: ECN thresholds as in the lab's A vs B,
or PFC on vs off with selective retransmission). State what cannot be concluded from the lab's
simulation, and what your experiment would and would not establish.
*Evidence required:* hypothesis; both configurations in full; workload; one controlled variable;
repetitions (≥ 5) and warm-up; metrics; analysis method; environment manifest fields; safety boundary;
a "cannot conclude" list of at least four items specific to the model.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Write the experiment plan; it is executed only on a dedicated L3 lab fabric. Put every deliverable in `outputs/`:

- `outputs/experiment_plan.md`
