# Chapter 12 — Exercises Answer Key (INSTRUCTOR ONLY)

Lab data are `[SIMULATED]`; fits are `[MODELED]`. Every number below was computed by hand and checked
with `solutions/lab/nccl_analysis.py`. Accept ±1 % for rounding.

## 12.1 Reduce-scatter and all-gather

Reduce-scatter: every rank contributes a buffer of n chunks; the element-wise reduction of chunk *r*
ends up only on rank *r*. All-gather: every rank contributes one chunk; every rank ends up with all n
chunks concatenated in rank order. Two ranks, R0 = [1, 2], R1 = [10, 20]: reduce-scatter → R0 [11],
R1 [22]; all-gather of those → both [11, 22] = all-reduce result.

## 12.2 Why all-to-all is harder

(1) Fan-out and incast: each rank sends to n − 1 destinations simultaneously, so every receiver gets
n − 1 concurrent flows (incast) and switch buffers/ECN/PFC are stressed (Chapter 9); rings are
neighbour-to-neighbour. (2) On a rail-optimized fabric, destinations on other rails require a spine hop
(or NVLink forwarding first, e.g. PXN). (3) For MoE, volumes per destination are data-dependent, so
hot experts create persistent imbalance. Any two with mechanisms = full marks.

## 12.3 Factors for n = 16

All-reduce 2 × 15/16 = **1.875**; all-gather **0.9375**; reduce-scatter **0.9375**; broadcast **1**;
all-to-all **0.9375**.

## 12.4 Protocols

LL: 8-byte stores with 4 B data + 4 B flag → ≈ 50 % payload efficiency, lowest latency (receiver polls
flags; no separate synchronization). LL128: 128-byte lines with 120 B data + 8 B flag → ≈ 94 %, low
latency, requires paths that preserve 128-byte write ordering (NVLink-class). Simple: bulk data plus
memory fences and per-chunk flag synchronization → ≈ 100 % efficiency, highest latency. Marking:
efficiency number + mechanism per row.

## 12.5 Channels

A channel is an independent instance of a ring or tree, run by one CUDA block per GPU, with its own
buffers and (for inter-node hops) its own NIC. NCCL splits each collective's buffer across channels.
Different channels cross between nodes on different NICs, so node egress = 8 × 50 GB/s = 400 GB/s; the
ring's busbw is limited by the busiest link class, so ≈ 350 GB/s = 88 % of 400 GB/s is consistent.

## 12.6 Variables

| Variable | Controls | Production template? |
|---|---|---|
| `NCCL_DEBUG` | log verbosity (`WARN`, `INFO`, …) | `WARN` yes; `INFO` only during start-up diagnosis |
| `NCCL_DEBUG_SUBSYS` | subsystems logged at INFO (`INIT`, `NET`, `GRAPH`, `TUNING`, `ENV`, …) | Only with INFO, for diagnosis |
| `NCCL_IB_HCA` | which RDMA devices/ports NCCL uses | Yes if needed, set by platform and validated; wrong lists halve bandwidth |
| `NCCL_SOCKET_IFNAME` | interface for bootstrap/socket transport | Yes (multi-homed hosts) |
| `NCCL_ALGO` | restrict algorithms | No (diagnosis only) |
| `NCCL_PROTO` | restrict protocols | No (diagnosis only) |
| `NCCL_TOPO_DUMP_FILE` | write detected topology XML | Acceptable (cheap) or diagnosis |
| `NCCL_IB_GID_INDEX` | RoCE GID index (RoCE version/IP family) | Yes, platform-wide value, when auto-selection is not used |

## 12.7 2,000 GB/s

The timer measured kernel *launch*, not execution: collectives are asynchronous with respect to the
host, so without `torch.cuda.synchronize()` (or CUDA events) before stopping the timer, the measured
time is microseconds of launch overhead. Fix: synchronize before starting and stopping the timer, warm
up first, and time many iterations. Also check the size computation (bytes vs elements).

## 12.8 Rows to bandwidth (c4, n = 32, factor 2 × 31/32 = 1.9375)

| Size | Time (µs) | algbw = S/t (GB/s) | busbw (GB/s) | Region |
|---|---|---|---|---|
| 1,048,576 | 43.08 | 1,048,576/43.08e−6/1e9 = 24.34 | 47.16 | latency (≤ 1.5 × 36 µs min; c4 latency region ends at 2 MiB) |
| 67,108,864 | 405.6 | 165.46 | 320.57 | bandwidth (≥ 0.8 × 349) |
| 4,294,967,296 | 23,762 | 180.75 | 350.20 | bandwidth |

Efficiency vs node NIC egress: 350.2/400 = **87.6 %**. Common mistake: comparing with 50 GB/s.

## 12.9 Buckets (α = 47 µs, B = 346 GB/s, n = 64, factor 1.96875)

(a) 4 MB: 47 + 1.969 × 4e6/346e9 s = 47 + 22.8 = **69.8 µs**; 25 MB: 47 + 142.3 = **189.3 µs**;
256 MB: 47 + 1,456.6 = **1,503.6 µs**. (b) n½ = α·B/factor = 47e−6 × 346e9 / 1.969 = **8.26 MB**.
(c) 4.375 GB / 25 MB = 175 buckets × 189.3 µs = **33.1 ms**; one message: 47 + 24,894 µs = **24.9 ms**.
Difference 8.2 ms ≈ 174 extra α payments × 47 µs. Buckets still win in practice because they overlap
with backward; the exposed cost is only the tail.

## 12.10 (O1) Collectives by hand

- all-reduce: all ranks **[13, 27, 41]**
- reduce (root R0): R0 **[13, 27, 41]**; R1, R2 unchanged
- reduce-scatter: R0 **[13]**, R1 **[27]**, R2 **[41]**
- all-gather of first elements: all ranks **[2, 1, 10]**
- broadcast (root R1): all ranks **[1, 3, 5]**
- all-to-all: R0 **[2, 1, 10]**, R1 **[4, 3, 20]**, R2 **[6, 5, 30]**

Ring trace (rank r sends chunk (r − k + 1) mod 3 to r + 1 in reduce-scatter step k):

| Step | R0→R1 | R1→R2 | R2→R0 | Buffers after step |
|---|---|---|---|---|
| RS 1 | c0 = 2 | c1 = 3 | c2 = 30 | R0 [2,4,36] R1 [3,3,5] R2 [10,23,30] |
| RS 2 | c2 = 36 | c0 = 3 | c1 = 23 | R0 [2,27,36] R1 [3,3,41] R2 [13,23,30] |
| AG 1 | c1 = 27 | c2 = 41 | c0 = 13 | R0 [13,27,36] R1 [3,27,41] R2 [13,23,41] |
| AG 2 | c0 = 13 | c1 = 27 | c2 = 41 | all [13,27,41] |

Bytes per rank: 4 steps × 4 B = **16 B**; formula 2(n − 1)/n × S = 4/3 × 12 B = **16 B** ✓.
Marking: 6 results (1 each), trace (3), byte count (1).

## 12.11 (O2) Result-set analysis (lab output)

| Config | Latency region | Bandwidth region | α (µs) | B (GB/s) | n½ (MB) | Plateau (GB/s) |
|---|---|---|---|---|---|---|
| c1 | 8 B – 1 MiB | ≥ 16 MiB | 14.1 | 448 | 3.6 | 449 |
| c2 | 8 B – 1 MiB | ≥ 32 MiB | 28.1 | 354 | 5.3 | 352 |
| c3 | 8 B – 1 MiB | ≥ 16 MiB | 39.2 | 185 | 3.9 | 184 |
| c4 | 8 B – 2 MiB | ≥ 32 MiB | 36.2 | 349 | 6.5 | 349 |
| c5 | 8 B – 2 MiB | ≥ 32 MiB | 47.3 | 346 | 8.3 | 345 |
| c6 | 8 B – 1 MiB | ≥ 16 MiB | 49.8 | 185 | 4.7 | 177 |

Scaling verdict (model answer): aligned multi-node plateau busbw is flat within 2 % from 2 to 8 nodes
(352 → 345 GB/s, 86–88 % of NIC egress), so the fabric scales for large messages; α grows ≈ 10 µs per
doubling of nodes (log-depth trees), so small-message collectives get slower with scale and n½ grows
from 5.3 to 8.3 MB — buckets below ≈ 8 MB on 64 ranks run at < 50 % of plateau. Two configurations
(c3, c6) are anomalous and must be excluded from the baseline. Note: a learner whose region
boundaries differ by one size step because they used different thresholds gets full marks if the
thresholds are stated. Plots must be log-log with labelled units.

## 12.12 (O3) Two rank mappings

(a) Prediction. c2: 8 NICs per node in use, every GPU↔NIC path `PIX`, GPUDirect RDMA on → ceiling 8 ×
50 = 400 GB/s; at ≈ 88 % efficiency ≈ 350 GB/s. c3 (`NCCL_IB_HCA` limited to mlx5_0–3): 4 NICs per node
→ ceiling 200 GB/s; ≈ 92 % → ≈ 185 GB/s; GPUs 4–7 reach NICs 2–3 across the inter-socket link (`SYS`),
GPUDirect RDMA disabled at that distance by default → staging through host memory → higher α
(+5–15 µs). (b) Data: c2 352 GB/s, α 28 µs; c3 184 GB/s, α 39 µs — consistent. (c) Evidence:

| Artifact | Command / source | If hypothesis true | Falsified if |
|---|---|---|---|
| NIC list in use | `NCCL_DEBUG=INFO`, line `NET/IB : Using …` | 4 devices listed in c3 | 8 devices listed |
| Environment | `cat /proc/<pid>/environ \| tr '\0' '\n' \| grep NCCL_` or job template | `NCCL_IB_HCA=mlx5_0,…,mlx5_3` and `NCCL_PXN_DISABLE=1` | variables unset / 8 devices / PXN enabled |
| Channel-to-NIC binding | INFO lines `Channel xx/0 : … via NET/IB/k[/GDRDMA]` | GPUs 4–7 via NET/IB/2–3 without GDRDMA | each GPU via its own NIC with GDRDMA |
| GPU↔NIC path type | `nvidia-smi topo -m` | GPU4↔mlx5_2 = `SYS` | `PIX` |
| Topology seen by NCCL | `NCCL_TOPO_DUMP_FILE=/tmp/topo.xml` | NICs 4–7 absent | all NICs present |
| Rail alignment of channels | INFO lines: exit and entry NIC index per channel (`via NET/IB/k` or PXN `NET/IB/k(p)`) | in c3, some channels exit/enter on NICs 2–3 only | every channel exits and enters on the same NIC index, all 8 used |
| NVLS on/off control (intra-node component) | rerun single-node and 2-node tests with `NCCL_NVLS_ENABLE=0` | intra-node part unchanged between c2 and c3 (difference is inter-node) | c3's deficit disappears or changes with NVLS off (problem is intra-node) |
| Traffic per NIC | per-NIC tx counters during the run (`ethtool -S`/`rdma statistic`, or switch port counters) | rails 4–7 idle | all rails carry ≈ equal traffic |

Marking: prediction with arithmetic 4, comparison 2, evidence table 6 (one per row, best six), falsification
column 3.

## 12.13 Lab

See `solutions/lab/README.md`. Expected labels: c3 `low_plateau_steady`, c6 `low_plateau_jittery`,
others `ok`.

## 12.14 Latency doubled, bandwidth fine

Ranked hypotheses: (1) algorithm/protocol restriction in the new image (e.g., `NCCL_ALGO=Ring` or
`NCCL_PROTO=Simple`): ring latency grows as 2(n − 1)α and Simple has the highest latency, while large
messages are unaffected — fits exactly; (2) proxy-thread or launch overhead from CPU affinity/frequency
changes (e.g., processes bound to the wrong NUMA node) — would raise latency, possibly modestly;
(3) different NCCL version with a tuning regression; (4) network latency increase (ECN/PFC changes) —
would usually affect bandwidth too. Tests: run with `NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=ENV,TUNING` and
look for lines like `NCCL_ALGO set by environment to Ring` (format varies) and the NCCL version banner;
diff `env | grep NCCL_` between images; re-run with the variable unset on a reserved node; check
`numactl --show` / process affinity. Root cause (model answer): the image's entrypoint exports
`NCCL_ALGO=Ring` left over from a debugging session. Fix: remove from the image under change control;
add an image lint that rejects `NCCL_ALGO`/`NCCL_PROTO` in production images. Validation: five launches
with 8 B time 47 ± 3 µs and plateau unchanged. Marking: hypotheses 4, tests 4, cause/fix 4,
validation 3.

## 12.15 Acceptance suite (marking guidance)

A strong answer includes: single-node `all_reduce_perf` and `all_gather_perf`/`reduce_scatter_perf`
8 B–8 GiB (NVLink/NVSwitch health; threshold ≥ 95 % of fleet median plateau, stating whether NVLS is assumed — ≈ 450 GB/s with NVLS, ≈ 360–380 GB/s ring-only); two-node pair tests with
a known-good reference node (NIC/rail health; ≥ 95 % of baseline, CV < 0.02); rail-pinned
one-GPU-per-node tests per rail (each rail at ≈ 45 GB/s busbw); periodic full 8-node and `alltoall_perf`
on idle windows; `#wrong == 0` everywhere; ≥ 5 launches, median and min reported; time budget (e.g.
≤ 15 min per node); artifacts (logs, NCCL INFO, topo dump, manifest); safety (only drained or
reserved nodes; never on rails shared with production during business hours). Defence paragraph must
weigh coverage against time and fabric impact.

## 12.16–12.19 Reflection (marking guidance)

- 12.16: it averages over all sizes including near-zero small-message rows; report plateau busbw
  (median of largest sizes) and small-message latency (p50 time at 8 B), plus n½.
- 12.17: algorithm/protocol switches (knees, sometimes non-monotonic busbw), channel-count changes
  between launches (bimodal results), NVLS/CollNet behaviour, PCIe/NVLink contention, congestion
  control dynamics (ECN/PFC), retransmission timing. Any three with appearance.
- 12.18: on an idle non-blocking fabric, cross-rail traffic finds idle spine capacity; in production,
  spines carry other jobs and ECMP collisions/congestion appear; misaligned GPU↔NIC paths also
  disable GPUDirect RDMA and consume inter-socket bandwidth that other work needs.
- 12.19: environment manifest (versions, firmware, topology, `NCCL_*` variables), node list, repeated
  launches with spread, warm-up/iteration counts, a baseline for comparison, and confirmation that the
  fabric was otherwise idle (or what else ran).
