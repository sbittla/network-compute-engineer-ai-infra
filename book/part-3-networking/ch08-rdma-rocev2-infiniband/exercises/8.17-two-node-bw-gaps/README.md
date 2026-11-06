# 8.17 — What a two-node ib_write_bw does not tell you (★, L1)

Type: Reflection · kind: `written` · 3 points

## Prompt

<!-- prompt:start -->
**8.17** ★ · L1 — Name three things a two-node `ib_write_bw` result at 390 Gb/s does **not** tell you about
a 256-GPU training job on the same fabric. *Evidence required:* three distinct gaps, each tied to a
mechanism (e.g., congestion, rail collisions, GPUDirect path).
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/8.17-two-node-bw-gaps/` (instructor material in the full repository; removed from student releases).

## What to submit

Answer in prose (a short table is fine where it helps); cite the manuscript section you rely on and label any number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
