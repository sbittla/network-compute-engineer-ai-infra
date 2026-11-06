# 13.9 — Trace a communication path (O1) (★★, L1)

Type: outline-mandated · Kind: written

## Prompt

<!-- prompt:start -->
**13.9 (O1) ★★ L1 — Trace a communication path.** Draw (Mermaid or ASCII) the path of a data-parallel
gradient chunk from GPU 6 on `orion-n05` to GPU 6 on `orion-n14`, annotating every hop (HBM, NCCL
buffer, PCIe switch, NIC, leaf name, NIC, PCIe switch, HBM) with its bandwidth class and an
illustrative latency. Draw it twice: with GPUDirect RDMA, and host-staged. Then show what changes if
the destination is GPU 2 on `orion-n14` (cross-rail).
*Evidence required:* two or three captioned diagrams, a copy/crossing count per variant, and the
canonical leaf/spine names used.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/13.9-trace-communication-path/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/path_diagrams.md (Mermaid or ASCII, with captions)`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
