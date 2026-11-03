# 20-L1 — Lab 20, safe-change automation: reference solution

**Relies on:** lab/README.md (Parts 1–3, Section 7 rubric), manuscript Sections 20.5.1, 20.7.4, 20.8 and
20.11 (Tables 20.9 and 20.13). Data are `[SIMULATED]`. The reference implementation is
`solutions/lab/safe_change.py` with `solutions/lab/findings.yaml`; its checker report is
`solutions/lab/outputs/check_solution.txt` (14/14 PASS).

## Checker evidence

All six `p1.*`, four `p2.*` and three `p3.*` checks PASS. The key lines: `p1.validate_planted_violations`
(4 violations, all planted ones found), `p1.plan_diff_blocked_unreachable` (24 actions on 22 targets),
`p1.idempotent_converge_and_noop` (3 capped batches of 8, 8, 6; re-plan empty), `p2.wave_decisions`
(wave 0 proceed, wave 1 proceed with `orion-n13` skipped, wave 2 abort), `p3.review_coverage` (17/17).

## Decision log (`run_rollout`, CHG-2026-1110)

| Wave | Nodes | Decision | Reasons `[SIMULATED]` |
|---|---|---|---|
| 0 | n01, n05 | proceed | all AC1–AC5 within thresholds |
| 1 | n09, n13, n17 | proceed | n13 fails precheck (health degraded, flapping in baseline) → skipped, deferred to repair; n09 has one ≈ 7 % dip, median within 5 % |
| 2 | n21, n25, n29, n02 | **abort** | n25 busbw 39.41 vs 43.67 GB/s (−9.8 %), CNP 986/s vs 200/s; n29 −9.9 %, 1,008/s; AC1 and AC2 |

Rollback (`all_changed`): n01, n02, n05, n09, n17, n21, n25, n29 → firmware 28.42.1000. Waves 3–5 never start.

## a. What each planted invalid value would have done

- **`orion-n10` host_mtu 9,216** (POL-MTU-FABRIC: 9,216 + 22 = 9,238 > 9,216). RoCE is *not* affected: its
  packets are bounded by the 4,096-byte path MTU. Backend TCP/UDP flows (NCCL bootstrap or socket fallback,
  iperf and health checks, ssh over backend addresses) send 9,216-byte packets that the leaf port drops; with
  no ICMP reply they black-hole. Connections open, small requests work, bulk transfers hang.
- **`orion-be-leaf-r5` pfc_priorities [4]** (POL-PFC). RoCE data on priority 3 is unprotected on rail 5: drops
  under incast, go-back-N retransmissions, a rail-5-only busbw collapse, while pauses on the empty priority 4
  are useless. The hardest kind to diagnose, because seven rails look fine.
- **`orion-n22` firmware 28.44.0500** (POL-FW, not in {28.42.1000, 28.43.1014}). Outside the Chapter 16
  compatibility matrix: risk of NIC init failures with the installed driver or a subtle behaviour change
  (for example in congestion handling) that nobody validated.
- **`orion-n25` ecn_enabled "yes"** (SCHEMA). Depends on the consumer: coerced to true, rejected mid-rollout
  at apply time, or read as false. ECN off means DCQCN gets no marks, senders do not slow down, and PFC
  becomes the only congestion control, with pause propagation.

## b. The two wave-1 traps

1. **`orion-n13` pre-existing link flaps.** Evaluated, it trips AC5 (flaps > 0) and aborts a good change. The
   controller runs prechecks *before* the change, skips and defers unhealthy nodes, and sends them to repair.
2. **`orion-n09` single-sample dip (≈ 7 %).** A `min` statistic aborts on it. AC1 uses the median of 12 post
   samples against the median of 6 baseline samples, which ignores one transient.

## c. Rollback scope

`all_changed` is right here. The regression mechanism (firmware behaviour under congestion: busbw −10 %,
CNP ≈ 5×) is load-dependent, so it may be latent on wave 0–1 nodes that simply saw different traffic during
their bake. Nothing distinguishes n25/n29 from n21/n02 or from the earlier waves: same firmware, same SKU.
Failing-wave-only rollback is defensible only when the failure is tied to an attribute unique to that wave,
and that is a decision to record before the rollout, not to improvise.

## L2/L3 manifest

An L2 submission records OS, kernel, NIC, firmware, driver, rdma-core version, MTU before and after, and the
second-run plan size (must be 0). L1-only submissions leave these fields empty.

## Marking (100 points, lab README Section 7)

15 + 20 + 20 + 5 + 15 + 10 + 15 as in `meta.yaml`. Deduct a point in (a) if the answer claims RoCE breaks on
`orion-n10`.

## Hardware run (L2 harness)

The course harness (`python scripts/hw_labs.py run ch20`) runs the decision half of the L3 canary on real
measurements. GEMM throughput samples stand in for busbw and go through `evaluate_wave` with the lab's
AC1 and bake rule. A no-op change must *proceed*, an injected ≈ 20 % regression must *abort* naming AC1,
and the regression with half the bake samples must *hold*; `run_rollout` must roll back every changed
node. It also reports run-to-run noise against the 5 % threshold, the point behind answer (b). The
MTU-changing reconciler is not runnable there (no root, no RDMA NIC).
