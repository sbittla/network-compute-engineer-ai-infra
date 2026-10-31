# 4.7 — Low occupancy: fine for the GEMM, fatal for the layernorm (model answer)

Relies on manuscript Section 4.3 ("Latency hiding and why occupancy exists"), Section 4.7 ("When occupancy
matters") and Section 4.8 (Tensor Cores). `solve.py` reproduces the Little's-law arithmetic `[MODELED]`.

**The GEMM (18.75 % occupancy, 12 of 64 warps).** Occupancy is only a proxy for "enough independent work in
flight". A Hopper GEMM gets that work from inside each warp rather than from many warps:

- TMA (Tensor Memory Accelerator) copies whole tiles from HBM into shared memory asynchronously, so one
  thread can have tens of kilobytes in flight;
- warp-group MMA (`wgmma`) instructions are asynchronous: a warp group issues a large matrix multiply-
  accumulate and continues, so instruction-level parallelism is high;
- large tiles are reused from shared memory many times (high arithmetic intensity), so the tensor pipes stay
  fed with only a few hundred bytes of HBM traffic per thousand FLOPs.

The result is 60 %+ of the BF16 roof at low occupancy. More warps would only cost registers and shared memory
that the tiles need.

**The layernorm backward (12.5 %, 8 warps).** It is memory-bound, so throughput is set by bytes in flight
(Little's law):

- Needed per SM = 3.35 × 10¹² B/s × 600 × 10⁻⁹ s / 132 = 2,010,000 B / 132 = **15,227 B ≈ 15.2 KB**.
- Available = 8 warps × ≈ 3.25 outstanding 128-B requests × 128 B = **3,328 B ≈ 3.3 KB**.
- Fraction = 3,328 / 15,227 = **21.9 % ≈ 22 %** of HBM bandwidth (≈ 0.73 TB/s), which is what the lab measures
  (21.6 %).

With one request per warp it would be 8 × 128 / 15,227 = 6.7 %; the vectorized 16-B loads are what lift it to
≈ 3 KB. The fix is more bytes in flight: fewer registers (more resident warps) or more independent loads per
warp.

**Common wrong answers.** "Low occupancy is always bad" (flagging the GEMM); "the layernorm needs more FLOPs";
quoting the occupancy without connecting it to bytes in flight.
