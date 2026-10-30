# Capstone G — Instructor Grading Guide (INSTRUCTOR ONLY)

Removed from student releases. Reference: [reference/ftops.py](reference/ftops.py). Exemplar:
[EXEMPLAR.md](EXEMPLAR.md).

## 1. Verifying the kit

```bash
cd capstones/capstone-g-fault-tolerant-512-node-training/starter-kit
python check.py --impl solution     # 11/11 PASS, exit 0, ≈ 2 s
python check.py                     # 1/11 PASS (dataset), 10 TODO, exit 1
python ../../../scripts/validate_labs.py capstone-g
```

## 2. Planted evidence (all SIMULATED)

| # | Planted | Correct handling | Teaches |
|---|---|---|---|
| P1 | **Proven cause:** Xid 94 on `orionxl-n377` GPU5 (PCI `0000:ab:00`) at 03:14:07.000 true time; CUDA "uncorrectable ECC error encountered" from rank 3013 0.4 s later; DCGM DBE = 1 and row-remap pending; Xid 63 | Rank 3013 has collective seq 1,203,455 (everyone else 1,203,456): it never entered the collective. Critical evidence on that rank's GPU → proven cause. Quarantine GPU, drain node, reset to activate the remap, re-accept | Proof = mechanism + the rank that stalled first, not "first log line" |
| P2 | **Independent fault:** `orionxl-n213` mlx5_3 flapped 4 times (−40, −31, −22, −9 min), `rx_crc_errors_phy` ≈ 5,600, switch port errors; step-time spikes at each flap | Job kept progressing after every flap → not the cause of the hang; still ≥ quarantine → quarantine HCA, drain node, Fabric ticket on the *observed* peer port | Correlated in time ≠ causal; a straggler is still a fault |
| P3 | **Stale cabling plan:** DCIM says `orionxl-n214` mlx5_3 ↔ port 22; LLDP says port 22 is `orionxl-n213` (cables swapped at install) | Map switch counters with LLDP; file DCIM correction; do **not** drain `orionxl-n214` | Observed topology beats documentation |
| P4 | **Skewed clock:** `orionxl-n042` is 180 s behind; its watchdog lines and last-progress stamps look earliest | Apply chrony offsets; classify by collective sequence, not timestamps | Never order cross-host events on raw host clocks |
| P5 | Background SBE on 150 GPUs (1–40) | Score 0 (trend only) | Noise floor |
| P6 | `orionxl-n101` GPU2 SBE 2,400; `orionxl-n099` GPU2 30 corrected AER | Watch tickets (scores 20 and 10) | Watch ≠ quarantine |
| P7 | Checkpoint 51,750: metadata not committed, 34 of 480 shards missing (rate-limited upload: 980 GB / 2.5 GB/s = 392 s, fault ≈ 208 s after start) | Reject | A started checkpoint is not a checkpoint |
| P8 | Checkpoint 51,612: committed, shard 232 checksum failure | Reject; restore 51,474 | Validate before restore; this is why the RPO target is missed |
| P9 | Spares: `orionxl-n481` acceptance pending; `orionxl-n482` idle but open quarantine (GPU1 row-remap failure); `orionxl-n497` in maintenance | Use `orionxl-n483`, `orionxl-n484` | "Idle" in the scheduler is not "healthy" — never reschedule onto an unhealthy device |
| P10 | `resume_unvalidated.csv` — an earlier drill restored 51,612: loss +1.1 decaying, NaN from step 51,950 | `validate_resume` fails (continuity, NaN) | Evidence that the job resumed *correctly*, not just that it is running |
| P11 | `resume_dataloader_not_restored.csv` — weights restored from 51,474 but the data loader restarted from sample 0: loss differs by only ≈ 0.1–0.24 %, grad norm by ≈ 0.6 % | Fails on sample index (exact) and on the 1e-3 tolerance; a 1 % tolerance would have passed it | Tolerances come from replay noise (≈ 2e-4 here); check state beyond weights |

## 3. Expected numbers

| Item | Expected | Class |
|---|---|---|
| Scores | GPU `orionxl-n377:5` 100; HCA `orionxl-n213:mlx5_3` 100 (70 flaps + 20 CRC + 20 switch, capped); `orionxl-n101:2` 20; `orionxl-n099:2` 10 | SIMULATED |
| First stalled | rank 3013 | SIMULATED |
| Replacements | `orionxl-n213` → `n483`; `orionxl-n377` → `n484`; 16 ranks remapped, GPU index preserved. The ops log shows the automation paired them the other way round (`n377` → `n483`, `n213` → `n484`); **either pairing is valid** because both spares are eligible and identical in role — grade eligibility and rail preservation, not the pairing | SIMULATED |
| Detect / isolate / RTO | 38 s / 242 s / 912 s (targets 120 / 600 / 1,800 s — met) | SIMULATED |
| RPO | 51,797 − 51,474 = 323 steps × 4.35 s = 1,405 s (target 276 steps — **missed**) | SIMULATED |
| Lost GPU-h | 3,840 × (1,405 + 912) / 3,600 = 2,471.5 | SIMULATED |
| Validated resume | max relative loss deviation ≈ 0.00065 = 65 % of the 1e-3 tolerance (replay noise σ ≈ 2e-4); sample indices identical. Data-loader-not-restored resume: ≈ 0.0024, sample indices differ → fails | SIMULATED |
| Expected loss per interruption | 3,840 × (300 + 392 + 900) / 3,600 ≈ 1,698 GPU-h | MODELED |
| Spare-pool sizing (Poisson) | 7.5 failures/day; 5-day MTTR → mean 37.5 in repair, P(≤ 32) ≈ 0.21, P95 48, P99 52; split 70 % 1-day / 30 % 5-day → mean 16.5, P95 23, P99 27. Expect students to show one of these and the 8-node elastic fallback (DP 60 → 48 without a batch change) | MODELED |
| Young interval | √(2 × 10 × 11,520) = 480 s | MODELED |

Arithmetic check for the step time: 3,840 × 4,096 = 15,728,640 tokens; 6 × 70 × 10⁹ × 15,728,640 =
6.606 × 10¹⁸ FLOP; 3,840 × 989 × 10¹² × 0.40 = 1.519 × 10¹⁸ FLOP/s; 6.606 / 1.519 = 4.35 s.

## 4. Rubric interpretation

| Dimension | Weight | 9–10 | 7–8 | 5–6 | < 5 |
|---|---|---|---|---|---|
| Problem framing and assumptions | 10 | SIMULATED on page one; MTBF, restart, cadence, targets as assumptions | Most stated | Implicit | — |
| Architecture and technical correctness | 20 | Correct chain; Xid 94/95 semantics; repair domain vs placement unit; restorable criteria | One error | Quarantines whole node as the repair domain or uses cabling plan | Wrong cause |
| Implementation / reproducibility | 15 | 11/11, one command | 11/11 | 8–10 | < 8 |
| Measurement and analysis | 20 | RTO/RPO/GPU-h with arithmetic; Young/Daly; durability lag; RPO miss explained by P8 | Metrics only | Totals without method | Unlabelled |
| Reliability, security and operations | 15 | Never-reschedule shown; re-acceptance; evidence preservation; who may quarantine/release | Partial | Generic | Unsafe |
| Troubleshooting and engineering judgment | 10 | Names discriminating evidence for P1 vs P2; rejects P3, P4 explicitly | Finds cause, weak on red herrings | Picks first log line | — |
| Communication and portfolio quality | 10 | Postmortem on true time; figures captioned | Clear | Hard to follow | — |

## 5. Common failure patterns

1. Blaming `orionxl-n042` (first watchdog line on raw host time) — P4.
2. Draining `orionxl-n214` via the cabling plan — P3. Treat as a wrong-node action: cap Reliability at 6.
3. Declaring the flapping HCA the cause because its errors came first — P2.
4. Restoring "latest checkpoint" (51,750) or 51,612 — the checker fails T6.
5. Picking spares by scheduler state only — P9; the checker fails T7. Related: sizing the pool by the average failure rate instead of a Poisson percentile of nodes *in repair*.
6. Quarantining the whole node as the *repair* domain (loses 7 healthy GPUs' repair history) or
   draining only the GPU (TP = 8 cannot run on 7 GPUs).
7. Reporting RTO from the alert rather than from the true fault time.
8. Quoting the 1-h correctable-ECC count as an admission failure.
9. Omitting "SIMULATED" — a stated success criterion of the outline; −3 under Communication.
10. Mixing up the PyTorch watchdog timeout and `NCCL_IB_TIMEOUT`.

## 6. Oral questions

1. What single field in `progress.csv` lets you ignore every timestamp, and why is it trustworthy?
2. The HCA flapped four times and the job survived. Why quarantine it now rather than at the next
   failure?
3. Xid 95 instead of 94 — what changes in your runbook?
4. Your RPO target was missed. Which of interval, durability lag or validation would you change,
   and what does it cost?
5. Spares are exhausted next time. What is your policy: wait, shrink DP, or borrow from inference?
