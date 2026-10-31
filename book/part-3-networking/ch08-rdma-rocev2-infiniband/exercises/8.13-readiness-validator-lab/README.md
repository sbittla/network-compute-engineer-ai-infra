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
