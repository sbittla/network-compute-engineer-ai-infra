# K3 — ECN codepoints and WRED (★, L1)

Type: Knowledge check · kind: `written` · 5 points

## Prompt

<!-- prompt:start -->
**K3 ★ L1 — ECN codepoints.** Give the IP ECN bit patterns for Not-ECT, ECT(0), ECT(1), and CE. Above
Kmin, what does a switch with both WRED and ECN enabled on a queue do to an ECT packet, and to a
Not-ECT packet? Why must the second behaviour never occur in ORION's TC 3?
*Evidence required:* four bit patterns; two behaviours; one reason.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/K3-ecn-codepoints/` (instructor material in the full repository; removed from student releases).

## What to submit

Answer in prose (a short table is fine where it helps); name the counters and cite the manuscript section you rely on. Put every deliverable in `outputs/`:

- `outputs/answer.md`
