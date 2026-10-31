# Exercise 5.8 — PCIe budget

★★ · Tier L1 · worked problem · kind: `computed`

<!-- prompt:start -->
**5.8** ★★ L1 — *PCIe budget.* (a) Compute per-direction theoretical bandwidth of Gen4 x16, Gen5 x8 and
Gen5 x16. (b) Which can carry a 400 Gb/s NIC at line rate? (c) An HX8 PCIe switch carries two GPUs and two
400 Gb/s NICs behind one Gen5 x16 uplink to the CPU. With GPUDirect RDMA, how much of the NIC traffic uses
the uplink? Without GDR (host-staged)? *Evidence required:* arithmetic for (a), justification for (b),
two traffic estimates for (c) with assumptions.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/
```
