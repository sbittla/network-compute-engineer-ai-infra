# 20.7 — Review a deliberately unsafe change plan (★★, L1)

Type: Outline-mandated · Kind: `lab` · Points: 20

## Prompt

<!-- prompt:start -->
Review `lab/data/unsafe_change_plan.md` (this is Lab Part 3). Identify missing validation,
blast-radius controls, and rollback mechanisms, recording them as structured findings in
`findings.yaml`. Then rewrite the plan as a safe change, or rather as **three** changes.

**Evidence required:** `findings.yaml` passing the three Part 3 checks; a rewritten plan (≤ 2
pages) that addresses every finding, with wave plan, abort conditions, and rollback.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/findings.yaml` (copy of lab/starter/findings.yaml)
- `outputs/rewritten_plan.md` (<= 2 pages, three changes)

Run:

```bash
cd ../../lab && python check.py   # the three p3.* lines must PASS
```
