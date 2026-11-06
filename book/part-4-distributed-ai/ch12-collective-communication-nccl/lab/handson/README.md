# Hands-on Lab 12: Collectives you can measure

## 1. What you will do

You will time real `torch.distributed` collectives (all-reduce, all-gather, reduce-scatter and
broadcast) across 2, 4 and 8 processes on one machine, from 4 B to 64 MiB, and report them the way
nccl-tests does: time, algbw and busbw. You will fit the chapter's alpha-beta model to every sweep, read
off α, B and n½, repeat launches to see the spread, and race a hand-written ring all-reduce against a
binomial tree to find where one overtakes the other. Last, you will put NCCL on the one GPU. This is
what a collective-communication engineer does before trusting a benchmark or a bucket size: sweep
sizes, fit the model, and say which region the workload lives in.

## 2. What is real here, and what is not

**Real:** `torchrun`, the gloo backend and its TCP transport, the library collectives that PyTorch
DDP and FSDP call, real `send`/`recv` for the hand-written algorithms, result validation on every size
(nccl-tests' `#wrong`), and NCCL's communicator setup and kernels on a real GPU. Every number in the
report is measured by the run; α, B and n½ are fits to those measurements.

**Not real:** the "network" is loopback TCP inside one kernel, and the reduction runs on CPU cores
that also run the sender and receiver threads. So α is tens to hundreds of microseconds, not the 5–30 µs
of NCCL over NVLink or a 400 Gb/s rail, and B is a few GB/s of memory copies through the kernel's TCP
stack, not a link. There is no switch, no congestion from other jobs, no NIC and no rail. NCCL cannot
run more than one rank on one GPU, so the GPU step shows NCCL's refusal and its one-rank per-call
floor, not a GPU all-reduce. What carries over to ORION is the *method* and the *shapes*: a
latency-flat region and a bandwidth region, n½ = α·B/factor, busbw that should not depend on n while
algbw falls, α that grows with n, all-reduce = reduce-scatter + all-gather, and a tree that wins small
messages while a ring wins large ones. The chapter's L2/L3 extensions (`../README.md`, section 8) give
the nccl-tests commands for real GPUs and fabrics.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | Optional (Step 4 only; skipped with a note if absent) |
| Docker | No |
| Root | No |
| CPU | 8+ cores recommended (8 ranks, 1 compute thread each, plus gloo's I/O threads) |
| RAM | ≈ 4 GB peak with 8 ranks and 64 MiB buffers; fits in 7 GB |
| Disk | < 5 MB of results |
| Time | ≈ 3–4 min for `run.sh`, plus any wait for the shared GPU lock (5 min in the reference run) |

Software: Python 3.12, the shared venv from `scripts/handson/venv.sh` (PyTorch 2.5.1 with CUDA 12.4,
`torchrun`, gloo and NCCL).

## 4. Safety

The lab starts only its own processes (`torchrun` and `ch12_collectives.py` workers), listens only on
loopback ports that `torchrun --standalone` picks, and writes only `results/`. It does not touch
network interfaces, GPU clocks or system settings. The GPU step takes the shared lock
`/tmp/handson-gpu.lock`. `teardown.sh` stops any leftover `ch12_collectives.py` process.

## 5. Setup

```bash
cd book/part-4-distributed-ai/ch12-collective-communication-nccl/lab/handson
bash setup.sh          # creates/uses ~/.venvs/ai-infra-handson, prints torch, gloo, NCCL, CPUs, GPU
. ../../../../../scripts/handson/venv.sh
TR=$HANDSON_VENV/bin/torchrun
```

From the repo root on Windows: `python scripts/handson.py setup ch12`.

## 6. Steps

`bash run.sh <run-id>` runs every step unattended and writes `results/<run-id>/`. The commands below are
what it runs, so you can repeat any step by hand. The worker follows the nccl-tests size convention (S is
the whole vector: each rank's buffer for all-reduce and broadcast, the gathered output for all-gather,
the input for reduce-scatter), times back-to-back calls for about 0.2 s per size, takes the slowest
rank's mean, then validates the result once on known data. Rank 0 prints an nccl-tests-like table and
appends one JSON line per (op, size) to `--out`. Write your answers in `results/<run-id>/answers.md`.

### Step 1: sweep the collectives at 2, 4 and 8 ranks

```bash
$TR --standalone --nproc-per-node=2 ch12_collectives.py --ops all_reduce,all_gather,reduce_scatter,broadcast,pingpong --out /tmp/n2.jsonl
$TR --standalone --nproc-per-node=4 ch12_collectives.py --out /tmp/n4.jsonl
$TR --standalone --nproc-per-node=8 ch12_collectives.py --out /tmp/n8.jsonl
python analyze.py results/<run-id>     # run.sh does this: fits and tables in report.md
```

Sizes double from 4 B to 64 MiB. `analyze.py` fits T(S) = α + factor·S/B to each sweep by least squares
weighted by 1/T (Section 12.5), and computes n½ = α·B/factor. The fit and the latency floor start at 8n B:
gloo's ring splits the vector into 2n chunks and skips empty ones, so calls with fewer than 2n elements
are faster than the true floor. **Look for:** a flat region at small sizes
and time that doubles with size at the top; busbw/algbw equal to 2(n − 1)/n, (n − 1)/n or 1; the busbw
plateau against n (ideally flat) and the algbw plateau (falls with n); α against the ring's 2(n − 1)
latency steps; and the all-reduce = reduce-scatter + all-gather table. **Question 1:** What are α and n½
for the 4-rank all-reduce, and at what fraction of plateau bandwidth would a 25 MiB DDP bucket run here?
Compare with the chapter's 82 % on 16 ORION ranks: which of α or B is so different on loopback, and why?

### Step 2: repeat launches

```bash
for i in 2 3; do $TR --standalone --nproc-per-node=4 ch12_collectives.py --ops all_reduce --out /tmp/n4_rep$i.jsonl; done
```

**Look for:** the plateau busbw of the three 4-rank launches and the per-size coefficient of variation
(CV). **Question 2:** Is a 10 % difference between two configurations on this machine a real
difference? What would Section 12.10 make you report alongside the median?

### Step 3: ring against tree, built from send and recv

```bash
$TR --standalone --nproc-per-node=4 ch12_collectives.py --ops all_reduce,ring_allreduce,tree_allreduce --step-factor 4 --out /tmp/a4.jsonl
$TR --standalone --nproc-per-node=8 ch12_collectives.py --ops all_reduce,ring_allreduce,tree_allreduce --step-factor 4 --out /tmp/a8.jsonl
```

gloo does not let you choose its all-reduce algorithm, so the worker builds two: `ring_allreduce`
(n − 1 reduce-scatter steps and n − 1 all-gather steps, each moving S/n) and `tree_allreduce` (a
binomial-tree reduce to rank 0 and a broadcast back, 2·log₂n steps each moving all of S). The 2-rank
`pingpong` from Step 1 gives the point-to-point α and B, and `analyze.py` predicts both algorithms
with Table 12.3's formulas: ring 2(n − 1)(α + S/(nB)), tree 2·log₂n·(α + S/B). **Look for:** the size
where the ring starts winning, against the model's crossover α·B·(2(n − 1) − 2log₂n)/(2log₂n − 2(n − 1)/n),
and how close gloo's own all-reduce is to the faster of the two. **Question 3:** Why does the tree win
at small sizes and lose at large ones, and why does the crossover move with n? Why is this simple tree
worse at large sizes than NCCL's double binary tree (Section 12.3)?

### Step 4: NCCL on the one GPU

```bash
with_gpu_lock() { flock /tmp/handson-gpu.lock "$@"; }
NCCL_DEBUG=WARN with_gpu_lock $TR --standalone --nproc-per-node=2 ch12_collectives.py --device cuda --same-gpu --ops all_reduce --max-bytes 1024
NCCL_DEBUG=INFO with_gpu_lock $TR --standalone --nproc-per-node=1 ch12_collectives.py --device cuda --out /tmp/nccl1.jsonl
```

The first command puts two ranks on GPU 0 on purpose; NCCL refuses with `Duplicate GPU detected`. The
second runs every collective on a one-rank communicator: no bytes cross any link, so it measures the
per-call floor (launch, NCCL's kernel and a local copy). **Look for:** the NCCL version and the
refusal line in the logs, and the one-rank all-reduce floor against gloo's 2-rank floor. **Question 4:**
Why is busbw 0 for every one-rank collective, and what would you need to measure a real GPU all-reduce
(Section 12.5, and `../README.md` section 8)?

Optional: if the CUDA toolkit (`nvcc`) is installed, build nccl-tests (`make` in a clone of
`NVIDIA/nccl-tests`) and run `./build/all_reduce_perf -b 8 -e 64M -f 2 -g 1`. With one GPU it shows the
same floor in nccl-tests' own format. `run.sh` records whether `nvcc` was found.

## 7. Check your results

```bash
python check.py results/<run-id>
```

It recomputes algbw and busbw from the raw sweeps and tests physical sense: every result is correct,
small messages sit in a flat latency region and 64 MiB takes far longer, every fit gives α > 0, B > 0
and a sensible n½, all-reduce latency grows and algbw falls from 2 to 8 ranks, repeated launches agree
within the stated spread, the tree wins the smallest message and the ring the largest, and NCCL
refuses two ranks on one GPU. It does not compare your numbers with the reference machine's. From the
repo root: `python scripts/handson.py check ch12 <run-id>`.

## 8. Reference results

Measured on the reference machine (WSL2 Ubuntu 24.04, i7-13700HX with 24 logical CPUs, 7.8 GiB for
WSL, RTX 4060 Laptop GPU, PyTorch 2.5.1, NCCL 2.21.5). The full bundle is in
[`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/report.md). Other labs were running on the
same host (load average 3–5), which shows up as spread in Step 2. All numbers are `[MEASURED]` unless
marked `[MODELED]`; GB = 10⁹ B.

**Step 1: sweeps and fits (gloo, loopback).**

| Op | Ranks | Floor, 8n B–4 KiB (µs) | α fit (µs) | B fit (GB/s) | n½ | Plateau algbw (GB/s) | Plateau busbw (GB/s) |
|---|---|---|---|---|---|---|---|
| all_reduce | 2 | 384 | 390 | 2.62 | 1.0 MiB | 2.35 | 2.35 |
| all_reduce | 4 | 1,577 | 1,640 | 2.58 | 2.7 MiB | 1.26 | 1.89 |
| all_reduce | 8 | 5,701 | 5,554 | 1.18 | 3.6 MiB | 0.57 | 0.99 |
| all_gather | 2 / 4 / 8 | 377 / 998 / 3,175 | 302 / 965 / 3,207 | 1.51 / 1.47 / 0.74 | 0.9 / 1.8 / 2.6 MiB | 1.96 / 1.37 / 0.67 | 0.98 / 1.03 / 0.59 |
| reduce_scatter | 2 / 4 / 8 | 482 / 1,517 / 5,201 | 470 / 1,551 / 5,115 | 0.92 / 0.68 / 0.39 | 0.8 / 1.3 / 2.2 MiB | 1.39 / 0.83 / 0.38 | 0.69 / 0.63 / 0.33 |
| broadcast | 2 / 4 / 8 | 174 / 329 / 504 | 186 / 275 / 444 | 5.33 / 2.58 / 1.59 | 0.7–1.0 MiB | 5.28 / 2.05 / 1.29 | 5.28 / 2.05 / 1.29 |

Every one of the 12 sweeps validated with `#wrong = 0`, and busbw/algbw equals the chapter's factor
exactly. The two regions are there. All-reduce time is flat from 8n B to tens of KiB, then from about
n½ (1–4 MiB) it roughly doubles with size. These are the shapes of Figure 12.2 on a machine with α 14–200× larger
and B over 100× smaller.

Three results differ from an ideal ring on independent links, and each one shows what loopback is.

- **α grows faster than the step count.** The fitted all-reduce α is 390, 1,640 and 5,554 µs for 2, 4
  and 8 ranks. That is 195, 273 and 397 µs per ring step (2(n − 1) steps), against 63 µs one way for a
  2-rank ping-pong. In a ring step every rank sends and receives at once, so every process must be
  woken and scheduled together, and that costs more as n grows.
- **busbw falls with n instead of staying flat** (all-reduce 2.35 → 1.89 → 0.99 GB/s). busbw is
  constant with n only when each rank has its own link. Here every "link" is a memory copy through the
  same kernel and the same memory system. The ring moves 2(n − 1)·S bytes in total, so more ranks
  share the same copy bandwidth. On ORION the rails are independent, and Section 12.10 expects a flat
  busbw; a falling one there means a shared bottleneck.
- **Below 8n B, gloo is faster than its own floor.** A 4 B all-reduce took 474 µs at 4 ranks and
  1,016 µs at 8, against floors of 1,577 and 5,701 µs. gloo's ring splits the vector into 2n chunks and
  skips the empty ones. With fewer than 2n elements, some steps carry nothing. Floors and fits
  therefore start at 8n B (two float32 per rank).

The identity all-reduce = reduce-scatter + all-gather does not hold for gloo's API. At 16 MiB on 4 ranks,
reduce_scatter took 19.3 ms against 13.1 ms for the whole all-reduce (RS / AR = 1.47, where a ring
gives 0.5). gloo's `reduce_scatter_tensor` costs at least a full all-reduce, so it is not the ring's
first half. NCCL's is (Section 12.2). This is why FSDP on CPU/gloo is a functional test, not a
performance one. For a 25 MiB DDP bucket on 4 ranks, the fit gives α + factor·S/B = 16.9 ms
`[MODELED]`, 90 % of plateau bandwidth, because n½ is 2.7 MiB. The chapter gets 82 % on 16 ORION ranks
with n½ = 5.3 MB. The fraction is similar because α and B are both far smaller here, and n½ = α·B/factor
is their product. The measured 32 MiB all-reduce took 26.9 ms.

**Step 2: spread.** Three separate 4-rank launches gave plateau busbw of 1.89, 2.37 and 2.54 GB/s (CV
0.12), and the median per-size CV was 0.15. The 64 MiB all-reduce took 56.1, 37.5 and 38.4 ms. On this
shared host a 10 % difference between two configurations is inside the noise. Report the median of at
least five launches with min and max, and say what else was running (Section 12.10).

**Step 3: ring against tree.** The 2-rank ping-pong gives α = 62.9 µs and B = 6.13 GB/s. With those, the
model puts the crossover at 301 KiB for 4 ranks and 709 KiB for 8.

| Size | 4 ranks: ring / tree (µs) | 8 ranks: ring / tree (µs) | gloo all_reduce, 4 / 8 ranks (µs) |
|---|---|---|---|
| 4 KiB | 1,135 / 415 | 4,008 / 649 | 1,522 / 4,200 |
| 256 KiB | 1,462 / 647 | 4,529 / 1,072 | 1,677 / 4,494 |
| 1 MiB | 1,894 / 1,228 | 5,098 / 2,151 | 2,168 / 5,504 |
| 4 MiB | **3,850 / 3,908** | 8,667 / 6,908 | 3,210 / 8,532 |
| 16 MiB | 13,599 / 18,236 | **22,624 / 28,239** | 10,808 / 21,995 |
| 64 MiB | 52,995 / 68,618 | 95,476 / 117,167 | 49,590 / 88,892 |

The tree wins every small message, and the ring wins from 4 MiB at 4 ranks and from 16 MiB at 8 ranks.
The crossover moves up with n, as the model says: the ring's latency term grows as 2(n − 1) and the
tree's only as 2·log₂n. The measured crossovers are 14–23× larger than the model's because the ping-pong
α and B do not describe a ring step here. A tree step costs about 105 µs (415 µs / 4 steps at 4
ranks), close to ping-pong. A ring step costs about 190 µs (1,135 µs / 6 steps). At 64 MiB the ring
runs 3× slower than its model (53 ms against 16.8 ms) because all n transfers share one memory system
at the same moment. The tree also beats its model at 64 MiB (69 ms against 44 ms): its large single
messages stream better than the mid-size ping-pong points that dominate the fit. gloo's own all-reduce
stays within about 35 % of the hand-written ring from 4 KiB up (1,522 against 1,135 µs; 49.6 against 53.0 ms at 64 MiB),
which is what you would expect from a ring implementation. This simple tree moves all of S on every
step, and an interior rank serves two children, so at large sizes it is worse than the ring. NCCL's
double binary tree splits S over two trees and comes within 1.14× of the ring (Section 12.3).

**Step 4: NCCL.** Two ranks on GPU 0 failed (exit 1) with
`NCCL WARN Duplicate GPU detected : rank 1 and rank 0 both on CUDA device 1000`. On one rank, NCCL 2.21.5
initialised in 0.31 s including the first collective. Its all-reduce floor was 15.1 µs, against 384 µs
for gloo's 2-rank floor. A one-rank in-place all-reduce or broadcast copies nothing, so its 64 MiB time
(14.6 µs) equals the floor. all_gather and reduce_scatter took 595 µs at 64 MiB, a device-memory copy at
113 GB/s of algbw. busbw is 0 for the three collectives whose factor contains (n − 1). Broadcast's
factor is 1, so its "busbw" just repeats algbw and means nothing here. Measuring a GPU all-reduce takes
at least two GPUs: nccl-tests with `-g 2` on one host, or one rank per node across a fabric (the
chapter's L2/L3 extensions). This host has no CUDA toolkit, so nccl-tests was not built.

Your numbers will differ. `check.py` tests physical sense, not equality.

## Troubleshooting

- `ERROR: missing command: flock` (or `timeout`) → install util-linux and coreutils (`sudo apt-get install util-linux coreutils`), then rerun `bash setup.sh`.
- `setup.sh` fails while creating the venv or installing PyTorch → it needs network access to PyPI and download.pytorch.org (PyTorch 2.5.1 + CUDA 12.4, a few GB); if `python3 -m venv` fails, `sudo apt-get install python3-venv`. After an interrupted install, delete `~/.venvs/ai-infra-handson` and rerun.
- The run sits silent before the GPU step → it is waiting for the shared GPU lock `/tmp/handson-gpu.lock`, held by another hands-on lab (`ps aux | grep -e run.sh -e vllm`). Wait for that run to finish; do not delete the lock.
- `raw/nccl_2ranks_1gpu.log` shows `Duplicate GPU detected` → expected: Step 4 puts two ranks on one GPU on purpose. Without a GPU, Step 4 is skipped with a note.
- One sweep failed or looks wrong → read `results/<run-id>/raw/<name>.log`; each sweep is killed after 900 s. With fewer than 8 cores the 8-rank sweeps are slow and noisy: close other workloads and rerun.
- Leftover `ch12_collectives.py` processes after Ctrl-C → `bash teardown.sh`.

## 9. Clean up

```bash
bash teardown.sh       # stops any ch12_collectives.py process
```

`run.sh` calls it on exit, even after a failure.

## 10. Connect to the chapter

- Section 12.2 (the collectives and their size conventions): Step 1.
- Section 12.3 (alpha-beta costs of ring and tree, n½): Steps 1 and 3.
- Section 12.5 (algbw, busbw, regions, the weighted fit, the DDP bucket at n½): Step 1.
- Section 12.9 (PyTorch Distributed on top of NCCL; synchronising before timing): Steps 1 and 4.
- Section 12.10 (repeated launches and spread): Step 2.
- Chapter 11's lab measures the same gloo all-reduce inside a DDP training step.
