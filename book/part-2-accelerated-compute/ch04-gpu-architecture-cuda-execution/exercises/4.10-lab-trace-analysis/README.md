# Exercise 4.10 — Lab 4: trace analysis of a training step

★★ · Tier L1 · hands-on lab · kind: `lab`

<!-- prompt:start -->
**4.10** ★★ L1 (L2 extension) — Complete [Lab 4](../../lab/README.md): implement the trace-analysis module,
pass `python check.py`, generate `report.md`, and write `analysis.md` (annotated execution trace and
short GPU performance analysis).
*Evidence required:* checker output (all PASS), `report.md`, `analysis.md` per the lab rubric.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 4 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

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

**Hardware run (L2 extension, optional):** from the repository root, `python scripts/hw_labs.py run ch04 --device gpu` (or `--device cpu`; the CPU fallback is automatic without a GPU) writes `lab/l2/results/<label>/report.md`. You may cite its `[MEASURED]` tables in your deliverables; say which host it ran on. The harness builds and runs a Docker image, so Docker must be running.