# 10.W1 — Link budget for a cross-hall DR4 link (★★, L1)

**Type:** Worked problem · **Kind:** computed · **Points:** 9

## Prompt

<!-- prompt:start -->
**10.W1 — Link budget for a cross-hall DR4 link (★★, L1).**
Halcyon AI adds a second data hall. A 400G-DR4 link runs 420 m over SMF with four mated MPO pairs
(two patch panels per hall) and two fusion splices. Assume 0.4 dB/km, 0.5 dB per mated MPO pair,
0.1 dB per splice; DR4 worst-case Tx −2.9 dBm per lane, receiver minimum −5.9 dBm average per lane,
maximum channel insertion loss 3.0 dB (`[VENDOR-SPEC, 2026-10]`, IEEE 802.3bs; verify).
(a) Compute channel loss, worst-case Rx power, and margin. (b) One MPO pair is dirty and adds 1.0 dB.
Does the link still meet the channel budget and the receiver minimum? (c) Convert the answer to (a)'s
Rx power to mW. (d) In service, all four lanes read Rx −4.1 dBm while the far end reports Tx +0.6 dBm
on every lane. Compute measured and excess loss and state where you look first.
*Evidence required:* every formula, substitution, and result in dB/dBm/mW; a one-sentence decision for
(b) and (d).
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: the worked answer: formula, substitution, result with units, decision sentence
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
