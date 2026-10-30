# Lab 14 — Instructor notes (INSTRUCTOR ONLY)

`storage_lab.py` in this folder is the reference implementation; `python ../../lab/check.py --impl
solution` passes 15/15. All data come from `lab/tools/generate_data.py` with seed 14 (trace), 15 (fio),
16 (checkpoints).

## Reference results (Part A, `[MODELED]`, inputs `data/orion_ckpt_inputs.yaml`)

| Strategy | Interval (steps) | Blocking s | Delta s | Completion s | Overhead % | RPO max s | E[time-to-resume] s | Lost GPU-h/day |
|---|---|---|---|---|---|---|---|---|
| async_pfs | 643.8 (37) | 0.65 | 1.19 | 18.5 | 0.18 | 662 | 904 | **55.6** |
| async_two_level | 522.0 (30) | 0.65 | 0.78 | 21.1 | 0.15 | 2,631 | 900 | 65.7 |
| sync_local_drain | 1,044.0 (60) | 2.59 | 3.08 | 20.4 | 0.30 | 1,064 | 900 | 69.0 |
| sync_pfs | 2,488.2 (143) | 17.83 | 17.83 | 17.8 | 0.72 | 2,506 | 904 | 121.1 |

Inputs follow the canonical reliability assumptions in `docs/REFERENCE_CLUSTER.md`: job MTBF 48 h
(1,536 node-hours / 32 nodes) and ≈ 15 min expected restart overhead (904 s).

Teaching points students should reach in the memo:

* Once blocking time is sub-second, **failure cost dominates**: for `async_pfs`, 44.3 of 55.6
  GPU-h/day is failure cost, and 32.1 GPU-h/day of that is time-to-resume (0.5 failures/day ×
  904 s × 256 GPUs / 3,600). Cutting detection from 300 s to 60 s saves 8.5 GPU-h/day, comparable
  to the whole remaining checkpoint overhead (11.3).
* `async_two_level` has the lowest overhead but loses because hard failures (40 %) must fall back to
  a PFS copy that is only taken every k = 5 checkpoints: RPO_max 2,631 s. With
  `hard_failure_frac: 0.1` it wins narrowly (51.75 vs 53.03 GPU-h/day); with `hard_failure_frac: 0.1`
  and `pfs_write_GBps: 20` (read unchanged) it wins clearly (55.9 vs 66.1). A partner-copy scheme (replicate each
  node's local shard to a neighbour, as in SCR) removes most of the hard-failure penalty; students
  who propose it earn the design points.
* Young vs Daly differ by < 1 % here (2,483 vs 2,471 s for the sync case): with δ ≪ M the
  first-order formula is adequate; rounding to whole steps matters more.

## Planted anomalies

| Dataset | Anomaly | Why it is there | Expected detection |
|---|---|---|---|
| `io_trace.csv` 0–6 s | Small-file epoch: one `open` (median 5 ms, lognormal σ 0.5) per 64–256 KiB sample | Metadata-bound pipeline: ~0.2 GB/s and ~1,200 samples/s per node, 89 % of op time in metadata | B2/B3 `metadata` phase |
| `io_trace.csv` 6–7 s | Idle gap (epoch boundary) | Classifier must not call an empty window "metadata" | B2 `idle` |
| `io_trace.csv` 7–19 s | 256 MiB shards read as 16 × 16 MiB | Bandwidth-bound pipeline: ~7.6 GB/s per node | B2/B3 `bandwidth` |
| `io_trace.csv` 13–17 s | Large-read latency × 2.5 with extra jitter | Checkpoint write burst on the shared PFS (interference). Throughput drops to ~3 GB/s; read p99 rises from ~60 ms to ~200–240 ms | B4 windows 13–16 |
| `io_trace.csv` target 5 | All reads × 4 latency | A degraded storage target (failing disk in a RAID set, rebuild, or overloaded server). Throughout the trace; inflates every window's p99 | B5 → [5] |
| `fio_nvme_acceptance.json` nvme2 | Sequential write 1.62 GB/s vs ~3.4 GB/s median | Typical causes: link trained at reduced width/speed (check `LnkSta`), thermal throttling, or a drive near end of life. Random read is normal, which points away from a host-wide problem | B6 LOW_BANDWIDTH |
| `fio_nvme_acceptance.json` nvme5 | Random-read p99.9 9.1 ms, p99.99 31 ms vs ~0.26/0.41 ms; mean only +12 % | Tail-only fault (firmware garbage collection stalls, media retries). Mean and p99 look healthy: only percentiles beyond p99 expose it | B6 TAIL_LATENCY |
| `checkpoints/step_001200` | `shard_05.bin` truncated to half | Writer died mid-file or ENOSPC; size check catches it before hashing | SIZE_MISMATCH |
| `checkpoints/step_001500` | One bit flipped in `shard_03.bin` | Silent corruption: only the checksum catches it | CHECKSUM_MISMATCH |
| `checkpoints/step_002100` | `shard_06.bin` missing but `COMMIT` present | A buggy writer that commits without a barrier on all ranks | MISSING_SHARD |
| `checkpoints/step_002400` | Manifest changed after commit (step 2400 → 2401) | Non-atomic manifest rewrite or a manual "fix"; the commit hash no longer matches | MANIFEST_HASH_MISMATCH |
| `checkpoints/step_002700` | No `COMMIT`; `latest` points here | Async persist was in flight when the job crashed; a restart that trusts `latest` loads a torn checkpoint | NO_COMMIT; select `step_001800` |

Retention lesson for discussion: a "keep last 3" policy would have kept 2100, 2400, and 2700 —
none restorable — and deleted the only two valid checkpoints (900 and 1800). Retention must count
*validated* checkpoints.

## Common mistakes

* Using RPO_max (k·τ + L_hard) where the expected lost work is asked for; the two differ by a factor
  of ~4 for the two-level strategy (2,631 s vs 689 s).
* Applying k to the soft-failure term of E_lost: soft failures restore from the local copy taken
  every τ, so only the hard-failure term uses k·τ/2.
* Forgetting the `- d` term in Daly or computing `sqrt(d/2M)` as `sqrt(d)/2M`.
* Window binning by completion time instead of start time; windows shift and B2 fails at the edges.
* Including `open` in per-target latency (B5) — opens go to the metadata service, not the target.
* Treating fio `clat_ns` as microseconds; `bw` (KiB/s) instead of `bw_bytes`.
* Hashing the manifest after `json.load`/`json.dumps` round-trip instead of the raw bytes.
