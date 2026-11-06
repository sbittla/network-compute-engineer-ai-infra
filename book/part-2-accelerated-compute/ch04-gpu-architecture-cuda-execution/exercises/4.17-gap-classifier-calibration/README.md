# Exercise 4.17 — Calibrating the gap classifier

★ · Tier L1 · reflection · kind: `written`

<!-- prompt:start -->
**4.17** ★ L1 — The lab's gap classifier uses a 10 µs launch-latency allowance and a 2 µs gap threshold.
How could each choice misclassify gaps on real hardware, and how would you calibrate them?
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 4 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

*Evidence required for 4.16–4.19:* short written answers (≤ 150 words each) that cite specific numbers or mechanisms.

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
