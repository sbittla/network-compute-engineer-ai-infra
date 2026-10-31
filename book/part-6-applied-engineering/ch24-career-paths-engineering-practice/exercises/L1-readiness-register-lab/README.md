# L1 — Role-readiness scorer and register validator (★★, L1)

Hands-on lab · difficulty ★★ · tier L1 · kind `lab` · [exercise index](../README.md)

<!-- prompt:start -->
**L1 ★★ L1 — Role-readiness scorer and register validator.** Complete
[lab/README.md](../../lab/README.md) Tasks 1–8, produce `readiness_report.md`, and explain every evidence
flag raised for the sample learner.
*Evidence required:* `python check.py` output showing 11/11 PASS; the generated report; a one-page
explanation of the flags (rule, why it exists, what the learner should do).
<!-- prompt:end -->

The prompt's `lab/README.md` link is relative to `exercises.md`; from this folder the lab guide is [../../lab/README.md](../../lab/README.md).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/check_output.txt`
- `outputs/readiness_report.md`
- `outputs/flags_explained.md`

Run:

```bash
cd ../../lab && python check.py | tee ../exercises/L1-readiness-register-lab/outputs/check_output.txt
python starter/career_lab.py --role ai_network --seniority senior --out ../exercises/L1-readiness-register-lab/outputs/readiness_report.md
```
