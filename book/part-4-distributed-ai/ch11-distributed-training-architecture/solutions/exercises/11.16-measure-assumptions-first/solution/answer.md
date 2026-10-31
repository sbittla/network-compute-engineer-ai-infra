# 11.16 — Which three Table 11.4 assumptions to measure first, and how

Choose by sensitivity: the assumptions that move the step time most (Exercise 11.11) are the ones to
replace with `[MEASURED]` values first.

1. **Kernel efficiency (0.50).** It scales the 13.9 s compute term, ≈ 80 % of the step; ±10 % moves the
   step by ≈ 1.3 s. *How:* profile a few steps with PyTorch profiler or Nsight Systems/Compute and
   compute achieved TFLOP/s of the GEMMs and attention kernels (FLOPs from shapes ÷ kernel time) against
   the 989 TFLOP/s BF16 dense peak; also measure end-to-end MFU from step time.
2. **TP overlap fraction (25 %).** Exposed TP is the largest communication term (3.08 s); 25 % → 60 %
   is worth 1.44 s. *How:* an Nsight Systems trace of one step; measure the fraction of NCCL kernel time
   that runs concurrently with compute kernels on other streams, per layer.
3. **Effective NVLink and rail busbw at the real message sizes (300 GB/s, 45 GB/s).** The model uses
   plateau values, but TP all-reduces are 67 MB and DP buckets ≈ 25 MB, below or near n½ on multi-node
   rings. *How:* `nccl-tests` (`all_reduce_perf`, `sendrecv_perf`) on the real communicator shapes —
   8 GPUs in one node, 8 nodes on one rail — at 1–256 MB, ≥ 5 launches, median (Chapter 12).

Also defensible: the fixed memory overhead (4 GB — measure with allocator peak statistics), the DP
backward fraction (overlap window), or the inter-node latency (30 µs, from small-message nccl-tests).

Record each measurement with its environment manifest and replace the `[ILLUSTRATIVE]` value in
`cluster_orion.yaml`, then rerun the candidate ranking: a ranking that flips is the real finding.
