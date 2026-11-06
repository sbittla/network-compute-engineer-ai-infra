# K5 · Who is pausing whom? (★ · L1)

Type: knowledge-check · Kind: written · Points: 4

<!-- prompt:start -->
**K5 ★ L1 — Who is pausing whom?** A backend host's `ethtool -S` shows `rx_prio3_pause` rising fast and
`tx_prio3_pause` flat. Another host shows the opposite. Interpret each.
*Evidence required:* direction of the pause for each host and the likely location of the bottleneck.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 18 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line, cite the
manuscript Section, table, metric, or lab data file you used, and label numbers with their evidence
class (`[MODELED]`, `[SIMULATED]`, `[ILLUSTRATIVE]`).
