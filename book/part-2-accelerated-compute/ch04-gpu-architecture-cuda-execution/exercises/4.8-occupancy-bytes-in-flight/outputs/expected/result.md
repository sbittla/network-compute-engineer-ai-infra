# Exercise 4.8 — occupancy and bytes in flight `[MODELED]`

Needed in flight per SM = 3.35 × 10¹² B/s × 600 ns / 132 = 15,227 B.

## Case a_b (shared memory 49,152 B per block)

- Warps per block = 128 / 32 = 4
- Warp limit = ⌊64 / 4⌋ = 16 blocks
- Register limit: 80 × 32 = 2,560 registers per warp; ⌊65,536 / 2,560⌋ = 25 warps → granularity 4 → 24 warps → 6 blocks
- Shared-memory limit = ⌊233,472 / (49,152 + 1,024)⌋ = 4 blocks
- Block limit = 32
- Resident = 4 blocks = 16 warps → occupancy 25.0 %, limiter shared_memory (tied: shared_memory)
- In flight = 16 × 2 × 128 B = 4,096 B → 26.9 % of HBM ≈ 0.90 TB/s upper bound

## Case c (shared memory 32,768 B per block)

- Warps per block = 128 / 32 = 4
- Warp limit = ⌊64 / 4⌋ = 16 blocks
- Register limit: 80 × 32 = 2,560 registers per warp; ⌊65,536 / 2,560⌋ = 25 warps → granularity 4 → 24 warps → 6 blocks
- Shared-memory limit = ⌊233,472 / (32,768 + 1,024)⌋ = 6 blocks
- Block limit = 32
- Resident = 6 blocks = 24 warps → occupancy 37.5 %, limiter registers (tied: registers, shared_memory)
- In flight = 24 × 2 × 128 B = 6,144 B → 40.3 % of HBM ≈ 1.35 TB/s upper bound

Reservation check (45 KB = 46,080 B per block): 5 blocks without the 1 KB reservation, 4 with it.
