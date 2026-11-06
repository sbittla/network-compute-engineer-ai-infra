# 7.K8 — Why one leaf is a cluster-wide fault domain (★, L1)

Type: Knowledge check · kind: `written` · 3 points

## Prompt

<!-- prompt:start -->
**7.K8** ★ L1 — Why is a single leaf a *cluster-wide* fault domain in ORION, whereas a top-of-rack
leaf failure in a conventional design affects one rack?
*Evidence required:* the rail mapping argument and its effect on a 256-GPU job.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/7.K8-leaf-fault-domain/` (instructor material in the full repository; removed from student releases).

## What to submit

Answer in prose (a short table is fine where it helps); cite the manuscript section you rely on. Put every deliverable in `outputs/`:

- `outputs/answer.md`
