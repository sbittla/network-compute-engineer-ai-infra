# Exercise 5.17 — Four-NIC node variant

★★★ · Tier L1 · design challenge · kind: `computed`

<!-- prompt:start -->
**5.17** ★★★ L1 — A cheaper node variant has 8 GPUs but only **4** × 400 Gb/s compute NICs, one per PCIe
switch (each switch: 2 GPUs + 1 NIC, each on its own downstream port, so both GPUs are `PIX` to the NIC). Design the rail architecture (4 or 8 rails?), the GPU→NIC mapping,
rank placement, and the NCCL/launcher settings; estimate the modeled busbw against HX8 for a 1 GiB
all-reduce over 32 nodes (a full-cluster job, unlike the 16-node worked example; state assumptions); and decide which workloads you would schedule on it.
*Evidence required:* topology diagram, mapping, model arithmetic, workload recommendation with a rejected
alternative.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 5 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 5.4 model parameters.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
