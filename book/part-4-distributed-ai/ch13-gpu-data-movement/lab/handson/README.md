# Chapter 13 hands-on lab: moving data to the GPU

## 1. What you will do

You measure the first hop of every training step, host memory to GPU memory, on a real GPU. You compare
pinned and pageable copies, overlap copies with compute on two CUDA streams and prove the overlap with
GPU timestamps, then tune a PyTorch `DataLoader` (`num_workers`, `pin_memory`, `prefetch_factor`) until
an input-bound training loop keeps the GPU busy.

## 2. What is real here, and what is not

Real: CUDA copies over this machine's PCIe link, CUDA streams and events, a PyTorch `DataLoader` with real
worker processes doing real CPU work, and a real (small) CNN training step. Every number is measured.

What one machine cannot show:

- **Only the host-to-GPU hop.** Chapter 13's main subjects, NVLink between GPUs, GPU-to-NIC paths,
  GPUDirect RDMA and stragglers across ranks, need several GPUs and RDMA NICs. This lab covers the hop
  that every one of those paths starts or ends with. The Level 1 lab ([`../README.md`](../README.md))
  covers the multi-rank diagnosis, and its L3 extension covers two drained nodes.
- **The overlap evidence is CUDA event timestamps, not a profiler trace.** On WSL2, CUPTI does not
  deliver GPU activity records, so `torch.profiler` returns no GPU rows (the run records how many it got).
  Events recorded on each stream before and after each operation give GPU-side start and end times, and
  the overlap is computed from those intervals. On native Linux, `nsys profile -t cuda` or
  `torch.profiler` shows the same overlap as stream rows.
- **The input pipeline is synthetic.** Samples are generated and transformed with NumPy (stand-ins for
  decode and augmentation), so the CPU cost is real but not that of JPEG decoding. The method of finding
  the knee carries over; the worker count does not.
- **The host is shared and is a laptop.** Other processes can steal CPU from the workers, so every
  configuration runs three times and the median is kept. The GPU (RTX 4060 Laptop, Gen4 x8, 15.75 GB/s
  per direction) is far smaller than an H100 on Gen5 x16: ratios carry over, absolute rates do not.

## 3. Requirements

| Item | Value |
|---|---|
| GPU | Yes: an NVIDIA GPU with CUDA (uses under 2 GB of its memory) |
| Docker | No |
| Root | No |
| Disk | Under 1 MB of results |
| RAM | About 3 GiB free (12 workers, pinned chunks of 64 MiB) |
| Time | About 3 minutes, plus any wait for the shared GPU lock |

## 4. Safety

The lab runs benchmarks only, under the shared GPU lock. It changes no host or GPU settings. DataLoader
workers exit with their loader; `teardown.sh` stops anything left behind.

## 5. Setup

```bash
cd book/part-4-distributed-ai/ch13-gpu-data-movement/lab/handson
bash setup.sh               # checks the GPU and creates the shared PyTorch venv if needed
```

## 6. Steps

Run everything unattended with `bash run.sh my-run` (results in `results/my-run/`), or step by step.
Write your answers in `results/<run-id>/answers.md`.

### Step 1: pinned versus pageable copies, and the cost of pinning

```bash
python copies.py
```

For 1, 8 and 64 MiB buffers: bandwidth from pageable and from pinned memory, how long the CPU is held by
a `non_blocking=True` copy from each, and what `pin_memory()` costs (first call and median of five).

**Question 1.** Which kind of copy actually returns to the CPU immediately, and what does that mean for a
training loop that issues the next kernel after the copy? Why is the first `pin_memory()` call far more
expensive than later ones of the same size, and what should a data pipeline do about it?

### Step 2: overlap copies with compute, and prove it

```bash
python overlap.py
```

Twelve 64 MiB chunks; the compute per chunk is calibrated to take about as long as its copy. Compare
`serial` (one stream), `overlap_pinned` (copy stream plus compute stream, double buffering) and
`overlap_pageable`. Look at `copy_intervals_ms` and `compute_intervals_ms` in the JSON: they are GPU
timestamps.

**Question 2.** How much of the copy time did the two-stream schedule hide, and how close is its wall time
to the ideal max(Σ copy, Σ compute)? Why does the same schedule hide nothing from pageable memory?

### Step 3: the DataLoader configuration that keeps the GPU busy

```bash
python loader.py
```

First it measures the ceiling (the training step on a batch already on the GPU) and the time one process
takes to build a batch, and estimates the workers needed: ⌈batch time ÷ step time⌉. Then it sweeps
`num_workers` 0 to 12, `pin_memory` off and on, and `prefetch_factor` 1 to 8.

**Question 3.** What is the cheapest configuration within 5 % of the best, and how does it compare with
the estimate? What does `pin_memory=True` change at the same worker count, and why? Does a larger
`prefetch_factor` help when the workers are the bottleneck? Compare nvidia-smi's `utilization.gpu` with the
event-based GPU busy fraction: which would you trust, and why can the CPU-side "data wait" be large even
when the GPU is busy?

## 7. Check your results

```bash
python3 check.py results/<run-id>
```

It checks completeness and mechanisms: a pinned `non_blocking` copy releases the CPU, the serial schedule
shows no overlap while the two-stream one hides at least half the copy time and never beats
max(copy, compute), and more workers raise the throughput of an input-bound loop without beating the
GPU-only ceiling.

## 8. Reference results

Measured on the reference machine (WSL2 Ubuntu 24.04, i7-13700HX with 24 logical CPUs, RTX 4060 Laptop
GPU); the full bundle is in [`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/report.md).

| Measurement | Result |
|---|---|
| H2D, 64 MiB, pageable / pinned | 9.79 / 12.85 GB/s |
| CPU held by a 64 MiB copy, pageable / pinned `non_blocking` | 6.76 / 0.024 ms |
| `pin_memory()` on 64 MiB, first call / steady state | 48.8 / 3.4 ms; pinning every batch drops the copy to 7.79 GB/s |
| 12 × 64 MiB copies with matched compute: serial / two streams, pinned | 118.1 / 67.2 ms (1.76×); 78 % of copy time hidden; ideal 62.7 ms |
| The same two-stream schedule with pageable memory | 128.6 ms, 0 % hidden |
| DataLoader ceiling (batch already on the GPU) | 3,586 samples/s |
| `workers 0` / `workers 4, pin` / `workers 8, pin` | 734 / 3,018 / 3,419 samples/s (GPU busy 29 / 83 / 94 %) |

Pinned memory is faster, and it also releases the CPU: a pageable copy holds the calling thread for the
whole transfer, because the driver first copies the data through a staging buffer. Pageable copies can't
overlap compute at all. The two-stream schedule then runs no faster than serial, which is why Section 13.6 pins
the buffers it overlaps. Pinning is not free, though: pinning each batch costs more than it
saves, so pin once and reuse the buffer. One process prepares a batch in 63 ms while the GPU needs 18 ms,
which predicts ⌈63 / 18⌉ = 4 workers. Four workers reach 84 % of the ceiling. Eight reach 95 %, because
workers do not overlap perfectly. More than eight adds nothing.

Your numbers will differ. `check.py` tests physical sense, not equality.

## Troubleshooting

- `ERROR: no NVIDIA GPU visible (nvidia-smi failed)` → this lab needs a GPU (there is no CPU path here; the L2 extension in `../README.md` has a CPU fallback). On WSL2, check `nvidia-smi` inside WSL.
- `ERROR: missing command: flock` → `sudo apt-get install util-linux`, then rerun `bash setup.sh`.
- `setup.sh` fails while creating the shared venv → it downloads PyTorch 2.5.1 + CUDA 12.4 (network needed); if `python3 -m venv` fails, `sudo apt-get install python3-venv`; after an interrupted install delete `~/.venvs/ai-infra-handson` and rerun.
- DataLoader workers die (`Bus error`, `DataLoader worker ... killed`) or pinning fails → free RAM (about 3 GiB is needed) and check the `/dev/shm` size that `setup.sh` prints; on WSL2, raise `memory=` in `.wslconfig`.
- The run sits silent → it is waiting for the shared GPU lock `/tmp/handson-gpu.lock` held by another lab; wait for it.

## 9. Clean up

```bash
bash teardown.sh
```

## 10. Connect to the chapter

| Step | Chapter section |
|---|---|
| 1 | Section 13.4 (the end-to-end path; host staging), Section 3.4 (pinned memory) |
| 2 | Section 13.6 (overlapping communication with computation: streams, events, the window) |
| 3 | Section 13.8 (the `utilization.gpu` trap; input-bound ranks), Section 13.5 (data-loader workers and locality) |
