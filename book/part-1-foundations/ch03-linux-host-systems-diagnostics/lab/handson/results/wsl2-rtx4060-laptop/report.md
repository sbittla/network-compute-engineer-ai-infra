# Chapter 3 hands-on: host diagnostics on `13th Gen Intel(R) Core(TM) i7-13700HX` (24 CPUs)

Run captured 2026-11-05T04:11:52+00:00 on kernel `6.18.54.1-rxe+` (WSL2), GPU: NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, 592.82. Every number below is `[MEASURED]` on this machine by the step named; raw outputs are in the step directories next to this file.

## Step 1: the chapter's read-only collector, root and non-root

- root: 13/15 sections ok `[MEASURED]`; gaps: cpufreq (missing), nvidia_smi (missing); `lspci -vv` lines reading `<access denied>`: 0 `[MEASURED]`.
- nonroot: 13/15 sections ok `[MEASURED]`; gaps: cpufreq (missing), nvidia_smi (missing); `lspci -vv` lines reading `<access denied>`: 4 `[MEASURED]`.
- Triage of the root snapshot against the ORION HX8 baseline: 16 critical, 0 warning, 2 info, verdict **DRAIN / repair** `[MEASURED]` (this machine is not an HX8, so inventory rules fire).

## Step 2: averages hide the saturated core

- One busy thread on CPU 14: that CPU 100.0 % busy, all-CPU average 4.5 % busy `[MEASURED]` (`mpstat -P ALL 1 5`, Average block). One core is 4.17 % of this host.
- `vmstat 1 6`: since-boot row 95 % idle versus live rows 96.0 % idle `[MEASURED]`.

## Step 3: CPU placement and throughput (per-worker throughput relative to one worker alone)

| Placement | Per worker | Total |
|---|---|---|
| alone | 1.00 `[MEASURED]` | 1.00 `[MEASURED]` |
| same_cpu | 0.49, 0.49 `[MEASURED]` | 0.98 `[MEASURED]` |
| smt_siblings | 1.00, 0.99 `[MEASURED]` | 1.99 `[MEASURED]` |
| separate_cores | 1.01, 1.00 `[MEASURED]` | 2.01 `[MEASURED]` |
| unpinned | 1.01, 1.01 `[MEASURED]` | 2.02 `[MEASURED]` |
| alone_again | 0.99 `[MEASURED]` | 0.99 `[MEASURED]` |

## Step 4: the page cache

- 1 GiB file: cold read 4.621 GB/s, warm read 9.252 GB/s (2.0× faster), O_DIRECT read 3.017 GB/s `[MEASURED]`.
- Page-cache residency (mincore): 0% after `POSIX_FADV_DONTNEED`, 100% after one cold read `[MEASURED]`; `Cached` fell by 1024 MiB on eviction `[MEASURED]`.

## Step 5: locked and pinned memory

- uid 0: mlock 128 MiB with RLIMIT_MEMLOCK 1016080 KiB: ok `[MEASURED]`.
- uid 65534: mlock 16 MiB with RLIMIT_MEMLOCK 65536 KiB: ok `[MEASURED]`.
- uid 65534: mlock 128 MiB with RLIMIT_MEMLOCK 65536 KiB: refused (Cannot allocate memory) `[MEASURED]`.
- 256 MiB H2D: pageable 10.99 GB/s, pinned 12.96 GB/s (1.18×) `[MEASURED]`; D2H pageable 10.71, pinned 13.16 GB/s `[MEASURED]`.
- CPU held by a `non_blocking=True` copy: pageable 24.116 ms, pinned 0.035 ms `[MEASURED]`. Pinning the buffer cost 206.4 ms (the pinned copy itself takes 20.705 ms) `[MEASURED]`.
- VmLck/VmPin after `pin_memory()`: 0/0 KiB `[MEASURED]`.

## Step 6: kernel log and /proc signals

- `dmesg`: 522 lines, 64 at err or worse; AER 0, EDAC 0, Xid 0, MCE 0, OOM 0, I/O errors 0, `dxg` ioctl failures 62 `[MEASURED]`; `oom_kill` counter 0 `[MEASURED]`.
- 48 niced busy loops on 24 CPUs: PSI `cpu some avg10` 0.58 → 39.15 %, `vmstat r` up to 48, 1-minute load 2.29 → 9.32 `[MEASURED]`.

