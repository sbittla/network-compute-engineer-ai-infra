# O3 — Compare two serving configurations: worked solution

**Comparison** (`compare_serving_configs` on `lab/data/configs.yaml`, 4,096-token capacity sequences,
average context 2,048 + 128 = 2,176) `[MODELED]`:

| Config | Max seqs | Batch | TPOT | tokens/s per node | Prefill (2k) | Meets 50 ms |
|---|---|---|---|---|---|---|
| L-tp8-bf16 (1 replica/node) | 312 | 32 | 11.7 ms | 2,740 | 90.6 ms | yes |
| T-tp4-fp8 (2 replicas/node) | 156 | 128 | 20.2 ms | 12,678 | 90.6 ms | yes |

**Recommendations.**

- *Latency-sensitive objective:* **L-tp8-bf16.** TPOT 11.7 ms (≈ 86 tokens/s per user) against 20.2 ms, and
  BF16 weights (no FP8 quality risk).
- *Throughput objective:* **T-tp4-fp8.** 12,678 vs 2,740 tokens/s per node (4.6×), still within the 50 ms
  TPOT SLO. The batch of 128 amortizes the 70 GB weight read.

**Flip conditions.**

1. *SLO:* if the TPOT SLO tightens below ≈ 20.2 ms (for example 15 ms), T fails it at batch 128 and the
   throughput recommendation becomes L, or T at a smaller batch.
2. *Context length:* T's batch of 128 needs 128 sequences in 40,054 blocks. Above 4,992 tokens per
   sequence (4,993 tokens need 313 blocks → ⌊40,054/313⌋ = 127), the batch is KV-capped below 128, and at 16k only 39 fit,
   so T's throughput advantage shrinks sharply. Longer contexts also lengthen T's step, pushing it toward
   the TPOT SLO.
3. *Quality:* if FP8 weights are unacceptable for the product, T is excluded regardless of the numbers.
4. *Load:* at low load neither runs a full batch. T's TPOT advantage over L shrinks and L's lower latency
   costs little, so L can serve both.
