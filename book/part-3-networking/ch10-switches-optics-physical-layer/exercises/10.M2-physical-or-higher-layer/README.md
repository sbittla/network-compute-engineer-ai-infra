# 10.M2 — Interpret counters: physical or higher-layer? (★★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 8

## Prompt

<!-- prompt:start -->
**10.M2 (Outline) — Interpret counters: physical or higher-layer? (★★, L1).**
The table below shows hypothetical deltas over 600 s for six 400G-DR4 ports on one leaf (pre-FEC BER
and Rx power are T1 values; "BER 7 days ago" is from the baseline). Classify each port as physical or
higher-layer, give the most likely cause, the first safe action, and one further piece of evidence you
would collect.

| Port | Link-down events | FEC corrected CW | FEC uncorr. CW | FCS errors | Pre-FEC corrected bits | Giants | Out discards | PFC pause tx | Pre-FEC BER (now / 7 days ago) | Rx power per lane (dBm) |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 0 | 3.1 × 10⁷ | 0 | 0 | 3.1 × 10⁷ | 0 | 52,410 | 1.1 × 10⁶ | 1.2e-7 / 1.1e-7 | −1.1, −1.3, −0.9, −1.2 |
| P2 | 0 | 8.6 × 10⁹ | 340 | 322 | 1.0 × 10¹⁰ | 0 | 0 | 0 | 4.0e-5 / 3.6e-5 | −2.0, −2.1, −1.9, −2.0 |
| P3 | 0 | 5.1 × 10⁶ | 0 | 1,870 | 5.1 × 10⁶ | 0 | 0 | 0 | 2.0e-8 / 2.1e-8 | −0.8, −0.7, −0.9, −0.8 |
| P4 | 5 | 2.0 × 10⁷ | 12 | 9 | 2.0 × 10⁷ | 0 | 0 | 0 | 8.0e-8 / 7.5e-8 | −1.4, −1.5, −1.3, −1.6 |
| P5 | 0 | 1.9 × 10¹⁰ | 0 | 0 | 2.3 × 10¹⁰ | 0 | 0 | 0 | 9.0e-5 / 2.0e-6 | −6.8, −2.1, −2.0, −2.2 |
| P6 | 0 | 2.6 × 10⁶ | 0 | 0 | 2.6 × 10⁶ | 12,044 | 0 | 0 | 1.0e-8 / 1.0e-8 | −0.5, −0.6, −0.4, −0.5 |

*Evidence required:* a six-row answer table (layer, cause, first action, further evidence) and, for
P2 and P5, the FEC margin in decades with arithmetic.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/10.M2-physical-or-higher-layer/` (instructor material in the full repository; removed from student releases).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: the worked answer: formula, substitution, result with units, decision sentence
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
