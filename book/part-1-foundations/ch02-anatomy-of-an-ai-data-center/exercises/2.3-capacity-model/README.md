# Exercise 2.3 — Simplified capacity model

**Difficulty:** ★★ · **Tier:** L1 · **Type:** outline-mandated · **Kind:** computed · **Points:** 20

## Prompt

<!-- prompt:start -->
*(Outline-mandated: build a simplified capacity model that includes accelerator count, usable GPU
memory, storage throughput, network bisection bandwidth, power, and utilization.)*

Extend ORION-128 from Exercise 2.2 with these assumptions `[ILLUSTRATIVE]`: 10 % of each GPU's 80 GB
reserved for runtime and fragmentation; workload is a 13 × 10⁹-parameter dense model trained with
16 B/param of training state, TP = 8, PP = 1, and a 14 B/param checkpoint; storage is 4 servers at
20 GB/s read and 10 GB/s write each; non-GPU racks draw 10.0 kW (network), 4.5 kW (storage), and
3.0 kW (management) at maximum; PUE 1.30; allocation target 80 %; MFU 38 %; goodput 92 %.

Build the model as a spreadsheet or a short Python script and report:

1. Accelerator count, total and usable HBM (GB), and per-GPU training state (GB). Does the state fit?
2. Aggregate storage read and write (GB/s), read per GPU, and the lower-bound checkpoint write time.
3. Bisection bandwidth per direction (from Exercise 2.2).
4. IT maximum power (kW) and facility power at the stated PUE.
5. Allocated GPU-hours per year and the fraction of peak capability that becomes durable progress.
6. Which resource would you expect to bind first if the team doubled the model size? Justify.

**Evidence required:** the model file or table with formulas visible; every output labelled
`[MODELED]`; a three-sentence interpretation.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/capacity_model.py`: or capacity_model.xlsx/.csv: the model with formulas visible
- `outputs/capacity.md`: the outputs labelled `[MODELED]` and a three-sentence interpretation

Command to run (from this folder):

```bash
python outputs/capacity_model.py > outputs/capacity.md
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
