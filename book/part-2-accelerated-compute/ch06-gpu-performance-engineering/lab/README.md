# Lab 6 — Benchmark Harness, Statistical Decisions and the Roofline

*Chapter 6 · Progressive Lab 4 (GPU baseline), part 2 · Tier **L1** (laptop) with an **L2** extension*

## 1. Goal and the real-world task it mirrors

Three things a GPU performance engineer is asked to do every month:

1. **Build a baseline you can trust** — a harness that measures with warm-up, repetitions, raw samples
   and an environment manifest, so that next month's number can be compared with this month's.
2. **Decide whether a change is real** — two candidate kernels claim improvements over a baseline on an
   ORION GPU; the supplied result sets contain the traps that fool teams in practice. Decide, with a
   pre-registered protocol, whether each improvement is statistically *and* operationally meaningful.
3. **Place kernels on the roofline** — classify nine profiled kernels as compute- or memory-bound against
   the right ceiling, say how far each is from its roof, and catch the measurement that cannot be true.

## 2. Tier and realism boundary

- **L1 (required):** the analysis datasets are `[SIMULATED]` (seeded generator — instructor copy only — seed 6). The
  harness measures *your* CPU: its numbers are `[MEASURED]` for your machine only.
- **L2 (optional):** run the same protocol on a real GPU (Section 8).

> **Realism boundary:** Simulated data has no time-correlated drift, bimodal kernel selection or
> interference; real GPU data does. Laptop CPU results say nothing about ORION. Vendor peaks in
> `device.yaml` are upper bounds, not achievable ceilings.

## 3. Setup

```bash
cd book/part-2-accelerated-compute/ch06-gpu-performance-engineering/lab
python -m pip install -r ../../../../requirements.txt     # numpy, pandas, pyyaml
python check.py                                            # progress meter
```

| File | Content |
|---|---|
| `data/bench_baseline.csv`, `bench_candidate_b.csv`, `bench_candidate_c.csv` | One row per iteration: `run_id`, `iter`, `latency_ms`, `sm_clock_mhz`, `gpu_temp_c`, `power_w`, `clocks_event_reasons`, `driver`, `cuda`, `torch`, `kernel_variant` |
| `data/bench_aa.csv` | The baseline kernel measured as two groups of runs (`AA1-*`, `AA2-*`) for the noise floor |
| `data/kernels.csv` | `name`, `precision`, `flop`, `dram_bytes`, `time_us` |
| `data/device.yaml` | Dense peaks per precision, HBM bandwidth, nominal SM clock |
| `starter/harness.py`, `starter/analysis.py` | Modules you complete |

The decision protocol (fixed in advance — do not change it after seeing results) is in `manifest.yaml`
under `decision_protocol` and in manuscript Section 6.7. Reference software: driver 570.124.06,
CUDA 12.8, PyTorch 2.4.0.

## 4. Background you need

Manuscript Sections 6.2–6.3 (intensity, roofline, Table 6.1), 6.4 (MFU/HFU), 6.5 (clocks and
`clocks_event_reasons`), 6.6 (protocol), 6.7 (statistics and decision rule), 6.8 (harness), 6.9 (worked example).

## 5. Tasks

1. **Harness** — implement `environment_manifest`, `time_samples`, `summarize_ns`, `matmul_bench`,
   `copy_bench` and `run_independent` (each run in a fresh process) in `starter/harness.py`. Then run
   `python starter/harness.py --runs 5 --out results.json` (full sizes; ≈ 1 minute) and
   `--quick --runs 5`. *Acceptance:* harness checks pass; `results.json` contains raw samples, config and
   manifest for 5 runs.
2. **Your own noise** — from `results.json`, report for each benchmark the median of run medians, the
   spread of run medians (min–max), and the within-run IQR. How large is your laptop's run-to-run noise
   compared with the A/A floor in the supplied GPU data? Which manifest fields would you suspect first?
3. **Statistics** — `quantile`, `summarize`, `cliffs_delta`, `run_medians`, `bootstrap_ratio_ci`,
   `permutation_test`, `mde`. *Acceptance:* quantiles equal numpy's linear method; bootstrap reproduces the
   documented RNG recipe; the exact permutation test and MDE match the checker's hand cases.
4. **Cleaning and decisions** — `clean_runs`, `noise_floor`, `naive_compare`, `compare`. Apply to B and C.
   *Acceptance:* decisions as checked; for each excluded run, quote the rows that justify the exclusion.
5. **Roofline and MFU** — `ridge_point`, `attainable`, `classify_kernels`, `mfu`. *Acceptance:* all nine
   kernels classified; the anomaly explained; W-TRAIN MFU and HFU computed.
6. **Deliverable (`benchmark_report.md`, ≤ 3 pages):** the benchmark protocol you would use on an ORION GPU
   (all ten controls of Table 6.5); your harness results table (labelled `[MEASURED]` with your manifest);
   the B and C decision table (naive vs cleaned, CI, effect size, decision) with the evidence for every
   exclusion; the roofline table with one recommended action per kernel; and a one-paragraph
   *performance conclusion* a manager could act on, including what you would need to make it `[MEASURED]`
   on ORION.

## 6. Running the checker

```bash
python check.py                    # starter
python check.py --impl solution    # instructor reference (not in the student release)
python starter/analysis.py         # once implemented: prints decisions and the roofline table
```

The harness check runs a tiny live benchmark but asserts only structure, never timings.

## 7. Deliverable and grading rubric (100 points)

| Item | Points | Full marks when |
|---|---|---|
| Task 1 — harness | 15 | Checks pass; 5-run results with manifest submitted |
| Task 2 — own noise analysis | 10 | Run-level vs within-run variation separated; plausible causes named |
| Task 3 — statistics | 10 | Checks pass |
| Task 4 — cleaning and decisions | 20 | Checks pass; each exclusion justified by quoted rows; naive vs cleaned contrast explained |
| Task 5 — roofline and MFU | 15 | Checks pass; anomaly and FP32-ceiling cases explained |
| Task 6 — report | 30 | Complete protocol, labelled results tables, actionable conclusion, limitations |

## 8. Extension (L2): the same protocol on a real GPU

On a GPU you control (not a shared production node):

```bash
# 1. Telemetry for the whole session (field names are version-sensitive; current drivers use clocks_event_reasons)
nvidia-smi --query-gpu=timestamp,index,uuid,clocks.sm,clocks.mem,temperature.gpu,power.draw,power.limit,clocks_event_reasons.active \
           --format=csv -lms 100 -i 0 > telemetry.csv &
nvidia-smi -q -d PERFORMANCE,CLOCK,POWER -i 0 > gpu_state_before.txt
# 2. Optional, root, dedicated node only: lock clocks for code comparisons AT OR BELOW the sustained clock
#    (e.g. 1,755–1,830 MHz on ORION), confirm clocks_event_reasons stays none, restore afterwards
#    sudo nvidia-smi -lgc 1755,1755 -i 0   ...   sudo nvidia-smi -rgc -i 0
```

Adapt `harness.py` to time a GPU callable with CUDA events, for example:

```python
import torch
a = torch.randn(8192, 8192, device="cuda", dtype=torch.bfloat16); b = torch.randn_like(a)
start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
def gemm_ms():
    start.record(); torch.matmul(a, b); end.record(); end.synchronize()
    return start.elapsed_time(end)          # ms, measured on the GPU
# FLOP per call 2*8192**3; compare achieved TFLOP/s with the 989 TFLOP/s dense BF16 roof
```

Run ≥ 6 interleaved runs per arm (e.g. two matmul precisions, or `torch.backends.cuda.matmul.allow_tf32`
off/on for FP32), plus an A/A pair, write the data in the lab's CSV schema including clocks and
`clocks_event_reasons`, and apply your `compare()` unchanged. Record every `extensions.record` field from
`manifest.yaml`. Label results `[MEASURED]`.

## 9. Intentionally flawed inputs

The result sets contain several planted traps, and the kernel table contains at least two cases where a
naive reading gives the wrong answer. They are documented for instructors in
`../solutions/exercises-key.md` ("Lab 6 — planted anomalies").
