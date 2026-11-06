# K4 — PCIe evidence (★, L1)

Type: Knowledge check · Kind: `computed` · Points: 6

## Prompt

<!-- prompt:start -->
**K4 ★ L1 — PCIe evidence.** Distinguish correctable, uncorrectable non-fatal, and fatal AER errors.
What does `LnkSta: Speed 32GT/s, Width x8` under `LnkCap: … Width x16` mean for a GPU's achievable
host bandwidth?
*Evidence required:* three definitions; bandwidth before/after in GB/s per direction.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/K4-pcie-evidence/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md` (definitions and bandwidth arithmetic)
