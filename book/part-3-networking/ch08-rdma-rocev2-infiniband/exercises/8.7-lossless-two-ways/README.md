# 8.7 — Lossless two ways: credits and PFC (★★, L1)

Type: Knowledge check · kind: `written` · 5 points

## Prompt

<!-- prompt:start -->
**8.7 Lossless two ways** ★★ · L1
Compare InfiniBand credit-based flow control with Ethernet PFC: how each prevents buffer overflow,
why one needs headroom buffer and the other does not, and which counter shows back-pressure on each.
*Evidence required:* mechanism of each; headroom reasoning; `PortXmitWait` and per-priority pause
counters named.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Answer in prose (a short table is fine where it helps); cite the manuscript section you rely on and label any number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
