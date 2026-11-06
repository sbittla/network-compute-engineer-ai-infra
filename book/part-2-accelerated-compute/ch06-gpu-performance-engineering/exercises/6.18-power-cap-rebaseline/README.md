# Exercise 6.18 — Re-baselining under a 500 W power cap

★★ · Tier L1 · reflection · kind: `written`

<!-- prompt:start -->
**6.18** ★★ L1 — Which of this chapter's numbers would change if ORION ran with a 500 W power cap, and how
would you re-baseline?
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 6.1 ceilings (989 TFLOP/s dense BF16, 1,979 TFLOP/s FP8, 67 TFLOP/s FP32 SIMT, 3.35 TB/s HBM).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/6.18-power-cap-rebaseline/` (instructor material in the full repository; removed from student releases).

*Evidence required for 6.16–6.20:* short written answers (≤ 150 words each) citing specific mechanisms or data.

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
