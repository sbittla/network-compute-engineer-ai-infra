# L1 — Lab 18 reference results

Checker: **14/14 PASS** (the dataset-reproducibility check SKIPs in the student release, where the
generator is absent). Reference: `solutions/lab/telemetry_analysis.py`. All values `[SIMULATED]`.

| Quantity | Value |
|---|---|
| Baseline step time trn-70b / ft-13b (00:00–02:00, non-checkpoint median) | 17.389 s / 5.998 s |
| Plateau median (02:20–04:00) | 21.24 s / 7.09 s |
| Onset / recovery (both jobs) | 02:10 / 04:07 |
| Training SLI trn-70b / ft-13b (6 h) | 0.678 / 0.681 |
| Lost GPU-hours onset → recovery | 43.76 + 18.66 = 62.4 |
| Availability burn at 05:16, 5 m / 1 h | 40.0 / 4.65 (no page) |
| `GPUUtilLow` firings | 63, all on orion-n25..n32 (inference at low load): noisy |
| `GPUTempHigh` | 1 ticket, orion-n08, 01:53–02:35 |
| Goodput alert first firing | 02:19 for both jobs |
| Fabric shift (02:30–03:30 vs 01:00–02:00) | leaf PFC TX × 91–98, ECN × 0.03; spine PFC RX × 104–107 |
| Trigger | CHG-4471; rejected FAC-0912 and CHG-4468 |
| Timeline | onset 02:10, detected 02:58, declared 03:12, mitigated 04:08:12, resolved 04:30; TTD 48.0, TTM 118.2, TTR 140.0 min |

**Written parts graders look for.**
- *Checkpoint exclusion:* checkpoint steps carry +9 s (trn-70b every 30 min) and +4 s (ft-13b every
  20 min) of stall; they barely move a median but trip a threshold rule twice an hour and inflate
  per-minute series, so they are excluded from baselines and SLI minutes (check: baseline-window max
  minute < 18.5 s).
- *Noisy-rule redesign:* replace `GPUUtilLow` (page, GPU_UTIL < 80 for 2 m) with a *ticket* on
  allocated-but-idle GPUs (GPU_UTIL < 5 for 30 m on GPUs allocated to a job); page on the training
  throughput symptom instead. *Goodput alert:* `job:train_throughput:ratio < 0.909` for 5 consecutive
  minutes of the 10-minute median (or the burn-rate form of Section 18.8) with `for: 2m`, justified by
  the median lag versus noise.
- *Proven vs correlated:* proven needs temporal precedence (leaf changes 02:08–02:12 before onset
  02:10), scope (both jobs share only the fabric), mechanism (ECN threshold up → PFC instead of DCQCN),
  and intervention (rollback restores within minutes). Without the rollback evidence the cause is only
  correlated; FAC-0912 is rejected by scope (ft-13b has no n08) and timing (heating from 01:45),
  CHG-4468 by scope (monitoring only).
- *Traps:* do not page on the 7-minute DEP-41 blip; `FabricOutDiscards` silence does not mean a
  healthy fabric (lossless class pauses instead of dropping); spine PFC RX is propagation, not origin;
  CHG-4471's "post-checks PASS" checked reachability, not RoCE performance.
