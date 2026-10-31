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

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/
```
