# M4 — 512-node incident (Section 20.1 of the course outline): reference solution

**Relies on:** Section 19.11 (INC-3107 worked example), Sections 19.4–19.7, Chapter 18 postmortem
template; lab `data/` `[SIMULATED]`; checker 12/12 PASS (`outputs/lab_checks.json`). Arithmetic `[MODELED]`.

## 1. Failure timeline (UTC, 2026-10-19/20)

| Time | Source | Event | Class |
|---|---|---|---|
| 23:10:05 | Slurm | Job 900198 starts on orionxl-n[001-512] (attempt 1) | — |
| 00:10:12 → | kernel n451 | Corrected AER (Physical Layer) every ≈ 40 min all night | Background (H4) |
| 01:12:44 | kernel n212 + switch | n212 `mlx5_5` link DOWN / p06-r5 Ethernet20/1 DOWN | **Fault** |
| 01:12:53 | nccl n211/n212/n213 | NET/IB status 12 (9 s after link-down) | Start of stall |
| 01:12:58 | kernel + switch | Link UP (14 s down > 8.6 s budget) | — |
| 01:23:40 | Slurm | 900198 FAILED; auto-requeue on the **same** allocation | Policy failure |
| 01:40:02 / 01:52:10 | Slurm / trainer | 900211 starts; resumes from ckpt-0081 (step 151200) | Attempt 2 |
| 02:47:03, 03:29:50 | kernel + switch | 6 s and 5 s flaps, both survived (< 8.6 s) | Warning ignored |
| 02:58:41 | dcgm + kernel n389 | GPU3 Xid 63, row remap pending | Real fault, not cause (H2) |
| 03:10:00–03:11:12 | trainer | ckpt-0084 complete, metadata committed | Restore point |
| 03:40:00–03:40:58 | trainer | ckpt-0085 shards written, **metadata commit in progress** | Unsafe checkpoint |
| 03:41:02 | kernel + switch | Link DOWN for 14 s | **Fault** |
| 03:41:11 | nccl | NET/IB status 12 from n211/n212/n213 | Start of stall |
| 03:41:20 | telemetry | spine-p06-03 PFC pause ×38 for 70 s | Consequence (H5) |
| 03:51:01 | PyTorch n103 | First watchdog line, rank 817 | First reporter (H3) |
| 03:52:15 | Slurm | 900211 FAILED; requeue **held** (INC-3107) | — |
| 04:31:00 | trainer | Resumed on spares from ckpt-0084 | Recovery |

## 2. Rank-to-hardware mapping (`rank_map.csv`)

| Rank | Node | Local GPU | GPU BDF | NUMA | HCA (BDF) | Rail | Leaf port | Role |
|---|---|---|---|---|---|---|---|---|
| 1693 | orionxl-n212 | 5 | 0000:ab:00.0 | 1 | mlx5_5 (0000:aa:00.0) | 5 | p06-r5 Ethernet20/1 | Suspect link, 10.135.1.167 |
| 1685 / 1701 | orionxl-n211 / n213 | 5 | — | 1 | mlx5_5 | 5 | p06-r5 | NET/IB reporters |
| 64 stuck ranks | orionxl-n193–n256 | 5 | — | — | mlx5_5 | 5 | p06-r5, p07-r5 | PP stage 3, last seq 88212 |
| 3107 | orionxl-n389 | 3 | 0000:5d:00.0 | 0 | mlx5_3 (0000:5c:00.0) | 3 | p12-r3 Ethernet5/1 | Xid 63 source; completed 88213 |
| 817 | orionxl-n103 | 1 | — | — | mlx5_1 | 1 | — | First reporter, stage 1 |

## 3. Health decision and quarantine

- **H1 orionxl-n212 rail-5 link: proven cause** (timing, locality, mechanism; intervention pending). The
  fault domain is the host transmit path: host TX −5.8 dBm vs fleet ≈ −1.6 dBm, switch RX −6.1 dBm
  median (sensitivity ≈ −5.9 dBm), 203,903 FEC-uncorrectable, host-side errors zero. Replace the host
  optic first, then the HCA if errors persist. **Unit removed:** node n212 (drain, reason INC-3107).
- **orionxl-n389 GPU3:** real fault, not the cause. Exclude n389 from this restart, reset the GPU,
  verify pending cleared, run `dcgmi diag -r 3`, then return it.
- **orionxl-n046 GPU6:** healthy; monitor. **Leaf p06-r5:** refuted (1 of 32 ports); do not quarantine.
- **orionxl-s00:** failed acceptance (DBE, remap failure); RMA; not a spare.
- **Proven vs correlated:** only H1 is causal. H3, H4 and H5 are correlations or consequences. Evidence
  was preserved before any reset (bug report, counters, DOM, flight recorder).

## 4. Checkpoint/restore validation and restart plan

- Restore **ckpt-0084** (step 151799, 03:10). ckpt-0085 has 4,096/4,096 shards but uncommitted metadata,
  so it is not restorable.
- Validate: shard count 4,096, checksums, metadata present. The first resumed step's loss must be
  consistent with the value logged at step 151799.
- Spares: s00 failed acceptance and s02 is in repair, so **s01 takes ranks 1688–1695** (from n212) and
  **s03 takes ranks 3104–3111** (from n389), with local ranks preserved (rail alignment and TP/PP/DP
  coordinates unchanged).
- Pre-restart: DCGM health and link checks on s01 and s03; n212 and n389 excluded (retry gate passes
  only after exclusion).
- Post-restart: step time within 5 % of baseline for 30 min; zero link events on s01's rails.

## 5. Recovery metrics

```text
Attempt 1: RPO = 01:12:44 − 01:00:00 = 12.73 min; RTO = 01:52:10 − 01:12:44 = 39.43 min;
           lost = 4,096 × 52.17 min / 60 = 3,561.2 GPU-h
Attempt 2: RPO = 03:41:02 − 03:10:00 = 31.03 min; RTO = 04:31:00 − 03:41:02 = 49.97 min;
           lost = 4,096 × 81 min / 60 = 5,529.6 GPU-h
Total ≈ 9,091 GPU-h ≈ $27,300 at $3.00/GPU-h
```

## 6. Postmortem (Chapter 18 template, blameless)

- **Summary:** Two hangs of job 900211/900198 (4,096 GPUs) caused by a marginal host optic on orionxl-n212
  rail 5. The first automatic restart reused the same nodes.
- **Impact:** 9,091 GPU-h; 31 min of training progress redone in attempt 2.
- **Root cause:** a host transmitter at the receiver-sensitivity edge produced 14 s link-downs, longer
  than the 8.6 s RC retry budget.
- **Contributing factors:** no flap-rate alert, so two survived flaps went unnoticed; the auto-requeue
  did not exclude implicated nodes; the async checkpoint's metadata commit was not checked; the 10-min
  watchdog was the only hang detector.
- **What went well:** the retry policy held the second requeue; spares were available; evidence was
  preserved.
- **Action items:**
  1. Flap-rate quarantine (2 flaps in 24 h) and DOM tickets. Owner: Fabric (FMEA F03).
  2. Retry-policy gate: exclude implicated nodes; ≤ 2 automatic restarts per 6 h. Owner: Platform.
  3. Metadata-commit validation in checkpoint selection; keep the previous checkpoint until the next is
     validated. Owner: Training Infra.
  4. Early hang detection: abort on the link-down plus NET/IB signature instead of waiting 600 s
     (saves ≈ 683 GPU-h per hang). Owner: Training Infra with Platform.
- **Open question:** H1 is proven pending intervention. Close it when the job has run ≥ 2 × job MTBF
  (6 h) without a rail-5 hang and the replaced optic has passed a 24 h BER soak.
