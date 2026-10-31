# Exercise 6.10 — Lab 6: benchmark harness and statistics

★★ · Tier L1 · hands-on lab · kind: `lab`

<!-- prompt:start -->
**6.10** ★★ L1 (L2 extension) — Complete [Lab 6](../../lab/README.md): harness, statistics, decisions,
roofline, and `benchmark_report.md`. *Evidence required:* checker output (all PASS), `results.json` with
5 runs, and the report per the lab rubric.
<!-- prompt:end -->

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
