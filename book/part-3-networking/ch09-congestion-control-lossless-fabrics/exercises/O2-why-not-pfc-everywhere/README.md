# O2 — Why not PFC everywhere? (★★, L1)

Type: Outline-mandated · kind: `written` · 15 points

## Prompt

<!-- prompt:start -->
**O2 ★★ L1 — Why not PFC everywhere?** Explain why enabling PFC indiscriminately can create operational
risk. Then describe, as a numbered procedure an on-call engineer could follow, how you would
investigate pause propagation and head-of-line blocking on ORION using switch and NIC counters and
latency probes.
*Evidence required:* at least four distinct risks, each with its mechanism; a procedure of at least six
steps naming the counters read at each step and the decision rule applied.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/O2-why-not-pfc-everywhere/` (instructor material in the full repository; removed from student releases).

## What to submit

Answer in prose (a short table is fine where it helps); name the counters and cite the manuscript section you rely on. Put every deliverable in `outputs/`:

- `outputs/answer.md`
