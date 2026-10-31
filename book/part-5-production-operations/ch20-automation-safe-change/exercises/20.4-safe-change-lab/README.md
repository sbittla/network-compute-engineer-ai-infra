# 20.4 — Lab 20: safe-change automation (★★, L1)

Type: Hands-on lab · Kind: `lab` · Points: 100

## Prompt

<!-- prompt:start -->
Complete [Lab 20](../../lab/README.md), Parts 1–3. Then answer:

a. For each planted invalid desired value found by `validate_desired`, describe the RoCE failure it
   would have caused on ORION if applied.
b. Explain the two wave-1 situations that would make a naive controller abort, and the design
   choice in your controller that prevents each.
c. Justify `rollback_scope: all_changed` for this rollout, or argue for failing-wave-only.

**Evidence required:** `python check.py` output with all 13 checks PASS; the decision log from
`run_rollout`; written answers a–c (≤ 1 page). L2/L3: a filled-in copy of `lab/manifest.yaml` with
the extension fields.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/check_output.txt` (python check.py, 13/13 PASS)
- `outputs/decision_log.md` (wave -> decision -> reasons)
- `outputs/answers.md` (a-c, <= 1 page)
- `outputs/manifest.yaml` (L2/L3 only)

Run:

```bash
cd ../../lab && python check.py
```
