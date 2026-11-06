# 8.1 — Keys and access rights (★, L1)

Type: Knowledge check · kind: `written` · 5 points

## Prompt

<!-- prompt:start -->
**8.1 Keys and access rights** ★ · L1
Explain the difference between an `lkey` and an `rkey`. An initiator posts an RDMA WRITE to a remote
buffer whose MR was registered with only `IBV_ACCESS_LOCAL_WRITE | IBV_ACCESS_REMOTE_READ`. What
happens, where is it reported, and what state does the initiator's QP end up in?
*Evidence required:* correct definitions; the failing check and the completion status; resulting QP
state.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/8.1-keys-access-rights/` (instructor material in the full repository; removed from student releases).

## What to submit

Answer in prose (a short table is fine where it helps); cite the manuscript section you rely on and label any number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
