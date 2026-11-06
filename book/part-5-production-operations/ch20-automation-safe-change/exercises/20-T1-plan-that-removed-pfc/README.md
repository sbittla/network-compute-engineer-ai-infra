# 20-T1 — The plan that wanted to remove PFC (★★★, L1)

Type: Troubleshooting · Kind: `written` · Points: 15

## Prompt

<!-- prompt:start -->
At 02:10 the nightly fabric reconciler posts this dry-run plan for review (it normally plans 0–3
actions):

```text
[ILLUSTRATIVE] reconciler dry-run  change=nightly-reconcile  desired=commit 41aa9d3 (unchanged since yesterday)
plan: 16 targets, 48 actions
  orion-n17  pfc_priorities   [3]   -> []
  orion-n17  ecn_enabled      true  -> false
  orion-n17  trust_mode       dscp  -> pcp
  ... (same three actions for orion-n18 .. orion-n32)
```

Supporting evidence:

```text
[ILLUSTRATIVE] reconciler log
02:09:58 inventory GET /api/groups/roce-lossless/members  status=200  items=16  next=/api/groups/roce-lossless/members?page=2
02:09:58 render: 16 targets in group roce-lossless -> profile lossless-v3
02:09:58 render: 16 targets not in any lossless group -> profile default (lossy)
02:10:01 diff complete: 48 actions
```

Nobody changed the desired-state repository. Yesterday's run planned 0 actions.

a. Rank three hypotheses and name the discriminating evidence for each.
b. Identify the root cause.
c. What would have happened with no safety controls? Which controls in Table 20.11 stop it?
d. Specify the fix and the validation, plus one new guard that prevents this class of defect.

**Evidence required:** ranked hypotheses with discriminating tests; root cause tied to specific log
lines; fix, validation, and guard.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 20 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are ORION `[ILLUSTRATIVE]` unless stated.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md` (a-d)
