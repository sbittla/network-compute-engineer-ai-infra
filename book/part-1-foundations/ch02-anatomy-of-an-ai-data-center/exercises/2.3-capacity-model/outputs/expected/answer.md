# 2.3 — ORION-128 simplified capacity model

Method: manuscript Section 2.9 ("The capacity model", "Four kinds of utilization") applied to ORION-128 from
Exercise 2.2. All outputs `[MODELED]` from the exercise's `[ILLUSTRATIVE]` assumptions; `solve.py` is the
reference model (formulas visible) and writes the same table.

| Line | Formula | Result `[MODELED]` |
|---|---|---|
| Accelerators | 16 nodes × 8 | 128 GPUs |
| Total HBM | 128 × 80 GB | 10,240 GB |
| Usable HBM | 128 × 80 × 0.90 | 9,216 GB (72 GB per GPU) |
| Training state per GPU | 13e9 × 16 B ÷ (TP 8 × PP 1) | 26.0 GB: fits in 72 GB with 46 GB left for activations |
| Storage read / write | 4 × 20; 4 × 10 GB/s | 80 GB/s; 40 GB/s |
| Read per GPU | 80 ÷ 128 | 0.625 GB/s |
| Checkpoint size | 13e9 × 14 B | 182 GB |
| Checkpoint lower bound | 182 ÷ 40 GB/s | 4.55 s |
| Bisection per direction | from 2.2 | 25.6 Tb/s |
| GPU racks, IT maximum | 5 × 30.8 + 1 × 10.4 kW (3,3,3,3,3,1 layout) | 164.4 kW |
| IT maximum, total | 164.4 + 10.0 + 4.5 + 3.0 | 181.9 kW |
| Facility power | 181.9 × 1.30 | 236.5 kW |
| Allocated GPU-hours per year | 128 × 8,760 × 0.80 | 897,024 |
| Durable fraction of peak | 0.80 × 0.38 × 0.92 | 0.28 |

The balanced 4 × 3 + 2 × 2 layout gives the same GPU-rack total (4 × 30.8 + 2 × 20.6 = 164.4 kW),
because rack power depends only on the node count plus 0.2 kW per rack.

Training state is *not* divided by data parallelism: without a sharded optimizer, every DP replica holds a
full copy of its TP shard.

**Item 6, if the model doubles to 26 × 10⁹ parameters:** per-GPU state doubles to 52 GB at TP 8, PP 1.
That still fits under 72 GB but leaves only 20 GB for activations, so **GPU memory binds first** and forces
PP > 1 or a sharded optimizer. The checkpoint doubles to 364 GB (9.1 s), still small, and compute only
lengthens the step. Storage write binds first only if the learner argues, with numbers, for very
frequent checkpoints.

**Interpretation (three sentences).** ORION-128 has ample storage and fabric for a 13B model: a
checkpoint takes under 5 s and each GPU gets 0.625 GB/s of read bandwidth. Only 28 % of the cluster's
peak capability becomes durable progress, so allocation, MFU and goodput are better levers than more
hardware. GPU memory is the first resource to bind as the model grows.

**Common wrong answers:** using GiB for HBM; forgetting the 10 % reserve; dividing training state by DP.
