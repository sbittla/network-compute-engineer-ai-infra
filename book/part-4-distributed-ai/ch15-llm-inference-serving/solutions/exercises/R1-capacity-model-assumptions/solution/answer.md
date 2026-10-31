# R1 — Capacity-model assumptions to measure: worked solution

| Parameter (lab value) | Output it drives | Why it matters | L2/L3 measurement |
|---|---|---|---|
| HBM efficiency 0.70 and step overhead 3 ms | Decode step, so TPOT and tokens/s | TPOT = 3 ms + bytes / (bw × 0.70). At 0.55 efficiency T-tp4-fp8's 20.2 ms becomes ≈ 24.9 ms; overhead adds directly | L2: sweep batch 1–128 at fixed context on one replica with the real engine (CUDA graphs on). Fit step time = a + b × bytes. Read DCGM DRAM active for cross-checking |
| Prefill MFU 0.40 | t_p, so TTFT, ρ_prefill and the pool size | t_p ∝ 1/MFU. At 0.30, t_p at 4k rises from 181 to 241 ms and W2's 10-replica pool runs at ρ = 0.60 | L2: time prefill for 1k–16k prompts at batch 1, including the attention kernel; compute achieved FLOP/s |
| KV-transfer efficiency 0.85 and its tail | Disaggregation feasibility, token-2 ITL | Sets transfer time and link headroom. The tail (case T1) matters more than the mean | L3: `ib_write_bw` between rail-local NICs, then connector-level transfer time p50/p99 for real KV sizes under background traffic |

**Why these three.** Each scales a headline number linearly or worse. Two of them (efficiency, MFU) are
`[ILLUSTRATIVE]` guesses that vary by engine version and kernel. The third decides an architectural
choice (shared vs disaggregated) that is expensive to reverse. Other parameters, such as KV bytes per
token and the weight size, are architecture facts and do not need measuring.

## Hardware run

`python scripts/hw_labs.py run ch15 --device gpu` runs a scripted, engine-free version of the first two L2
measurements on one GPU (`lab/l2/experiment.py`, a random-weight GQA decoder with no download). It sweeps
decode over batch and context, fits step time = overhead + bytes / B, and divides the `decode_step_time_s`
lower bound by the measured step to get the implied `hbm_efficiency`. It times prefill from 128 to 2,048
tokens and divides `prefill_time_s` at MFU 1 by the measured time to get the implied `prefill_mfu`. It
also confirms that `kv_bytes_per_token` is exact (allocator delta), which supports the claim above that KV
bytes per token need no measurement. The values describe eager PyTorch with no CUDA graphs on a laptop
GPU, so they show the method and the shape, not engine numbers for W-INFER. The third parameter (KV
transfer over RDMA) is L3 and is listed as not runnable. **Fallback:** with no GPU, the same sweeps run in
FP32 on the CPU, and the bandwidth and peak bounds are skipped.
