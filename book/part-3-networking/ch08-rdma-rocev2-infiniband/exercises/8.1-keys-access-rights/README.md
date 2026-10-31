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

## What to submit

Answer in prose (a short table is fine where it helps); cite the manuscript section you rely on and label any number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
