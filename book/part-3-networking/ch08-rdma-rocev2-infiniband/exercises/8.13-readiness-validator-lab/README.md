# 8.13 — RDMA readiness validator and perftest analyzer (★★, L1)

Type: Hands-on lab · kind: `lab` · 100 points

## Prompt

<!-- prompt:start -->
**8.13 RDMA readiness validator and perftest analyzer** ★★ · L1
Complete [lab/README.md](../../lab/README.md) Tasks 1–8. Submit `readiness_report.md`, `diagnosis.md`, and
your completed starter modules.
*Evidence required:* `python check.py` output showing all checks PASS; the report; a diagnosis for each
flagged perftest pair with mechanism, evidence, and next discriminating test, stating that the data are
`[SIMULATED]`.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 8 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Complete lab Tasks 1–8 in `lab/starter/` until the checker reports every check PASS (the data-regeneration check may SKIP). Put every deliverable in `outputs/`:

- `outputs/check_output.txt` (the full checker output)
- `outputs/readiness_report.md`
- `outputs/diagnosis.md`
- `outputs/starter/` (copies of your completed lab/starter/*.py modules)

Run:

```bash
cd ../../lab && python check.py | tee ../exercises/8.13-readiness-validator-lab/outputs/check_output.txt
```
