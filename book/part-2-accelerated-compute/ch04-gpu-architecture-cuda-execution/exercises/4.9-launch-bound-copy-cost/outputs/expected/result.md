# Exercise 4.9 — launch-bound loop and copy cost `[MODELED]`

(a) Eager: iteration = max(400 × 10 µs, 400 × 6 µs) = 4.0 ms (CPU-limited);
kernel-busy = 2.4 / 4.0 = 60 %.

(b) CUDA Graph: 15 + 400 × 6 + 399 × 1 = 2,814 µs = 2.81 ms;
speedup 4.0 / 2.814 = 1.42×; kernel-busy 85 %.

(c) Input 256 MiB = 268,435,456 B.
Pageable: 268,435,456 B / 12 × 10⁹ B/s = 22.4 ms, serial and host-blocking, so the eager
iteration is ≈ 26.4 ms.
Pinned: 268,435,456 B / 50 × 10⁹ B/s = 5.37 ms. Prefetched on a side stream, the steady state is
max(2.81, 5.37) = 5.37 ms: copy-bound. Reduce the bytes per iteration.
