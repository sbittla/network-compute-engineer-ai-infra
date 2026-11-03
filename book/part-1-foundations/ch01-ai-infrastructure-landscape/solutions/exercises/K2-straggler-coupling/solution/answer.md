# K2 — Why one 10 % slow GPU costs about 10 % of a 256-GPU job

Source: manuscript Section 1.1 (coupling) and Section 1.7 (goodput). `[MODELED]`.

**Mechanism.** In synchronous data/tensor/pipeline-parallel training every step ends with collectives
(TP all-reduces, the DP gradient all-reduce). A collective completes only when *every* participant has
contributed, so step time = max over ranks, not the mean. If one GPU computes at 90 % of its peers'
speed, its share of the step takes 1 / 0.9 = 1.111× as long, and the other 255 GPUs finish early and
wait inside the NCCL kernel. The whole job advances at the slowest member's pace.

**Arithmetic** (`solve.py`, compute-bound step, all of the step scaled by the straggler):

```text
step time      = T / 0.9 = 1.111 T
job throughput = 0.9 of baseline  → loss = 10 %
GPU-equivalents lost = 0.10 × 256 = 25.6 GPUs
naive (wrong) answer = 10 % / 256 = 0.039 %
```

If "10 % slow" is read as "takes 10 % longer", throughput is 1 / 1.1 = 0.909, a 9.1 % loss
(23.3 GPU-equivalents): still ≈ 10 %, which is the point.

**Why it matters:** the 255 waiting GPUs still show high `nvidia-smi` utilization because they are inside a
running NCCL kernel (see K7). At $3.00/GPU-hour (Chapter 21) a 10 % straggler on ORION wastes
25.6 × $3.00 = $76.80 per hour.

**Marking note:** the key gives 2 points; this folder scores it out of 4 (the key's 2 × 2).
