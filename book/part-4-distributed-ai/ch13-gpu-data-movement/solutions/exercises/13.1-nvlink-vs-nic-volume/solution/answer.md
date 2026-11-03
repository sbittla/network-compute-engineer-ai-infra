# 13.1 — NVLink versus NIC bytes per step: worked solution

**Answer.** NVLink carries ≈ 122× (≈ 120×) more bytes per GPU per step than the NIC because tensor
parallelism (TP 8) keeps its traffic inside the node. `[MODELED]`

**Inputs (Table 13.1, Section 13.1, from Chapter 11 Table 11.2) `[MODELED]`:**

| Traffic | Bytes per GPU per step | Path |
|---|---|---|
| Tensor parallel | 1.20 TB | NVLink/NVSwitch |
| Data parallel | 7.66 GB | PCIe → NIC → rail leaf |
| Pipeline parallel | 2.15 GB | PCIe → NIC → rail leaf |

**Method.**

1. NIC bytes = DP + PP = 7.66 GB + 2.15 GB = **9.81 GB** per GPU per step.
2. Ratio = 1.20 × 10¹² B / 9.81 × 10⁹ B = **122.3** (the manuscript rounds to ≈ 122×; the prompt says
   "roughly 120×").
3. Against DP alone: 1.20 × 10¹² / 7.66 × 10⁹ = **156.7** (≈ 157×).

**Why.** Tensor parallelism splits every layer's matrix multiplications across the 8 GPUs of a node.
Each layer needs four collectives (all-reduce or reduce-scatter/all-gather pairs) per micro-batch in
forward and backward, each about 67 MB, about 10,240 collectives per step. That is why TP is mapped onto
NVLink/NVSwitch: 450 GB/s per direction per GPU, about 9× one 400 Gb/s (50 GB/s) NIC `[VENDOR-SPEC, 2026-10]`. DP reduces gradients once per step and
PP sends 8.4 MB activations between stages, so both are much smaller and go over the network.

**Consequence (Section 13.1).** Intra-node faults, such as a degraded NVLink or P2P falling back to PCIe,
are catastrophic because they hit the dominant volume. Inter-node faults show up as tail latency and
stragglers.

**Common wrong answers.** Comparing link bandwidths (450 GB/s vs 50 GB/s) instead of bytes moved.
Counting only DP and calling the result "120×" without the PP term. Attributing the volume to data
parallelism.
