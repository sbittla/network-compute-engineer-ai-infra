# Chapter 13 — Exercises Answer Key (INSTRUCTOR ONLY)

Lab data are `[SIMULATED]`; analyses are `[MODELED]` unless stated. Numbers verified by hand and with
`solutions/lab/telemetry_diag.py`.

## 13.1

TP moves 1.20 TB per GPU per step over NVLink; DP + PP move 7.66 + 2.15 = 9.81 GB over the NIC;
1.20e12 / 9.81e9 ≈ 123 (≈ 157 vs DP alone). Tensor parallelism's four collectives per layer per
micro-batch cause it. Accept "≈ 120–160×" with arithmetic.

## 13.2

(1) PCIe P2P-capable platform with supported GPU and NIC; (2) peer-memory mechanism
(`nvidia-peermem` module or dma-buf path); (3) ACS/IOMMU configured so P2P is not redirected through
the root complex; (4) compatible driver/firmware/library versions. Proof requires observing the path
in use: NCCL channel lines ending in `/GDRDMA`, CUDA-buffer perftest at line rate, and a GDR-on vs
GDR-off difference.

## 13.3

PIX: through at most one PCIe switch (same switch); PXB: through multiple PCIe switches but not a host
bridge; PHB: through a PCIe host bridge (CPU root complex); SYS: across the inter-socket link. NCCL's
default `NCCL_NET_GDR_LEVEL` enables GDR for close paths (PIX/PXB in typical releases) and not across
SYS `[VENDOR-SPEC, 2026-10]` — accept "PIX and PXB, not SYS" with the label and a "verify" note.

## 13.4

`utilization.gpu` = fraction of sample time in which any kernel ran; NCCL's collective kernels spin
on flags while waiting, so the GPU counts as busy. Better: DCGM SM active (`DCGM_FI_PROF_SM_ACTIVE`) or
tensor-pipe active, and per-rank phase timings (wait vs transfer vs compute).

## 13.5

Only compute that does not depend on the reduced gradients can hide it — with PP + accumulation, the
last micro-batch's backward on the stage: 13.9 s / 128 micro-batches × 2/3 (backward share) ≈ 72 ms,
against ≈ 170 ms of DP time → ≥ ≈ 100 ms exposed.

## 13.6

Independent failures at exactly the same step on eight nodes have negligible joint probability
(p⁸ for small p); a shared component is far more likely. All eight share the rail-2 leaf
(`orion-be-leaf-r2`), its configuration, and possibly an optics batch. Suspect the leaf/config.

## 13.7 One pipeline message

| Path | Host copies | PCIe transfers | PCIe bytes | Time |
|---|---|---|---|---|
| GPUDirect RDMA | 0 | 2 (NIC reads GPU; remote NIC writes GPU) | 2 × 8.39 = 16.8 MB | 8.39e6 / 45e9 = 186 µs (+ ≈ 10 µs fixed) |
| Host-staged | 2 | 4 (GPU→host by the NCCL kernel, host→NIC, NIC→host, host→GPU by the NCCL kernel) | 4 × 8.39 = 33.6 MB | unpipelined bound: 168 + 186 + 168 = 522 µs |

With chunked pipelining the host-staged time approaches ≈ 186 µs plus a chunk latency, but it still
doubles PCIe bytes and adds DRAM traffic. Marking: table 4, times 3.

## 13.8 Amplification

(a) 1 − (1 − 0.0005)^N: N = 256 → **12.0 %**; 1,024 → **40.1 %**; 4,096 → **87.1 %**.
(b) 63 ranks × (774 − 600) ms = 63 × 0.174 s = **10.96 GPU-s per step**; fraction = 10.96 / (64 × 0.924)
= **18.5 %** (matches the lab's 18.6 % for steps 0–19).

## 13.9 (O1) Path trace (marking guidance)

Same rail (GPU 6 → GPU 6): HBM → NCCL buffer (HBM, ≈ 3.35 TB/s) → PCIe switch SW3 (Gen5 x16, ≈ 63 GB/s
per direction theoretical) → NIC 6 (400 Gb/s) → `orion-be-leaf-r6` (≈ 0.6–1 µs cut-through,
`[ILLUSTRATIVE]`) → NIC 6 on `orion-n14` → SW3 → HBM. With GDR: 0 host copies, 2 PCIe transfers,
1 switch hop. Host-staged: the NCCL kernel stores to / loads from pinned host buffers in socket 1 DRAM: 2 copies, 4 PCIe transfers. Cross-rail
(to GPU 2): either leaf r6 → `orion-be-spine-S` → leaf r2 (3 hops) or, with NCCL PXN, an NVLink hop on
the sender to GPU 2 first and then rail 2 (1 switch hop). Full marks require canonical names, both
variants, counts, captions, and evidence labels on latencies.

## 13.10 (O2) Verdict per window

| Steps | Verdict | Evidence |
|---|---|---|
| 0–19 | Synchronization caused by **data imbalance** (rank 12) | Wait ≈ 172 ms/rank; rank 12 compute z ≫ 6 with tokens +31 %, clocks/temperature normal; transfer 120 ms normal; burst NIC ≈ 360 Gb/s |
| 20–29 | Same, plus a **thermal straggler** (rank 37) hidden behind it | Rank 37 compute slow from step 20, clock −22 %, 90 °C, `sw_thermal_slowdown`, tokens normal; step time unchanged because max(12, 37) unchanged |
| 30–59 | Adds **communication-bound** degradation on rail 2 | Transfer 120 → 198 ms for all; retransmissions ≈ 3,200/step on local index 2 on every node vs ≈ 1 elsewhere; burst NIC rate falls to ≈ 222 Gb/s |

Decoy: rank 51, 84 °C but clocks normal and no reason → not a cause. Misleading metric:
`utilization.gpu` (99.7 % throughout) because NCCL kernels spin while waiting; also the step-averaged
NIC rate (≈ 45 Gb/s) hides 360 Gb/s bursts. Amplification steps 30–59: 334 GPU-s, 17.3 %.

## 13.11 (O3) Measurement plan

Expect Table 13.5 content: topology (`nvidia-smi topo -m`, `lstopo`), peer-memory (`lsmod | grep
nvidia_peermem` or dma-buf), ACS (`lspci -vvv` ACSCtl), IOMMU (`/proc/cmdline`), PCIe link
(`LnkSta`), perftest host vs `--use_cuda=<aligned GPU>` vs `--use_cuda=<misaligned GPU>`, NCCL INFO
channel lines with `/GDRDMA`, nccl-tests default vs `NCCL_NET_GDR_LEVEL=LOC` (GDR off), DCGM PCIe
bytes / host memory bandwidth; ≥ 5 repetitions with median and spread; manifest fields; safety: read-only
checks, drained nodes, no ACS/IOMMU changes outside change control. Marking: 1 pt per valid row up to
8, 2 pts for misaligned and GDR-off controls, 2 pts for repetitions/manifest/safety.

## 13.12 Lab

See `solutions/lab/README.md`: stragglers [12, 37]; causes data_imbalance (onset 0), thermal (onset 20);
rail 2 flagged, onset 30; decoy [51]; amplification 334 GPU-s (17.3 %) for steps 30–59.

## 13.13 One slow node in a TP job

Hypotheses: (1) NVLink/NVSwitch path degraded on `orion-n09` after the reboot — fabric-management
service not running or links down — so intra-node P2P falls back to PCIe/host paths (fits: TP-only,
one node, after driver update); (2) NCCL topology misdetected (container/driver mismatch) choosing a
non-NVLink transport; (3) GPU clocks low (rejected: clocks normal); (4) network (rejected: DP/PP
normal). Tests: `nvidia-smi nvlink --status` (links inactive or fewer active); `nvidia-smi topo -m`
(GPU↔GPU shows `NV18` when healthy vs a PCIe label); `systemctl status nvidia-fabricmanager` (or the
platform's fabric-management service) `[VENDOR-SPEC]`; single-node `all_reduce_perf -g 8` on the
node vs a peer (busbw ≈ 450 vs far lower); NCCL INFO shows non-NVLink P2P/SHM transports. Root
cause (model): fabric-management service failed to start after the driver update (version mismatch).
Fix: checkpoint, drain the node (a drain does not move the job), restart without it at reduced DP or wait for repair (ORION-256 has no spares); Fleet aligns service and driver versions under change control,
reboot, acceptance tests. Validation: links active, single-node busbw within 5 % of fleet median,
rejoin; job TP time on n09 within 5 % of median.

## 13.14 Design (marking guidance)

Strong answers: fields as in Section 13.7 instrumentation box (phases from CUDA events, entry skew,
tokens, clocks/reasons/temp/power, NIC throughput and retransmission counters, map keys); sampling
every 10–50 steps per rank plus DCGM 1 Hz; volume estimate e.g. 4,096 ranks × 20 fields × 8 B ×
(86,400 s / 2 s per step / 10) ≈ 2.8 GB/day before compression — accept any consistent arithmetic;
arrival skew from collective duration minus post-arrival transfer or periodic all-gather of entry
timestamps; alerts on robust z (≥ 6 in ≥ 25 % of a window), wait fraction > 10 %, rail-grouped
retransmission ratios; trade-off defended.

## 13.15–13.18 Reflection (guidance)

- 13.15: busy may mean slow (retransmissions, low burst rate), or simply that waiting ended and the
  burst began; compare burst rate with line rate and transfer time with baseline.
- 13.16: validate against the *maximum*, not per-rank improvement; fix all stragglers or measure the
  rank's own compute and wait distribution, not just step time.
- 13.17: missing samples, clock skew, counter wraps/resets, mixed intervals, interacting causes
  (throttled GPU slowing TP peers), overlapping collectives.
- 13.18: cross-socket NIC use, cross-rail placement, NUMA misbinding — idle benchmarks find spare
  inter-socket/spine capacity; production adds contention and variance, which synchronous training
  amplifies.
