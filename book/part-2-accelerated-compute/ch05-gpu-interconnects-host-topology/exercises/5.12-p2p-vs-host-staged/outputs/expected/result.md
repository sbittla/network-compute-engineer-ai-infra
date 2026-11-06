# Exercise 5.12 — transfer times `[MODELED]`

4 GiB = 4,294,967,296 B.

| Path | Formula | Time |
|---|---|---|
| NVLink P2P | 4,294,967,296 B / 370 × 10⁹ B/s | 11.6 ms |
| Host-staged, unpipelined | 2 × 4,294,967,296 B / 52 × 10⁹ B/s = 2 × 82.6 ms | 165.2 ms |
| Host-staged, 64 MiB chunks (64 chunks) | 82.6 ms + 67,108,864 B / 52 × 10⁹ B/s | 83.9 ms |

NVLink is 7.2× faster than the best host-staged path.
