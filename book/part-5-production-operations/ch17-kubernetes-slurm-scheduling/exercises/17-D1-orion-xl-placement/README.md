# 17-D1 · ORION-XL block placement rules (★★★ · L1)

Type: design-challenge · Kind: computed · Points: 10

<!-- prompt:start -->
**17-D1** ★★★ L1 — ORION-XL placement. ORION-XL has 512 HX8 nodes; each block of 32 nodes (a canonical ORION-XL pod,
`p00`–`p15`) shares one set of 8 rail leaves, and cross-block traffic crosses a spine tier with 2:1 oversubscription
`[ILLUSTRATIVE]` for this exercise. W-TRAIN is scaled to 64 nodes (512 GPUs). Design the placement
rules: (a) write the `topology.conf` structure (or the equivalent Kubernetes topology labels);
(b) decide whether a 64-node job must be confined to 2 blocks, may use 3, or may spread freely, and
quantify the cross-block traffic exposure; (c) choose a `--switches` (or equivalent) maximum wait and
defend it against the GPU-hours lost while waiting.
*Evidence required:* the config fragment, a modeled comparison of placements (show formula), and a
wait-time trade-off with numbers.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
