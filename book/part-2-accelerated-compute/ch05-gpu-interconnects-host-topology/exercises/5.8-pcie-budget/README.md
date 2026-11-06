# Exercise 5.8 — PCIe budget

★★ · Tier L1 · worked problem · kind: `computed`

<!-- prompt:start -->
**5.8** ★★ L1 — *PCIe budget.* (a) Compute per-direction theoretical bandwidth of Gen4 x16, Gen5 x8 and
Gen5 x16. (b) Which can carry a 400 Gb/s NIC at line rate? (c) An HX8 PCIe switch carries two GPUs and two
400 Gb/s NICs behind one Gen5 x16 uplink to the CPU. With GPUDirect RDMA, how much of the NIC traffic uses
the uplink? Without GDR (host-staged)? *Evidence required:* arithmetic for (a), justification for (b),
two traffic estimates for (c) with assumptions.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 5.4 model parameters.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/5.8-pcie-budget/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
