# 14.17 — Evidence missing before production: worked solution

The worked example (Section 14.12) recommends asynchronous PFS checkpoints about every 37 steps for
W-TRAIN. Before production approval:

**Can stay modeled (adequate for design)** `[MODELED]`:

- checkpoint size (980 GB) and per-rank shard size, which are arithmetic on known parameters;
- Young/Daly interval and its rounding to whole steps;
- sensitivity of lost GPU-h/day to M, hard-failure fraction and PFS efficiency, plus strategy ranking
  over a plausible input range;
- PFS capacity needed for the retention policy.

**Must be measured** `[MEASURED]` before approval:

1. PFS write efficiency for a real 256-writer checkpoint burst, open → commit, ≥ 5 runs.
2. Snapshot (blocking) time on HX8 and the pinned staging memory it needs per node (× 2 if
   double-buffered), checked against host memory headroom.
3. Interference: step time during versus outside persist windows over ≥ 50 checkpoints.
4. Restore read rate, including read amplification and resharding, and the validator's run time on
   980 GB (checksums ≈ 8.2 s modeled).
5. Time-to-resume components (detect, relaunch, load, warm-up) from drilled restarts, soft and hard.
6. Real job MTBF and hard-failure fraction for ORION, from incident records.
7. A full restore test: planted corrupt checkpoint rejected, and first-step loss equal to the value
   recorded at save.

The recommendation is approved when the measured values, substituted into the planner, keep the same
ranking and stay within the RPO/RTO objectives.
