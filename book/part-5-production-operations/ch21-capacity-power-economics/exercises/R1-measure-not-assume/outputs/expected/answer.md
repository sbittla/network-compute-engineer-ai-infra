# R1 — Measured rather than assumed: model answer

Sources: `lab/data/designs.yaml`, `lab/data/power_cap_curve.csv`, `lab/data/assumptions.yaml`;
manuscript Sections 21.4–21.5 (sensitivity, break-even) and 21.8.

Choose inputs by how much they move a *decision*, not by how uncertain they feel. The three that do:

1. **Design B's per-GPU throughput (2.2×, `designs.yaml`).** The design choice flips at ≈ 1.86×
   (Section 21.5). *Measure:* run W-TRAIN-like training and the inference benchmark on B-class
   hardware with the Chapter 22 method: warm-up, ≥ 5 runs, median and p95 step time, same model and
   parallelism, one variable changed. Include the 2:1 spine penalty by testing at a scale that crosses
   spines, or measure exposed communication and apply the Section 21.5 formula. Label the result
   `[MEASURED]` in the manifest.
2. **The power/throughput curve (`power_cap_curve.csv`) and the 4.6 kW node base
   (`power_cap_case.yaml`).** The 650 W option leaves 0.1 kW of planned headroom. A 2 % higher base
   changes the best cap to 600 W (Section 21.8). *Measure:* the lab's L2 extension, sweeping
   `nvidia-smi -pl` across the curve's caps on a dedicated host with a fixed benchmark and recording
   median step time and mean power. Measure node base power at the PDU/BMC (Redfish) with GPUs idle
   and at each cap. Repeat on several nodes, because the curve varies per GPU.
3. **Allocation and fragmentation factors (0.85 target, 5 % fragmentation, `assumptions.yaml`).**
   Allocation 0.85 → 0.75 moves cost per useful GPU-hour by +13 % (Table 21.4), more than any price
   input. *Measure:* a quarter of scheduler accounting, giving allocated GPU-hours over usable GPU-hours,
   plus the free-GPU histogram at the moments the head-of-queue job waits. That histogram measures
   fragmentation directly (Section 21.11).

Acceptable alternatives with the same reasoning: goodput (from step and failure records, Chapters
18–19), the repair fraction (from the measured MTTR), or the energized-kW schedule (from the
facility's commissioning plan).

## Hardware run

`python scripts/hw_labs.py run ch21 --device gpu` measures one of these inputs instead of assuming it: how power
and throughput relate on a real GPU. It duty-cycles a GEMM from 0 to 100 % and adds a memory-bound copy. It
records power every 100 ms, throughput, SM clock and `SW_POWER_CAP` share, and derives perf/W and a static-power
term. The cap sweep itself (`nvidia-smi -pl`) needs root on a dedicated bare-metal host, so the run records it as
not runnable and keeps the lab's modeled curve. That is the measurement this answer says must replace
`power_cap_curve.csv` on your own GPUs. With `--device cpu` the sweep runs on the CPU, where host power is not
readable.
