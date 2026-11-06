# Chapter 6 hands-on lab: benchmark it properly

## 1. What you will do

You decide whether two small optimizer changes make a training step faster, on a real GPU, using the
chapter's protocol (Table 6.5). You first see three wrong ways to time a GEMM. Then you run four arms
(baseline, an A/A copy of the baseline, fused AdamW and `zero_grad(set_to_none=False)`) as fresh,
interleaved processes with clock telemetry, and decide each candidate with the pre-registered statistic,
A/A noise floor, exact permutation test and Table 6.6. You finish with an empirical roofline from a copy
and a GEMM sweep, stated at the clock the GEMM really ran at.

## 2. What is real here, and what is not

Real: every kernel, every CUDA-event timing and every clock and power sample. The statistics are the
chapter's, computed from the raw per-iteration times that the bundle keeps.

What one machine cannot show:

- **One GPU, one host, one driver.** A fleet comparison (Section 6.11's driver upgrade) needs several nodes
  and controlled software versions. Here the only variable is the code.
- **No clock locking.** The lab never touches GPU clocks or power limits; on a shared machine that is not
  yours to change. The protocol's other route applies instead: record clocks and limiters at 100 ms and apply the
  pre-registered exclusion rule. Laptop GPUs run under a power cap almost all the time, so `sw_power_cap`
  is routine. Thermal or hardware slowdown is not.
- **A shared, noisy laptop.** Other processes and the laptop's own power management add noise that a
  dedicated ORION node would not have. The A/A arm measures exactly that noise, which is the point.
- **The roofline is GEMM and copy only.** There are no DRAM counters (Nsight Compute) here, so the bytes
  in the sweep are compulsory bytes worked out from the shapes, not measured traffic. Section 6.3 explains why
  that over-counts for thin GEMMs that stay in L2.

The L2 extension in [`../l2/`](../l2/) adds FP32 and shape sweeps. The Level 1 lab ([`../README.md`](../README.md))
covers the planted traps the statistics are meant to catch.

## 3. Requirements

| Item | Value |
|---|---|
| GPU | Yes: an NVIDIA GPU with `nvidia-smi` and CUDA (uses under 1.5 GB of its memory) |
| Docker | No |
| Root | No |
| Disk | About 2 MB of results |
| RAM | About 2 GiB free |
| Time | Setup under a minute (once the shared venv exists); run about 6 minutes, plus any wait for the shared GPU lock |

## 4. Safety

The lab only runs benchmark processes on the GPU, under the shared GPU lock, and samples `nvidia-smi`. It
changes no clocks, power limits, persistence mode or application clocks, and no host settings.
`teardown.sh` stops any benchmark or sampler left running.

## 5. Setup

```bash
cd book/part-2-accelerated-compute/ch06-gpu-performance-engineering/lab/handson
bash setup.sh          # the shared PyTorch venv (scripts/handson/venv.sh), then prints the GPU's clocks
```

## 6. Steps

Run everything unattended with `bash run.sh my-run` (results in `results/my-run/`), or step by step as
below (`PY=~/.venvs/ai-infra-handson/bin/python`). Write your answers in `results/<run-id>/answers.md`.
Before step 3, write down the decision rule you will use. The lab's rule is fixed in the docstring of
`analyze.py`: 1 % practical threshold, per-arm clock rule, 95 % bootstrap band, exact permutation test.

### Step 1: four ways to time one GEMM

```bash
$PY naive.py | python3 -m json.tool
```

`naive.py` times a 4096³ BF16 GEMM four ways. A: a host timer with no synchronize. B: one cold
synchronized call. C: the mean of 20 calls including the first. D: CUDA events, warm-up dropped, median
of 50. It prints the TFLOP/s each method implies next to the BF16 dense peak at the maximum clock.

**Question 1.** Which methods give a physically impossible number, and how can you tell without a profiler?
What did method A actually time?

### Step 2: warm-up

The protocol (below) keeps every iteration, including the five warm-up iterations it discards. Look at
`runs.jsonl`: compare `ms[0]` with the median of `ms[5:]`.

**Question 2.** How much slower is the first iteration of a fresh process than its steady state? Do five
discarded iterations cover the transient? Check `ms[1]` to `ms[4]` too.

### Step 3: the protocol session

```bash
$PY protocol.py results/my-run --runs 8 --iters 50 --python $PY
```

32 runs (4 arms × 8), each a fresh `bench.py` process. The arms run round-robin with the start rotated each
round. `nvidia-smi` samples SM clock, memory clock, temperature, power and the clock-event reasons every
100 ms for the whole session (`telemetry.csv`). `schedule.txt` is the order, written before the first run.

**Question 3.** Why is the run, not the iteration, the unit of replication? What does interleaving protect
against that running all baseline runs first would not?

### Step 4: clocks and the A/A floor

```bash
$PY roofline.py > results/my-run/step6_roofline.json     # (run.sh does this as step 6)
python3 analyze.py results/my-run
```

`analyze.py` matches each run to its telemetry samples, applies the clock rule, and computes the A/A
comparison (base against aa). The noise floor is the largest of |A/A point| and |band bounds|.

**Question 4.** Were any runs excluded, and why? Which clock-event reasons were active, and which of them
does the protocol treat as routine? What is the noise floor, and what is the smallest change
(MDE) that 8 runs per arm could detect?

### Step 5: decisions

Read the decision table in `report.md`. Each candidate gets the same statistic: the difference in arm means
of run medians, as a percentage of the baseline. It also gets its bootstrap band, its exact permutation p
(and the smallest p that test can produce with these run counts), and a decision from Table 6.6.

**Question 5.** Which candidate is an improvement, and which is not demonstrated? What would three runs per
arm have let you conclude (the `three_runs` line), and why?

### Step 6: an empirical roofline

`roofline.py` measures the memory roof (a 256 MiB device-to-device copy, 8 times L2) and the compute
roof (square BF16 GEMMs). It then sustains the 8192³ GEMM for 4 s while sampling the SM clock, and
sweeps M = N = 4096 with K from 16 to 4096.

**Question 6.** What fraction of the DRAM spec does the copy reach? What fraction of the BF16 peak does
the GEMM reach at the maximum clock, and at the clock it actually sustained? Which number would you put
in a target, and why? At what K does the sweep cross the measured ridge point? Do any thin GEMMs appear to
beat the copy roof, and what does that say about counting bytes from shapes?

## 7. Check your results

```bash
python3 check.py results/<run-id>
```

`check.py` recomputes the run medians, the A/A point, every candidate's change and exact permutation p,
and every decision from the raw runs, without using `analyze.py` or `stats.py`. It also checks protocol
compliance and physical sense: separate, interleaved processes; at least 5 runs of 50 timed iterations
per arm; telemetry covering the session; the no-synchronize timer reading far too fast; the first
iteration slower than the steady state; no GEMM above its BF16 peak at its own clock; no copy above the
DRAM spec; thin GEMMs memory-bound and square ones compute-bound.

## 8. Reference results

Measured on the reference machine (WSL2 Ubuntu 24.04, i7-13700HX, RTX 4060 Laptop GPU, driver 592.82,
PyTorch 2.5.1 + CUDA 12.4); the full bundle is in
[`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/report.md).

| Step | Quantity | Measured |
|---|---|---|
| 1 | 4096³ BF16 GEMM, host timer without synchronize | 0.027 ms, "5,170 TFLOP/s" (impossible: it timed 20 launches) |
| 1 | One cold synchronized call | 141.1 ms, 1.0 TFLOP/s (cuBLAS initialisation) |
| 1 | Mean of 20 including the cold call | 12.04 ms, 11.4 TFLOP/s |
| 1 | CUDA events, warm-up dropped, median of 50 | **4.823 ms, 28.5 TFLOP/s** |
| 2 | First iteration ÷ steady median (median of 32 runs) | 7.07× (iteration 0 ≈ 296 ms, iteration 1 ≈ 118 ms, steady from iteration 4–5) |
| 3–4 | Mean of run medians: base / aa / fused / zero | 44.25 / 44.26 / 39.19 / 45.78 ms, 8 runs each, 0 excluded |
| 4 | Median SM clock per arm; max temperature | 2,426–2,464 MHz; 71–72 °C; `sw_power_cap` active in about 90 % of samples, no thermal or hardware slowdown |
| 4 | A/A (base vs aa) | +0.03 %, band [−0.18 %, +0.24 %], p = 0.81: **noise floor 0.24 %**; σ_run = 0.23 %, MDE ≈ 0.32 % at 8 runs |
| 5 | Fused AdamW vs base | **−11.43 %**, band [−11.63 %, −11.23 %], p = 0.0002 (the floor for 8 + 8): **improvement** |
| 5 | `zero_grad(set_to_none=False)` vs base | **+3.47 %**, band [+3.27 %, +3.66 %], p = 0.0002: **regression** |
| 5 | Fused vs base with the first 3 runs per arm only | −11.40 %, p = 0.100: the 3 + 3 floor, so never significant |
| 6 | Device-to-device copy, 256 MiB | **226 GB/s** (88 % of 256 GB/s) |
| 6 | 8192³ BF16 GEMM sustained for 4.1 s | **27.9 TFLOP/s at 2,295 MHz and 80 W**: 99 % of the 28.2 TFLOP/s peak at that clock, 73 % of the 38.2 TFLOP/s maximum-clock figure |
| 6 | Measured ridge point; K sweep | 125 FLOP/B; K ≤ 128 memory-bound, K ≥ 256 compute-bound at 27.3–28.5 TFLOP/s |
| 6 | Thin GEMMs (K = 16–64) by compulsory bytes | 240–252 GB/s, 106–111 % of the copy roof but under the 256 GB/s spec |

All `[MEASURED]`. The bundle is from one unattended `run.sh` on a laptop shared with other jobs. The GPU
lock kept other GPU work away, but not CPU work.

**Physical sense check against the published specs.** NVIDIA's RTX 4060 Laptop GPU is AD107 with 24 SMs,
8 GB of GDDR6 on a 128-bit bus at 16 Gbps (256 GB/s), 32 MB of L2, a boost clock of up to 2,370 MHz that
depends on the laptop's power setting (35–115 W), and 512 dense BF16 FLOP per SM per clock with FP32
accumulation (the GeForce Ada rate). Where the measurements differ, and why:

- **Copy: 226 of 256 GB/s (88 %).** This is normal for a copy kernel on GDDR6: refresh, read/write
  turnaround and row misses take about 10 %. The memory clock read 8,000 MHz in all but 19 of the 1,240 telemetry
  samples (6,000 MHz for a moment), so the spec is the right denominator.
- **GEMM: 27.9 TFLOP/s, against "38.2 TFLOP/s".** The 38.2 figure uses `clocks.max.sm` = 3,105 MHz, the
  highest clock the part can be programmed to. No real load holds that clock. This laptop's power limit
  is 80 W (`gpu_state_before.txt`), and under the GEMM the card drew 80 W and settled at 2,295 MHz, with
  `sw_power_cap` the active reason. At 2,295 MHz the peak is 24 × 512 × 2.295 GHz = 28.2 TFLOP/s, and the
  GEMM reaches 99 % of it. At NVIDIA's rated 2,370 MHz boost the peak would be 29.1 TFLOP/s. The gap to the
  maximum-clock figure is the power limit, not the kernel (Section 6.3).
- **Thin GEMMs above the copy roof.** Their inputs (≤ 0.5 MB) stay in L2 between iterations, and the
  33.5 MB output is about the size of L2, so some of the bytes counted from the shapes never reach DRAM.
  They stay under the 256 GB/s spec, and the lab treats the copy as the memory roof.
- **Training-step clocks (2,426–2,464 MHz) are higher than the GEMM's (2,295 MHz)** because the MLP step
  is not compute-dense all the time, so it draws less power. This is why the protocol compares clocks
  within an arm (Section 6.5, Pitfall).

Your numbers will differ. `check.py` tests physical sense, not equality.

## 9. Clean up

```bash
bash teardown.sh
```

## 10. Connect to the chapter

| Step | Chapter section |
|---|---|
| 1 | Section 6.6, Table 6.5 ("Timing method"); Chapter 4, Section 4.5 (asynchrony and the queue) |
| 2 | Section 6.6, Table 6.5 ("Warm-up") |
| 3 | Section 6.6 (repetitions, ordering, concurrency) and Section 6.8 (manifests) |
| 4 | Section 6.5 (clocks, power, `clocks_event_reasons`, the per-arm peer-clock pitfall), Section 6.7 (A/A noise floor, MDE) |
| 5 | Section 6.7 (one statistic, bootstrap band, exact permutation test), Table 6.6 |
| 6 | Section 6.3 ("Empirical ceilings", "State the clock behind every compute peak") |
