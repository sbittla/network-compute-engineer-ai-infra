# 17-L1 · Lab 17: ORION scheduler simulator and diagnoser (★★ · L1)

Type: hands-on-lab · Kind: lab · Points: 100

<!-- prompt:start -->
**17-L1** ★★ L1 (L2/L3 extensions) — Complete [Lab 17](../../lab/README.md): implement
`starter/orion_sched.py` Tasks 1–6 and write `placement-report.md` and `pending-guide.md`.
*Evidence required:* `python check.py` output showing `9/9 checks passed`; the two reports per the lab
rubric. For an L2/L3 extension, the filled-in copy of `manifest.yaml` and the captured events or
`all_reduce_perf` results (≥ 5 repetitions, median and p95).
<!-- prompt:end -->

## What to submit

Put these files in `outputs/`:

- `check_output.txt` — from the chapter folder, `cd lab && python check.py > ../exercises/17-L1-orion-scheduler-lab/outputs/check_output.txt`
- `placement-report.md` and `pending-guide.md` (lab Tasks 7–8)
- L2/L3 extension only: your filled `manifest.yaml` and the captured events or `all_reduce_perf` results

**Hardware run (course harness).** L2 on the course harness: `python scripts/hw_labs.py run ch17` runs
your `diagnose_pending` on a node object built from the host's real GPU discovery, and measures what
time-slicing one GPU between two jobs costs; see `lab/l2/results/`. The kind/k3s/Slurm part is recorded
as not runnable there.
