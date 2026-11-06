# K2 · PCIe Gen 1 at idle: defect or power management? (★ · L1)

Type: knowledge-check · Kind: written · Points: 5

<!-- prompt:start -->
**K2 ★ (L1).** On an idle HX8, `nvidia-smi` reports `pcie.link.gen.current = 1` and
`pcie.link.width.current = 16` for GPU 0. Under a burn-in load it reports Gen 5 x16. Is this a
defect? What would make it one?
*Evidence required:* verdict with the mechanism (idle power management) and the condition that
would indicate a defect.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 16 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line; cite the
manuscript Section, table, or lab file you relied on, and label any number you use with its evidence class
(`[MODELED]`, `[ILLUSTRATIVE]`, `[SIMULATED]`, ...).
