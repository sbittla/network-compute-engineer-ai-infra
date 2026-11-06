# Exercise 4.6 — NVTX ranges versus GPU kernel extent

★★ · Tier L1 · knowledge check · kind: `written`

<!-- prompt:start -->
**4.6** ★★ L1 — Nsight Systems shows an NVTX range `forward` lasting 2.3 ms, but the forward kernels
on the GPU row span 19.6 ms. Explain the discrepancy and how correlation IDs resolve it.
*Evidence required:* explanation of CPU-side ranges and the join.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/4.6-nvtx-cpu-side-ranges/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
