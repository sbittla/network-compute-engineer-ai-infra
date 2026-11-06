# Hands-on Lab 11: Multi-process training on one machine

## 1. What you will do

You will run real data-parallel training jobs with `torchrun` and PyTorch DistributedDataParallel
(DDP): 1, 2, 4 and 8 processes on the CPU with the gloo backend, plus one process on the GPU as a
reference. You will measure step time, how much of it is gradient all-reduce, and scaling efficiency;
change the gradient bucket size and accumulate gradients with `no_sync()`; then kill one rank, hang
another, and recover from the last checkpoint with torchrun's elastic restart, measuring the work lost
against the checkpoint interval as Section 11.12 predicts. This is what a
training-infrastructure engineer does before trusting a launcher, a bucket setting or a checkpoint
policy on a real cluster.

## 2. What is real here, and what is not

**Real:** `torchrun`, its elastic agent and `--max-restarts`; DDP's bucketing, its iteration-1 bucket
rebuild, `no_sync()` and gloo's all-reduce; real process death (SIGKILL), a real hang and the real
process-group timeout; real checkpoints written with `fsync` and an atomic rename; real step times on
this machine's cores and on its GPU. Every number in the report is measured by the run.

**Not real:** the "network" is loopback TCP inside one kernel and the reduction runs on CPU cores that
also do the compute, so the all-reduce costs far more relative to compute than NCCL over NVLink or a
400 Gb/s rail would. One machine has no stragglers from other hosts, no NIC, no switch and no
multi-node rendezvous; when a rank dies here, the local torchrun agent sees the process exit within a
second, whereas across nodes the survivors may sit in a collective until the NCCL watchdog fires. The
model is a small MLP (9.4 M parameters), not a transformer, and there is no tensor or pipeline
parallelism (one GPU). What carries over to ORION: the *shape* of the results (communication grows
with ranks while the ring's bytes per rank approach 2× the gradient; accumulation divides the
all-reduce cost by the number of micro-batches; a hang costs the timeout; a restart loses exactly the
steps since the last checkpoint; the C/τ against τ/(2·MTBF) trade-off and Young/Daly). Absolute step
times, R and C do not carry over. The chapter's Level 3 extension (`../README.md`, section 8) covers
multi-node runs.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | Optional (Step 4 only; skipped with a note if absent) |
| Docker | No |
| Root | No |
| CPU | 8+ cores recommended (8 ranks × 1 thread) |
| RAM | ≈ 5 GB peak with 8 ranks (each rank ≈ 0.6 GB); fits in 7 GB |
| Disk | < 50 MB (checkpoints in `/tmp/ch11-handson-*`, removed at the end) |
| Time | ≈ 9–10 min for `run.sh`, plus any wait for the shared GPU lock (18 min in the reference run) |

Software: Python 3.12, the shared venv from `scripts/handson/venv.sh` (PyTorch 2.5.1 with CUDA 12.4,
`torchrun`, gloo and NCCL).

## 4. Safety

The lab starts only its own processes (`torchrun` and `ch11_ddp.py` workers) and writes only
`/tmp/ch11-handson-<pid>/` and `results/`. It kills only processes it started (a worker kills itself
with SIGKILL; torchrun stops its own workers). It does not touch network interfaces, GPU clocks or
system settings. The GPU step takes the shared lock `/tmp/handson-gpu.lock`. `teardown.sh` stops any
leftover `ch11_ddp.py` process and removes the scratch directory.

> **Safety:** on a real cluster, never kill ranks or hang collectives on a shared production job to
> "see what happens"; do it on a reserved allocation, as here.

## 5. Setup

```bash
cd book/part-4-distributed-ai/ch11-distributed-training-architecture/lab/handson
bash setup.sh          # creates/uses ~/.venvs/ai-infra-handson, prints torch, gloo, NCCL, CPUs, GPU
. ../../../../../scripts/handson/venv.sh
TR=$HANDSON_VENV/bin/torchrun
```

From the repo root on Windows: `python scripts/handson.py setup ch11`.

## 6. Steps

`bash run.sh <run-id>` runs every step unattended and writes `results/<run-id>/`. The commands below
are what it runs, so you can repeat any step by hand. Each worker appends JSON events to
`--event-log` (start, step with its duration and loss, checkpoint, done with peak memory, DDP's
buckets and a parameter checksum per replica) and fault events to `--fault-log`. Write your answers in
`results/<run-id>/answers.md`.

### Step 1: scaling across processes

```bash
for n in 1 2 4 8; do
  $TR --standalone --nproc-per-node=$n ch11_ddp.py --steps 25 --micro-batch 32 --event-log /tmp/w$n.jsonl
  $TR --standalone --nproc-per-node=$n ch11_ddp.py --steps 25 --micro-batch 32 --no-comm --event-log /tmp/c$n.jsonl
  $TR --standalone --nproc-per-node=$n ch11_ddp.py --steps 25 --micro-batch $((64 / n)) --event-log /tmp/s$n.jsonl
done
```

Weak scaling keeps 32 samples per rank; strong scaling keeps 64 samples per step. `--no-comm` runs the
same step under `no_sync()`, so it measures compute only; the difference is the *exposed* all-reduce
time. Each rank runs one thread, so up to 8 ranks get their own core. **Look for:** step time against
ranks, exposed communication against the ring's 2(n − 1)/n × 37.8 MB per rank, the peak memory of all
ranks, and identical parameter checksums on every replica. **Question 1:** By how much does the
exposed all-reduce time grow from 2 to 8 ranks, and how does that compare with the growth of the
ring's bytes per rank (0.5 → 0.875 of 2 × G)? What else grows with n here?

### Step 2: gradient bucket size

```bash
for b in 1 5 25 100; do
  $TR --standalone --nproc-per-node=4 ch11_ddp.py --steps 25 --bucket-cap-mb $b --event-log /tmp/b$b.jsonl
done
```

**Look for:** the bucket layout DDP built (`rebuilt_bucket_sizes` in the `done` event; a 4.2 MB weight
cannot be split, so a 1 MB cap gives one bucket per layer) and the step time. **Question 2:** Why does
one 37.8 MB bucket (cap 100) remove all overlap of communication with backward, and why do very small
buckets not win either? Which bucket setting was fastest here, and is the difference larger than the
run-to-run noise?

### Step 3: gradient accumulation with no_sync

```bash
for k in 1 2 4 8; do
  $TR --standalone --nproc-per-node=4 ch11_ddp.py --steps 15 --warmup 3 --accum $k --event-log /tmp/a$k.jsonl
done
```

**Look for:** step time, time per micro-batch, samples per second and the communication share of the
step. **Question 3:** Model step time as k × compute + one all-reduce. Does the measurement fit? What
does accumulation cost the training recipe in exchange (Section 11.3)?

### Step 4: the same job on the GPU

```bash
with_gpu_lock() { flock /tmp/handson-gpu.lock "$@"; }
with_gpu_lock $TR --standalone --nproc-per-node=1 ch11_ddp.py --device cuda --steps 40 --warmup 10 --event-log /tmp/g.jsonl
```

**Look for:** the GPU step time against one CPU rank. **Question 4:** Why can't this machine run
multi-rank DDP on the GPU with NCCL, and what would you need to measure the GPU all-reduce (Chapter 12)?

### Step 5: kill a rank, hang a rank, restart from checkpoint

```bash
# a rank dies (SIGKILL) before step 23, no restarts allowed: the job fails
$TR --standalone --nproc-per-node=4 --max-restarts=0 ch11_ddp.py --steps 40 --ckpt-dir /tmp/ch11-handson-x/k0 \
    --ckpt-every 10 --fault kill --fault-rank 2 --fault-steps 23 --event-log /tmp/k0.jsonl --fault-log /tmp/k0f.jsonl
# the same with one elastic restart: resumes from the step-20 checkpoint
$TR --standalone --nproc-per-node=4 --max-restarts=1 ch11_ddp.py ... --ckpt-dir /tmp/ch11-handson-x/k1 ...
# a rank hangs (stops calling collectives): the others wait for the process-group timeout
$TR --standalone --nproc-per-node=4 --max-restarts=1 ch11_ddp.py --steps 40 --ckpt-dir /tmp/ch11-handson-x/h10 \
    --ckpt-every 10 --fault hang --fault-rank 2 --fault-steps 23 --pg-timeout 10 ...
```

`--pg-timeout` sets `init_process_group(timeout=...)`. The fault fires once; a marker file in the
checkpoint directory stops it from firing again after the restart. **Look for:** the exit code and
torchrun's `ChildFailedError` summary, how fast the survivors learn of the death (a gloo
`Connection closed by peer` error or torchrun's SIGTERM), the `Timed out waiting 10000ms` error after a
hang, the restart time R, the lost steps, and whether the resumed run's loss equals the uninterrupted
run's loss at step 40. **Question 5:** Why is a hang so much more expensive to detect than a crash, and
what does that imply for the timeout you set on a 4,096-GPU job (Section 11.11)? Which evidence would you
collect before restarting?

### Step 6: lost work against checkpoint interval

```bash
for K in 2 4 8 16 32; do
  $TR --standalone --nproc-per-node=4 --max-restarts=6 ch11_ddp.py --steps 192 --ckpt-dir /tmp/ch11-handson-x/K$K \
      --ckpt-every $K --fault kill --fault-rank 2 --fault-steps 50,117,121,132,145,152 ...
done
```

The same six kills hit every interval (the steps are drawn once with a fixed seed), and a run with no
checkpoints and no faults gives the useful step time and the reference loss. **Look for:** lost steps
per kill against (s − 1) mod K, their mean against τ/2, checkpoint overhead C/τ against lost work
(τ/2)/MTBF, the K where their sum is lowest against Young/Daly τ_opt = √(2·C·MTBF), and R.
**Question 6:** Where is the measured minimum, and does it agree with τ_opt? On this machine R is
several seconds and MTBF a few seconds; what does that do to total waste, and which term would you
engineer first (Section 11.12, asynchronous checkpointing)?

## 7. Check your results

```bash
python check.py results/<run-id>
```

It tests physical sense (communication costs time, accumulation amortizes it, bucket counts follow the
cap, a killed job fails without restarts, a hang is detected after the timeout, lost work equals the
steps since the last checkpoint, every resumed run reaches the uninterrupted loss), not the reference
numbers. From the repo root: `python scripts/handson.py check ch11 <run-id>`.

## 8. Reference results

Measured on the reference machine (WSL2 Ubuntu 24.04, i7-13700HX with 24 logical CPUs, 7.8 GiB for
WSL, RTX 4060 Laptop GPU, PyTorch 2.5.1, NCCL 2.21.5). The full bundle is in
[`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/report.md). Other labs were running on the
same host (load average 7.5 at the end), so treat differences under about 10 % as noise. All numbers
are `[MEASURED]` unless marked `[MODELED]`.

**Step 1: scaling.** The model has 9,446,400 parameters, so each step all-reduces 37.8 MB of FP32
gradients.

| Ranks | Weak step (s) | Compute only (s) | Exposed all-reduce (s) | Weak efficiency | Samples/s | Strong efficiency | Implied busbw (GB/s) |
|---|---|---|---|---|---|---|---|
| 1 | 0.062 | 0.045 | 0.017 | 1.00 | 517 | 1.00 | n/a |
| 2 | 0.066 | 0.041 | 0.025 | 0.94 | 967 | 0.58 | 1.50 |
| 4 | 0.105 | 0.052 | 0.053 | 0.59 | 1,218 | 0.20 | 1.07 |
| 8 | 0.190 | 0.090 | 0.100 | 0.33 | 1,348 | 0.05 | 0.66 |

From 2 to 8 ranks the exposed all-reduce grows 4.0× (25 → 100 ms), while the ring's bytes per rank
grow only 1.75× (0.5 → 0.875 of 2 × 37.8 MB `[MODELED]`). Two other costs grow with n here. The ring's
latency steps rise from 2 to 14, and on loopback each step is a TCP round trip through the kernel. All
the ranks also share one memory system and one set of cores for both the reduction and the compute,
which is why the compute-only step itself grows 2.2× (41 → 90 ms) even though each rank has its own
core. The one-rank job still exposes 17 ms: DDP copies gradients into its buckets even when there is
no one to talk to. The implied busbw of 0.66–1.5 GB/s is memory copies through a TCP stack, about
1–3 % of one 400 Gb/s rail. Strong scaling collapses (0.05 at 8 ranks) because 8 samples per rank
leave almost nothing to compute while the all-reduce stays at full size. Every replica ended with the
same parameter checksum, and 8 ranks peaked at 5.19 GiB of RSS in total.

**Step 2: buckets (4 ranks).** DDP built 9, 5, 2 and 1 buckets for caps of 1, 5, 25 and 100 MB (a
4.2 MB layer cannot be split, so a 1 MB cap gives one bucket per layer). Step times were 0.108, 0.102,
0.099 and 0.137 s; the default (3 buckets: a small first bucket, then 29.4 and 4.2 MB) took 0.105 s.
Only the single 37.8 MB bucket is clearly worse, 38 % slower than the 25 MB cap: nothing can be sent
until backward has finished, so none of the all-reduce overlaps compute. The 1–25 MB settings lie
within 9 % of each other, which is about the noise (the same default configuration took 0.105 s in
Step 1 and 0.110 s in Step 3). Small buckets pay one α per bucket, so they do not win either.

**Step 3: accumulation with `no_sync` (4 ranks).** With k micro-batches per all-reduce, throughput was
1,164, 1,686, 2,095 and 1,863 samples/s for k = 1, 2, 4 and 8, a 1.80× gain at k = 4. The model
"k × compute + one all-reduce" fits up to k = 4: step minus k × 52 ms leaves 58, 48 and 36 ms of
communication, about one all-reduce each time. At k = 8 the first eight steps took 0.42–0.46 s, as
the model predicts (8 × 0.052 + 0.05 ≈ 0.47 s), but from step 10 they rose to 0.67–0.76 s while
another job loaded the host. The median (0.550 s) includes that, so k = 8 shows less gain than k = 4;
`raw/accum_8.jsonl` shows the jump. In exchange, accumulation makes the global batch k times larger
for the same number of all-reduces, which changes the learning-rate recipe (Section 11.3).

**Step 4: GPU.** One rank on the GPU took 8.0 ms per step against 61.9 ms for one CPU rank (7.7×), with
169 MiB of peak CUDA memory. A one-rank NCCL group moves no gradient bytes; NCCL needs one GPU per rank,
so multi-rank GPU DDP needs a second GPU.

**Step 5: faults (4 ranks, checkpoint every 10 steps, fault on rank 2 at step 23).**

| Run | Exit | Survivors learn of it after | How | Lost steps | Restart R | Loss at step 40 = uninterrupted |
|---|---|---|---|---|---|---|
| kill, `--max-restarts=0` | 1 | 0.06 s | gloo `Connection reset by peer` | (job failed) | n/a | n/a |
| kill, `--max-restarts=1` | 0 | 0.05 s | gloo `Connection reset by peer` | 2 | 3.2 s | yes, bit-exact |
| hang, timeout 10 s | 0 | 10.04 s | gloo `Timed out waiting 10000ms` | 2 | 13.6 s | yes, bit-exact |
| hang, timeout 20 s | 0 | 20.02 s | timeout | 2 | 23.9 s | yes, bit-exact |

A crash is visible in 50 ms because the kernel closes the dead process's sockets. A hang closes
nothing, so the survivors wait for the whole process-group timeout, and the restart then costs the
timeout plus about the same 3–4 s that a crash costs. On a 4,096-GPU job that timeout has to be longer
than the slowest legitimate collective, so a hang costs minutes, not milliseconds (Section 11.11).
Every restart lost exactly 2 steps: the fault fired before step 23, the last checkpoint was step 20,
and steps 21–22 were run again.

**Step 6: checkpoint interval (4 ranks, 192 steps, kills at steps 50, 117, 121, 132, 145 and 152).**
The step time is 0.118 s, the median checkpoint cost C = 0.084 s (write, `fsync`, rename and barrier),
and the productive MTBF is 3.76 s (192 steps ÷ 6 kills).

| K (steps) | τ (s) | Lost steps per kill | Checkpoint overhead (C/τ `[MODELED]`) | Lost work ((τ/2)/MTBF `[MODELED]`) | Sum, measured (model) | R median (s) |
|---|---|---|---|---|---|---|
| 2 | 0.24 | 1, 0, 0, 1, 0, 1 | 31.3 % (30.2 %) | 1.6 % (3.1 %) | 32.9 % (33.4 %) | 2.82 |
| 4 | 0.47 | 1, 0, 0, 3, 0, 3 | 16.9 % (16.9 %) | 3.6 % (6.2 %) | 20.5 % (23.2 %) | 2.72 |
| 8 | 0.94 | 1, 4, 0, 3, 0, 7 | 8.9 % (8.9 %) | 7.8 % (12.5 %) | 16.7 % (21.4 %) | 2.75 |
| 16 | 1.88 | 1, 4, 8, 3, 0, 7 | 4.8 % (4.7 %) | 12.0 % (25.0 %) | 16.7 % (29.7 %) | 2.62 |
| 32 | 3.76 | 17, 20, 24, 3, 16, 23 | 2.7 % (2.6 %) | 53.6 % (50.0 %) | 56.3 % (52.6 %) | 2.56 |

Every lost-step count equals (s − 1) mod K exactly: a restart loses precisely the work since the last
checkpoint. The checkpoint overhead matches C/τ to within a point. Lost work is below the τ/2 model
for K = 4 to 16 because six kills is a small sample and several landed just after a checkpoint (a kill
at a step that is 1 mod K loses nothing). Young/Daly gives τ_opt = √(2·C·MTBF) = 0.79 s = 6.8 steps
`[MODELED]`; the measured minimum is at K = 8 and 16 (16.7 % each), and the model's at K = 8, the
tested interval nearest 6.8. Every run finished at the uninterrupted run's loss: four bit-exact, and
K = 8 differed by 1.5 × 10⁻⁷ relative. CPU float sums are not guaranteed bit-identical across a
restart, so `check.py` allows 10⁻⁵.

The term that dominates here does not depend on τ at all. Six restarts at R ≈ 2.7 s cost 15–17 s
against 22.6 s of useful compute: R/MTBF ≈ 0.7, against at most 0.17 for checkpoints plus lost work at
the best K. On this machine R is process start, gloo rendezvous and a checkpoint load. Engineer the
restart first (warm spares, faster rendezvous, in-memory or asynchronous checkpoints; Section 11.12),
then the interval.

Your numbers will differ. `check.py` tests physical sense, not equality.

## Troubleshooting

- `ERROR: missing command: flock` (or `timeout`) → install util-linux and coreutils (`sudo apt-get install util-linux coreutils`), then rerun `bash setup.sh`.
- `setup.sh` fails while creating the venv or installing PyTorch → it needs network access to PyPI and download.pytorch.org (PyTorch 2.5.1 + CUDA 12.4, a few GB); if `python3 -m venv` fails, `sudo apt-get install python3-venv`. After an interrupted install, delete `~/.venvs/ai-infra-handson` and rerun.
- The run sits silent before the GPU step → it is waiting for the shared GPU lock `/tmp/handson-gpu.lock`, held by another hands-on lab (`ps aux | grep -e run.sh -e vllm`). Wait for that run to finish; do not delete the lock.
- `no GPU: step 4 will be skipped` → expected without a GPU; on WSL2, check that `nvidia-smi` works inside WSL (the driver is installed on Windows, not in Linux).
- One case failed or looks wrong → read `results/<run-id>/raw/<case>.log`; each launch is killed after 900 s. The `fault_kill_norestart` case fails on purpose. With fewer than 8 cores the 8-rank cases are slow and noisy: close other workloads and rerun.
- Leftover `ch11_ddp.py` processes or a scratch directory after Ctrl-C → `bash teardown.sh`.

## 9. Clean up

```bash
bash teardown.sh       # stops any ch11_ddp.py process, removes /tmp/ch11-handson-*
```

`run.sh` calls it on exit, even after a failure.

## 10. Connect to the chapter

- Section 11.1 (anatomy of a step) and 11.3 (data parallelism, buckets, `no_sync`): Steps 1–3.
- Section 11.9 (weak and strong scaling): Step 1.
- Sections 11.11 (hangs, rank loss) and 11.12 (Young/Daly, restart time R, the failure-aware workflow): Steps 5–6.
- Chapter 12 measures the collective itself; Chapter 14 the checkpoint storage.
