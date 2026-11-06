# M1 · Node acceptance test design (★★ · L1)

Type: outline-mandated · Kind: written · Points: 20

<!-- prompt:start -->
**M1 ★★ (L1; L2/L3 to execute) [Outline] — Node acceptance test design.** Design a node acceptance
test for an HX8 covering accelerator discovery, memory checks, NIC link validation, storage, thermals,
and burn-in (and, beyond the outline minimum, NVLink/fabric state, RDMA pair bandwidth, and a
single-node NCCL test). For each check give: the command or tool, what is measured, pass criterion,
FAIL vs WARN classification, approximate duration, and the order in which checks run.
*Evidence required:* a table with ≥ 12 checks in fail-fast order; every threshold labelled with its
evidence class; a total duration estimate; the policy-version field you will record.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/M1-node-acceptance-design/` (instructor material in the full repository; removed from student releases).

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line; cite the
manuscript Section, table, or lab file you relied on, and label every number with its evidence class
(`[MODELED]`, `[ILLUSTRATIVE]`, `[SIMULATED]`, ...).

On a single GPU host you can execute the GPU subset of your design with `python scripts/hw_labs.py run ch16 --device gpu`
(CPU fallback with `--device cpu`). The HX8-only checks are reported as not runnable. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.