# Exercise TS — Slow inference replica orion-n29

**Difficulty:** ★★★ · **Tier:** L1 · **Type:** troubleshooting · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
One W-INFER replica (`orion-n29`) shows TPOT p95 of 19 ms while the other seven replicas of the
default pool show 12 ms `[ILLUSTRATIVE]`. Healthy p95 sits above the ≈ 9.5 ms median decode step of
Section 1.9 because, under continuous batching, some steps also carry prefill chunks of newly
admitted requests, and p95 adds scheduler jitter. Batch sizes, prompt mix, and model version are
identical (the router balances evenly). Evidence available so far:

| Signal | `orion-n29` | Other replicas (median) |
|---|---:|---:|
| `DCGM_FI_PROF_DRAM_ACTIVE` (mean of 8 GPUs) | 0.41 | 0.63 |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | 0.05 | 0.08 |
| NVLink link state, GPU 5 (`nvidia-smi nvlink --status`) | links 0–17 `inactive` | 18 links at 26.562 GB/s |
| NVLink replay counter, GPU 2 | rising, ≈ 1/s | 0 |
| Clock-event reasons active | none | none |
| GPU temperature (max) | 71 °C | 70 °C |

1. Rank at least three hypotheses across compute, network (scale-up and scale-out), and orchestration.
2. Explain mechanistically why a problem on one GPU's links slows all eight GPUs of the replica, and
   why decode is especially sensitive to it.
3. Propose two discriminating tests, both safe on a production serving node, and the expected result
   of each under your top hypothesis.
4. Propose a safe remediation and a validation criterion.

**Evidence required:** ranked hypotheses with for/against evidence; mechanism paragraph; two tests
with expected outcomes; remediation with a measurable validation criterion; explicit statement of what
is proven versus correlated.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/TS-slow-replica-n29/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/report.md`: ranked hypotheses, mechanism, two safe tests, remediation and validation,
  proven versus correlated

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show
formula, substitution and result with units.
