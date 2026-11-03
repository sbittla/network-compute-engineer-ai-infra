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

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`
