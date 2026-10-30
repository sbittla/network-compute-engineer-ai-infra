# Benchmark Plan (harness and test plan)

## 1. Workload definition

| Item | Value |
|---|---|
| Workload | <fill: W-TRAIN replica TP8 × PP4, 128 × 4,096-token sequences per replica; or CPU proxy config> |
| Scaling mode | <fill: weak scaling over DP; why not strong scaling> |
| Scales | <fill: 32, 64, 128, 256 GPUs> |
| Metric | <fill: steady-state step time → tokens/s → per-GPU tokens/s> |

## 2. Method

| Control | Policy | Justification |
|---|---|---|
| Warm-up | <fill> | <fill> |
| Repetitions | <fill: ≥ 8 runs per configuration (so an exact test can survive a multiple-comparison correction), ≥ 50 steady steps each> | |
| Statistic | <fill: median per run; median of run medians> | |
| Spread | <fill: min/max of run medians, IQR within run> | |
| Significance | <fill: exact permutation test (statistic: difference of means of run medians) + bootstrap CI of the speedup; Holm across all tests in the family> | |
| One variable at a time | <fill: what is held constant; how manifests prove it> | |
| Admissibility | <fill: restart, environment drift, outlier rule; report with and without exclusions> | |

## 3. Test matrix

| ID | Tier | Configuration | Changed variable | Runs | Command / harness call | Expected | Status |
|---|---|---|---|---|---|---|---|
| T-01 | L1 | CPU proxy, 4 ranks | — | 10 reps after 3 warm-up | `run_benchmark(...)` | checksum stable | <fill> |
| T-02 | L2 | 8 GPUs, `all_reduce_perf -b 1M -e 8G -f 2 -g 1 -w 5 -n 20` | — | 5 | see starter-kit README §8 | busbw ≈ 360–380 GB/s for a plain ring (algbw ≲ 257 GB/s); ≈ 450 GB/s busbw implies NVLS `[VENDOR-SPEC, 2026-10]` | <fill> |
| T-03 | L3 | 16 GPUs on 2 nodes, same command via `mpirun` | transport | 5 per variant | | ≈ 350+ GB/s with NET/IB + GDRDMA | <fill> |
| T-04 | L3 | training proxy 32 → 256 GPUs | scale | 5 per point | `torchrun ...` | eff ≥ <fill> | <fill> |
| <fill> | | | | | | | |

## 4. Pre-flight checks before any measured run

- [ ] `ibv_devinfo` inside the job container lists the 8 backend HCAs
- [ ] NCCL log shows `Using network IB` and channel lines with `/GDRDMA`
- [ ] `nvidia-smi topo -m` matches the golden topology (GPU *i* PIX NIC *i*)
- [ ] Clocks, power limits and ECC state recorded; no `clocks_event_reasons` active at idle
- [ ] Manifest filled; image referenced by digest

## 5. Risks to validity

<fill: thermal drift across a day, noisy neighbours on a shared fabric, node-set differences between
runs, background checkpoint I/O.>
