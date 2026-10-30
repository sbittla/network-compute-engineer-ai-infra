# Capstone B — Instructor Grading Guide

INSTRUCTOR ONLY. Removed from the student edition by `scripts/make_student_release.py`, together with
`starter-kit/tools/`, because the generator encodes the faults.

## 1. Context of the capture

W-TRAIN runs on the default 24-node training partition, `orion-n01`–`n24`, which is TP 8 × PP 4 × DP 6 =
192 GPUs: a declared variation from the full 32-node run, matching the REFERENCE_CLUSTER default split.
Because 1,024 sequences do not divide by DP = 6, the variation uses a global batch of 1,152 (192 per
replica), with the learning rate adjusted for the larger batch.
`orion-n25`–`n32` serve inference and carry ≈ 2 GB/s per backend NIC. That is why the mean host-port rate
per leaf is ≈ 184 Gb/s (24 ports at ≈ 240 Gb/s plus 8 at ≈ 16 Gb/s).

## 2. Ground truth (`data/ground_truth.sha256`: hash, onset, tolerance)

A page matches only if it **fires** (`fired_ts`, when persistence is satisfied) inside
[onset, onset + tolerance].

Shipping the onsets in plain text in the learner copy is **deliberate**. Onsets carry no device or fault
class, so they do not reveal the answers, and the checker needs them to score timing in the student
edition (where `instructor/` and `tools/` are removed). The cost is that learners know *when* something
starts. Graders should check that the incident report reasons from counters, not from the truth file. Earlier pages and non-matching pages are false positives. A re-page for a
fault that was already matched is a duplicate.

| Key | Onset (UTC) / tolerance | Mechanism | Signature in the capture |
|---|---|---|---|
| `orion-n17:mlx5_5\|pfc_storm` | 10:15 / 600 s | Stuck receiver: the host stops draining its rail-5 receive queue and the NIC transmits PFC pause continuously | orion-be-leaf-r5 Ethernet1/17 `RxPause3` ≈ 50,000/s; NIC `tx_prio3_pause` ≈ 50,000/s; NIC receive bytes ≈ 0.02 GB/s. HoL spreading shows as `TxPause3` ≈ 2,000–2,700/s on the other leaf-r5 host ports and ≈ 600/s on its uplinks |
| `orion-be-leaf-r2:Ethernet1/50\|link_degradation` | 10:04 / 1,200 s | Degrading receive path on the leaf-r2 uplink to orion-be-spine-3 | Corrected codewords trend from the ≈ 1.5 × 10⁵/s healthy baseline to ≈ 3 × 10⁷/s (≈ 7.7 × 10⁵/s at 10:13, ≈ 2.1 × 10⁶/s at 10:18). `FCSErrors` 5–50/s from 10:18; `FECUncorr` from 10:20. The spine side is clean, which is the clue to direction |
| `orion-be-leaf-r6:*\|ecn_misconfig` | 10:00 / 600 s | ECN marking disabled on the lossless queue of leaf r6 | `EcnMarked3` = 0 on every leaf-r6 port; host-port PFC ≈ 50–130× the other rails; rail-6 NICs show `np_ecn_marked_roce_packets` (CE received) and `np_cnp_sent` at 0 |
| `orion-be-leaf-r1:*\|ecmp_imbalance` | 10:00 / 600 s | Hash polarization after a config push | Uplink tx CV ≈ 0.78 (others ≈ 0.08); four hot uplinks at 3.2× the mean with `OutDiscards` ≈ 800/s |
| `orion-n24:mlx5_2\|link_degradation` | 10:11 / 600 s | Host-side receive errors | NIC `rx_crc_errors_phy` 20–60/s, `out_of_sequence` 15–25/s; leaf-r2 Ethernet1/24 clean |

## 3. Benign traps

| Trap | Where | Naive behaviour | Correct behaviour |
|---|---|---|---|
| Synchronized checkpoint burst | 192 W-TRAIN host ports, interval ending ≈ 10:12 | `RxPause3` ≈ 15,000–16,500/s → 192 PFC-storm pages, including orion-n17 mlx5_5 at 10:12, **before** its real storm (a pre-onset FP) | Persistence ≥ 2 suppresses it |
| Healthy FEC activity | every switch port: ≈ 1.5 × 10⁵ corrected codewords/s (p99 ≈ 2.2 × 10⁵) | An absolute "corrected > 100k/s" rule pages on all 512 leaf ports | Page on FCS/uncorrectable. Trend corrected codewords against each port's own baseline as an early warning (≈ 10:15 for leaf-r2 Eth1/50), and ask for pre-FEC BER and symbol-error histogram bins where the platform exports them (VERIFIED_FACTS) |
| Single FCS errors | orion-be-leaf-r1 Ethernet1/25 (~10:11), orion-be-leaf-r3 Ethernet1/16 and Ethernet1/28 (~10:13) | 3 link-degradation pages | Persistence 2 suppresses them |
| 32-bit pause-counter wrap | orion-be-leaf-r4 Ethernet1/7 `TxPause3`, during the burst | Treated as a reset (data lost) or as a 64-bit decrease (a ≈ 1.8 × 10¹⁹ jump) | Wrap recovered (≈ 2,000/s), within the 2 × 10⁶/s plausibility bound |
| Counter clears that look like wraps | orion-be-leaf-r7 (cleared ≈ 10:19:30) and orion-be-spine-2 (≈ 10:16:40, not in the calendar) | The pure "prev ≥ 2³¹ → wrap" heuristic reads a clear of a high 32-bit counter as a wrap | The **correct policy** needs a discontinuity signal (device uptime, boot ID, or a counter-discontinuity timestamp) or at least a plausibility bound (max rate × dt). The reference uses the bound and recommends the signal |
| Planned reboot of an inference node | orion-n30 (CHG-20817): the router drained the replica; NIC counters reset ≈ 10:16:20 | Reset misread; link_down at persistence 1 | Reset → invalid interval; CHG-20817 suppresses it. W-TRAIN is not on n30 |
| Optic swap | orion-be-leaf-r7 Ethernet1/41–42 down 10:19–10:24 | link_down on leaf-r7 **and on orion-be-spine-2 Ethernet1/57–58** | Suppression extends to the link peer |
| Timestamp encodings | ISO-8601, epoch ns, epoch s | Misaligned series | All UTC; real dt (polls jitter by 1–3 s) |

## 4. Reference results (`[SIMULATED]`, time-aware scoring)

| Setting | TP | FP | FN | Detection latency from onset |
|---|---|---|---|---|
| Default rules (persistence 2–3; episodes open on `persistence` consecutive true intervals, close after 3 false) | 5 | 0 | 0 | ECN 181 s; ECMP 181 s; n24 CRC 183 s; PFC storm 182 s; leaf-r2 901 s (paged on FCS at 10:19, early warning at 10:15) |
| Persistence 1 | 5 | 195 | 0 | 192 burst pages (one is n17 at 10:12) + 3 glitches |
| Persistence 2 | 5 | 0 | 0 | worst 901 s |
| Persistence 3 / 4 / 5 | 5 | 0 | 0 | worst 962 / 1,022 / 1,081 s |
| Empty change calendar | 5 | 4 | 0 | link_down on leaf-r7 ×2 and spine-2 ×2 |
| PFC threshold 2,000–20,000/s | 5 | 0 | 0 | 60,000/s misses the storm (peak ≈ 54,000/s) |

With 5 positives, "precision ≥ 0.9" means **zero** FPs (one FP gives 5/6 = 0.83). Five positives are
too few to estimate a production precision. The analysis shows mechanisms, not base rates.

Leaf health table: ≈ 184 Gb/s mean per host port on healthy leaves and ≈ 133 on leaf r5; ECN marks ≈
3,600–3,900/s per host port except r6 (0); uplink CV ≈ 0.07–0.08 except r1 (0.78); leaf-r2 FCS
increments ≈ 19,700.

## 5. Dimension-by-dimension expectations

| Dimension | Exemplary | Proficient | Developing | Insufficient |
|---|---|---|---|---|
| Problem framing (10) | On-call success criteria with numbers (incl. the zero-FP meaning of 0.9 at N = 5); assumptions include poll intervals, widths, clock source | Criteria present, partly qualitative | Generic "detect problems" | Absent |
| Architecture and correctness (20) | Direction semantics right (switch ECN marked vs NIC CE received; Rx vs Tx pause); wrap/reset policy with a discontinuity signal or bound; topology-based attribution; FEC paging on FCS/uncorrectable with BER/trend as early warning | One semantic slip | Symptom ports reported as root causes, or absolute FEC paging | Rates wrong |
| Implementation (15) | 13/13 checks, own unit tests, one-command reproduction | 13/13 | 9–12 | < 9 |
| Measurement and analysis (20) | Time-aware scoring, persistence/threshold sweeps, per-fault latency from onset, small-N caveat | Sweeps without latency | Single operating point | Simulated presented as measured: cap at 40 % |
| Reliability, security, ops (15) | Read-only-first runbook with approvals, meta-monitoring, peer-aware suppression, hysteresis, least-privilege collection | Thin meta-monitoring | Generic runbook | None |
| Judgment (10) | Incident report separates cause from correlation, explains HoL spreading, recommends a PFC watchdog and an alert on unplanned clears | Sound diagnosis | Lists symptoms | Wrong root cause |
| Communication (10) | Dashboard answers on-call questions; reproducible tables | Clear | Hard to follow | Disorganized |

## 6. Common failure patterns

1. Paging on pause counters without persistence: 192 pages for one checkpoint burst.
2. Scoring without time: the 10:12 n17 page looks like a "hit" when it fired before the storm.
3. Treating the leaf port as the PFC-storm root cause, or confusing `RxPause3` and `TxPause3`.
4. An absolute corrected-codeword threshold: 512 healthy ports page.
5. One canonical name for switch-egress ECN marks and NIC CE-received counts.
6. Per-device suppression only, which produces two spine-2 pages during leaf-r7's optic swap.
7. Thresholds set to the checker, with no baseline percentiles.
8. Missing F5: parsing only switch data never shows the host-side CRC errors.

## 7. Viva questions

0. (Hysteresis.) The leaf-r6 ECN rule is true from 10:01, briefly false around the 10:12 checkpoint
   burst (the peer median of PFC jumps), then true again from ≈ 10:13. Why is that one page and not two?
   What would a scorer without duplicate handling call the second page, and why must hysteresis be
   applied only after an episode has opened (two isolated glitches must not page)?

1. Why does a single stuck receiver raise `TxPause3` on the other ports of the same leaf?
2. Leaf r6 has very high PFC but no storm alert. Why is ECN misconfiguration the right root-cause class?
3. Healthy links correct 10⁵ codewords per second. What would you alert on, and what would you ask the
   switch vendor to export?
4. Persistence 2 and 3 both give zero FPs. Which would you deploy, and what does each cost in latency?
5. How do you tell a 32-bit wrap from a `clear counters`, and how do you know the collector is healthy?
