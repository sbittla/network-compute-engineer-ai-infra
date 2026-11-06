# Chapter 4 hands-on lab: profile a training step

## 1. What you will do

A small language-model training step on your GPU is slower than it should be, and nothing in the code
calls `synchronize()` except at the end of the step. You profile it with `torch.profiler` and Nsight
Systems and find two hidden host syncs in the loss function. You confirm them with PyTorch's sync debug
mode, remove them, and re-measure with separate, interleaved processes. Finally you try CUDA Graphs:
the old step cannot be captured, and the fixed step can, which turns hundreds of launches per step into one.

## 2. What is real here, and what is not

Real: the model, the kernels, the CUDA runtime calls, the Nsight Systems timeline and every timing. The
step is a 6-block, 384-wide language model of residual MLP blocks without attention (10.2 M parameters,
vocabulary 4096), in BF16 autocast with AdamW. Each step accumulates gradients over 4 micro-batches of
8 × 256 tokens with padding masks. At that size the GPU's work per step and the CPU's ~1,000 launches per
step take about the same time.

The two hidden syncs are Table 4.3 patterns, written the way they appear in real training code:

- `per_token[mask].mean()`: boolean indexing has a data-dependent output size, so the CPU must wait to
  learn it (`aten::nonzero`).
- `if not torch.isfinite(loss): raise ...`: a Python branch on a GPU value (`aten::is_nonzero`, a
  `.item()` in disguise).

The fix is `torch.where(mask, per_token, 0).sum() / mask.sum()` (static shapes) plus a NaN flag kept on
the GPU and read once per step, at the end, where the CPU waits for the GPU anyway.

What one machine cannot show, said plainly:

- **No GPU activity in `torch.profiler` on WSL2.** CUPTI delivers the CPU side (every runtime call and
  aten op), so call counts are exact, but the GPU rows are empty (`device_events` = 0 in the bundle).
  The GPU timeline comes from Nsight Systems, which records kernel and copy activity on WSL2.
- **No Nsight Compute.** Occupancy and per-kernel counters (Sections 4.7 and 4.10) need `ncu` with GPU
  performance-counter access. The Level 1 lab ([`../README.md`](../README.md)) covers them on a
  simulated capture.
- **A small model on a laptop GPU.** The step takes a few tens of milliseconds, so launch overhead is a
  larger share than on an H100 running a real model. The signatures (sync gaps, launch-bound combs, one
  graph launch) are the same; the size of the saving is not. On WSL2 each launch also costs more than on
  native Linux, because work is submitted through the GPU paravirtualization layer. That is why the timeline
  shows short `dependency` gaps: the kernel was already queued, but the GPU had not yet picked it up.
  Section 4.12's worked example and its L2 extension ([`../l2/`](../l2/)) cover a larger, multi-cause case.
- **One process, one GPU, a shared CPU.** There are no NCCL kernels and no data loader. Other jobs on the
  host can slow the CPU that issues the launches, so step 5 runs every variant in separate interleaved
  processes and tests the difference instead of trusting one run.

## 3. Requirements

| Item | Value |
|---|---|
| GPU | Yes: an NVIDIA GPU with CUDA (uses under 1 GB of its memory) |
| Docker | No |
| Root | Only for `setup.sh` to install Nsight Systems (or skip it with `CH04_NSYS=0`) |
| Disk | About 420 MB for the Nsight Systems package (once); about 3 MB of results |
| RAM | About 3 GiB free (`nsys export` of a capture) |
| Time | Setup 2–5 minutes; run about 5 minutes, plus any wait for the shared GPU lock |

## 4. Safety

The lab runs its own Python processes on the GPU under the shared GPU lock, plus `nvidia-smi` sampling and
`nsys profile` around its own process. It changes no clocks, power limits, persistence mode, interfaces
or host settings. Scratch files go to `/tmp/ch04-handson`, which `teardown.sh` deletes. Nsight Systems
stays installed; `CH04_PURGE_NSYS=1 sudo bash teardown.sh` removes it.

## 5. Setup

```bash
cd book/part-2-accelerated-compute/ch04-gpu-architecture-cuda-execution/lab/handson
sudo bash setup.sh             # shared PyTorch venv + Nsight Systems 2025.6.3 (pinned .deb from NVIDIA's CUDA repo)
CH04_NSYS=0 bash setup.sh      # or: venv only; the timeline steps are then skipped
```

## 6. Steps

Run everything unattended with `bash run.sh my-run` (results in `results/my-run/`), or step by step as
below (`PY=~/.venvs/ai-infra-handson/bin/python`). Write your answers in `results/<run-id>/answers.md`.

### Step 1: the symptom

```bash
python3 with_util.py util.csv -- $PY train_step.py --variant baseline --steps 150
```

The step timer closes every step with `torch.cuda.synchronize()`, so the window covers the GPU work
(the Section 4.10 pitfall). `with_util.py` samples nvidia-smi's GPU-Util, SM clock and power every 100 ms.

**Question 1.** What is the median step time, and what GPU-Util does nvidia-smi report while it runs?
Does a high GPU-Util tell you the GPU is doing useful work all the time (Section 4.9)?

### Step 2: torch.profiler, the CPU side

```bash
for v in baseline fixed graphed; do $PY train_step.py --variant $v --mode profile --trace trace_$v.json; done
```

Each run prints per-step counts inside the step body: kernel launches, synchronize calls,
`aten::_local_scalar_dense` (a scalar read by the CPU), `aten::nonzero` and `aten::is_nonzero`. The
end-of-step synchronize and NaN-flag read are counted separately (`end_of_step_*`). The key-averages table
goes to stderr. Open `trace_baseline.json` in `chrome://tracing` or Perfetto.

**Question 2.** How many synchronize calls does the baseline make per step that the fixed step does not?
Which aten ops trigger them? How many launches per step does each variant make?

### Step 3: the timeline in Nsight Systems

```bash
nsys profile -t cuda,nvtx,osrt -s none --cuda-graph-trace=node \
  --capture-range=cudaProfilerApi --capture-range-end=stop \
  -o step_baseline $PY train_step.py --variant baseline --mode nsys
nsys export --type sqlite -o step_baseline.sqlite step_baseline.nsys-rep
nsys stats --report cuda_api_sum,cuda_gpu_kern_sum step_baseline.sqlite
python3 gaps.py step_baseline.sqlite
```

The capture covers steps after warm-up (two by default, six in `run.sh`), each in an NVTX range
`train_step_N` that ends after the synchronize. `gaps.py` applies Section 4.11's rule to every idle gap of 10 µs or more. It finds the API
call that submitted the next GPU activity through its correlation ID, and labels the gap `host_sync`,
`launch_bound` or `dependency`.

**Question 3.** What fraction of the step window is the GPU busy? How many `host_sync` gaps are there per
step, how long are they in total, and which blocking call precedes each? What do the `launch_bound` gaps
look like (Table 4.6)?

### Step 4: which lines synchronize

```bash
$PY train_step.py --variant baseline --mode syncdebug
```

`torch.cuda.set_sync_debug_mode("warn")` prints a warning for every synchronizing operation, with the file
and line.

**Question 4.** Which two lines of `train_step.py` does it flag? Rewrite each so it does not synchronize
and keeps the same meaning, including the NaN guard. Compare your fix with `loss_fixed` and
`Trainer.end_of_step`.

### Step 5: the fix, re-measured

```bash
for r in 1 2 3 4 5 6 7; do for v in baseline fixed graphed; do $PY train_step.py --variant $v; done; done
```

`run.sh` runs the variants in separate processes, rotates the start each round, and records every run in
`step5_runs.jsonl`. `summarize.py` compares the arms with the exact permutation test on run medians,
Chapter 6's protocol in a light form. It also captures the fixed step in Nsight Systems so you can
compare the two timelines.

**Question 5.** By how much did removing the two syncs shorten the step, and is the difference larger than
the run-to-run spread (look at the exact permutation p and the spread of run medians)? In the fixed step's
timeline, what kind of gap is left, and what would remove it?

### Step 6: CUDA Graphs

```bash
$PY train_step.py --mode capture          # tries to capture the baseline step: it must fail
$PY train_step.py --variant graphed --mode profile
```

The graphed variant captures the whole fixed step (4 micro-batches of forward and backward, and AdamW
with `capturable=True`) once, then replays it: one `cudaGraphLaunch` per step. Nsight Systems needs
`--cuda-graph-trace=node` to show the kernels inside the graph.

Nothing runs during capture, so the baseline's host reads see a loss that was never computed. On the
reference machine CUDA did not reject the read. The NaN guard acted on the bogus value and raised, which
ended the capture (`step6_capture_baseline.json`). Do not rely on getting an error: whether a host read
during capture is rejected or returns garbage depends on the call and the capture mode. Either way, a step
that reads GPU values on the host cannot be captured correctly.

Step 6b repeats fixed against graphed with `--batch 4`, which halves the GPU work per launch while the
launch count stays the same. That makes the step launch-bound, the regime CUDA Graphs are for:

```bash
for r in 1 2 3 4; do for v in fixed graphed; do $PY train_step.py --variant $v --batch 4; done; done
```

**Question 6.** What stopped the baseline capture, and why can no step that reads a GPU value on the host be
captured? How many launches per step does the graphed variant make? Why does removing about 950 launches
save little at `--batch 8` and a lot at `--batch 4`? When else would CUDA Graphs not pay off (Section 4.5
production note)?

## 7. Check your results

```bash
python3 check.py results/<run-id>
```

`check.py` checks that the bundle is complete and physically sensible. The baseline must synchronize
inside the step and the fixed step must not. Sync debug mode must point at the boolean-mask line. The
fixed step must be faster, by an exact permutation test on the run medians (recomputed from the raw runs),
and the graphed step must not be slower than the fixed one. The baseline capture must fail, and the
graphed step must make about one launch per step. In the launch-bound regime (step 6b), the graph must
be faster in every run, by at least 1.15×. When Nsight Systems was installed, it also checks that the
baseline timeline has `host_sync` gaps that the fixed one lacks, that the GPU is busy a larger share of the
fixed step, and that every traced window covers at least 90 % of the timed median step.

## 8. Reference results

Measured on the reference machine (WSL2 Ubuntu 24.04, i7-13700HX, RTX 4060 Laptop GPU, driver 592.82,
PyTorch 2.5.1 + CUDA 12.4, Nsight Systems 2025.6.3); the full bundle is in
[`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/report.md).

| Step | Quantity | Baseline | Fixed | Graphed |
|---|---|---|---|---|
| 1 | Median step, 150 steps (tokens/s) | 39.80 ms (205,800) | | |
| 1 | nvidia-smi GPU-Util while running (median of 62 samples) | 87 % | | |
| 2 | Kernel launches per step | 1,010 | 956 | 3 (1 graph launch) |
| 2 | Synchronize calls per step inside the step body | **12** | **0** | 0 |
| 2 | `aten::nonzero` / `aten::is_nonzero` per step | 8 / 4 | 0 / 0 | 0 / 0 |
| 3, 5 | nsys: step window, GPU busy (median of 6 traced steps) | 63.4 ms, 54 % | 46.3 ms, 72 % | 34.6 ms, 96.5 % |
| 3, 5 | nsys: `host_sync` gaps per step (total) | 11 (0.90 ms) | 0 | 0 |
| 3, 5 | nsys: `launch_bound` gaps per step (total) | 353 (25.8 ms) | 178 (10.8 ms) | 2 (0.37 ms) |
| 4 | Sync debug warnings for one step | 12: lines 94 and 95 (`[mask]`, `isfinite`) 4 times each, plus the mask's backward in autograd | 0 | |
| 5 | Mean of 7 run medians | 40.52 ms | **36.97 ms (−8.7 %, p = 0.016)** | **34.57 ms (−6.5 % vs fixed, p = 0.0006, the floor)** |
| 6 | Capture the baseline step | fails: `FloatingPointError: non-finite loss` | | captures |
| 6b | `--batch 4` (launch-bound), mean of 4 run medians | | 35.5 ms (30.2–39.4) | **21.2 ms (−40 %, 1.67×, p = 0.029)** |

All `[MEASURED]`; p is the exact two-sided permutation test on run medians. For 7 + 7 runs the smallest
possible p is 0.0006, and for 4 + 4 it is 0.029. The bundle is from one unattended `run.sh` on a laptop
shared with other jobs. The GPU lock kept other GPU work away, but not CPU work. Single runs of 49 and
41 ms in step 5 are CPU contention, and the interleaved design spreads it across the variants.

What the numbers say:

- **The syncs cost more than their gaps.** The traced `host_sync` gaps add up to only 0.9 ms per step,
  yet removing the syncs saved 3.5 ms untraced. After each sync the GPU queue is empty and the CPU has to
  refill it one launch at a time. That cost shows up as extra `launch_bound` gaps (353 against 178), not as
  sync gaps. This is the Section 4.11 point that a gap's attribution and its cost are different questions.
- **Graphs pay off in proportion to how launch-bound the step is.** At batch 8 the fixed step is already
  close to GPU-bound, and the graph saves 6.5 %. At batch 4 the GPU work per launch halves, the CPU's ~950
  launches dominate, and the same graph saves 40 %.
- **Tracing changes the step.** Nsight Systems adds CPU time to every runtime call. The traced baseline
  window is 63 ms against 40 ms untraced. Use the timeline to find *causes*, and the untraced runs
  (step 5) to measure *savings*. Every traced window still covers ≥ 90 % of the untraced step, so the busy
  and gap figures are valid (the Section 4.10 check).

**Physical sense check against the published specs.** The RTX 4060 Laptop GPU (AD107) has 24 SMs, a boost
clock of up to 2,370 MHz depending on the laptop's power setting, and 512 dense BF16 FLOP per SM per clock
with FP32 accumulation, so about 29 TFLOP/s at the rated boost. The Chapter 6 hands-on lab measured
28 TFLOP/s sustained on this card. The model does 6 × 8.65 M (matmul parameters) × 8,192 tokens ≈ 425 GFLOP
per step. At 34.6 ms the graphed step therefore achieves about 12.3 TFLOP/s, roughly 44 % of the sustained
BF16 peak, with the GPU busy 96.5 % of the step. The rest is not lost to the host any more. It goes to small
GEMMs (M = 2,048, K = 384), the FP32 loss over a 4,096-word vocabulary, and unfused elementwise kernels,
which are kernel-level problems (fusion, `torch.compile`, Section 4.7) rather than launch problems. The
GPU-Util of 87 % is consistent with the timeline: 33.4 ms of GPU work in a 39.8 ms baseline step is 84 %
busy. It says nothing about how well the busy time is used (Section 4.9). The card ran at 2,250–2,535 MHz
and up to 73 W during step 1, under this laptop's 80 W limit.

Your numbers will differ. `check.py` tests physical sense, not equality.

## 9. Clean up

```bash
bash teardown.sh
```

## Troubleshooting

- **`ERROR: no NVIDIA GPU visible (nvidia-smi failed)`** → install the NVIDIA driver (on WSL2, the Windows
  driver). On WSL2 `nvidia-smi` lives in `/usr/lib/wsl/lib`; the scripts add it to `PATH`, so start them
  with `bash setup.sh` / `bash run.sh` rather than calling the Python files directly.
- **First `setup.sh` is slow or fails in `pip`** → it builds the shared venv `~/.venvs/ai-infra-handson` and
  downloads PyTorch 2.5.1+cu124, so it needs network access. If `python3 -m venv` fails, install
  `python3-venv` (`sudo apt-get install python3-venv`). After a broken install, delete the venv and re-run.
- **`setup.sh` fails with `CUDA not visible to PyTorch`** → the driver works but PyTorch cannot use it; check
  `nvidia-smi` and that the driver is version 550 or newer (the venv uses the CUDA 12.4 build).
- **`setup.sh` asks for root or `curl` fails** → installing Nsight Systems needs `sudo` and network access.
  Without it, run `CH04_NSYS=0 bash setup.sh`; `run.sh` then skips the timeline steps.
- **The run stops with no output before a GPU step** → it is waiting for the shared GPU lock
  `/tmp/handson-gpu.lock`, held by another hands-on run. Let that run finish; `pgrep -fa flock` shows it.
- **`check.py` prints its usage text and exits 2** → pass the run folder: `python3 check.py results/<run-id>`.

## 10. Connect to the chapter

| Step | Chapter section |
|---|---|
| 1 | Section 4.9 (what GPU utilization measures), Section 4.10 pitfall (step windows) |
| 2 | Section 4.10 ("PyTorch profiler"), Section 4.6 (Table 4.3, implicit synchronization) |
| 3 | Section 4.10 ("Nsight Systems: the timeline"), Section 4.11 (gap rule, Table 4.6) |
| 4 | Section 4.6 (`set_sync_debug_mode`) |
| 5 | Section 4.12 (fix, then validate with repeated runs); Chapter 6 protocol |
| 6 | Section 4.5 ("Reducing launch overhead", CUDA Graphs), Table 4.13 |
