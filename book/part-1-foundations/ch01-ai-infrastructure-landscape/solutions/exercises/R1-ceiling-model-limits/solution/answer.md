# R1 — What the ceiling model cannot capture

Source: manuscript Section 1.6 (Equation block 1.1 and the max-versus-sum discussion). The model divides
work by *peak* rates and takes the maximum, assuming everything else overlaps perfectly.

| Limitation | Why the model misses it | Measurement that exposes it |
|---|---|---|
| Achievable versus peak rates | Real GEMMs reach a fraction of 989 TFLOP/s; NCCL bus bandwidth stays below 450 GB/s or 50 GB/s | Microbenchmarks: a GEMM sweep, `all_reduce_perf` (nccl-tests), `fio` for storage; compare with the peaks |
| Overlap of communication and compute | Max-of-bounds assumes perfect overlap; the sum assumes none; reality is in between | Nsight Systems timeline showing whether NCCL kernels run concurrently with compute kernels |
| Fixed latency and launch overhead | Bandwidth terms cannot see 160 × ≈ 10 µs all-reduce latencies or CPU launch gaps | Small-message `all_reduce_perf` latency; per-kernel gaps in the timeline; CUDA-graph on/off comparison |
| Stragglers and contention | One slow rank or another job on a shared PFS or fabric lengthens the step | Per-rank step timing, DCGM per-GPU clocks, PFS client statistics and switch counters during the job |

Any three rows earn full credit when each limitation is paired with a specific measurement. The W-INFER
decode gap (6.02 ms bound against 9.5 ms observed) is the chapter's concrete example: most of it is
all-reduce latency, which only the latency measurement reveals.
