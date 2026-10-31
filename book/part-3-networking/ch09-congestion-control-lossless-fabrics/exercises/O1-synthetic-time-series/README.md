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

## What to submit

Quote rates computed by your own code (not raw cumulative counters), with units, for each episode. Put every deliverable in `outputs/`:

- `outputs/answer.md`
- `outputs/episode_values.csv` (the rates you quote, per episode and port)
