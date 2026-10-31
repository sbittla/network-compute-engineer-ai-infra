# 3.8 — `orion-n12`: CPU utilization is low but throughput is poor

Method: manuscript Section 3.9 (the USE method and the "CPU is low but throughput is poor" pattern),
Sections 3.4–3.7 for each signal. The snapshot is `[SIMULATED]`; derived numbers are `[MODELED]` and
`solve.py` recomputes them from `lab/data/snapshots/orion-n12.json`.

## 1. Abnormal signals

| Section | Value | Baseline / peer |
|---|---|---|
| `iostat` (live report) | `nvme3n1` r_await **48.60 ms**, aqu-sz **40.34**, %util **99.90**, 830 r/s | siblings `nvme0–2n1`: 0.21 ms, 0.17, 17.4 % |
| `iostat` | `md0` r_await **49.10 ms**, aqu-sz 40.75, %util 100.0, 830 r/s × 512 KiB | healthy md0 < 1 ms |
| `iostat` avg-cpu | %iowait **6.90**, %idle 88.90 | < 1 % |
| `vmstat` (live rows) | `b` = 14, 14, 16, 17 (mean **15.25**); `wa` 6–8; `bi` ≈ 370–440 MB/s | `b` ≤ 1 |
| `mpstat` | all-CPU busy ≈ 11.5 %; **CPU0 99.5 % busy** (%soft 76.5, %sys 22.4) | no CPU > 90 % |
| `interrupts` | all 8 `mlx5_comp` IRQs of `rail0` (19:00.0) **and** of `fe0` (4c:00.0) on **CPU0** | spread over local cores |
| `numastat_pid` / `taskset_pid` | PID 48211 bound to node-0 CPUs (`0-55,112-167`); **210,855.6 of 213,171.2 MB on node 1 (98.9 %)** | < 25 % remote |
| `nvidia_smi` | GPU utilization **55–60 %**, links Gen5 x16 | peers ≈ 95–99 % |
| Normal | PCIe Gen5 x16 everywhere, MTU 9000, rail/fe speeds nominal, `intel_pstate` + `performance`, no AER/EDAC/Xid | — |

Raw lines quoted from the snapshot:

```text
nvme3n1  830.00 106240.00 ... 48.60  128.00 ... 40.34  99.90
 4 14      0 1594204192 412000 198000000    0    0  438770 ...  4  2 87  7  0
Total                    2315.60       210855.60       213171.20
```

## 2–3. Ranked hypotheses and discriminating tests

| Rank | Hypothesis | Explains ≈ 40 %? | Discriminating test (L2) | Confirming result |
|---|---|---|---|---|
| 1 | **Slow RAID 0 member `nvme3n1` gates `md0`**; loader workers block and the GPUs starve | **Fully.** md0 delivers 830 × 512 KiB = 435 MB/s; a loader that needs ≈ 725 MB/s gets 60 % of it. Utilization ≈ 58 % agrees | `nvme smart-log /dev/nvme3` (temperature, `critical_warning`, media errors); kernel log for nvme timeouts/resets; read-only `fio --readonly` per member on the drained node; PSI `io` | nvme3 throttling or media errors; member latency ≫ siblings |
| 2 | **IRQ/softirq concentration on CPU0** | Partially: caps kernel-path traffic (PFS reads, checkpoint uploads) and slows threads on CPU0; W-MM reads local NVMe | `/proc/softirqs` NET_RX delta per CPU; `/proc/irq/<n>/smp_affinity_list`; `systemctl is-active irqbalance` | NET_RX grows only on CPU0 |
| 3 | **NUMA-remote loader memory** (98.9 %) | Partially: slows decode/copy, but the workers are *blocked*, not busy | `perf stat -e cycles,instructions -p 48211` against a peer; launcher's `numactl` arguments | IPC clearly lower than the peer's |
| 4 | **PCIe/GPU constraint** | No: Gen5 x16 under load; GPUs low because they wait | `nvidia-smi` link query under load; GPU timeline | Gaps occur before data arrives |
| 5 | **CPU frequency** | No: `intel_pstate` + `performance` | `turbostat` Bzy_MHz | Matches peers |

## 4. Root cause and remediation order

Primary cause: **`nvme3n1` latency** (48.6 ms, ≈ 231× its siblings' 0.21 ms), inherited by every
512 KiB `md0` read because a RAID 0 stripe waits for its slowest member. Contributing factors: the IRQ
concentration on CPU0 (stopped `irqbalance` or a bad affinity profile) and the loader's remote memory.
W-MM is a single-node job, so the loss is node-local: 0.40 × 8 ≈ 3.2 GPU-h per hour, against 8 × 0.25 h =
2 GPU-h to stop at the next checkpoint. Stop, repair, restart. Order: (1) drain the node, stop the job
at a checkpoint; Fleet replaces or reseats `nvme3` (or rebuilds the cache without it). (2) Platform
restores the IRQ affinity profile or `irqbalance` through config management. (3) Training Infra fixes the
launcher binding (`--cpunodebind` with a matching `--membind`). Every change goes through the change
process on the drained node.

## 5. Validation

Fixed W-MM configuration on the repaired node: 50 warm-up steps, then 300 measured steps, three runs.
Report median and p95 samples/s per run with the min–max spread, against two peer nodes; accept at median
within 3 % of peers. Secondary: md0 `r_await` < 1 ms, `vmstat b` ≤ 2, GPU utilization ≥ 90 %, CPU0
`%soft` back to background.

**Common wrong answers:** calling NUMA primary because 98.9 % looks worst; reading 6.9 % iowait as
"fine"; blaming `md0` without naming the member; changing IRQ affinity live on the training node.

*Marking note:* the key's two 1.5-point items (root cause and order; validation plan) are merged into one
3-point criterion in `meta.yaml`, so every criterion carries whole points.
