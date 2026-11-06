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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **The lab model:** `model_wtrain.yaml` is [lab/data/model_wtrain.yaml](../../lab/data/model_wtrain.yaml) (`seq_len`, `global_batch_seqs`). The step-time and memory output comes from `lab/starter/stepmodel.py`, so finish lab Tasks 1–4 first (Exercise 11.13). To keep the lab inputs intact, copy `lab/data/` to `outputs/data/`, edit the copy, add your candidate layout(s) to `outputs/data/candidates.csv`, and run `python ../../lab/starter/stepmodel.py --data outputs/data` from this folder.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
