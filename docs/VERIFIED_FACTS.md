# Verified Facts and Book-Wide Corrections

Independent reviewers record facts here that they checked against source code or primary documentation, and
errors they found repeated across several chapters. Every chapter must agree with this file. When you cite a
fact from this list, keep its `[VENDOR-SPEC, 2026-10]` label. Readers must still re-verify it against the release
they actually run.

## NCCL

| Topic | Correct statement |
|---|---|
| GPUDirect RDMA log lines | No NCCL release prints `NET/IB : GPU Direct RDMA Enabled/Disabled for HCA …`. Do not use that line. The topology code (`ncclTopoCheckGdr`) prints `GPU Direct RDMA Disabled for GPU <id> / HCA <id> (distance X > Y)` or `… Enabled for GPU <id> / HCA <id> (distance X <= Y), read N[ mode M]` at INFO level (2.18–2.28; newer builds may demote these lines to TRACE). These lines reflect the PCIe distance compared with `NCCL_NET_GDR_LEVEL`. They do **not** show whether a peer-memory module is present. |
| Reliable GDR evidence | Channel lines such as `Channel 00/0 : 0[0] -> 8[0] [send] via NET/IB/0/GDRDMA` show GDR in use. If `/GDRDMA` is absent, the path is host-staged. Check `lsmod \| grep nvidia_peermem` as well, and remember that DMA-BUF can provide GPUDirect RDMA without `nvidia_peermem`. |
| GDR distance gate | By default NCCL uses GPUDirect RDMA only when the GPU↔NIC distance is within the `NCCL_NET_GDR_LEVEL` threshold. Recent releases default to about PXB, so SYS/NODE-distance pairs are host-staged (verify per release, `[VENDOR-SPEC]`). A model that keeps GDR on at SYS distance must state that it assumes `NCCL_NET_GDR_LEVEL=SYS`. |
| PXN | PXN lets a GPU send through a NIC owned by a peer GPU on the same node over NVLink. Relevant controls include `NCCL_PXN_DISABLE`, `NCCL_P2P_PXN_LEVEL` and `NCCL_CROSS_NIC` (`[VENDOR-SPEC]`). "Nearest NIC vs forced remote NIC" is not the only choice: PXN is a third policy. PXN is used only through a peer GPU that is NVLink-connected to the source and reaches the NIC at ≤ PXB distance. That eligibility rule is separate from `NCCL_NET_GDR_LEVEL`. If the NIC is PHB/SYS from every GPU, PXN is never engaged. `NCCL_P2P_PXN_LEVEL` governs point-to-point/all-to-all traffic, not ring collectives (verify per release). |
| `NCCL_IB_TIMEOUT` default | 18 up to and including 2.22 (4.096 µs × 2¹⁸ ≈ 1.07 s per retry interval); 20 from 2.23 onward (≈ 4.3 s). Always state which version you assume. |
| `NCCL_IB_QPS_PER_CONNECTION` | Exists; default 1. |
| Single-node busbw (8 × H100-class, NVLink4) | Ring all-reduce algbw ceiling ≈ 450 / 1.75 ≈ 257 GB/s. A plain ring reaches busbw ≈ 360–380 GB/s; busbw above ≈ 400 GB/s implies NVLS (NVLink SHARP) is active (the single threshold used book-wide). Acceptance floors must state whether NVLS is assumed. |
| Multi-node busbw on ORION (8 × 400G NICs per node) | Expect ≈ 350+ GB/s busbw for a large all-reduce across nodes with all 8 rails. A per-rail figure is busbw ÷ 8, measured against the 50 GB/s line rate. |

## GPU telemetry

| Topic | Correct statement |
|---|---|
| Clock event reasons | Current drivers use `clocks_event_reasons.*` and the label "Clocks Event Reasons". `clocks_throttle_reasons.*` and "Clocks Throttle Reasons" are the deprecated names on older drivers. DCGM field: `DCGM_FI_DEV_CLOCKS_EVENT_REASONS` (formerly `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS`). |
| Xid 94 vs 95 | 94 = contained ECC error: drain when convenient, then reset. 95 = uncontained: drain immediately. |
| Throttle detection baseline | Judge throttling against the peers' *sustained* clock (≈ 1,830 MHz on ORION under dense training), not the 1,980 MHz max boost. `sw_power_cap` events are routine under heavy GEMMs. Exclude a run only when events affect a meaningful share of iterations (e.g. > 5 %) or the clock falls clearly below peers. MFU always uses the vendor dense peak; report any clock-adjusted efficiency separately. |
| HW vs SW thermal slowdown | HW slowdown triggers a few °C above the SW thermal (max operating) limit. Do not show HW slowdown active at temperatures where SW slowdown would already be active and HW slowdown would not. |

## Network

| Topic | Correct statement |
|---|---|
| ORION switch capacity | 64 × 400G = 25.6 Tb/s in use. A 51.2 Tb/s-class ASIC normally exposes 128 × 400G, or 64 × 800G cages. If you say "51.2T", say how the ports are configured. |
| Host MTU vs RoCE | RoCE packet size is set by the RDMA path MTU (e.g. 4096), not the IP MTU. A larger host IP MTU does not break RoCE. It black-holes TCP/UDP on the backend NIC if that NIC exceeds the switch MTU. A 1500 B netdev MTU caps `active_mtu` at 1024. |
| Switch MTU semantics | These vary by vendor. EOS/NX-OS L3 interface `mtu` = IP MTU. Junos media MTU includes the L2 header. Treat a "+22 B" rule as a conservative portable policy, not as a universal fact. |
| FRR ECMP width | `maximum-paths N` is capped by the build-time `MULTIPATH_NUM` (often 16) and by `zebra -e`. |
| 400GBASE-DR4 receive power | Receiver sensitivity/minimum average power ≈ −5.9 dBm (clause 124). Operational warnings must fire *before* that limit (e.g. warn ≈ −4 dBm, critical ≈ −5.9 dBm). Module-programmed alarm thresholds may be lower. |
| PCIe switch structure | A PCIe switch has one upstream port and several downstream ports. Each downstream port is a point-to-point bridge to exactly one device (or the next switch). Two devices can never sit under the same downstream bridge. "PIX" means the deepest common ancestor is a single switch. "PXB" means the path crosses more than one switch without traversing a host bridge. "PHB" means it goes through a PCIe host bridge (the CPU); "NODE" means it crosses host bridges within one NUMA node; "SYS" means it crosses the inter-socket link. ACS redirect settings that matter for P2P/GDR sit on the downstream ports above each device. |
| PCIe Gen5 achievable bandwidth | x16: ≈ 504 Gb/s raw, ≈ 400–440 Gb/s (50–55 GB/s) achievable. x8: ≈ 252 Gb/s raw, ≈ 200–220 Gb/s achievable. A NIC on a degraded x8 link tops out near 200–220 Gb/s, not 252. |
| RC go-back-N loss cost | A mid-stream loss triggers a NAK; recovery costs ≈ 1 RTT plus resending the in-flight window (≈ 200–250 KB on ORION). A lost **tail** packet (the last before the QP goes idle, or a lost final ACK) costs the ACK timeout, 4.096 µs × 2^timeout (≈ 4.3 s at 20, ≈ 1.07 s at 18). Timeout exposure is therefore per burst, not per message, for back-to-back traffic. |
| `ibv_rc_pingpong` defaults | 4,096 B messages, 1,000 iterations, path MTU 1,024 (`-m` changes it). A default run passes even when switch ports are at 1,500 MTU. |
| GPUDirect RDMA validation | Having `nvidia_peermem` loaded is not proof that GDR works. Also check ACS/IOMMU on the PCIe switch ports above the GPU and NIC (`lspci -vvv` ACSCtl), and run `ib_write_bw --use_cuda=<gpu>` per rail. |
| RDMA memory registration | `ibv_reg_mr` failures are commonly caused by locked-memory limits. Require `ulimit -l unlimited`, including inside Slurm and container limits. |
| FEC corrected-codeword alerting | 400G PAM4 with RS(544,514) carries ≈ 78 M codewords/s per port. A healthy link at pre-FEC BER ≈ 1e-6 can show hundreds of thousands of corrected codewords per second, so an absolute corrected-codeword threshold pages on healthy links. Alert on pre-FEC BER (and its trend), on high symbol-error histogram bins approaching the correction limit (15 symbols), and on FCS/uncorrectable counts. Treat corrected-codeword growth as an early-warning trend. |
| Alert scoring | When scoring detectors against injected faults, match an alert to a fault only if it fires within [onset, onset + tolerance]. Count alerts before onset as false positives. Report detection latency from onset. |
| Inter-token latency vs TPOT | TPOT is a per-request mean. ITL is the per-token gap distribution (report p95/p99). Chunked or unchunked prefill stalls show up in ITL tails and can be hidden by mean TPOT. |
| Slurm QOS limits | QOS limits such as `GrpTRES` are enforced only with `AccountingStorageType=accounting_storage/slurmdbd` and `AccountingStorageEnforce` that includes `limits,qos`. |

## Distributed training operations

| Topic | Correct statement |
|---|---|
| Spare nodes on ORION-256 | ORION-256 has **no spare nodes**: W-TRAIN uses all 32 nodes / 256 GPUs. When a node must leave, the choices are (a) wait for repair; (b) restart at reduced DP, e.g. DP = 7 (224 GPUs, −12.5 %), which needs a global batch divisible by the new DP or a batch/LR adjustment; or (c) a spare pool declared explicitly as a variation from the reference cluster. Compare degraded-loss × time-to-repair against restart cost (≈ 64 GPU-h at 900 s) plus any shrink shortfall. |
| Drain vs running job | `scontrol update … state=drain` (or a Kubernetes cordon) stops new placement. It does **not** move a running job. Moving the job requires a checkpoint followed by a requeue or elastic restart. |
| Rail-aligned rings and PXN | On rail-optimized systems NCCL keeps a channel's exit and entry on the same NIC index (rail). When the GPU at a node boundary is not local to that rail's NIC, PXN forwards the data over NVLink to the GPU that owns the right NIC. A ring that exits on NIC 7 and enters the next node on NIC 0 is cross-rail and goes through the spine. `NCCL_CROSS_NIC` controls whether cross-NIC rings are allowed. |
| DP gradient overlap window | With pipeline parallelism, only the last micro-batch's backward pass can hide the DP reduce-scatter/all-reduce. On W-TRAIN that window is ≈ 70 ms, so most DP time is exposed. Model exposure as max(0, T_DP − T_window), not as a fixed overlap percentage. |
| Single-node ring busbw vs NVLS | A plain ring reaches busbw ≈ 0.80–0.85 × 450 ≈ 360–380 GB/s. Busbw above ≈ 400 GB/s (often near 450 GB/s, ≈ 100 % of link) implies fewer bytes per GPU, i.e. NVLS. To prove it, rerun with `NCCL_NVLS_ENABLE=0` (expect ≈ 360 GB/s) and check the INFO log for NVLS initialisation. |
| OOMKilled vs GPU OOM | Kubernetes `OOMKilled` / exit code 137 is a host-memory (cgroup) kill, not a GPU out-of-memory. A GPU OOM appears as a CUDA error ("CUDA out of memory") in the process log. Under vLLM, `DCGM_FI_DEV_FB_USED` near 100 % is normal, because vLLM pre-allocates `--gpu-memory-utilization` (default 0.9) of HBM for weights and KV cache at start-up. |
| MPS isolation | On Volta and later, each MPS client has its own GPU virtual address space, but MPS gives no fault isolation (a fatal fault in one client can affect all clients of that server) and no memory-bandwidth or cache QoS. `CUDA_MPS_ACTIVE_THREAD_PERCENTAGE` limits SMs only. MIG is the option with hardware isolation (`[VENDOR-SPEC]`). |
| Checkpoint waste vs interval | Waste ≈ C/τ + (τ/2 + R)/MTBF, where R is restart time. The R/MTBF term does not depend on τ, so it leaves the optimum τ ≈ √(2·C·MTBF) unchanged; chapters may drop it when only comparing intervals, but must say so. The τ term is linear, not quadratic. Young/Daly is a first-order result and is invalid once τ approaches MTBF. Report an "invalid" flag rather than a number in that case. |

## Book-wide numbers

| Topic | Canonical value |
|---|---|
| Reliability | See REFERENCE_CLUSTER.md: node MTBF 1,536 h; 256-GPU job 48 h (= 1,536 / 32); ORION-XL 3 h; restart **≈ 15 min (900 s)**. Do not use 600 s or "1 failure per 50 node-days" unless you label it as a deliberate variation. |
| Frontend oversubscription | 3:1 by port count, 1.5:1 by bandwidth (200G hosts, 400G uplinks). |
| Names | See REFERENCE_CLUSTER.md "Canonical names" (`orion-nNN`, `rack-NN`, `orion-be-leaf-rR`, `orion-be-spine-S`). |

## G4 verification additions (2026-10-30)

Merged from the per-group reports in [verification/](verification/). Each row was checked against primary source, either code at a tagged release or official docs. Where two reports disagreed, the coordinator re-checked the source; the result is noted in the row.

### NCCL

| Topic | Correct statement |
|---|---|
| IB completion WARN format | Re-checked in `src/transport/net_ib.cc` at the v2.19.4-1, v2.20.5-1, v2.21.5-1, v2.22.3-1 and v2.23.4-1 tags. Formats by release: ≤ 2.19 `NET/IB : Got completion from peer … with error N, opcode N, len N, vendor err N (…)`; 2.20–2.21 `NET/IB : … with status=N opcode=N len=N vendor err N (…)` with no `hca` field; **2.22+** `NET/IB: … status=N … hca mlx5_N` (no space before the colon); named status codes `status=<name>(N) opcode=<name>(N) vendor_err=N … hca …` from v2.28.9-1, with `qp_num=N` from v2.32.3-1 (checked in the tagged source). Status 12 = `IBV_WC_RETRY_EXC_ERR`. Parsers must accept `NET/IB ?:` and both `error N,` and `status=`. |
| `NCCL_MIN/MAX_NCHANNELS` | Deprecated since 2.17 in favour of `NCCL_MIN_CTAS` / `NCCL_MAX_CTAS`. |
| `NCCL_NVLS_ENABLE` | Since 2.17. Values 0/1/2; default 2 (use NVLS if supported, do not fail). |
| `NCCL_CROSS_NIC` | Default 2 (prefer same NIC, allow a different NIC if faster); 0 = same NIC only; 1 = allow different. |
| `NCCL_ALGO` names | Ring, Tree; CollnetDirect/CollnetChain (2.14+); NVLS (2.17+); NVLSTree (2.18+); PAT (2.23+). |
| `NCCL_IB_HCA` matching | Names are prefixes unless the list starts with `=`; `^` makes the list an exclude list. `^mlx5_1` also excludes `mlx5_10`–`mlx5_19`; use `^=mlx5_1`. |
| P2P channel lines | `via P2P/CUMEM` (≥ 2.19, cuMem on by default), `via P2P/IPC` (cuMem off or older releases), `via P2P/direct pointer` (same process). |
| PXN channel line | `… via NET/IB/<netDev>(<proxyRank>)/GDRDMA`; the number in parentheses is the proxy rank. |
| nccl-tests `-w` | Warm-up defaults to 1 and `-n` to 20. Pass `-w` explicitly whenever a warm-up policy is claimed. |

### GPU, DCGM, host

| Topic | Correct statement |
|---|---|
| H100 SXM peaks | Dense BF16 ≈ 989 TFLOP/s and dense FP8 ≈ 1,979 TFLOP/s; the datasheet's 1,979 / 3,958 figures are *with sparsity*. 80 GB HBM3 at 3.35 TB/s; NVLink4 900 GB/s total = 450 GB/s per direction; up to 700 W. DGX H100-class node maximum is 10.2 kW. |
| DCGM 4.6 field renames | `PROF_SM_ACTIVE`→`PROF_SM_UTIL_RATIO`, `PIPE_TENSOR_ACTIVE`→`TENSOR_UTIL_RATIO`, `DRAM_ACTIVE`→`DRAM_UTIL_RATIO`, `GR_ENGINE_ACTIVE`→`GR_ENGINE_UTIL_RATIO`, and similar. The old names remain aliases with the same IDs (1001–1008), so the tables and labs in this book keep the old names. |
| DCGM 4.7 deprecations | `DCGM_FI_DEV_GPU_UTIL` (203, %) → `DCGM_FI_DEV_GPU_UTIL_RATIO` (1613, 0–1). `POWER_VIOLATION`/`THERMAL_VIOLATION` (240/241) → `DCGM_FI_DEV_GPU_POWER_THROTTLE_SECONDS_TOTAL` (1617) / `DCGM_FI_DEV_GPU_THERMAL_THROTTLE_SECONDS_TOTAL` (1618), in seconds (verified in `dcgm_fields.h` at tag v4.7.0; absent in v4.6.1; siblings 1619–1624). The units of 240/241 are µs in 3.x and ns in 4.x headers. |
| DCGM ECC/row remap | `ECC_SBE_VOL_TOTAL` 310, `ECC_DBE_VOL_TOTAL` 311, `ROW_REMAP_FAILURE` 395, `ROW_REMAP_PENDING` 396. A pending remap takes effect only after a GPU reset. |
| SM activity during collectives | SM_ACTIVE/TENSOR_ACTIVE drop during collective waits because NCCL kernels occupy only a few SMs (one block per channel) and issue no tensor work. They do not drop because SMs "idle in spin loops". |
| nvidia-smi v590 | "Driver Version"/"CUDA Version" in `-q` output are deprecated in favour of "KMD Version"/"CUDA UMD Version". |
| lspci annotations | pciutils 3.6–3.7 print `(ok)`/`(downgraded)`; 3.8+ print nothing for a healthy link and only `(downgraded)`/`(overdriven)` otherwise. Compare numbers, never annotations. |
| cpufreq `powersave` | Dynamic only with active-mode `intel_pstate` and `amd-pstate-epp`. With `acpi-cpufreq`, `intel_cpufreq` or passive `amd-pstate` it pins the minimum frequency. |
| GDS check | `/usr/local/cuda-<ver>/gds/tools/gdscheck.py -p`. |

### Network and physical layer

| Topic | Correct statement |
|---|---|
| perftest latency | `ib_*_lat` reports RTT/2 for SEND/WRITE and the full round trip for READ/ATOMIC. `-a` sweeps 2 B–2²³ B; `-m` defaults to active_mtu. |
| DCQCN paper parameters | g = 1/256, N = 50 µs, K = T = 55 µs, B = 10 MB, F = 5, Kmin 5 KB, Kmax 200 KB, Pmax 1 % (Zhu et al. 2015). NIC defaults differ. |
| ethtool module labels | Threshold label is `Laser rx power low warning threshold`. CMIS per-lane labels: `Rcvr signal avg optical power (Channel n)`, etc. OSFP identifier 0x19. |
| FRR RFC 8212 | `bgp ebgp-requires-policy` is on under the `traditional` profile and off under `frr defaults datacenter`. |
| SONiC | Port MTU default 9100. `show interfaces counters fec-stats` adds FEC_PRE_BER/FEC_POST_BER/FLR/FEC_MAX_T columns on current builds. |

### Training, storage, serving, orchestration

| Topic | Correct statement |
|---|---|
| PyTorch flight recorder | `TORCH_FR_BUFFER_SIZE` (fallback `TORCH_NCCL_TRACE_BUFFER_SIZE`; 0 disables), `TORCH_FR_DUMP_TEMP_FILE` (legacy `TORCH_NCCL_DEBUG_INFO_TEMP_FILE`), `TORCH_NCCL_DUMP_ON_TIMEOUT`. |
| PyTorch PG timeout | `init_process_group` default timeout is 10 min for NCCL and 30 min for other backends (2.15 docs). |
| DDP `bucket_cap_mb` | Default `None`, which selects 25 MiB. |
| DCP | `*.distcp` data files plus `.metadata`. `async_save` returns a `Future` or an `AsyncSaveResponse` (separate staging and upload futures). |
| Megatron async save | On current main, `--async-save` needs `--use-persistent-ckpt-worker`, and fully parallel save is on by default. |
| S3 throttling | Requests above the current request rate can get `503 Slow Down` while S3 scales. Bursts are not rejected deterministically. |
| vLLM | V1 metric `vllm:kv_cache_usage_perc` replaces V0 `vllm:gpu_cache_usage_perc`. The current `--gpu-memory-utilization` default is 0.92 (older releases used 0.90); always set it explicitly. |
| Kueue | `kueue.x-k8s.io/v1beta2` is served from v0.15; v0.20 no longer serves v1beta1. The cohort field is `spec.cohortName` (v1beta1 `spec.cohort`). |
| Kubernetes | DRA core API GA in 1.34 as `resource.k8s.io/v1`. Topology Manager stable since 1.27. |
| GFD labels | `nvidia.com/cuda.driver.major` etc. are deprecated; use `nvidia.com/cuda.driver-version.major`. |
| Slurm | `topology/block` from 23.11 (reworked 24.05); multiple topologies via `topology.yaml` from 25.05. |
| Xid | 63 row-remap event, 64 row-remap failure, 92 excessive SBE rate, 119/120 GSP RPC timeout/GSP error, 154 recovery action changed. |
