# O1 — Memory demand vs batch, sequence length and concurrency: worked solution

**Setup** `[MODELED]`: T-tp4-fp8, TP = 4, usable HBM = 4 × 80 GB × 0.90 = **288 GB**, FP8 weights 70 GB,
BF16 KV 327,680 B/token, reserve 4 × 2 GB = 8 GB, so the KV budget is 210 GB (lab Part A,
Section 15.3). Demand = 70 GB + B × L × 327,680 B.

| Seq length | B = 16 | B = 64 | B = 128 | Max seqs (KV 210 GB) |
|---|---|---|---|---|
| 1,024 | 70 + 5.4 = 75.4 GB | 70 + 21.5 = 91.5 GB | 70 + 42.9 = 112.9 GB | 625 |
| 4,096 | 70 + 21.5 = 91.5 GB | 70 + 85.9 = 155.9 GB | 70 + 171.8 = 241.8 GB | 156 |
| 16,384 | 70 + 85.9 = 155.9 GB | **70 + 343.6 = 413.6 GB ✗** | **70 + 687.2 = 757.2 GB ✗** | 39 |

✗ = exceeds 288 GB usable HBM. Max sequences = ⌊40,054 blocks / ⌈L/16⌉⌋, from 40,054 blocks of
16 tokens × 327,680 B in the 210 GB budget.

Note that 241.8 GB (4k, B = 128) is below 288 GB but above the 210 GB KV budget once the 8 GB reserve is
counted: 70 + 8 + 171.8 = 249.8 GB fits, and 128 < 156 sequences, so it runs.

**Explanation.** KV memory grows as B × context while the weights stay at 70 GB, so at long context the
KV term dwarfs the weights (343.6 GB vs 70 GB at 16k × 64). Concurrency then falls inversely with sequence
length (625 → 156 → 39), and memory, not compute, binds the batch. That in turn lowers throughput.
