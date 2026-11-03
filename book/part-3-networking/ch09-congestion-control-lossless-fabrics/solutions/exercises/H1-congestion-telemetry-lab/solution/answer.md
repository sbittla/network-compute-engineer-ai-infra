# H1 — Progressive Lab 3: congestion telemetry diagnosis (reference solution)

Data are seed-generated, `[SIMULATED / SYNTHETIC]`. Reference implementation:
`solutions/lab/congestion_lab.py`. `python lab/check.py --impl solution` reports **15/15 PASS**;
`data_determinism` reports SKIP in the student release (no `lab/tools/`). The named checks and their PASS
lines are in `outputs/lab_checks.json`. Relies on manuscript Sections 9.2–9.12 and lab README §6–§8.
Per-episode evidence is worked in O1, the experiment plan in O3.

## What the checker confirms

| Task | Reference result |
|---|---|
| 1 rates | First sample NaN; gaps divided by the true elapsed time (spine-2 at t = 312 s divides by 14 s); the counter reset on `orion-be-leaf-r4:eth1/2` at 200 s gives NaN; no negative rates across 9,588 samples |
| 2 episodes | 3 episodes: 100–158 s, 250–318 s, 400–468 s; the busy-but-healthy 520–558 s window on leaf-r4 eth1/7 is **not** an episode |
| 3 labels and roots | incast (root `orion-be-leaf-r3:eth1/5`), pause_propagation (root `orion-be-leaf-r3:eth1/10`), pfc_storm |
| 4 storm source | `orion-n12:mlx5_3`, confirmed by its own `pfc_tx_p3` ≈ 23,750 /s |
| 5 victims | P1 (n03 → n07) in the incast (p99 ≈ 21×) and the storm (≈ 358×); P4 (n04 rail 4 → n13 rail 3) in the propagation (≈ 39×). **Not** P3 (its destination is the incast root) and not P2 (control) |
| 6 QoS audit | `orion-be-leaf-r3 ECN_KMIN_HIGH`, `orion-be-leaf-r3 PFC_WATCHDOG_DISABLED`, `orion-be-leaf-r4 CNP_CLASS_MISMATCH`, `orion-be-spine-2 PFC_PRIORITY_MISMATCH`; nothing on spine-1 |
| 7 simulation | A 960.0 µs, peak 1,660 KB, paused 862.8 µs, 0 CNPs; B 1,256.8 µs, paused 113.6 µs, 60 CNPs; C (lossy) 3,875.2 µs, 17,840,000 B dropped; line-rate lower bound 960 µs |
| 8 report | All 9 `REPORT_SECTIONS`, the simulation labelled `[SIMULATED]`, the storm source named |

## Report content a full-marks submission adds (≤ 3 pages)

**Diagnosis, ranked per episode, with discriminating evidence** (values that would differ under the
competing label; see O1):
- *Incast:* eth1/5 at line rate, queue held near the 1,000 KB Xoff-equivalent (≈ 1,430 KB median), ECN
  marks only on peaks (median 0), senders paused ≈ 17–19 k frames/s each, no pause rx; pause only on the
  first hop. Contributing cause: `ECN_KMIN_HIGH` (Kmin 1,500 KB = 7.5 × the 200 KB same-rail BDP, a
  template value × 10). Marks start after Xoff, so the leaf runs on pause.
- *Propagation:* root eth1/10. Leaf-r3 uplinks pause the spines, the spines pause leaf-r4, and leaf-r4
  pauses its rail-4 NICs. Worsened by `CNP_CLASS_MISMATCH` on leaf-r4 (feedback stuck behind pauses).
  The cross-rail traffic suggests a rank-to-rail mapping error: **correlated, not proven**.
- *Storm:* the NIC is **proven** as the source by its own counters. `PFC_WATCHDOG_DISABLED` is why it
  lasted ≈ 70 s.
- *Latent:* spine-2's extra lossless priority 4 wastes headroom and gives path-dependent behaviour,
  with no episode yet.

**Victim explanations:** P1's destination port eth1/7 is uncongested, but its *source* NIC orion-n03 is
paused by the leaf (HOL blocking). P4 crosses paused leaf-r4 and spine ports.

**Simulation table `[SIMULATED]`** with "cannot conclude" items (≥ 4): absolute magnitudes on real
ASICs; shared-buffer and per-PG behaviour; real DCQCN timers, byte counter and additive/hyper increase
(the model has fast recovery only); NIC loss recovery (the C config assumes best-case selective repeat);
multi-hop propagation, ECMP, storms, deadlock and watchdog behaviour; generalization beyond 12
synchronous equal senders.

**Experiment plan:** A vs B on an isolated L3 fabric. One variable (Kmin/Kmax); ≥ 5 interleaved
repetitions; warm-up discarded; counters snapshotted per run; manifest fields; rollback (see O3).

**Mitigation, ordered and safe:** (1) enable the PFC watchdog fabric-wide (canary leaf, then roll out);
(2) restore the template ECN profile on leaf-r3 (150 / 1,500 KB) via change control with rollback;
(3) fix CNP mapping on leaf-r4 (DSCP 48 → TC 6); (4) remove priority 4 from spine-2; (5) drain and
inspect orion-n12. Validation: ECN-mark/pause ratio up on leaf-r3, pause on fabric ports ≈ 0 during the
next incast, zero TC 3 discards over 24 h, and a config-compliance audit clean.

## Common mistakes

Flagging the 520–558 s window. Naming P3 as a victim. Presenting simulated numbers without the label.
Claiming the rank-mapping cause as proven.

## Hardware run (L2 harness)

The course harness (`python scripts/hw_labs.py run ch09`) has no RDMA NIC, so the PFC/ECN/CNP counter
capture is not runnable. It does exercise the same method: `counters_to_rates` on real cumulative
counters (`RetransSegs`, `InCEPkts`, `InECT0Pkts`, loss probes) snapshotted around a loopback TCP incast,
with per-flow percentiles and Jain's index. The report notes that loopback has no egress queue, so it
cannot reproduce the episodes in this lab.
