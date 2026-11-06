# 7.K3 — MTU mismatch and the eBGP session (★★, L1)

Type: Knowledge check · kind: `written` · 4 points

## Prompt

<!-- prompt:start -->
**7.K3** ★★ L1 — A leaf-spine link has MTU 9216 on one end and 1500 on the other. Explain why the
eBGP session on that link comes up and stays up, and which traffic fails.
*Evidence required:* the role of the TCP MSS; the direction(s) in which large frames are lost.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 7 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Answer in prose (a short table is fine where it helps); cite the manuscript section you rely on. Put every deliverable in `outputs/`:

- `outputs/answer.md`
