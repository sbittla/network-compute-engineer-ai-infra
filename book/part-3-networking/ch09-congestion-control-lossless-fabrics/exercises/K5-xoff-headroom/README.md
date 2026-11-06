# K5 — Xoff threshold versus headroom (★★, L1)

Type: Knowledge check · kind: `written` · 4 points

## Prompt

<!-- prompt:start -->
**K5 ★★ L1 — Xoff and headroom.** Explain the difference between the Xoff threshold and the headroom
reservation. What is the observable symptom of undersized headroom, and why does it usually appear on
the longest links first?
*Evidence required:* two definitions; symptom naming a specific counter; reason tied to the formula.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 9 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Answer in prose (a short table is fine where it helps); name the counters and cite the manuscript section you rely on. Put every deliverable in `outputs/`:

- `outputs/answer.md`
