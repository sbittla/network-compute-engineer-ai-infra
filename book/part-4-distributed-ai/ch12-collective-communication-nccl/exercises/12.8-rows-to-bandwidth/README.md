# 12.8 — From rows to bandwidth (★★, L1)

**Type:** Worked problem · **Kind:** computed · **Points:** 6

## Prompt

<!-- prompt:start -->
**12.8 ★★ L1 — From rows to bandwidth.** From `lab/data/c4_4node_aligned.log`, take the rows for
1 MiB, 64 MiB, and 4 GiB (out-of-place). Recompute algbw and busbw by hand, state the region each row
is in, and compare the 4 GiB busbw with the node's NIC egress limit. *Evidence required:* nine
computed values with arithmetic, region labels, and an efficiency percentage.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units and evidence labels
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
