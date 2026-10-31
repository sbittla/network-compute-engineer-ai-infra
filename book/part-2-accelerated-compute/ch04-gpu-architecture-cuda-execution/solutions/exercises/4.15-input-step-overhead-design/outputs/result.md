# Exercise 4.15 — budgets `[MODELED]`

- Per-GPU input rate = 104,857,600 B / 0.060 s = 1.75 GB/s = 3.5 % of ≈ 50 GB/s.
- Per PCIe switch (2 GPUs) = 3.5 GB/s; copy time per step = 104,857,600 B / 50 × 10⁹ B/s = 2.10 ms.
- Pinned staging = 3 × 100 MiB = 300 MiB per rank; × 8 = 2,400 MiB = 2.34 GiB per node
  (0.11 % of 2 TiB).
- Unfused optimizer ≈ 1,400 × 5 = 7,000 launches ≈ 70 ms of CPU issue time at 10 µs each,
  more than the whole 60 ms step: fusion is mandatory.
