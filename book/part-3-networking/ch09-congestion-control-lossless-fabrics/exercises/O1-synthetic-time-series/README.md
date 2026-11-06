# O1 — Analyze the synthetic time series (★★, L1)

Type: Outline-mandated · kind: `computed` · 12 points

## Prompt

<!-- prompt:start -->
**O1 ★★ L1 — Analyze a synthetic time series.** Analyze the lab's time series (queue depth, ECN marks,
CNPs, pause frames tx/rx, throughput, latency) and identify the likely congestion pattern of each
episode. For each, quote the two or three numbers (with units, from your rates) that most strongly
discriminate it from the alternatives.
*Evidence required:* per episode: label, root or source device, and the quoted discriminating values.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 9 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Quote rates computed by your own code (not raw cumulative counters), with units, for each episode. Put every deliverable in `outputs/`:

- `outputs/answer.md`
- `outputs/episode_values.csv` (the rates you quote, per episode and port)
