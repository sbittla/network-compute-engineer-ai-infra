# Lab 5 — GPU-to-NIC Topology Mapping and the Cost of Misalignment

*Chapter 5 · Course week 3 · Tier **L1** (laptop) with **L2/L3** extensions · Implements outline Section 20.4*

## 1. Goal and the real-world task it mirrors

Four ORION HX8 nodes are about to (re)enter the training partition. Fleet has collected the standard
node-acceptance captures from each. Your job is the one a GPU-cluster engineer does after every
provisioning and hardware service: turn raw tool output into a **machine-readable GPU→NIC/HCA mapping**
(GPU UUID and BDF → NIC/HCA, BDF, netdev, NUMA node, physical slot, rail), detect locality, wiring and
GPUDirect RDMA configuration faults, decide which nodes may run large synchronous jobs, and quantify —
with a clearly labelled model — what happens to an all-reduce if flawed nodes are scheduled anyway.

## 2. Tier and realism boundary

- **L1 (required):** pure Python against committed `[ILLUSTRATIVE]` captures (from a seeded generator — instructor copy only;
  seed 5). The all-reduce numbers are `[MODELED]` from `[ILLUSTRATIVE]` parameters in `data/path_model.yaml`.
- **L2 (optional):** capture the same files on a real multi-GPU host. **L3 (optional):** measure aligned
  vs misaligned rank/rail maps with nccl-tests on ≥ 2 nodes (Section 8).

> **Realism boundary:** The captures are reconstructions of real tool formats, abridged (real HGX boards
> have more bridges, NVSwitch functions and retimers). The model ignores spine congestion, PCIe uplink
> contention, NCCL algorithm/protocol choice, congestion control and time-correlated slow paths. Nothing
> in L1 proves P2P support, GDR activation or NVLink health on hardware.

## 3. Setup

```bash
cd book/part-2-accelerated-compute/ch05-gpu-interconnects-host-topology/lab
python -m pip install -r ../../../../requirements.txt     # numpy, pandas, pyyaml (Python >= 3.10)
python check.py                                            # progress meter
```

`data/hosts/<host>/` for `orion-n01`, `orion-n02`, `orion-n17`, `orion-n23`:

| File | Captured with |
|---|---|
| `nvidia-smi_topo_m.txt` | `nvidia-smi topo -m` |
| `lstopo.txt` | `lstopo-no-graphics --no-caches` (Core/PU objects removed) |
| `gpu_inventory.csv` | `nvidia-smi --query-gpu=index,uuid,pci.bus_id --format=csv` |
| `lspci_vmm.txt` | `lspci -D -vmm -d 15b3:` (abridged fields: Slot, Class, Vendor, Device, PhySlot, Driver, NUMANode) |
| `ibdev2netdev.txt` | `ibdev2netdev` (NVIDIA networking utility) |
| `lldp.txt` | `lldpcli show neighbors -f keyvalue` (chassis name and port only) |
| `gdr_prereqs.txt` | Sectioned summary (simplified): kernel version and command line, `lsmod` peer-memory check, driver and OFED versions, ACSCtl of the downstream switch port above each GPU and NIC |

Fleet conventions: GPU *i* ↔ rail *i*; backend leaves are named `orion-be-leaf-rR`; golden layout puts
each GPU and its rail NIC under the same PCIe switch (`PIX`); fleet driver `570.124.06`.

## 4. Background you need

Manuscript Sections 5.2 (PCIe, ACS), 5.4 (data paths), 5.6 (reading `topo -m` and `lstopo`; the mapping
schema), 5.7 (GPUDirect prerequisites), 5.8 (joint placement), 5.9 (the model) and 5.10 (worked example).

## 5. Tasks

Implement `starter/topo_mapper.py` (every function's docstring is its contract).

1. **Parsers** — `normalize_bdf`, `parse_topo_matrix`, `parse_lstopo`, `parse_gpu_inventory`,
   `parse_lspci_vmm`, `parse_ibdev2netdev`, `parse_lldp`, `rail_from_chassis`, `parse_gdr`.
   *Acceptance:* checker parser checks pass.
2. **Derive and cross-check** — `classify_path`: derive PIX/PXB/PHB/NODE/SYS from the `lstopo` tree.
   *Acceptance:* matches `nvidia-smi` on all 160 GPU–NIC pairs of two hosts.
3. **Mapping** — `load_host`/`build_mapping`; write `gpu_nic_mapping.csv` for all hosts.
   *Acceptance:* `orion-n01` fully aligned; the flawed rows on other hosts identified.
4. **Findings** — `detect_issues`. *Acceptance:* every planted fault found with the right severity, and
   **no findings** on the clean host.
5. **Rank maps and model** — `make_rank_map` (aligned, nearest, cross_socket, pxn), `path_params` (with the GDR distance gate),
   `model_allreduce`; then run `analyze()` for scenarios S1–S5 and S4@SYS. *Acceptance:* deterministic case matches
   the closed-form formula; S1–S5 and S4@SYS ordering as in the checker.
6. **Report (`topology_report.md`, ≤ 3 pages):** annotated topology diagram of one host (Mermaid/ASCII:
   sockets, host bridges, switches, GPUs, NICs with slot/NUMA/rail); the mapping CSV excerpt; findings
   per host with the raw lines that prove each; scenario table labelled `[MODELED]`; locality
   recommendations (which nodes to drain, what to fix, which policy to use meanwhile and why); a node
   acceptance **validation checklist** with pass criteria; benchmark methodology for the L3 measurement;
   limitations.

## 6. Running the checker

```bash
python check.py                    # starter
python check.py --impl solution    # instructor reference (not in the student release)
python starter/topo_mapper.py --data data --out gpu_nic_mapping.csv   # once implemented
```

## 7. Deliverable and grading rubric (100 points)

| Item | Points | Full marks when |
|---|---|---|
| Task 1 — parsers | 15 | Checks pass; robust to the three BDF forms |
| Task 2 — derive/cross-check | 10 | Checks pass; one disagreement scenario discussed in the report |
| Task 3 — mapping CSV | 15 | Checks pass; CSV keyed by UUID/BDF; slot, NUMA, rail present |
| Task 4 — findings | 15 | Checks pass; each finding cites raw evidence lines |
| Task 5 — rank maps and model | 15 | Checks pass; model formula and parameter labels reproduced in the report |
| Task 6 — report | 30 | Diagram, recommendations, validation checklist, L3 methodology, limitations; measured vs modeled never confused |

## 8. Extensions (L2/L3): capture and measure on real hardware

Run only on nodes you are authorized to use, drained from production scheduling.

```bash
# L2 — capture with the supplied script; it writes the same files and section format as data/hosts/<host>/
sudo bash capture/capture_topology.sh /tmp/topo-$(hostname)     # root needed for full lspci -vvv
nvidia-smi nvlink --status -i 0; systemctl status nvidia-fabricmanager
```

The lab's files are **simplified and reformatted** reconstructions: `gdr_prereqs.txt` is a sectioned
summary produced by the capture script (not raw tool output), and `lstopo.txt` omits cores, caches and
most bridge detail. Adapt your parsers to the real formats (expect more bridges, NVSwitch functions, extra
fields, vendor-specific names), then build the mapping CSV.

```bash
# L3 — aligned vs misaligned all-reduce with nccl-tests (2 nodes, one rank per GPU, all 8 NICs in use).
# Change ONE variable: which NIC each local rank uses. Keep every other setting identical, and disable PXN so
# NCCL cannot forward around the forced choice. Record NCCL_NET_GDR_LEVEL (unset = release default).
cat > hca_wrap.sh <<'EOF'
#!/usr/bin/env bash
LR=${OMPI_COMM_WORLD_LOCAL_RANK:-$SLURM_LOCALID}
if [ "${MISALIGN:-0}" = 1 ]; then export NCCL_IB_HCA="=mlx5_$(( (LR + 4) % 8 )):1"   # rail NIC of GPU (i+4)%8: SYS
else                              export NCCL_IB_HCA="=mlx5_${LR}:1"; fi               # own rail NIC: PIX
exec "$@"
EOF
chmod +x hca_wrap.sh
COMMON="-x NCCL_DEBUG=INFO -x NCCL_DEBUG_SUBSYS=INIT,NET -x NCCL_PXN_DISABLE=1 -x CUDA_DEVICE_ORDER=PCI_BUS_ID"
mpirun -np 16 -N 8 --bind-to numa $COMMON -x MISALIGN=0 ./hca_wrap.sh \
       ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1 -w 20 -n 100 | tee aligned_run1.log
mpirun -np 16 -N 8 --bind-to numa $COMMON -x MISALIGN=1 ./hca_wrap.sh \
       ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1 -w 20 -n 100 | tee misaligned_run1.log
# --bind-to numa keeps each rank on its socket's cores; it does not pin one core set per GPU.
# Slurm equivalent (ranks 0-3 on NUMA 0, 4-7 on NUMA 1; export the same NCCL variables first):
#   MISALIGN=0 srun -N 2 --ntasks-per-node=8 --gpus-per-node=8 --gpu-bind=none \
#        --cpu-bind=map_ldom:0,0,0,0,1,1,1,1 \
#        ./hca_wrap.sh ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1 -w 20 -n 100
# Keep all 8 GPUs visible to every rank: --gpus-per-task=1 with device cgroups hides the peers, and
# intra-node channels can fall back from P2P/CUMEM or P2P/IPC to SHM. Check the intra-node channel lines.
# Prove the path: which NIC each rank used, and whether channels say /GDRDMA (GDR) or not (host-staged).
grep -E 'NET/IB : Using|via NET/IB' aligned_run1.log misaligned_run1.log | head -40
```

The `=` prefix makes NCCL use exactly the listed device (`NCCL_IB_HCA` syntax is release-dependent;
check the NCCL environment-variable documentation for yours). With the default GDR distance gate, expect
the misaligned channels to lose `/GDRDMA` (SYS is beyond ≈ PXB). That is part of what you are measuring,
so record it.

Repeat each configuration ≥ 5 times (separate launches), record busbw median and spread at 1 GiB and
8 GiB, plus the out-of-place time column for tail analysis; record the manifest fields listed under
`extensions` in `manifest.yaml`. (Option names for `mpirun` differ between MPI implementations; the commented
`srun` line is the Slurm form.) Compare measured busbw with Table 5.5 and
recalibrate `path_model.yaml`; label everything `[MEASURED]` with the manifest attached (include
`NCCL_NET_GDR_LEVEL`, `NCCL_PXN_DISABLE`, the per-rank HCA table and the `/GDRDMA` evidence lines).

> **Safety:** Misaligned runs deliberately degrade performance; run them only on drained lab nodes,
> never inside a shared production job.

### Running the L2 experiment (course harness)

From the repository root:

```bash
python scripts/hw_labs.py build ch05
python scripts/hw_labs.py run ch05 --device gpu   # measure on the GPU -> lab/l2/results/gpu-<model>/
python scripts/hw_labs.py run ch05 --device cpu   # CPU fallback        -> lab/l2/results/cpu-fallback/
python scripts/hw_labs.py test ch05               # quick run now + committed-evidence checks
```

The experiment is `lab/l2/experiment.py`. With `--device auto` (the default) it uses the GPU when one is
visible; without a GPU the CPU fallback runs automatically and its report says which invariants were
skipped. Add `--quick` for a smoke test (never committed as evidence).

It captures the real `nvidia-smi topo -m` (parsed with the lab's own `parse_topo_matrix`), the GPU's PCIe
capability and negotiated link at idle and under load, a PCI/sysfs scan for RDMA NICs, and every Table
5.3 GPUDirect RDMA prerequisite readable without root. It measures pinned/pageable H2D and D2H bandwidth
against the link ceiling, then applies the lab's GDR gate (`path_model.yaml: gdr_max_relation`) to the
GPU-NIC pairs actually found. With no NIC the verdict is "GDR impossible on this host".

Not runnable on the harness: the capture script's root-only parts (`lspci -vvv` ACS/LnkSta, `lstopo`,
`ibdev2netdev`, LLDP), NVLink status, and the L3 aligned-versus-misaligned `all_reduce_perf` runs.

The CPU fallback captures the PCI/NUMA/RDMA probes and the Table 5.3 gate without a GPU, and measures
host-memory copy bandwidth.

**Observed on the reference run.** `lab/l2/results/` holds the committed evidence bundles
(`environment.json`, `results.json`, `report.md`) from the course's reference host: a laptop GeForce RTX
4060 (Ada, 8 GB, PCIe Gen4 x8) under WSL2, not an H100-class server. `gpu-<model>/` is the GPU run and
`cpu-fallback/` the CPU run; each `report.md` lists what was measured, what was not runnable and why, and
the invariants it passed. The Table 5.3 evidence table and its verdict are the input to Exercise 5.15.
Rerun on your own hardware and compare like with like.

## 9. Intentionally flawed inputs

Three of the four hosts contain planted faults of different kinds, and one is clean. The fault list,
the raw lines that reveal each, and the reasoning they exercise are in
`../solutions/exercises-key.md` ("Lab 5 — planted anomalies"). Do not look before submitting.
