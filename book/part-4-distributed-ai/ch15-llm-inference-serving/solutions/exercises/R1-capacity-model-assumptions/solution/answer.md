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
