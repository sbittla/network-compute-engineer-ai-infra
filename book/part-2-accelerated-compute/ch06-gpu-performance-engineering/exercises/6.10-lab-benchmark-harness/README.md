# Exercise 6.10 — Lab 6: benchmark harness and statistics

★★ · Tier L1 · hands-on lab · kind: `lab`

<!-- prompt:start -->
**6.10** ★★ L1 (L2 extension) — Complete [Lab 6](../../lab/README.md): harness, statistics, decisions,
roofline, and `benchmark_report.md`. *Evidence required:* checker output (all PASS), `results.json` with
5 runs, and the report per the lab rubric.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 6 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 6.1 ceilings (989 TFLOP/s dense BF16, 1,979 TFLOP/s FP8, 67 TFLOP/s FP32 SIMT, 3.35 TB/s HBM).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in `outputs/`:

- `outputs/check.txt` — the checker output for your implementation (all PASS)
- `outputs/results.json` — your harness results (5 runs, raw samples, config, manifest)
- `outputs/benchmark_report.md` — protocol, results tables, decision table, roofline actions, conclusion (at most 3 pages)

Run from the chapter's `lab/` folder:

```bash
python check.py | tee ../exercises/6.10-lab-benchmark-harness/outputs/check.txt
python starter/harness.py --runs 5 --out ../exercises/6.10-lab-benchmark-harness/outputs/results.json
python starter/analysis.py
```

**Hardware run (L2 extension, optional):** from the repository root, `python scripts/hw_labs.py run ch06 --device gpu` (or `--device cpu`; the CPU fallback is automatic without a GPU) writes `lab/l2/results/<label>/report.md`. You may cite its `[MEASURED]` tables in your deliverables; say which host it ran on. The harness builds and runs a Docker image, so Docker must be running.