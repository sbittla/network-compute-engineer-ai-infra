# Chapter 22 hands-on lab: find the bottleneck

## 1. What you will do

You run a small training job on your own GPU whose input batches come over a network from a data
server. Then you inject four bottlenecks one at a time: a dataloader stall, CPU contention from a noisy
neighbour, a hidden host synchronization, and network delay on the data path. For each one you collect
the evidence the chapter tells you to collect (the workload's own clock first, then the layer that
explains it), name the cause with rules written down before the runs, apply the fix, and prove the fix
with an interleaved A/B test and an exact permutation test.

## 2. What is real here, and what is not

Real: a PyTorch training loop (a 4-block MLP, bf16 autocast, fused AdamW) on a real GPU; DataLoader
worker processes fetching batches over HTTP from a server in another network namespace and decoding
them on real CPUs; a real competing process pinned with `taskset`; real CUDA synchronizations counted by
`torch.profiler` and flagged by `torch.cuda.set_sync_debug_mode`; real kernel run-queue delay from
`/proc/thread-self/schedstat`; real `tc netem` delay on a veth; real `nvidia-smi` GPU-Util. Every
number in the reference results is `[MEASURED]`.

Not real, or not ORION:

- **One GPU, no collectives.** The step equation (Section 22.1.2) here has `T_compute`,
  `T_data,exposed` and `T_host`. There is no `T_comm,exposed` and no `T_bubble`: no NCCL, no NVLink, no
  pipeline and no stragglers. The chapter's placement and rail questions (Sections 22.10 and 22.12) need
  two or more nodes.
- **Injected, known causes.** You know the answer before you start, and each scenario has one cause.
  Production regressions mix causes and need attribution across a population of jobs (Section 22.4);
  this lab tests the diagnostic loop and the A/B method, not attribution.
- **Sizes are calibrated to this machine.** `run.sh` measures the GPU-only step first and sizes the
  CPU decode work (about 2 × the GPU step on one CPU) and the netem delay (about 6 × the GPU step) from
  it, so each bottleneck is large enough to see on any GPU. The absolute times do not transfer.
- **The "network" is one veth pair.** Delay is added by netem on the data server's side. There is no
  congestion, loss, ECMP or storage tier behind it.

The L2 and L3 extensions in [../README.md](../README.md) validate the method on injected regressions
and on a real multi-node fabric (nccl-tests with aligned and cross-rail placement).

## 3. Requirements

| Item | Need |
|---|---|
| GPU | Yes: one NVIDIA GPU; the job (an MLP with 34 M parameters, batches of 4,096 × 1,024) needs under 2 GB of GPU memory |
| Docker | No |
| Root | Yes: network namespaces, the veth pair, `tc netem` |
| Kernel | veth (built in on WSL2) and the `netem` qdisc (`CONFIG_NET_SCH_NETEM`, module `sch_netem`). Stock Ubuntu and stock WSL2 kernels load it on demand; a custom kernel needs its modules installed or `NETEM=y`. `setup.sh` and `run.sh` both test it before measuring. |
| CPUs | At least 16 logical CPUs for the default CPU sets (`CH22_CPUS_A=8-11` for the job, `CH22_CPUS_B=12-15` for the fix); set both on smaller machines, as two disjoint sets of four |
| Software | The shared venv (`scripts/handson/venv.sh`: PyTorch 2.5.1 + CUDA 12.4, NumPy 2.1.3), iproute2, util-linux |
| Disk, RAM | under 1 MB of results; about 2 GB of RAM (the data server holds 1 MB, each loader worker a few hundred MB) |
| Time | setup under 1 min with the venv present; run about 10–15 min with 5 runs per arm |

## 4. Safety

- The lab creates two network namespaces, `ch22-train` and `ch22-data`, joined by the veth pair
  `ch22-t0`/`ch22-d0` (10.22.0.1/30 and 10.22.0.2/30), both ends created inside the namespaces. The data
  server listens only on 10.22.0.2 inside `ch22-data`. netem sits on `ch22-d0` inside that namespace.
  The lab never touches a host interface, route or firewall rule.
- The noisy neighbour is eight Python busy loops named `ch22-hog`, pinned to `CH22_CPUS_A`. `run.sh`
  starts it only for scenario 2 and only while it holds the GPU lock.
- `run.sh` holds the shared GPU lock (`/tmp/handson-gpu.lock`) for the whole measured part. No other
  lab's GPU job runs between its A/B arms, and it never changes GPU clocks or power limits.
- `teardown.sh` stops the hog, the trainer and the data server, deletes both namespaces (and with them
  the veth pair and the netem qdisc), removes `/tmp/ch22-*`, and verifies that nothing is left. `run.sh`
  calls it on exit, also after a failure.

## 5. Setup

```bash
cd book/part-5-production-operations/ch22-cross-layer-performance-engineering/lab/handson
sudo bash setup.sh          # venv check (torch sees the GPU), iproute2, taskset, ping; tests netem
sudo bash run.sh my-run     # the whole lab, unattended -> results/my-run/   (CH22_RUNS=5 runs per arm)
python3 check.py results/my-run
```

From the repository root on Windows: `python scripts/handson.py setup ch22`, `... run ch22 my-run`,
`... check ch22 my-run`.

To follow the steps by hand, bring the network up and keep it until you run `teardown.sh`:

```bash
sudo bash netlab.sh up                  # namespaces, veth, data server on 10.22.0.2:8222
sudo bash netlab.sh status              # addresses, qdisc, a ping, the server's health
sudo bash scenario.sh healthy fixed /tmp/h.json --profile     # one trainer run; one JSON line of evidence
python3 diagnose.py /tmp/x.json /tmp/h.json                   # the verdict for an evidence file x
```

`scenario.sh <scenario> <arm>` runs the trainer once in `ch22-train`, pinned with `taskset`, under the
GPU lock. The arm is `bad` (bottleneck present) or `fixed` (remedy applied). The trainer prints one JSON
line: step time (window / steps); the exposed data-wait share, the GPU's idle time between steps measured
with CUDA events; the share of the window the loop spent blocked in `next(iterator)`; per-batch fetch,
network wait, decode wall and CPU time, decode run-queue delay, the main thread's CPU and run-queue
shares, GPU-Util, the loader PIDs, and with `--profile` the synchronize calls per step.

## 6. Steps

Write your answers in `results/<run-id>/answers.md`.

### Step 1: calibrate and measure the healthy job

```bash
sudo ip netns exec ch22-train taskset -c 8-11 python trainer.py --no-data      # GPU-only step time
sudo bash scenario.sh healthy fixed /tmp/h.json --profile
```

`run.sh` measures the GPU-only step (one pinned batch reused), times the decode on one CPU, and sizes the
decode rounds to about 2 × the GPU step and the netem delay to about 6 × it (`calibration.json`). Then it
runs one profiled healthy run and five plain ones. Look for: a healthy step close to the GPU-only step, a
data-wait share near zero (four workers decode in parallel, so they keep up with about 2× headroom), and
zero synchronize calls inside the step. Raw output: `calibration*.json`, `evidence_healthy.json`,
`healthy_runs.jsonl`, `net_healthy_status.txt`.

The time blocked in `next(iterator)` is not the same thing as exposed data wait. The loop launches a
step's kernels and returns at once, so while it waits for the next batch the GPU is still running the
previous step. The healthy job can spend a third of its time blocked in `next()` with the GPU idle for
under 1 % of it. `trainer.py` therefore records both and the rules use the exposed one: the gap on the
GPU timeline between one step's last kernel and the next step's first (CUDA events).

**Question 1.** Write the healthy step in the terms of the step equation (Section 22.1.2). Which terms
exist on this machine, and which are zero by construction?

### Step 2: dataloader stall

```bash
sudo bash scenario.sh loader bad /tmp/l.json --profile      # num_workers=0: decode in the training process
python3 diagnose.py /tmp/l.json /tmp/h.json
```

Look for: the step grows to roughly fetch + decode + GPU step, run serially; the data-wait share jumps;
the loader PID equals the trainer's PID; GPU-Util falls. The fix restores `num_workers=4`. Raw output:
`evidence_loader.json`, `diagnosis_loader.json`, `ab_loader.jsonl`.

**Question 2.** GPU-Util and the data-wait share both moved. Which one is the workload's own clock, and
why does the chapter tell you to read it first (Section 22.2)?

### Step 3: CPU contention

```bash
sudo bash hog.sh start 8-11 8                     # eight busy loops on the job's CPUs
sudo bash scenario.sh cpu bad /tmp/c.json --profile
ps -eo pid,psr,pcpu,comm,args | grep -E 'ch22-hog|trainer'
sudo bash hog.sh stop
```

Look for: the same job, slower, with the data-wait share up again. What separates this from Step 2 is
the decode threads' run-queue delay, the time a runnable thread waited for a CPU. It is near zero when
healthy and a large share of decode time here. The `ps` snapshot shows the hog on the job's CPUs. The
fix re-pins the job to `CH22_CPUS_B`. Raw output: `evidence_cpu.json`, `cpu_ps_snapshot.txt`,
`ab_cpu.jsonl`.

**Question 3.** Steps 2 and 3 both show "the GPU waits for data". Name the measurement that
discriminates them (Section 22.3.3), and say what each hypothesis predicts for it.

### Step 4: a hidden host sync

```bash
sudo bash scenario.sh sync bad /tmp/s.json --profile --sync-debug
```

The injected "debug statistic" copies each block's output to the host with `.cpu()` and takes its
maximum with numpy, plus `loss.item()` every step. Look for: the data-wait share stays low (the pipeline
is fine), but `torch.profiler` counts synchronize calls inside every step and
`set_sync_debug_mode("warn")` prints a warning naming the line. Each copy makes the CPU wait for the GPU
to finish the block, and then the GPU sits idle while the CPU copies and summarizes 16 MB and only then
queues the next kernels.
Raw output: `evidence_sync.json`, `evidence_sync.stderr`, `ab_sync.jsonl`.

**Question 4.** Why would a CPU sampling profiler (`py-spy`, `perf`) alone mislead you here, and what
does the timeline show that it cannot (Table 22.1, `T_host`)?

### Step 5: network delay on the data fetch

```bash
sudo bash netlab.sh delay 30      # run.sh uses the calibrated delay
sudo bash netlab.sh status        # the ping now shows the delay
sudo bash scenario.sh network bad /tmp/n.json --profile
sudo bash netlab.sh nodelay
```

Look for: data-wait share up, decode run-queue delay normal, and each worker's network wait per batch
at least the added delay. The fix keeps four fetches in flight per worker, so the latency overlaps
instead of adding up: the bandwidth was never the problem, the round trips were. Raw output:
`evidence_network.json`, `net_delay_status_*.txt`, `ab_network.jsonl`.

`netlab.sh up` turns off `net.ipv4.tcp_slow_start_after_idle` in the data server's namespace. With it on,
a keep-alive connection that sits idle longer than its retransmission timeout restarts slow start from a
10-segment window, and the 64 KB reply then pays extra round trips of slow start. Prefetching makes
each connection idle longer between requests, so with the default the fix partly undoes itself: a
cross-layer interaction of exactly the kind this chapter is about. The data server also raises its
listen backlog from Python's default of 5, because the fixed arm opens 16 connections at once and the
extra SYNs would otherwise wait for the 1 s SYN retransmit. To see it, run
the fixed arm once with `sudo ip netns exec ch22-data sysctl -w net.ipv4.tcp_slow_start_after_idle=1`.

**Question 5.** The fix did not remove the delay. Use Little's law (requests in flight = throughput ×
latency) to explain why it works, and how many fetches in flight the calibrated delay needs.

### Step 6: validate every fix with an A/B test

For each scenario `run.sh` runs 5 bad and 5 fixed runs as separate processes, alternating the order
each round (bad-fixed, fixed-bad, ...). `abstats.py` compares the arm means of the run step times with
a 95 % bootstrap band and an exact two-sided permutation test (252 splits; the smallest possible p is
2/252 ≈ 0.008), the Chapter 6 method. The decision is "improvement" only if p < 0.05 and the change is at
least the 5 % practical threshold. Look for: every fix is an improvement, and the fixed arm is back near
the healthy step time. Raw output: `ab_*.jsonl`; summary in `report.md`.

**Question 6.** There is no A/A arm here, so the decision bar is the 5 % threshold alone. Using the
healthy runs' spread and the MDE formula of Section 22.6.1, is 5 runs per arm enough to detect a 5 %
change on your machine?

## 7. Check your results

```bash
python3 check.py results/<run-id>
```

It checks that the bundle is complete and that the environment names the GPU. The healthy job must not
wait for data (data-wait share under 15 %), must have no host sync (under one synchronize call per step),
and must run within 35 % of the GPU-only step. For each scenario, the injected bottleneck must slow the
job by at least 10 %, and the evidence must name exactly the injected cause. The A/B must have at least 5
interleaved runs per arm, and check.py recomputes its statistic and exact p from the raw runs. Each fix
must be an improvement beyond 5 % with p < 0.05 and bring the job back within 25 % of healthy. The layer
evidence must agree with the mechanism: the loader decoded in the training process, the decode threads
waited for a CPU, the hog is visible in `ps`, the syncs were counted and flagged, the ping shows the
netem delay, each fetch waited at least that delay, and the healthy veth's RTT is under 5 ms. It does not
compare your numbers with ours.

## 8. Reference results

Not yet recorded. The reference machine runs the custom WSL2 kernel of
[docs/HANDS_ON_LABS.md](../../../../../docs/HANDS_ON_LABS.md) section 6, and that kernel has no modules
installed: `sch_netem` is `=m` in its configuration and absent, so Step 5 cannot run (`run.sh` stops
before measuring). The reference run will be committed in `results/wsl2-rtx4060-laptop/` once the
reference kernel provides netem. Your numbers will differ with the GPU, the CPU and the kernel; the check
tests physical sense, not equality.

## 9. Clean up

```bash
sudo bash teardown.sh            # hog, trainer, data server, ch22-* namespaces, /tmp/ch22-*
ip netns list | grep ch22; pgrep -fa 'ch22-hog|dataserver.py'      # both should print nothing
```

## 10. Connect to the chapter

| Section | What this lab makes concrete |
|---|---|
| 22.1.2 The step-time equation | `T_compute`, `T_data,exposed` and `T_host` measured from the loop's own clock |
| 22.2 Evidence by layer | Workload clock first; GPU-Util and its pitfall; CPU run-queue delay; `tc` and ping on the data path; `torch.profiler` |
| 22.3 Hypotheses and discriminating tests | Rules written before the runs; run-queue delay separates a slow loader from a starved one; network wait separates the network |
| 22.6 Benchmark design | Interleaved A/B, separate processes, warm-up excluded, exact permutation test, practical threshold, MDE |
| 22.7 Evidence-based tuning | One knob per fix (`num_workers`, CPU affinity, removing a sync, fetches in flight), each with a predicted and a measured effect |
| 22.8 Anti-patterns | "GPU-Util says it is busy", a debug statistic left in the hot loop, tuning without an A/B |
