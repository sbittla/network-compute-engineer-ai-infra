# Chapter 14 hands-on: storage and checkpoints on `wsl2-rtx4060-laptop`

Captured 2026-11-05T03:02:46+00:00 on 13th Gen Intel(R) Core(TM) i7-13700HX (24 CPUs, 7.8 GiB), GPU NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, 592.82, kernel 6.18.54.1-rxe+. Every number below is `[MEASURED]` by the step named, except rows labelled `[MODELED]` (computed from measured values) or `[ASSUMED]`.

Test file: `/var/tmp/ch14-handson/fio-test.dat` (1.0 GiB) on `ext4   /dev/sdd`; 5 interleaved repetitions of 2 s ramp + 6 s; fio-3.36, `--ioengine=libaio`. 67 fio jobs, 0 failed.

## Step 1: O_DIRECT reads on the ext4 virtual disk `[MEASURED]`

| Pattern | QD | IOPS median (min-max) | GB/s | mean latency µs | p99 µs | p99.9 µs | IOPS x latency (Little) |
|---|---|---|---|---|---|---|---|
| randread-4k | 1 | 3,933 (3,410-6,492) | 0.016 | 249.8 | 452.6 | 766.0 | 1.0 |
| randread-4k | 4 | 14,899 (12,762-27,111) | 0.061 | 266.3 | 493.6 | 831.5 | 4.0 |
| randread-4k | 16 | 43,161 (37,316-67,777) | 0.177 | 369.2 | 831.5 | 1,188 | 15.9 |
| randread-4k | 32 | 50,605 (44,161-67,333) | 0.207 | 631.0 | 1,417 | 2,114 | 31.9 |
| seqread-1m | 1 | 1,557 (1,211-2,102) | 1.632 | 638.0 | 995.3 | 1,335 | 1.0 |
| seqread-1m | 4 | 3,664 (2,823-5,640) | 3.842 | 1,088 | 1,712 | 5,341 | 4.0 |
| seqread-1m | 16 | 6,085 (3,711-6,255) | 6.383 | 2,626 | 4,178 | 6,783 | 16.0 |
| seqread-1m | 32 | 5,922 (3,902-6,335) | 6.215 | 5,397 | 7,963 | 11,338 | 32.0 |

Random 4 KiB IOPS grow 12.9x from QD 1 to QD 32 `[MEASURED]`, and IOPS x mean latency recovers the queue depth fio was asked for (Section 14.2). Sequential 1 MiB write while laying out the file: layout-ext4 4.19 GB/s, layout-9p 0.19 GB/s `[MEASURED]`.

## Step 2: the same reads over 9P (`/mnt/<drive>`) `[MEASURED]`

`/mnt/c/Users/Public/ch14-handson` on `9p     C:\`.

| Path | Pattern | QD | IOPS | GB/s | mean latency µs |
|---|---|---|---|---|---|
| 9P, O_DIRECT | randread-4k | 1 | 1,668 | 0.007 | 592.3 |
| 9P, O_DIRECT | randread-4k | 32 | 1,914 | 0.008 | 16,687 |
| 9P, O_DIRECT | seqread-1m | 1 | 81.65 | 0.086 | 12,235 |
| 9P, O_DIRECT | seqread-1m | 32 | 82.26 | 0.092 | 378,915 |
| 9P, buffered | randread-4k | 1 | 1,690 | 0.007 | 584.8 |
| 9P, buffered | randread-4k | 32 | 1,924 | 0.008 | 16,604 |
| 9P, buffered | seqread-1m | 1 | 82.72 | 0.087 | 12,076 |
| 9P, buffered | seqread-1m | 32 | 76.04 | 0.085 | 407,226 |
| ext4, O_DIRECT | randread-4k | 1 | 3,933 | 0.016 | 249.8 |
| ext4, O_DIRECT | randread-4k | 32 | 50,605 | 0.207 | 631.0 |
| ext4, O_DIRECT | seqread-1m | 1 | 1,557 | 1.632 | 638.0 |
| ext4, O_DIRECT | seqread-1m | 32 | 5,922 | 6.215 | 5,397 |

ext4 reads sequentially 68x faster than 9P at QD 32, and 9P random IOPS barely move with queue depth (QD 32 / QD 1 = 1.15) `[MEASURED]`: every 9P request is a message to a file server in Windows, so the path, not the drive, sets the rate.

## Step 3: the page cache inflates "storage" numbers `[MEASURED]`

| Pattern | QD | O_DIRECT IOPS | buffered, cold cache | buffered, warm cache | warm GB/s |
|---|---|---|---|---|---|
| randread-4k | 1 | 3,933 | 2,787 | 326,286 | 1.34 |
| randread-4k | 4 | 14,899 | 3,146 | 324,403 | 1.33 |
| randread-4k | 16 | 43,161 | 2,960 | 326,330 | 1.34 |
| randread-4k | 32 | 50,605 | 3,180 | 321,994 | 1.32 |
| seqread-1m | 1 | 1,557 | 1,187 | 6,481 | 6.80 |
| seqread-1m | 4 | 3,664 | 1,508 | 6,541 | 6.86 |
| seqread-1m | 16 | 6,085 | 2,354 | 5,374 | 5.64 |
| seqread-1m | 32 | 5,922 | 1,476 | 5,295 | 5.56 |

With the file in the page cache, 4 KiB random reads at QD 1 run 83x faster than the disk delivers `[MEASURED]`: that is the kernel copying pages from RAM, not storage. Sequential 1 MiB reads at QD 32 from the warm cache run at 0.9x the O_DIRECT rate `[MEASURED]`: a buffered read is a single-threaded memory copy, while O_DIRECT large reads on a virtual disk can be served from the hypervisor host's own cache, so for large sequential I/O the two converge. Cold buffered random reads gain only 1.14x from QD 1 to QD 32 (O_DIRECT: 12.9x): buffered libaio submits synchronously, so the requested queue depth never reaches the device. Cold buffered sequential reads at QD 1 get 0.76x the O_DIRECT rate because kernel readahead adds the parallelism the application did not.

## Step 4: checkpoint save and load `[MEASURED]`

State: 0.403 GB (33.6 M params, MLP d=1024 layers=4 (FP32 + Adam)); baseline training step 35.9 ms; peak GPU memory 1.28 GiB; swap growth during the run 4 MiB.

| Method | blocking s (min-max) | completion s (min-max) | on disk GB | end-to-end GB/s | step ms before / during | interference | δ (effective cost) s |
|---|---|---|---|---|---|---|---|
| dcp.save (sync) | 0.439 (0.358-0.532) | 0.439 (0.358-0.532) | 0.403 | 0.92 | 36.9 / n/a | 0 % | 0.439 |
| dcp.async_save | 0.249 (0.055-0.302) | 0.749 (0.487-0.920) | 0.403 | 0.54 | 36.9 / 36.8 | 0 % | 0.249 |
| pinned snapshot + thread | 0.032 (0.032-0.033) | 0.467 (0.359-1.169) | 0.403 | 0.86 | 36.8 / 37.2 | 1 % | 0.037 |

Pinned D2H snapshot: 12.5 GB/s `[MEASURED]`. dcp.load: cold cache (drop_caches) 0.493 s = 0.82 GB/s; warm cache 0.342 s = 1.18 GB/s `[MEASURED]`.

Consistency: an async_save taken while 7 training steps ran differs from the state at the call in 0 of 64 tensors (live state changed meanwhile: True) `[MEASURED]`.

## Step 5: the checkpoint interval (Young/Daly) `[MODELED]` from measured δ and `[ASSUMED]` MTBF

MTBF values are assumptions, not measurements: 48 h is the chapter's ORION-256 planning value and 3 h its ORION-XL value (Section 14.11). This laptop has no failure history to measure.

| MTBF `[ASSUMED]` | Method | δ s | τ* Young s | τ* Daly s | time lost at τ* | τ* ≥ completion |
|---|---|---|---|---|---|---|
| 48 h | dcp.save (sync) | 0.439 | 390 | 389 | 0.225 % | True |
| 48 h | dcp.async_save | 0.249 | 293 | 293 | 0.170 % | True |
| 48 h | pinned snapshot + thread | 0.037 | 113 | 113 | 0.066 % | True |
| 3 h | dcp.save (sync) | 0.439 | 97 | 97 | 0.902 % | True |
| 3 h | dcp.async_save | 0.249 | 73 | 73 | 0.679 % | True |
| 3 h | pinned snapshot + thread | 0.037 | 28 | 28 | 0.263 % | True |

Absolute values describe a 0.4 GB state on one laptop disk; ORION's δ is set by 980 GB going to a shared PFS (Section 14.12). The relations carry over: τ* grows with √δ, async shrinks δ to the blocking snapshot plus interference, and the time lost at the optimum is √(2δ/M).
