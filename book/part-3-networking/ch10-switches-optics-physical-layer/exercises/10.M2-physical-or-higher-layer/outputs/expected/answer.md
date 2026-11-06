# 10.M2 — Physical or higher-layer? (six ports, 600 s deltas)

Method: the five discriminating questions of Section 10.8.1 and the counter-to-layer map of Table
10.6. Values are hypothetical `[ILLUSTRATIVE]`; derived numbers `[MODELED]`. `solve.py` applies the
rules mechanically and reproduces the table and margins.

| Port | Layer | Most likely cause | First safe action | Further evidence |
|---|---|---|---|---|
| P1 | Higher-layer | Congestion: 52,410 discards and 1.1 × 10⁶ / 600 s = 1,833 PFC pause frames/s, with FEC/FCS clean and BER stable (1.2e-7 vs 1.1e-7) | Hand to the Chapter 9 congestion workflow | Queue depth, ECN marks, which flows (incast?) |
| P2 | Physical | Bursty corruption: 340 uncorrectable CW and 322 FCS at a moderate BER (4.0e-5, stable) with normal DOM → reflection, damaged connector or intermittent cable | Drain; inspect/clean both ends; swap cable, then optic | FEC histogram tail; far-end counters |
| P3 | Physical *elsewhere* | 1,870 FCS errors with zero uncorrectables and a clean BER (2.0e-8, below the 1 × 10⁻⁵ warn threshold; its 5.1 × 10⁶ pre-FEC corrected bits are just BER × 425 × 10⁹ × 600) → stomped frames from an upstream cut-through hop | Do not touch this link; find the upstream port with uncorrectables | Upstream switch ingress FEC-uncorrectable counters; stomped-CRC counter if available |
| P4 | Physical | Flapping link (5 link-down events in 600 s); the 12 uncorrectables and 9 FCS are side effects of transitions | Drain; reseat/inspect; check firmware and far end; replace optic if it repeats | Link up/down syslog timestamps, far-end logs, DOM history |
| P5 | Physical (critical) | One lane at −6.8 dBm (below the −5.9 dBm receiver minimum, 4.7 dB below its siblings) and BER up 45× in 7 days → contamination or damage on one MPO fiber, worsening | Drain now (host link: via the scheduler); inspect/clean both ends; replace jumper | Far-end per-lane Tx; FEC histogram |
| P6 | Higher-layer | 12,044 giants, everything else clean → MTU mismatch (port MTU below host frame size) | Compare port vs host MTU (Chapter 7) | Port config, host `ip link` MTU |

**FEC margins** (Section 10.4.3, limit 2.4 × 10⁻⁴):

```text
P2: margin = log10(2.4e-4 / 4.0e-5) = log10(6.0)  = 0.78 decades
P5: margin = log10(2.4e-4 / 9.0e-5) = log10(2.67) = 0.43 decades
P5 trend: 9.0e-5 / 2.0e-6 = 45× in 7 days;  lane imbalance: −2.1 − (−6.8) = 4.7 dB (> 3 dB rule)
```

P2's uncorrectables at 0.78 decades of margin are impossible under independent errors: the
binomial model of Table 10.1 gives P(uncorrectable) ≈ 7.9 × 10⁻²⁵ per codeword at BER 4.0 × 10⁻⁵, so
600 s × 78.1 × 10⁶ codewords/s = 4.7 × 10¹⁰ codewords should yield ≈ 4 × 10⁻¹⁴ uncorrectables, not 340.
The errors are bursty. P5 has no uncorrectables yet but is
critical on two counts (Rx below receiver minimum, BER ≥ 10⁻⁴ policy is close).

**Common mistakes.** Calling P1 physical because of "errors" (discards are not corruption);
replacing P3's cable; treating P5 as a warning because uncorrectables are zero.
