# 10.M2 — Physical or higher-layer? `[MODELED]`

| Port | Layer | Cause | Margin (decades) | BER now/7 d | Lane imbalance (dB) | P(uncorr) random model |
|---|---|---|---|---|---|---|
| P1 | higher-layer | congestion | 3.301 | 1.09x | 0.4 | 4.2e-65 |
| P2 | physical | bursty corruption (uncorrectables at moderate BER, DOM normal) | 0.778 | 1.11x | 0.2 | 7.9e-25 |
| P3 | physical-elsewhere | stomped frames from an upstream cut-through hop | 4.079 | 0.95x | 0.2 | 1.5e-77 |
| P4 | physical | link flap (FEC/FCS counts are side effects of transitions) | 3.477 | 1.07x | 0.3 | 6.3e-68 |
| P5 | physical | one-lane loss: contamination/damage on one MPO fiber, BER rising | 0.426 | 45.0x | 4.8 | 2.6e-19 |
| P6 | higher-layer | MTU mismatch | 4.38 | 1.0x | 0.2 | 2.2e-82 |

Margins: P2 log10(2.4e-4/4.0e-5) = 0.78; P5 log10(2.4e-4/9.0e-5) = 0.43.
P1 PFC rate = 1.1e6 / 600 s = 1833.3 frames/s.
P2's uncorrectables are far above the random-error model at its BER: bursts.
