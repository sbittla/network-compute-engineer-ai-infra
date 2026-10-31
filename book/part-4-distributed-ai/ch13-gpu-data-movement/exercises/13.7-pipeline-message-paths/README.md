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

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
