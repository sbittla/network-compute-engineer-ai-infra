# 8.5 — Entropy from the UDP source port (★★, L1)

Type: Knowledge check · kind: `written` · 5 points

## Prompt

<!-- prompt:start -->
**8.5 Entropy** ★★ · L1
What role does the UDP source port play in RoCEv2? A rail-to-rail all-to-all uses two QPs per NIC pair.
Explain why bandwidth may vary between otherwise identical runs, and two mitigations.
*Evidence required:* ECMP hashing mechanism; collision explanation; two mitigations with their
trade-off.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/8.5-udp-source-port-entropy/` (instructor material in the full repository; removed from student releases).

## What to submit

Answer in prose (a short table is fine where it helps); cite the manuscript section you rely on and label any number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
