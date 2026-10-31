# 10.T1 — Leaf r6 uplinks are dirty (incomplete evidence) (★★★, L1)

**Type:** Troubleshooting case · **Kind:** written · **Points:** 5

## Prompt

<!-- prompt:start -->
**10.T1 — "Leaf r6 uplinks are dirty" (incomplete evidence).**
An automated alert says `orion-be-leaf-r6:Ethernet33`–`Ethernet40` (all eight uplinks to spine-1) show
rising output discards and PFC pause frames received. They rise only during the 20-minute nightly
run of an MoE evaluation job whose expert-parallel all-to-all crosses rails through the spines
(Chapter 12); backend training traffic otherwise stays on its rail, and checkpoints use the
frontend/storage NICs. A colleague files a ticket to clean all eight uplinks. You have: discards and
PFC counters for those eight ports (rising only between 01:00 and 01:20), FEC-uncorrectable = 0 and FCS = 0 on all eight,
pre-FEC BER 10⁻⁸–10⁻⁷, DOM normal. You do **not** have spine-side counters or host-side counters.
(a) Is this physical? Apply the five discriminating questions of Section 10.8.1. (b) What evidence
is missing, and how would you collect it safely? (c) Who owns the next step, and what do you write on
the cleaning ticket?
*Evidence required:* the five questions answered from the given evidence; a list of ≥ 3 missing items
with the command or data source for each; a two-sentence ticket update.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Show every formula, substitution and result with units, and label each number with its evidence label.
