# Exercise 4.10 — Lab 4: trace analysis of a training step

★★ · Tier L1 · hands-on lab · kind: `lab`

<!-- prompt:start -->
**4.10** ★★ L1 (L2 extension) — Complete [Lab 4](../../lab/README.md): implement the trace-analysis module,
pass `python check.py`, generate `report.md`, and write `analysis.md` (annotated execution trace and
short GPU performance analysis).
*Evidence required:* checker output (all PASS), `report.md`, `analysis.md` per the lab rubric.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/check.txt` — the checker output for your implementation (all PASS)
- `outputs/report.md` — the generated findings report
- `outputs/analysis.md` — annotated execution trace and short GPU performance analysis (lab Task 7, at most 2 pages)

Run from the chapter's `lab/` folder:

```bash
python check.py | tee ../exercises/4.10-lab-trace-analysis/outputs/check.txt
python starter/trace_analysis.py --out ../exercises/4.10-lab-trace-analysis/outputs/report.md
```
