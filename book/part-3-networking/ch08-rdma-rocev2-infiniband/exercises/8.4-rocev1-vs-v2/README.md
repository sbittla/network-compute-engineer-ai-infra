# 8.4 — RoCEv1 versus RoCEv2 (★, L1)

Type: Knowledge check · kind: `written` · 5 points

## Prompt

<!-- prompt:start -->
**8.4 v1 versus v2** ★ · L1
Explain why a RoCEv1 GID cannot work on ORION's backend, and what an operator would see in counters
on the leaf and on the hosts.
*Evidence required:* encapsulation difference (EtherType vs UDP/IP); routed /31 consequence; at least
two counter-level signatures.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Answer in prose (a short table is fine where it helps); cite the manuscript section you rely on and label any number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
