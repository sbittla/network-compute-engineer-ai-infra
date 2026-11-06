# 6.4 — MFU and HFU (model answer, 3 points)

Relies on manuscript Section 6.4 ("Model FLOPs utilization").

**Formulas (1 point).**

- MFU (model FLOPs utilization) = model FLOPs per second / (number of GPUs × peak FLOP/s per GPU), with the
  dense-transformer convention of **6*N* FLOPs per token** (2*N* forward + 4*N* backward, *N* = parameters):
  MFU = 6*N* × tokens/s / (GPUs × peak).
- HFU (hardware FLOPs utilization) counts the FLOPs the hardware actually *executed*, including recomputation:
  with full activation recomputation the forward pass runs twice, ≈ **8*N* per token**:
  HFU = 8*N* × tokens/s / (GPUs × peak).

**Why HFU can exceed MFU (1 point).** Recomputed forward passes (activation checkpointing) are real work for
the GPU but not work the model requires; HFU counts them, MFU does not. With full recomputation
HFU = 8/6 × MFU (Exercise 6.9: 0.497 → 0.663; Lab 6 W-TRAIN: 40.0 % → 53.3 % `[MODELED]`). A job can therefore
raise HFU by recomputing more while getting slower.

**Which to report (1 point).** Report **MFU** when comparing clusters or software stacks: it measures useful
progress per unit of hardware and cannot be inflated by recomputation. State the convention (6*N*, attention
FLOPs included or not) and use the vendor **dense** peak for the precision trained (989 TFLOP/s BF16 on
ORION), never the sparse or FP8 peak for a BF16 job.

**Common wrong answers.** Calling HFU "hardware utilization from nvidia-smi"; using different peaks for the
two clusters.
