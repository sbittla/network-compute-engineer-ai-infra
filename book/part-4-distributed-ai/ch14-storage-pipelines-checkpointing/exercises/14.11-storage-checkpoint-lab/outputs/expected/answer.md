# 14.11 — Progressive Lab 6 — Storage and checkpoint: worked solution

**Checker.** `python lab/check.py` reports **15/15 checks passed**. Reference values from the solution
report:

| Check | Expected result |
|---|---|
| A1 | 980 GB; 16.33 s at 60 GB/s effective `[MODELED]` |
| A2 | Young 2,483 s, Daly 2,471 s (synchronous PFS δ) |
| A3 | Young floored at completion latency, rounded up to whole 17.4 s steps |
| A5 | sync @30 min 0.99 % overhead, 125.7 GPU-h/day; async @30 min 68.9 GPU-h/day |
| A6 | async PFS best at a 37-step interval (55.6 GPU-h/day); two-level pays for its k·τ RPO |
| B1–B6 | open p50 5.0 ms, read p99.9 193 ms; 0–6 s metadata-bound (≈ 0.2 GB/s), 7–19 s bandwidth-bound (≈ 7.6 GB/s); 3 phases; read p99 inflated 13–17 s; storage target 5 slow; nvme2 low write bandwidth, nvme5 p99.9 outlier `[SIMULATED]` |
| C1–C3 | 5 planted defects classified; restore from `step_001800`, not the `step_002700` pointer; unseen defects (rank coverage, truncated manifest) detected |

**Memo expectations (lab Section 7).**

- *Part A, planner:* reproduce Table 14.8 with assumptions stated. Explain why async PFS wins at
  M = 48 h, and why two-level local + PFS loses despite the lowest overhead: 40 % of failures are hard
  and lose the node's NVMe, so they fall back to a PFS copy up to k·τ = 5τ old.
- *Part B, trace:* the first epoch is metadata-bound (`meta_time_share` high, small reads, ≈ 0.2 GB/s).
  Sharded reads are bandwidth-bound (≈ 7.6 GB/s). Read p99 inflation at 13–17 s is caused by a concurrent
  write burst: the next evidence is PFS write throughput and checkpoint-log timestamps for the same
  window. Target 5 is slow: check per-target server metrics and RAID rebuild status. nvme2 has low write
  bandwidth: check `LnkSta` (link width/speed) and temperature. nvme5 is a tail-only fault: repeat with
  a longer runtime and check firmware.
- *Part C, validator:* explain each defect (no COMMIT, size mismatch, checksum mismatch, manifest hash,
  missing shard). Explain why `latest` → `step_002700` is unsafe and why `step_001800` is the newest
  valid checkpoint.

Reference: `solutions/lab/README.md` and `solutions/lab/storage_lab.py`. Values are `[MODELED]` (Part
A) or derived from `[SIMULATED]` data (Parts B and C).
