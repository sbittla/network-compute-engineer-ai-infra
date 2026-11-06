# Chapter 14 hands-on lab: storage and checkpoints on one machine

## 1. What you will do

You measure the storage path a training job actually uses on this machine, the way Section 14.6 says a
defensible measurement is made: `fio` random and sequential reads at queue depths 1, 4, 16 and 32, with
the page cache bypassed and then with it in the way, on the Linux file system and over the 9P path that
WSL2 uses for Windows drives. Then you checkpoint a real model and optimizer on the GPU three ways
(synchronous `dcp.save`, `dcp.async_save`, and a pinned snapshot persisted by a background thread),
measure blocking time, completion time, interference and restore time, and feed the measured cost into
the Young/Daly interval of Section 14.11.

## 2. What is real here, and what is not

Real: every fio number comes from fio 3.36 reading a file on this machine; every checkpoint number comes
from PyTorch 2.5.1 writing and reading real tensors with `fsync`; the consistency test compares real
tensors. The page-cache and queue-depth effects are the kernel's own.

Not real, or not ORION:

- **The disk is virtual.** In WSL2 the ext4 file system lives in a VHDX file on the laptop's NVMe drive,
  reached through Hyper-V's virtual SCSI. `O_DIRECT` bypasses the Linux page cache, but the Windows host
  may still cache the VHDX, so O_DIRECT numbers are an upper bound for the physical drive. There is no
  `nvme smart-log`, no `lspci` link state and no per-drive view.
- **One drive, one node, no parallel file system.** ORION's checkpoint cost is set by 980 GB going to a
  shared PFS from 256 ranks (Section 14.12); here a 0.4 GB state goes to one local disk. Absolute seconds do
  not transfer. What transfers is the shape: Little's law, the queue-depth curve, how much the page cache
  inflates a read benchmark, blocking much shorter than completion for asynchronous saves, and
  τ* = √(2δM).
- **MTBF is assumed.** A laptop has no failure history. Step 5 uses the chapter's planning values
  (48 h for ORION-256, 3 h for ORION-XL), labelled `[ASSUMED]`.
- **9P is a WSL2 detail.** On native Linux there is no `/mnt/c`; step 2 is skipped and the checker accepts
  that. Its lesson (the path, not the drive, can set the rate) is the same one Section 14.3 makes about
  the host-to-storage path.

The Level 3 extension in [../README.md](../README.md) (Section 8) measures the parts one machine cannot:
striping, aggregate PFS write rate and time-to-resume on shared storage.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | Yes, NVIDIA, for step 4 (peak about 1.5 GiB of device memory) |
| Docker | No |
| Root | Yes: `drop_caches` between runs, package install |
| Disk | 2 GB free on the ext4 file system (`/var/tmp`), 0.3 GB on `/mnt/c` (WSL2 only) |
| RAM | 7 GB; step 4 refuses to run below 4 × the checkpoint state + 1 GiB available (about 2.5 GiB) |
| Time | setup 1-3 min; run about 20 min (mostly fio; the checkpoint step takes about 2 min once it has the GPU lock) |

## 4. Safety

- fio only **reads** in steps 1-3 (`--readonly`); it writes one 1 GiB test file under
  `/var/tmp/ch14-handson/` and one 0.25 GiB file under `/mnt/c/Users/Public/ch14-handson/`, both deleted at
  the end. Nothing touches a raw device.
- `echo 1 > /proc/sys/vm/drop_caches` drops the clean page cache of the **whole** host. It is harmless to
  data but slows every other process's next reads, and it disturbs any other benchmark running at the same
  time. Do not run this lab alongside another storage measurement.
- Step 4 takes the shared GPU lock (`/tmp/handson-gpu.lock`) and writes checkpoints under
  `/var/tmp/ch14-handson/ckpt/`, deleted at the end. No clocks, power limits, interfaces or routes change.

Override the scratch locations with `CH14_EXT4_DIR` and `CH14_9P_DIR` (each path must contain
`ch14-handson`, which teardown checks before deleting).

## 5. Setup

```bash
cd book/part-4-distributed-ai/ch14-storage-pipelines-checkpointing/lab/handson
sudo bash setup.sh          # fio 3.36 (apt), the shared PyTorch venv; prints versions
```

From Windows: `python scripts/handson.py setup ch14` at the repository root.

## 6. Steps

`sudo bash run.sh <run-id>` runs every step unattended and writes `results/<run-id>/`. The commands below
are what it runs, so you can repeat any step by hand.

### Step 1: queue depth and Little's law on the ext4 disk

```bash
fio --name=randread --filename=/var/tmp/ch14-handson/fio-test.dat --readonly --rw=randread --bs=4k \
    --iodepth=32 --ioengine=libaio --direct=1 --ramp_time=2 --runtime=6 --time_based --output-format=json
```

The script runs 4 KiB random and 1 MiB sequential reads at QD 1, 4, 16 and 32, five interleaved
repetitions each, and reports the median with min-max. Look at IOPS against QD, and compute
IOPS × mean latency for each row (the table's last column).

**Question 1.** By how much do 4 KiB random IOPS grow from QD 1 to QD 32, and does IOPS × mean latency
recover the queue depth you asked for? What would it show if you had used `--ioengine=psync`?

### Step 2: the same reads over 9P

The script repeats the reads at QD 1 and 32 on a file under `/mnt/c`, which WSL2 serves from Windows
over the 9P protocol (`findmnt /mnt/c` shows `9p`).

**Question 2.** How many times faster is ext4 than 9P for sequential reads at QD 32, and why does 9P
barely respond to queue depth? Where in a real training setup would you meet the same lesson?

### Step 3: the page cache inflates "storage" numbers

```bash
sync; echo 1 | sudo tee /proc/sys/vm/drop_caches         # cold: before every cold run
fio ... --direct=0 --invalidate=1                          # buffered, cold
fio --name=warm --filename=... --rw=read --bs=1M --direct=0 --invalidate=0   # read the file once
fio ... --direct=0 --invalidate=0                          # buffered, warm: the file is in RAM
```

Compare O_DIRECT, buffered-cold and buffered-warm IOPS for the same pattern and QD.

**Question 3.** How many times faster than the disk is a warm-cache 4 KiB random read at QD 1? Why do
cold buffered random reads not scale with QD, and why are cold buffered *sequential* reads at QD 1 faster
than O_DIRECT ones? Which of Section 14.6's four rules does each observation illustrate?

### Step 4: checkpoint save and load, synchronous and asynchronous

```bash
. ../../../../../scripts/handson/venv.sh
sudo flock /tmp/handson-gpu.lock "$HANDSON_PY" ckpt_bench.py --out results/<run-id> --reps 5
```

A 34 M-parameter MLP with FP32 weights and fused Adam (0.40 GB of state, 12 B/param) trains on the GPU.
Each method runs one warm-up and five timed saves, interleaved; training steps run back to back while an
asynchronous persist is in flight. `dcp.load` is then timed with the page cache dropped and warm. Last, an
`async_save` is taken while training continues, and the checkpoint is compared tensor by tensor with a
copy of the state made at the call.

**Question 4.** What are the blocking and completion times of each method? Why is the pinned-snapshot
method's blocking time so much shorter than `dcp.async_save`'s, and what does it cost in host memory?
How does the end-to-end checkpoint write rate compare with fio's sequential write rate on the same disk,
and why?

### Step 5: the checkpoint interval

`summarize.py` computes δ per method as in Section 14.12 Step 4 (synchronous: the whole save;
asynchronous: blocking + interference × persist time), then τ* = √(2δM) (Young) and Daly's estimate for
M = 48 h and 3 h `[ASSUMED]`.

**Question 5.** With δ from your measurements, what are τ* and the fraction of time lost at τ* for the
synchronous and the best asynchronous method at M = 48 h? Using the per-node share of W-TRAIN (30.6 GB)
and your measured synchronous write rate, what δ would one ORION node see if it saved at this disk's
speed, and what does that say about where ORION's δ really comes from?

## 7. Check your results

```bash
python check.py results/<run-id>        # or, from the repository root: python scripts/handson.py check ch14 <run-id>
```

It checks the bundle is complete, recomputes medians from the raw fio JSON, and tests physical sense:
IOPS rise with QD under O_DIRECT, Little's law holds within 20 %, the warm cache beats the disk by more
than 5x, cold buffered reads scale with QD less than O_DIRECT, ext4 beats 9P, asynchronous saves block
for less than synchronous ones, the async checkpoint equals the state at the call, no paging occurred,
and the Young/Daly numbers follow from δ. Write your answers in `results/<run-id>/answers.md`.

## 8. Reference results

Measured on the reference machine (WSL2 Ubuntu 24.04, i7-13700HX, 7.8 GiB for WSL, RTX 4060 Laptop GPU,
driver 592.82, fio 3.36, PyTorch 2.5.1); the full bundle is in
[`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/report.md). Every number is `[MEASURED]`
except the Young/Daly rows, which are `[MODELED]` from measured δ and an `[ASSUMED]` MTBF.

| Step | Result | Value |
|---|---|---|
| 1 | 4 KiB random read, O_DIRECT, QD 1 → QD 32 | 3,933 → 50,605 IOPS (12.9x); mean latency 250 → 631 µs |
| 1 | 1 MiB sequential read, O_DIRECT, QD 1 → QD 16 → QD 32 | 1.63 → 6.38 → 6.22 GB/s |
| 1 | IOPS × mean latency, all 8 cells | 0.98-1.0 × the requested QD |
| 1 | Sequential 1 MiB write (laying out the file) | 4.19 GB/s ext4, 0.19 GB/s 9P |
| 2 | 1 MiB sequential read at QD 32, ext4 vs 9P | 6.22 vs 0.092 GB/s (68x) |
| 2 | 9P 4 KiB random IOPS, QD 32 / QD 1 | 1,914 / 1,668 = 1.15 |
| 3 | 4 KiB random read at QD 1: O_DIRECT, cold buffered, warm buffered | 3,933, 2,787, 326,286 IOPS (warm = 83x the disk) |
| 3 | Cold buffered 4 KiB random reads, QD 32 / QD 1 | 1.14x (O_DIRECT 12.9x) |
| 4 | `dcp.save`: blocking = completion | 0.439 s (0.92 GB/s end to end) |
| 4 | `dcp.async_save`: blocking / completion | 0.249 / 0.749 s (blocking ranged 0.055-0.302 s) |
| 4 | Pinned snapshot + thread: blocking / completion | 0.032 / 0.467 s; snapshot D2H 12.5 GB/s; 1 % step-time interference |
| 4 | `dcp.load`, cold / warm page cache | 0.493 s (0.82 GB/s) / 0.342 s (1.18 GB/s) |
| 4 | Async consistency | 0 of 64 tensors differ from the state at the call; 7 training steps ran meanwhile |
| 5 | τ* (Young) at M = 48 h: sync / dcp.async / pinned | 390 / 293 / 113 s; time lost 0.23 / 0.17 / 0.07 % |

What the numbers mean:

- **Little's law holds exactly** because libaio with `O_DIRECT` really keeps QD requests in flight: IOPS ×
  latency returns 1.0, 4.0, 15.9 and 31.9. Random IOPS grow 12.9x while latency only grows 2.5x, so the
  virtual disk has internal parallelism that QD 1 leaves idle. Sequential reads flatten at about 6.3 GB/s
  from QD 16: the path is then bandwidth-bound, and more depth only adds queueing delay (2.6 → 5.4 ms).
  6 GB/s is more than a laptop NVMe drive sustains through a VHDX, which is the Windows host cache showing
  through `O_DIRECT` (Section 2 above).
- **9P sets its own rate.** Every 9P request is a round trip to a file server in Windows, about 12 ms
  per 1 MiB read, and the requests are served one after another, so queue depth changes nothing (1.15x)
  and the drive's speed never shows. The same lesson applies to a data loader reading over a slow
  network mount: the hop, not the drive, is the bound.
- **The warm page cache is not storage.** 326k random IOPS is the kernel copying 4 KiB pages from RAM,
  83x what the disk delivers. Cold buffered random reads barely respond to QD (1.14x) because buffered
  libaio completes each read synchronously inside `io_submit`, so the device never sees the queue. For
  large sequential reads the warm cache (5.6 GB/s at QD 32) is no faster than `O_DIRECT` (6.2 GB/s): a
  buffered read is one thread doing `memcpy`, and the virtual disk's `O_DIRECT` path is fast too.
- **Async saves trade blocking time for host memory and completion time.** The pinned-snapshot method
  blocks for 32 ms: copying 0.40 GB over PCIe at 12.5 GB/s, close to the link's measured D2H rate in the
  Chapter 5 lab (13.2 GB/s pinned). It costs 0.40 GB of pinned host RAM held for the whole run.
  `dcp.async_save` in PyTorch 2.5 stages into newly allocated, pageable CPU memory on each call, so it
  pays for the allocation and the slower pageable copy, and its blocking time varies (55-302 ms over five timed
  calls). Both finish later than the synchronous save (0.47 and 0.75 s against
  0.44 s), because the background writer competes with training for CPU and memory bandwidth.
- **Checkpoints write far below the disk's sequential rate**: 0.92 GB/s end to end against 4.19 GB/s for
  fio's sequential write. The difference is serialisation, many tensors written as separate items, the
  metadata file, and `fsync` waiting for the virtual disk to make the data durable.
- **Young/Daly**: shrinking δ from 0.44 s to 0.037 s cuts the optimal interval from 390 s to 113 s and the
  time lost from 0.23 % to 0.07 % at an `[ASSUMED]` 48 h MTBF. Daly matches Young to within 1 s because
  δ ≪ M. Using the per-node W-TRAIN share (30.6 GB) at this disk's 0.92 GB/s gives δ ≈ 33 s per node
  `[MODELED]`; ORION's real δ comes from 256 nodes sharing one PFS, not from any single node's disk.

The fio numbers are noisy on this machine: the min-max ranges in the bundle are up to 2x wide, and an
earlier development run measured 7,772 IOPS at QD 1 and 72,200 at QD 32. Other labs were running on the
same laptop during the reference run, and the VHDX shares the physical drive with Windows. The medians
of five interleaved repetitions are what the checker judges; the ratios (Little's law, QD scaling, cache
inflation, ext4 against 9P) were stable across both runs.


Results on other hardware will differ; the checker tests physical sense, not equality.

## 9. Clean up

```bash
sudo bash teardown.sh     # run.sh already calls it, even after a failure
```

It deletes the scratch directories and stops any fio or checkpoint process this lab started. Results stay.

## 10. Connect to the chapter

| Step | Chapter section |
|---|---|
| 1 | 14.2 (queue pairs, Little's law, the psync pitfall), 14.6 (fio used properly) |
| 2 | 14.3 (the host-to-storage data path: which hop bounds the workload) |
| 3 | 14.6 rule 1 (control the cache), 14.7 (page cache and readahead in data loaders) |
| 4 | 14.8-14.9 (snapshot vs persist, staging memory, interference), 14.10 (consistency boundary, atomic commit with `os.replace`) |
| 5 | 14.11 (Young/Daly, overhead and recomputation), 14.12 (the worked example's δ) |
