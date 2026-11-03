# T1 — Periodic stalls on the full run (★★★, L1)

Troubleshooting case · difficulty ★★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**T1 ★★★ (L1 analysis; L3 to confirm) — Periodic stalls on the full run.** The 256-GPU W-TRAIN run's
median step time moved from 17.9 s to 18.5 s, and roughly every 30–50 steps one step takes 24–27 s. All
ranks see the long steps at the same step numbers. Evidence collected so far:

```text
data_wait per step:            0.04–0.06 s on all ranks, including the long steps
per-rank collective wait:      unimodal; on long steps every rank waits 6–9 s
DCGM:                          clocks 1,830 MHz, no slowdown reasons, temperatures 65–70 °C
NCCL (2.23+):                  no timeouts; NET channel lines end in /GDRDMA on all nodes
orion-be-leaf-r3 Ethernet28 (→ orion-n15 NIC3), 10-minute deltas:
    FEC corrected codewords   1.9e9   (other ports: 1–4e6)
    pre-FEC BER               ≈ 1e-5  (other ports: ≈ 1e-8)
    FEC uncorrectable         312     (other ports: 0)
    in-errors (CRC)           297
orion-n15: ethtool -S <rail-3 netdev> | grep -E 'rx_crc_errors_phy|rx_symbol_err_phy'
    rx_crc_errors_phy: 4,118   (rising)      rx_symbol_err_phy: 89,233 (rising)
orion-n15: /sys/class/infiniband/mlx5_3/ports/1/hw_counters/out_of_sequence  rising; local_ack_timeout_err rising
change log: none for ORION in 72 h; orion-n15 had a NIC3 optic reseated 3 days ago
```

a. Build a hypothesis tree with at least four leaves and state each leaf's predicted fingerprint.
b. Rank three next tests by information value, cost, and risk.
c. State the most likely root cause and the full causal chain from physical layer to step time.
d. Specify the safe fix (who, what scope, what acceptance test) and the validation with numbers.

*Evidence required:* tree; ranked test table with scores; causal chain naming the counters that support
each link; a fix plan that obeys the runbook's "not without change approval" list; validation criteria.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`
