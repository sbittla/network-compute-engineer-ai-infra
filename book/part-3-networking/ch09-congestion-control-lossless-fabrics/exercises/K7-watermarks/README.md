# K7 — Instantaneous samples versus watermarks (★, L1)

Type: Knowledge check · kind: `written` · 3 points

## Prompt

<!-- prompt:start -->
**K7 ★ L1 — Watermarks.** A dashboard samples instantaneous queue depth every 10 s and shows ≤ 20 KB at
all times, yet ECN-marked counters increase by 2 million per interval. Explain the contradiction and
what you would plot instead.
*Evidence required:* explanation and the replacement metric.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Answer in prose (a short table is fine where it helps); name the counters and cite the manuscript section you rely on. Put every deliverable in `outputs/`:

- `outputs/answer.md`
