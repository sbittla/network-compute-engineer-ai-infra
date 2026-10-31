# 10.M2 — Interpret counters: physical or higher-layer? (★★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 8

## Prompt

<!-- prompt:start -->
**10.M2 (Outline) — Interpret counters: physical or higher-layer? (★★, L1).**
The table below shows hypothetical deltas over 600 s for six 400G-DR4 ports on one leaf (pre-FEC BER
and Rx power are T1 values; "BER 7 days ago" is from the baseline). Classify each port as physical or
higher-layer, give the most likely cause, the first safe action, and one further piece of evidence you
would collect.

| Port | Link-down events | FEC corrected CW | FEC uncorr. CW | FCS errors | Symbol errors | Giants | Out discards | PFC pause tx | Pre-FEC BER (now / 7 days ago) | Rx power per lane (dBm) |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 0 | 3.1 × 10⁷ | 0 | 0 | low | 0 | 52,410 | 1.1 × 10⁶ | 1.2e-7 / 1.1e-7 | −1.1, −1.3, −0.9, −1.2 |
| P2 | 0 | 8.6 × 10⁹ | 340 | 322 | high | 0 | 0 | 0 | 4.0e-5 / 3.6e-5 | −2.0, −2.1, −1.9, −2.0 |
| P3 | 0 | 5.1 × 10⁶ | 0 | 1,870 | ≈ 0 | 0 | 0 | 0 | 2.0e-8 / 2.1e-8 | −0.8, −0.7, −0.9, −0.8 |
| P4 | 5 | 2.0 × 10⁷ | 12 | 9 | low | 0 | 0 | 0 | 8.0e-8 / 7.5e-8 | −1.4, −1.5, −1.3, −1.6 |
| P5 | 0 | 1.9 × 10¹⁰ | 0 | 0 | high | 0 | 0 | 0 | 9.0e-5 / 2.0e-6 | −6.8, −2.1, −2.0, −2.2 |
| P6 | 0 | 2.6 × 10⁶ | 0 | 0 | ≈ 0 | 12,044 | 0 | 0 | 1.0e-8 / 1.0e-8 | −0.5, −0.6, −0.4, −0.5 |

*Evidence required:* a six-row answer table (layer, cause, first action, further evidence) and, for
P2 and P5, the FEC margin in decades with arithmetic.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: the worked answer: formula, substitution, result with units, decision sentence
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
