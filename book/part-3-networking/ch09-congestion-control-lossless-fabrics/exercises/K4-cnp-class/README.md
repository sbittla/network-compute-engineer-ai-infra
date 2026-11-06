# K4 — CNPs in the wrong class (★★, L1)

Type: Knowledge check · kind: `written` · 4 points

## Prompt

<!-- prompt:start -->
**K4 ★★ L1 — CNP class.** ORION carries CNPs in DSCP 48 / TC 6 with strict priority. Explain what goes
wrong, step by step, if a leaf maps CNPs into TC 3 instead.
*Evidence required:* a causal chain of at least three steps ending in an observable counter symptom.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/K4-cnp-class/` (instructor material in the full repository; removed from student releases).

## What to submit

Answer in prose (a short table is fine where it helps); name the counters and cite the manuscript section you rely on. Put every deliverable in `outputs/`:

- `outputs/answer.md`
