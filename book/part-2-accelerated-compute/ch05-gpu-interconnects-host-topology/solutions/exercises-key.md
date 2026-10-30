# Chapter 5 — Answer Key (INSTRUCTOR ONLY)

Values from REFERENCE_CLUSTER.md and manuscript Tables 5.1–5.4. Modeled numbers use the formula of
Section 5.9; each was computed by hand and re-checked with Python. Deduct for missing units, labels or
arithmetic.

---

## Knowledge checks

**5.1** BDF = PCI domain:bus:device.function, the enumeration address of a PCIe function. It reflects
where the device enumerated (bus numbers assigned by firmware/OS), not the labelled physical slot; the
same slot can get a different bus after a BIOS change, and two platforms can map slots to buses
differently. Slot sources: `lspci -vmm` `PhySlot:` (or `lspci -v` "Physical Slot"), `dmidecode -t slot`,
or `/sys/bus/pci/slots/*/address`.

**5.2** PIX: at most a single PCIe bridge; PXB: multiple PCIe bridges without traversing the host bridge;
PHB: PCIe plus a PCIe host bridge (typically the CPU); NODE: PCIe plus the interconnect between host
bridges within a NUMA node; SYS: PCIe plus the SMP interconnect between NUMA nodes. Best → worst: PIX <
PXB < PHB < NODE < SYS, because each step adds bridges/root-complex/inter-socket traversal, lowering
achievable P2P bandwidth and raising variance; at SYS, GDR may be refused (`NCCL_NET_GDR_LEVEL`).

**5.3** nvidia-smi numbers NIC *columns* in PCI bus order (frontend NIC at bus `0d` → `NIC0`), while RDMA
device names are assigned by the kernel/udev (ORION pins `mlx5_i` to rail *i* by naming rules). Neither a
column index nor a device name is evidence of where a cable goes. Authoritative for the rail: the LLDP
neighbour (`orion-be-leaf-rR`) cross-checked against the cabling database.
*Common mistake:* "NIC1 = rail 1".

**5.4** 18 NVLink4 links × 25 GB/s = 450 GB/s per direction per GPU, spread across four NVSwitch chips,
so every GPU pair is one switch hop at full bandwidth → `NV18` everywhere. It says nothing about GPU↔NIC
locality, which is purely a PCIe question.

**5.5** ACS Request/Completion Redirect forces peer requests from a switch downstream port up to the root
complex so the IOMMU can validate them; VMs need this to stop a passed-through device from DMAing into
another guest's device. On bare metal it converts a one-hop in-switch GPU↔NIC P2P into a root-complex
round trip, reducing bandwidth and adding variance (or breaking P2P on some platforms).

**5.6** (1) Platform P2P support, GPU and NIC under one switch; (2) peer-memory mechanism — `nvidia_peermem`
(legacy `nv_peer_mem`) **or** a verified DMA-BUF path (no `nvidia_peermem` needed); (3) supported driver/
CUDA/NCCL/NIC driver/firmware combination; (4) IOMMU per vendor guidance (often `iommu=pt`); (5) no ACS
redirect on the GPU/NIC switch ports; (6) runtime proof: NCCL channel lines ending `/GDRDMA`, or
`ib_write_bw --use_cuda`. The `GPU Direct RDMA Enabled for GPU … / HCA … (distance X <= Y)` lines are only
the distance check and are **not** sufficient evidence. *Marking:* deduct if the learner cites a
"NET/IB : GPU Direct RDMA Enabled for HCA" line (no NCCL release prints it).

**5.7** Host memory for staging/pinned buffers (`numactl --hardware`, `numastat -p <pid>`); CPU threads of
the rank, NCCL proxy and loaders (`taskset -cp <pid>`, topo -m CPU Affinity); NIC interrupts
(`/proc/interrupts`, `/proc/irq/<n>/smp_affinity_list`).

## Worked problems

**5.8**
(a) Gen4 x16: 16 × 10⁹ × 128/130 × 16 / 8 = **31.5 GB/s**; Gen5 x8: 32 × 10⁹ × 128/130 × 8 / 8 = **31.5 GB/s**;
Gen5 x16: **63.0 GB/s** (per direction, after encoding).
(b) A 400 Gb/s NIC needs 50 GB/s payload per direction: only Gen5 x16 (achievable ≈ 50–55 GB/s, tight).
Gen4 x16 and Gen5 x8 cap it at ≈ 25–27 GB/s achievable (≈ 200–215 Gb/s) after packet overheads.
(c) With GDR the NIC↔GPU DMA stays inside the switch: uplink carries only control traffic (doorbells,
completions, small CPU-side buffers) — essentially 0 of the 2 × 50 GB/s. Host-staged: in each direction
both the GPU↔host copy and the NIC↔host DMA cross the uplink. With both NICs sending and receiving at
line rate, the upstream direction carries GPU D2H for sends (2 × 50) plus NIC writes of received data
(2 × 50) = 200 GB/s of demand against 63 GB/s; the uplink caps each NIC at ≈ 63 / 4 ≈ 16 GB/s per
direction `[MODELED]` — consistent with the model's 18 GB/s host-staged cap.

**5.9** ring factor 2 × 255/256 = 1.99219; per-ring bytes 134,217,728.
(a) *t* = 1.99219 × 134,217,728 / 48 × 10⁹ + 0.2 ms = 5.571 + 0.2 = 5.771 ms → busbw = 1.99219 × 1,073,741,824 /
5.771 × 10⁻³ = **370.7 GB/s**.
(b) Only the ring for that NIC's rail is slow, but the slowest ring sets the collective: 1.99219 × 134,217,728 = 267,386,880 B;
/ 27 × 10⁹ B/s = 9.903 ms → + 0.2 ms = 10.10 ms → busbw = 1.99219 × 1,073,741,824 / 10.10 × 10⁻³ = **211.7 GB/s**.
(c) All eight rings pass through the node: 14.855 + 0.2 = 15.055 ms → **142.1 GB/s**.
(d) Every ring visits every node, and a synchronous ring runs at its slowest member: one node with
eight slow NIC paths slows all eight rings, so 1/32 of the nodes costs 62 % of the bandwidth. Averages
over nodes are the wrong mental model for collectives. All `[MODELED]`.

## Hands-on lab (5.10) — expected results

Reference output (`solutions/lab/topo_mapper.py`):

| Scenario `[MODELED]` | Median (ms) | p99 (ms) | busbw (GB/s) | CV |
|---|---|---|---|---|
| S1 aligned, 16 healthy | 6.05 | 6.17 | 352.3 | 0.008 |
| S2 cross-socket, 16 healthy (SYS → host-staged by the GDR gate) | 52.25 | 74.18 | 40.8 | 0.269 |
| S3 14 healthy + n02 + n17, nearest | 12.07 | 12.85 | 176.6 | 0.027 |
| S4 same nodes, forced aligned | 15.33 | 37.45 | 139.0 | 0.331 |
| S5 same nodes, PXN (not eligible on n17 → falls back to nearest) | 12.07 | 12.85 | 176.6 | 0.027 |
| S4@SYS (`NCCL_NET_GDR_LEVEL=SYS`) | 11.46 | 18.32 | 186.0 | 0.173 |

Key reasoning to look for: with the default GDR gate (≈ PXB) forcing alignment on n17 is *worse* than
the default nearest-NIC choice (the conclusion reverses if the host-staged rate exceeds 22.5 GB/s); PXN is
never engaged on n17 because no peer GPU reaches the misplaced NIC at ≤ PXB (it is PHB, NODE or SYS from every GPU — best is PHB from GPU4/5 — never ≤ PXB), so
S5 = S3; S2's deterministic value is 15.0 ms / ≈ 142 GB/s, the 52 ms median being an independent-CV sensitivity case;
fixing n17 alone leaves n02 capping the job at ≈ 262 GB/s (deterministic).

Mapping: **29 of 32** rows have `aligned=True` — all 16 rows of n01 and n02, 7 of n17 (GPU3 fails), 6 of n23
(GPU4 and GPU5 fail). n02 is topologically aligned; its fault (ACS/IOMMU) is a host-level finding.

### Lab 5 — planted anomalies (do not distribute)

| Host | Planted fault | Revealing evidence | Expected finding(s) |
|---|---|---|---|
| `orion-n01` | None (control) | All GPU rows `PIX` to their rail NIC; LLDP r0–r7 in order; clean GDR file | None — any finding is a false positive |
| `orion-n02` | BIOS/kernel baseline drift after motherboard swap: ACS redirect on all 16 downstream switch ports above the GPUs and NICs; `intel_iommu=on` without `iommu=pt` | `ACSCtl: SrcValid+ … ReqRedir+ CmpltRedir+`; `/proc/cmdline` | `ACS_REDIRECT` (major), `IOMMU_NOT_PASSTHROUGH` (minor) |
| `orion-n17` | Replacement rail-3 NIC (`mlx5_3`) installed in slot 11 on a socket-1 root port instead of slot 4 under GPU3's switch | topo -m GPU3 row: no `PIX`; `NIC4` (`mlx5_3`) `SYS`; lstopo `PCI 86:00.0` under Package L#1; `PhySlot: 11`, `NUMANode: 1`; GPU2 and GPU3 both nearest to `mlx5_2` | `NIC_NOT_LOCAL` (GPU3), `NIC_SHARED` (`mlx5_2`) |
| `orion-n23` | Cables of the rail-4 and rail-5 NICs swapped at the patch panel; `nvidia_peermem` not loaded; old driver | LLDP `enp153s0np0 → orion-be-leaf-r5`, `enp163s0np0 → orion-be-leaf-r4`; empty lsmod section; driver `550.127.05` | `RAIL_MISMATCH` ×2 (blocker), `GDR_PEERMEM_MISSING` (major), `DRIVER_DRIFT` (minor) |

Teaching points: names and column indices are not rails (n23's cards carry the right names on the wrong
cables); topology can be golden while GDR is degraded (n02); NCCL's nearest-NIC behaviour hides a
misplaced card by sharing a NIC (n17); a missing peer-memory module must be verified against a possible
DMA-BUF path before declaring GDR absent.

*Common mistakes:* keying the CSV by GPU index; treating `NICk` as `mlx5_k`; flagging n23 GPU4/5 as
`NIC_NOT_LOCAL` (they *have* a PIX NIC — it is cabled wrong); running the model with n23 included
(blocker nodes must not be scheduled); presenting Table 5.5 values as measurements.

**Report marking (30 pts):** diagram (6), recommendations with drain/fix/policy reasoning (6), validation
checklist with pass criteria (6), L3 methodology with repetitions and manifest (6), limitations and
correct labels (6).

## Outline-mandated exercises

**5.11** On `orion-n01`: GPU*i* → `mlx5_i`, `PIX`, for i = 0–7 (topo columns NIC1–NIC4 for GPUs 0–3, NIC6–NIC9
for GPUs 4–7). Examples: PXB GPU0↔NIC2 (`mlx5_1`); PHB GPU0↔NIC0 (`mlx5_8`, frontend, same host bridge);
NODE GPU0↔NIC3 (`mlx5_2`, other switch, same socket); SYS GPU0↔NIC6 (`mlx5_4`). Accept any correct examples
quoted from the matrix.

**5.12** GPU2 is on socket 0, GPU6 on socket 1.
(a) NVLink P2P: one DMA GPU2 HBM → GPU6 HBM via NVSwitch; completion via event; no host involvement.
Host-staged (pinned): copy 1 D2H GPU2 → pinned buffer; sync point (event recorded after copy 1, waited on by
the stream doing copy 2); copy 2 H2D buffer → GPU6.
(b) Pageable: each leg adds a CPU copy between the user buffer and the driver's pinned bounce buffer and
blocks the host thread; effectively 2 DMA + 2 CPU copies, with implicit synchronization per call.
(c) 4 GiB = 4,294,967,296 B. NVLink: / 370 × 10⁹ = **11.6 ms**. Host-staged unpipelined: 2 × 4,294,967,296 /
52 × 10⁹ = 2 × 82.6 = **165.2 ms**. Pipelined in 64 MiB chunks: ≈ 82.6 + 67,108,864 / 52 × 10⁹ = 82.6 + 1.3 =
**83.9 ms**. `[MODELED]`
(d) Any choice puts one leg across the inter-socket link (buffer on socket 0: H2D to GPU6 crosses UPI;
socket 1: D2H from GPU2 crosses). Prefer NVLink; if forced to stage, split the buffer or use two staging
buffers per socket with a CPU-side copy — which shows why host staging between sockets is a poor fallback.

**5.13** Model answer: ranks 0–7 on node A → GPU0–7 (`CUDA_VISIBLE_DEVICES` unset or 0–7 in PCI bus
order, `CUDA_DEVICE_ORDER=PCI_BUS_ID`), ranks 8–15 on node B likewise; TP group = the 8 ranks of a node
(NVLink); DP pairs (r, r+8) communicate over rail *r* via `mlx5_r` (`PIX`). CPU binding: ranks 0–3 to
NUMA 0 cores (0–55,112–167), 4–7 to NUMA 1; memory bound to the same node; leave NIC selection to NCCL's
topology detection (or set `NCCL_IB_HCA=mlx5_0,…,mlx5_7` — order irrelevant to the selection, but excluding
`mlx5_8/9` prevents use of frontend NICs). Validation checklist: mapping CSV golden on both nodes; NCCL
log `NET/IB : Using` lists `mlx5_0`–`mlx5_7` and channel lines show `/GDRDMA`; `NCCL_TOPO_DUMP_FILE` shows
each GPU paired with its `PIX` NIC; `taskset`/`numastat` confirm affinity; `all_reduce_perf` across the two
nodes ≥ fleet floor, 5 runs, median and spread. *Marking:* mapping (3), launcher settings (3), checklist
with pass criteria and evidence (4).

**5.14** Graded with the lab report rubric; additionally require that measured results (if any) carry a
manifest and ≥ 5 runs, and that model results are labelled `[MODELED]` with Table 5.4's parameters cited.

**5.15** Full marks require raw output for all six items and a verdict consistent with them, e.g.
"`nvidia_peermem` absent but NCCL channels show `/GDRDMA` → DMA-BUF path in use; verified by driver and
kernel versions". Deduct if the verdict relies on the distance-check log line alone.

## Troubleshooting case (5.16)

Hypotheses: (1) swapped cables on `orion-n12` rails 4/5 — LLDP shows exactly that; (2) optics/FEC errors
— ruled out by clean counters; (3) GDR disabled — ruled out by `/GDRDMA`; (4) PCIe link degradation —
check `LnkSta` (clean in the case). Root cause: patch-panel swap during the rack move. Why it still runs:
on an L2 rail VLAN design (unlike ORION's routed /31 plan, where the swap would break IP adjacency and NCCL
connections on those NICs), the NIC on GPU4 now sits in rail 5's VLAN and still reaches peers; same-rail
traffic from GPU4 on other nodes to GPU4 on n12 must cross between rails via the spines (or via NVLink
PXN forwarding inside the node, depending on NCCL version/config), adding a hop, sharing spine capacity,
and producing the tail increase. Fix: drain at checkpoint, swap the two patch cords per the cabling plan,
update/verify LLDP. Validation: LLDP shows `orion-be-leaf-r4`/`-r5` for the correct netdevs; mapping diff
clean; 2-node and 8-node nccl-tests within the fleet floor; p99 iteration time back to baseline over ≥ 5
runs. *Marking:* hypotheses/tests (3), root cause (2), path explanation (3), fix/validation (2).

## Design challenge (5.17) — model answer outline

Four NICs per node → four rails; GPU pair (2k, 2k+1) shares NIC *k*, both `PIX` (each GPU and the NIC on
their own downstream ports of one switch). Per node 4 × 50 = 200 GB/s vs 400 GB/s on HX8. Modeled
(α = 0.2 ms, no variance, *n* = 256): eight rings, two per NIC → 48 / 2 = 24 GB/s per ring:
*t* = 1.99219 × 134,217,728 / 24 × 10⁹ + 0.2 ms = 11.141 + 0.2 = 11.34 ms → busbw ≈ **188.6 GB/s** vs 370.7 GB/s
for HX8 — roughly half. (Equivalently four rings carrying S/4 at 48 GB/s: same 11.141 ms.) Recommendation: schedule inference,
fine-tuning and TP-only jobs whose cross-node traffic is light; keep large data-parallel pretraining on
HX8. Rejected alternative: 8 rails with 2 ports per NIC split across rails — needs dual-port NICs and
doubles leaf ports without adding PCIe bandwidth. *Marking:* diagram/mapping (3), arithmetic (3),
recommendation with rejected alternative (4).

## Reflection

**5.18** Raw: the capture files. Derived: relations from lstopo, mapping rows, findings. Modeled:
Table 5.5. Measured requires L3 nccl-tests with manifests and ≥ 5 runs per configuration, then
recalibrating the parameters.

**5.19** Correlated slowness makes consecutive iterations slow together: p99 over a run rises (whole
stretches at the slow rate), and run-to-run variance grows. The forced-aligned SYS path suffers most; the
"nearest" shared-NIC policy, being deterministic, suffers less — strengthening the conclusion that neither
replaces repair.

**5.20** GPU index and HCA name are software labels that change with `CUDA_VISIBLE_DEVICES`, device-ordering
settings, udev naming rules or a card replacement; UUID and BDF identify the physical device and its
enumeration point. Example: after a NIC swap, a udev rule names the new card `mlx5_3` regardless of slot;
an index-keyed diff shows "no change" while the BDF moved from `43:00.0` to `86:00.0` (orion-n17).

**5.21** Platform features the simple tree model does not capture (extra bridges, retimers, multi-level
switches, firmware-hidden bridges, NVSwitch functions, GPUs on a different domain), or a driver
classifying differently. Investigate with `lspci -tv`, compare to the vendor's block diagram, and treat
the vendor-documented topology and measured P2P bandwidth as tie-breakers.
