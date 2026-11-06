# 12.12 — Two rank mappings (★★★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
**12.12 (O3) ★★★ L1 — Two rank mappings.** Compare c2 (aligned) and c3 (alternative map). (a) Before
looking at the plateau, *predict* the plateau busbw of each from the topology (number of NICs used,
GPU↔NIC path type, GPUDirect RDMA on or off), with arithmetic. (b) Compare with the data. (c) List the
topology information you would need to *prove* the hypothesis on real hardware, the exact command or
log line for each item, and what result would falsify your hypothesis.
*Evidence required:* the prediction with arithmetic, the comparison, and an evidence table of at
least five items (artifact, command, expected result if hypothesis true, result that falsifies it).
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units and evidence labels
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
