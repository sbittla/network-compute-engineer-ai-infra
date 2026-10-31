# 4.8 — Occupancy and bytes in flight (model answer)

Relies on manuscript Section 4.7 ("The calculation", Table 4.3) and Section 4.3 (Little's law). Device
limits from Table 4.1 / `lab/data/device.json`; all results `[MODELED]`. `solve.py` implements the same
rules and asserts every number below.

## (a) 48 KB (49,152 B) of shared memory per block

Warps per block *w* = 128 / 32 = 4.

| Limit | Arithmetic | Blocks per SM |
|---|---|---|
| Warps | ⌊64 / 4⌋ | 16 |
| Registers | 80 × 32 = 2,560 per warp (= 10 × 256, no rounding); ⌊65,536 / 2,560⌋ = 25 warps → 24 after the allocation granularity of 4; ⌊24 / 4⌋ | 6 |
| Shared memory | ⌊233,472 / (49,152 + 1,024)⌋ = ⌊233,472 / 50,176⌋ = ⌊4.65⌋ | **4** |
| Blocks | hardware maximum | 32 |

Resident = 4 blocks = 16 warps → 16 / 64 = **25 %**, limiter **shared memory**.

## (b) Bandwidth bound

- Needed per SM = 3.35 × 10¹² B/s × 600 × 10⁻⁹ s / 132 = 2.01 × 10⁶ B / 132 = **15,227 B ≈ 15.2 KB**.
- In flight = 16 warps × 2 loads × 128 B = **4,096 B**.
- Fraction = 4,096 / 15,227 = **26.9 %** → ≈ 0.269 × 3.35 TB/s ≈ **0.90 TB/s** upper bound `[MODELED]`.

## (c) 32 KB (32,768 B) of shared memory per block

- Shared memory: ⌊233,472 / (32,768 + 1,024)⌋ = ⌊233,472 / 33,792⌋ = ⌊6.91⌋ = 6 blocks.
- Registers: still 6 blocks. Warps 16, blocks 32 unchanged.
- Resident = 6 blocks = 24 warps → **37.5 %**. Limiter **registers**: registers and shared memory tie at 6,
  and the Section 4.7 rule reports the first in the order warps → registers → shared memory → blocks.
  "Registers and shared memory tie" is equally correct.
- In flight = 24 × 2 × 128 B = 6,144 B → 6,144 / 15,227 = **40.3 %** → ≈ **1.35 TB/s**.

**What it means.** Cutting shared memory buys 50 % more resident warps, but the kernel is still far below
the roof; further gains need fewer registers *and* less shared memory, or more independent loads per warp.

**Common wrong answers.**

- Forgetting the 1 KB per-block reservation. It does not change these answers (233,472 / 49,152 = 4.75 → 4;
  233,472 / 32,768 = 7.1 → 7, still above the register limit of 6) but it does at other sizes: with 45 KB
  (46,080 B), 233,472 / 46,080 = 5.07 → 5 without it, but 233,472 / 47,104 = 4.96 → **4** with it.
- Skipping the warp-allocation granularity (25 warps → 6.25 → 6 blocks gives the same answer here by luck).
- Reporting occupancy without naming the limiter.
