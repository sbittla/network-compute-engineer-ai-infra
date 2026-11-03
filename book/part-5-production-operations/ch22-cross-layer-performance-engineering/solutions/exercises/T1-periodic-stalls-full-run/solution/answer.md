# T1 — Periodic stalls on the full run (solution)

Evidence `[ILLUSTRATIVE]` (from the prompt). Manuscript: Sections 22.3 (tree, ranking), 22.12 and the
RB-PERF-03 runbook; NCCL timeout defaults from docs/VERIFIED_FACTS.md.

**(a) Hypothesis tree.** Root: median 17.9 → 18.5 s (+0.6 s) plus a collective-wide 6–9 s stall every
30–50 steps; data wait flat; per-rank wait unimodal.

| Leaf (term) | Predicted fingerprint | Verdict |
|---|---|---|
| Physical-layer degradation on one link → RoCE loss → retransmission (`T_comm,exposed`) | Errors on one port only; NIC `out_of_sequence` (NAK-recovered loss) and `local_ack_timeout_err` (timeout-recovered loss) rising on that NIC; all ranks stall together | **Matches**: Ethernet28 FEC corrected 1.9e9 vs 1–4e6 elsewhere (475–1,900×), 312 uncorrectable, 297 CRC; host `rx_crc_errors_phy` and `rx_symbol_err_phy` rising |
| Fabric congestion / PFC storm (`T_comm,exposed`) | ECN marks and PFC pauses on many ports, load-correlated; no CRC/FEC | Contradicted: errors are port-local |
| Straggler compute (`T_compute`) | Bimodal wait (slow rank waits least); clock or thermal reasons | Contradicted: unimodal, 1,830 MHz, no reasons |
| Storage or checkpoint stall (`T_data`, `T_ckpt`) | Data wait up, or period equal to checkpoint interval | Contradicted: data wait 0.04–0.06 s, irregular period |
| Host jitter on one node (`T_host`) | One rank late; timeline gaps on one host | Possible, but NIC counters point elsewhere |

**(b) Ranked tests** (`score = info / (cost_h × risk_mult)`, low = 1, medium = 2):

| Rank | Test | Info | Cost (h) | Risk | Score |
|---|---|---|---|---|---|
| 1 | Correlate long-step timestamps with increments of `local_ack_timeout_err` (orion-n15 `mlx5_3`) and FEC uncorrectable (orion-be-leaf-r3 Ethernet28) from existing telemetry | 0.8 | 0.5 | low | 1.6 |
| 2 | Module diagnostics on both ends: host `ethtool -m <rail-3 netdev>` (DOM Rx/Tx power), switch transceiver DOM | 0.6 | 0.5 | low | 1.2 |
| 3 | Drained orion-n15 and a peer: `ib_write_bw -d mlx5_3 --report_gbits` on rail 3 with counters | 0.7 | 3 | medium | 0.117 |

**(c) Root cause and chain.** The NIC3 optic on orion-n15, reseated three days ago (likely a
contaminated or damaged connector), has a marginal optical budget → high pre-FEC bit error ratio (FEC
corrected codewords 1.9e9 per 10 min) → some codewords uncorrectable (312). The mean pre-FEC BER (≈ 1e-5) is
far below the RS(544,514) limit (≈ 2.4e-4), so random errors would give almost none; the errors are bursty
(dirty connector) and the FEC symbol-error histogram shows codewords at the 15-symbol limit → frames fail CRC and are
dropped (297 in-errors; host `rx_crc_errors_phy` 4,118 and `rx_symbol_err_phy` 89,233, rising) →
RoCE packets lost on reliable-connected QPs. A loss followed by more packets is detected as
out-of-sequence and recovered by NAK and go-back-N (`out_of_sequence` rising; small delays → median
+0.6 s). Loss of the *last* packets of a message is recovered only by the ACK timeout
(`local_ack_timeout_err` rising). With NCCL 2.23+, `NCCL_IB_TIMEOUT` defaults to 20:
4.096 µs × 2²⁰ = 4.29 s, so one or two timeouts on the critical path give 4.3–8.6 s, matching the 6–9 s
stalls; all ranks see them because the collective waits for one flow. (On NCCL ≤ 2.22 the default 18 gives
1.07 s per retry, and 6–9 s would need several consecutive retries.)

**(d) Safe fix and validation.** Fabric team, under a change ticket: at the job's next checkpoint, cordon
orion-n15 (ORION has no spare; Training Infra decides pause or restart at reduced DP), clean or replace
the rail-3 optic and inspect both ends. Acceptance: link at 400 Gb/s; pre-FEC BER within the fleet
baseline (≈ 1e-8 here; e.g. < 1e-7) and stable over a 1 h soak; zero FEC uncorrectable and zero CRC over
the soak; module Rx power inside the warning thresholds on both ends (corrected-codeword counts are a
trend signal, not a pass/fail threshold); `ib_write_bw` ≥ 90 % of line rate; two-node
`all_reduce_perf` busbw at fleet baseline. Return through the lifecycle workflow (Chapter 16).
Validation: 5 × 100-step windows with median 17.9 ± 0.1 s, no step > 20 s in 1,000 consecutive steps,
`local_ack_timeout_err` flat. Not allowed: switch configuration changes, raising `NCCL_IB_TIMEOUT` (masks
the fault), reseating optics on a live job without a ticket.
