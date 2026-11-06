# K9 — Silent data corruption (★★, L1)

Type: Knowledge check · Kind: `written` · Points: 5

## Prompt

<!-- prompt:start -->
**K9 ★★ L1 — Silent data corruption.** Training loss on a 512-node job spikes at step 41,200 and
recovers slowly; there are no Xids, AER errors, link events, or NCCL warnings. Explain why none of the
detectors in Tables 19.4–19.5 fired, how you would find the faulty node, and which checkpoint you
restore.
*Evidence required:* why SDC evades error-based detectors; two detection methods; the restore choice
with its reason.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/K9-silent-data-corruption/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`
