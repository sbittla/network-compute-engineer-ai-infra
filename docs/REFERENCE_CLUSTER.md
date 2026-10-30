# The ORION Reference Cluster (Running Example)

Every chapter uses one running example so that concepts connect across layers: **ORION**, a
256-GPU training and inference cluster operated by **Halcyon AI**, a fictional AI company. All values
below are `[ILLUSTRATIVE]` H100-class approximations chosen for teaching. Where a value approximates a
public vendor specification it is marked `[VENDOR-SPEC, 2026-10]`; readers must re-verify against the
current datasheet for any real platform. Chapters may *vary* a parameter for an exercise, but must say
so explicitly.

## 1. Node: `HX8` (8-GPU training/inference server)

| Component | Value | Notes |
|---|---|---|
| CPUs | 2 sockets × 56 cores (112 cores, 224 threads) | 2 NUMA nodes (one per socket, NPS1) |
| System memory | 2 TiB DDR5 (1 TiB per socket) | |
| GPUs | 8 × H100-SXM-class, 80 GB HBM3 each (640 GB/node) | `[VENDOR-SPEC, 2026-10]` class values |
| GPU HBM bandwidth | ≈ 3.35 TB/s per GPU | `[VENDOR-SPEC, 2026-10]` |
| GPU dense BF16 tensor peak | ≈ 989 TFLOP/s per GPU (≈ 1,979 dense FP8) | Dense (no sparsity) `[VENDOR-SPEC, 2026-10]` |
| GPU TDP | 700 W | |
| GPU SM clock | Max boost ≈ 1,980 MHz `[VENDOR-SPEC, 2026-10]`; typical sustained under dense training ≈ 1,830 MHz `[ILLUSTRATIVE]` | When comparing a throttled GPU with its peers, use the peers' *sustained* clock and say which one you used |
| Scale-up | NVLink 4th gen via 4 NVSwitch chips: 18 links/GPU, 900 GB/s total bidirectional (450 GB/s per direction) per GPU | All-to-all within node |
| PCIe | Gen5 x16 to each GPU and compute NIC: ≈ 63 GB/s per direction theoretical, ≈ 50–55 GB/s achievable `[ILLUSTRATIVE]` | |
| Compute (backend) NICs | 8 × 400 Gb/s single-port RDMA NICs (ConnectX-7-class), one per GPU; NIC *i* is on rail *i* | 400 Gb/s = 50 GB/s line rate |
| Frontend/storage NICs | 2 × 200 Gb/s (one per socket) | Storage, control, ingress |
| Local NVMe | 8 × 3.84 TB U.2 NVMe (≈ 30.7 TB raw), 4 per socket | Scratch, dataset cache, checkpoint staging |
| Management | 1 GbE BMC (Redfish/IPMI) | Out-of-band network |
| Node power | ≈ 10.2 kW max; ≈ 8–9 kW sustained under training `[ILLUSTRATIVE]` | |

### PCIe / NUMA topology of `HX8`

```text
            Socket 0 (NUMA 0)                              Socket 1 (NUMA 1)
     ┌──────────────┴──────────────┐                ┌──────────────┴──────────────┐
  PCIe SW0                     PCIe SW1          PCIe SW2                     PCIe SW3
  ├ GPU0  ├ NIC0 (rail 0)      ├ GPU2 ├ NIC2     ├ GPU4 ├ NIC4                ├ GPU6 ├ NIC6
  └ GPU1  └ NIC1 (rail 1)      └ GPU3 └ NIC3     └ GPU5 └ NIC5                └ GPU7 └ NIC7
  Socket 0 root ports also: FE-NIC0 (200G), NVMe0–3 | Socket 1: FE-NIC1 (200G), NVMe4–7
  All 8 GPUs are additionally connected through 4 NVSwitch chips (NVLink, all-to-all).
  Sockets connected by the inter-socket link (UPI/xGMI-class).
```

*Figure R.1 — HX8 host topology. GPU i and NIC i share a PCIe switch: the "PIX" relationship in
`nvidia-smi topo -m` terms. GPU0↔NIC2 crosses root ports on the same socket ("PXB"/"PHB"-class);
GPU0↔NIC4 crosses the inter-socket link ("SYS").*

## 2. Cluster: `ORION-256`

| Item | Value |
|---|---|
| GPU nodes | 32 × HX8 = **256 GPUs** |
| Racks | 8 GPU racks × 4 nodes (≈ 41 kW IT per rack at max node power) + 2 network racks + 2 storage racks + 1 management rack |
| Backend (compute) fabric | Rail-optimized 400 GbE RoCEv2, 2-tier leaf-spine. 8 rail leaves (one per rail), each 64 × 400G ports: 32 down to node NIC *r* of every node, 32 up. 4 spines × 64 × 400G; each leaf has 8 uplinks to each spine. **1:1 (non-blocking)**. 64 × 400G = **25.6 Tb/s** of switching capacity in use per switch. Assume one 400G port per cage (either a 25.6 Tb/s-class ASIC, or a 51.2 Tb/s-class ASIC with 64 × 800G cages each running at 400G; the latter leaves headroom for an 800G refresh). |
| Backend alternative | InfiniBand NDR (400 Gb/s) with an equivalent rail-optimized fat tree — used in comparison exercises |
| Frontend/storage fabric | 2 × 200 GbE per node, dual-homed to a pair of frontend leaves; eBGP leaf-spine. Each frontend leaf: 48 × 200G host-facing ports and 16 × 400G uplinks, which is 3:1 by port count but **1.5:1 by bandwidth** (9.6 Tb/s down : 6.4 Tb/s up); with only 32 hosts per leaf populated it is 1:1 |
| OOB management | 1 GbE BMC network, separate switches |
| Storage | Parallel file system on 8 storage servers: ≈ 160 GB/s aggregate read, ≈ 80 GB/s aggregate write `[ILLUSTRATIVE]`; object store for datasets and checkpoint archive |
| Scheduling | Slurm for the training partition; Kubernetes for inference and platform services. By default the 32 nodes are split 24 training (`orion-n01`–`n24`, racks 01–06) + 8 inference (`orion-n25`–`n32`, racks 07–08) (Chapter 17). A full-size W-TRAIN run (all 32 nodes) borrows the inference nodes through a lifecycle transition. **There are no spare nodes outside these 32.** A chapter that wants a spare pool must declare it as an explicit variation. |

### Canonical names (use these in every chapter, lab dataset, and capstone)

| Object | Name pattern | Example |
|---|---|---|
| GPU node | `orion-nNN` (01–32; ORION-XL: `orionxl-nNNN`, 001–512) | `orion-n13` |
| Rack | `rack-NN` (01–08 GPU racks; 4 nodes each: rack-01 = n01–n04) | `rack-04` |
| Backend rail leaf | `orion-be-leaf-rR` (R = rail 0–7) | `orion-be-leaf-r3` |
| Backend spine | `orion-be-spine-S` (S = 1–4) | `orion-be-spine-2` |
| Frontend leaf / spine | `orion-fe-leaf-NN`, `orion-fe-spine-S` | `orion-fe-leaf-01` |
| Compute NIC / rail | NIC *i* ↔ GPU *i* ↔ rail *i* (0–7); Linux RDMA device `mlx5_i` `[ILLUSTRATIVE]` | `mlx5_3` |

### Addressing and routing plan (used in Chapters 7–10)

| Network | Plan |
|---|---|
| Backend, rail *r* | Host NIC ↔ leaf as routed /31: `10.100.r.(2n)/31` for node *n* (leaf side even, host side odd). Host routes `10.100.0.0/16` via its rail gateway per NIC (policy routing per rail). |
| Backend, leaf ↔ spine | Routed /31s from `10.101.<spine>.0/24` (spine side even, leaf side odd), one /31 per physical uplink (as defined in Chapter 7) |
| Loopbacks | `10.255.0.0/24` (spines `.1–.4`, rail leaves `.11–.18`) |
| Frontend | `10.10.0.0/16` |
| OOB | `172.16.0.0/16` |
| BGP ASNs (backend) | Spines share AS 65100; each rail leaf unique AS 65101–65108 (RFC 7938-style eBGP). |
| MTU | Switch ports 9216; host IP MTU 9000; RDMA path MTU 4096 |
| Backend RTT `[ILLUSTRATIVE]` | ≈ 4 µs same-rail (host → leaf → host); ≈ 5 µs cross-rail via a spine. Use 5 µs as the worst case in PFC headroom sizing. At 400 Gb/s the bandwidth-delay product is ≈ 200 KB same-rail and ≈ 250 KB cross-rail. |
| RoCE QoS `[ILLUSTRATIVE]` | RoCE data DSCP 26 → traffic class 3, lossless (PFC on priority 3) with ECN marking; CNP DSCP 48 → TC 6 strict priority; all other traffic lossy |

### Software baseline `[ILLUSTRATIVE — verify against current vendor compatibility matrices]`

Ubuntu 22.04/24.04 LTS; NVIDIA data-center driver 550/570-series; CUDA 12.x; NCCL 2.2x;
PyTorch 2.x; vendor RDMA stack (MLNX_OFED/DOCA-host class) with matching NIC firmware; Slurm 23.x/24.x;
Kubernetes 1.30+ with the NVIDIA GPU Operator/device plugin; Prometheus + Grafana; DCGM exporter.

## 3. Reference workloads

### W-TRAIN — 70B dense transformer pretraining

| Parameter | Value |
|---|---|
| Model | Decoder-only transformer, 70 × 10⁹ parameters, 80 layers, hidden 8192, 64 query heads, 8 KV heads (GQA), head dim 128 |
| Sequence length / global batch | 4,096 tokens × 1,024 sequences ≈ 4.19 M tokens per step |
| Precision | BF16 mixed precision, Adam |
| Training-state memory | ≈ 16 B/param → ≈ 1.12 TB (2 B weights + 2 B grads + 12 B fp32 master/m/v) `[MODELED]` |
| Checkpoint size (weights + optimizer) | ≈ 14 B/param → ≈ 980 GB `[MODELED]` |
| Baseline parallelism | TP = 8 (inside the NVLink domain), PP = 4, DP = 8 → 256 GPUs |
| Step compute | ≈ 6 × N × tokens = 6 × 70e9 × 4.19e6 ≈ 1.76 × 10¹⁸ FLOP `[MODELED]` |
| Step time at 40 % MFU | 1.76e18 / (256 × 989e12 × 0.40) ≈ 17.4 s `[MODELED]` |

### W-INFER — 70B chat model serving

| Parameter | Value |
|---|---|
| Model | Same architecture as W-TRAIN |
| Weights | BF16: ≈ 140 GB; FP8: ≈ 70 GB |
| KV cache per token | 2 (K,V) × 80 layers × 8 KV heads × 128 dim × 2 B = 327,680 B ≈ **320 KiB/token** (BF16) `[MODELED]` |
| KV cache per 4,096-token sequence | ≈ 1.34 GB `[MODELED]` |
| Serving baseline | TP = 8 on one HX8 (BF16) or TP = 4 (FP8); continuous batching; paged KV cache |
| SLO targets `[ILLUSTRATIVE]` | TTFT p95 ≤ 800 ms for 2k-token prompts; TPOT p95 ≤ 50 ms; availability 99.9 % |

### Reliability assumptions (canonical, `[ILLUSTRATIVE]`)

Use these in every chapter that computes checkpoint intervals, lost work, or recovery cost
(Chapters 11, 14, 19, 21, 23, and Capstones F/G) so the numbers agree across the book:

| Quantity | Value |
|---|---|
| Job-interrupting failure rate per HX8 node | MTBF ≈ 1,536 node-hours (≈ 64 days) — includes GPU, NIC/HCA, host, and link faults attributable to the node |
| 256-GPU (32-node) synchronous job | MTBF ≈ 1,536 / 32 = **48 h** |
| 4,096-GPU (512-node, ORION-XL) job | MTBF ≈ 1,536 / 512 = **3 h** |
| Restart overhead (detect + reschedule + restore + warm-up) | ≈ 15 min for ORION-256 |

These are deliberately conservative teaching values that make failure frequency visible. They are in
the same order of magnitude as published large-scale training reports (for example, the Llama 3 paper,
Meta 2024, reports roughly one unexpected interruption every ~3 hours on a ~16k-GPU job). Real fleets
vary widely.

### Repair, power and facility constants (canonical, `[ILLUSTRATIVE]`)

| Quantity | Value | Source chapter |
|---|---|---|
| Node repair turnaround (MTTR, drain → return to service) | **5 days** → ORION-256 averages 0.5 failures/day × 5 d ≈ **2.5 nodes in repair** (Poisson) | Ch 16 |
| Spare sizing method | Poisson quantile of the in-repair count (e.g. P(≤ k) at the target), placed *outside* the production partition and declared as a variation | Ch 16 |
| Node power model | 10.2 kW max = **4.6 kW base** (CPUs, memory, NICs, NVMe, fans, PSU loss) + 8 × 700 W GPU. Under a GPU cap *P*: node ≈ 4.6 kW + 8·*P* | Ch 2, Ch 21 |
| Sustained training node power | ≈ 8.5 kW | Ch 2 |
| Rack circuits | 415 V 3-phase 60 A, power factor 0.95, NEC 80 % → **32.78 kW per circuit**; 2 circuits per side → **65.55 kW per side** (2N A/B feeds) | Ch 2 |
| PUE | **1.25** (liquid-assisted hall). Any other value must be labelled as a variation | Ch 2, Ch 21 |
| Facility power for the 32 GPU nodes | IT ≈ 326 kW max for the nodes alone. Facility = IT × PUE | Ch 2, Ch 21 |

## 4. Scale-out variant: `ORION-XL`

512 HX8 nodes (4,096 GPUs), rail-optimized backend with a 3-tier (or larger 2-tier) Clos. Used for
fault-tolerance and large-scale reliability material (Chapter 19, Capstone G). With the canonical
reliability assumptions above, a full-cluster synchronous job is interrupted roughly every 3 hours
(≈ 8 interruptions per day), and some GPU, NIC, optic, or link fault is effectively always in progress
somewhere in the fleet.

ORION-XL conventions:
- Names: nodes `orionxl-nNNN` (001–512); pods `pPP` (p00–p15, 32 nodes each); rail leaves `orionxl-be-leaf-pPP-rR`; spines `orionxl-be-spine-pPP-SS` (pod spines) and `orionxl-be-core-CC` (third tier).
- Backend addressing: host links on rail R use `10.(130+R).0.0/16` (10.130–10.137). Leaf–spine and spine–core /31s come from `10.120.0.0/14`. Neither collides with ORION-256's `10.100.r.0/24` host links or its `10.101.<spine>.0/24` leaf–spine block.
- Any spare pool (e.g. `orionxl-s00`–`s31`) is a declared variation, sized with the Ch 16 Poisson method.
- Elastic training granularity is one DP replica (TP × PP GPUs). With TP = 8 and PP = 8, one lost node removes a whole 8-node replica, and DP must still divide the global batch.

## 5. Organisation (for incident and operations scenarios)

Halcyon AI teams: **Fabric** (network), **Fleet** (bare-metal lifecycle), **Platform** (Kubernetes,
Slurm), **Training Infra**, **Inference**, **SRE**, and **Facilities** (power/cooling, MEP).
Incidents use severity SEV1–SEV4 and a blameless postmortem template (Chapter 18).
