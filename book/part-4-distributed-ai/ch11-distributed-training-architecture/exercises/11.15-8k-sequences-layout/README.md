# 11.15 — 8k sequences next quarter (★★★, L1)

**Type:** Design challenge · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
**11.15 ★★★ L1 — 8k sequences next quarter.** Research wants W-TRAIN at sequence 8,192 with the same
global batch in tokens (512 sequences). Propose a layout for ORION-256, show it fits under 68 GB, and
estimate the step time with the lab model (edit `model_wtrain.yaml`). Defend your choice against one
alternative on memory, communication, and risk.
*Evidence required:* the config, memory and step-time output from the tool, and a trade-off table.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
