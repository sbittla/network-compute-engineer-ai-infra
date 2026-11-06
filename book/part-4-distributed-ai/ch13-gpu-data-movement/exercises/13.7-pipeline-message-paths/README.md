# 13.7 — One pipeline message, two paths (★★, L1)

Type: worked-problem · Kind: computed

## Prompt

<!-- prompt:start -->
**13.7 ★★ L1 — One pipeline message, two paths.** For one 8.39 MB (M/t = 67.1 MB / 8) pipeline
activation message between two ORION nodes, count host-DRAM copies, PCIe transfers, and total PCIe
bytes with and without GPUDirect RDMA. Estimate the transfer time with GPUDirect RDMA (45 GB/s
effective NIC) and an upper bound without it if staging is not pipelined (50 GB/s per copy).
*Evidence required:* a two-row table and both times with arithmetic.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
