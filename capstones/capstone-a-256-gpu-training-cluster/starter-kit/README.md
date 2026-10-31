# Capstone A starter kit: the ORION-256 design model

This kit gives you a design model that computes, from one set of stated inputs, the quantitative core
of a 256-GPU training-cluster design: the fabric topology, the cable plan, power and cooling, a
communication and step-time model for W-TRAIN, the bill of materials, the size of the acceptance
campaign, and the cost per million training tokens. Senior architects build this kind of model before
anyone signs a purchase order, because it lets a reviewer trace every number in the design pack back to
an input.

> **Realism boundary:** Everything here is Level 1 (L1). The inputs are `[ILLUSTRATIVE]` and every output
> is `[MODELED]`. The model can show that rail-optimized cabling needs three times as many optics as a
> top-of-rack design, or that a shuffled hostfile doubles leaf-uplink load. It cannot tell you how NCCL
> will choose rings on a real fabric, how many ECMP hash collisions you will actually get, what
> sustained power your nodes will draw under W-TRAIN, or whether an optic will pass at 70 m. Those
> claims need the L2/L3 procedures in Section 8, run in a dedicated lab.

## 1. Goal and the real-world task it mirrors

Halcyon AI's Fabric, Facilities and Training Infra teams must agree on a backend fabric for ORION-256
before procurement closes. You are the architect who owns the design pack. Two fabric options are on
the table, plus a vendor quote that is cheaper on paper. The model you build here produces the numbers
that the design pack, the bill of materials and the cost/performance memo depend on.

## 2. Tier and realism

| Tier | What you do | Evidence class |
|---|---|---|
| L1 (required) | Implement `starter/cluster_model.py`; pass `check.py`; use outputs in your design pack | `[MODELED]` |
| L2 (optional) | Validate host topology, NIC/GPU locality and node power on one HX8-class host | `[MEASURED]` for that host only |
| L3 (optional) | Validate rail and spine bandwidth, rank-layout sensitivity and optic DDM on 2+ nodes | `[MEASURED]` for that fabric only |

## 3. Setup

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r ../../../requirements.txt                 # numpy, pandas, pyyaml (Python >= 3.10)
# (instructor edition only) python tools/generate_data.py regenerates data/ byte-identically
python check.py                                          # progress meter: TODO / FAIL / PASS per check
```

## 4. Inputs (in `data/`)

| File | Contents |
|---|---|
| `design_inputs.yaml` | Cluster shape, component catalogue (USD, W, reach), fixed items, three fabric options, W-TRAIN parameters and two parallelism scenarios, economics |
| `facility.yaml` | Rack positions with feed voltage/breaker/phases, power factor, continuous-load derate, 2N policy, cooling units per row (N+1), PUE, cabling rules |
| `floorplan.csv` | 13 racks: position, row, x/y in metres, kind (gpu, network, storage, mgmt) |
| `hostfile_job4471.txt` | The node order the inventory API handed to the launcher for job 4471 |

Read all four before writing code. Several inputs are deliberately awkward in the way real inputs are.
The checker will tell you when your model has handled them; your design pack must explain them.

## 5. Background you need

- Rail-optimized versus top-of-rack leaf-spine designs, oversubscription and ECMP:
  [Chapter 7](../../../book/part-3-networking/ch07-ethernet-datacenter-network-foundations/) and
  [Chapter 8](../../../book/part-3-networking/ch08-rdma-rocev2-infiniband/).
- Optics, DAC reach and cable plans: [Chapter 10](../../../book/part-3-networking/ch10-switches-optics-physical-layer/).
- Rack power, 2N feeds and N+1 cooling: [Chapter 2](../../../book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/)
  and [Chapter 21](../../../book/part-5-production-operations/ch21-capacity-power-economics/).
- Parallelism, ring all-reduce bytes and FSDP/ZeRO-3 traffic:
  [Chapter 11](../../../book/part-4-distributed-ai/ch11-distributed-training-architecture/) and
  [Chapter 12](../../../book/part-4-distributed-ai/ch12-collective-communication-nccl/).

Two formulas you will use repeatedly:

```text
Ring all-reduce, bytes sent per GPU   = 2 (n − 1) / n × S
ZeRO-3 / FSDP, bytes per GPU per step = 3 (n − 1) / n × S     (all-gather fwd + all-gather bwd + reduce-scatter)
Usable kW of one 3-phase feed         = √3 × V_LL × I × PF × continuous-load derate / 1000
```

## 6. Tasks (100 points)

| # | Task | Acceptance criterion | Points |
|---|---|---|---|
| 1 | `fabric_counts`, `leaf_of`: switch, link and oversubscription counts for options A, B and C; design-rule warnings | Checks 02–04 pass; your design pack explains *why* option C is rejected | 12 |
| 2 | `cable_length_m`, `choose_media`, `cable_plan`: every backend link with routed length and medium | Checks 05–06 pass; pack contains a cable-plan summary by medium and length | 14 |
| 3 | `feed_usable_kw`, `rack_power`, `cooling_check`: rack power with 2N, row cooling with N+1 | Checks 07–10 pass; pack names each facility violation and a mitigation with its owner | 16 |
| 4 | `rank_layout`, `contention`, `comm_step_model`: W-TRAIN bytes, contention and step time | Checks 11–13 pass; pack contains the scenario × option × layout table | 20 |
| 5 | `bom`, `acceptance_counts`, `cost_per_million_tokens` | Checks 14–16 pass; BOM and acceptance plan tables in the pack | 13 |
| 6 | Sensitivity analysis: rerun the FSDP scenario on option B with an *effective* contention of 2, 3 and 4 (ECMP collisions) and find the break-even against option A in $/M tokens | Table plus one paragraph; break-even stated with its assumption | 10 |
| 7 | Oversubscription comparison write-up (advanced extension): which layouts and workloads make option B's 2:1 visible, and which hide it | One page, every number labelled | 15 |

## 7. Running the checker

```bash
python check.py                    # your starter implementation
python check.py --impl solution    # instructor edition only
```

One line per check: `PASS`, `FAIL` (with the expected value and the formula hint) or `TODO`. The kit
is complete when all 16 checks pass. Passing the checker earns the implementation points; the design
pack earns the rest (see [../README.md](../README.md) and [../../RUBRIC.md](../../RUBRIC.md)).

## 8. Extensions: hardware-backed validation (L2/L3)

> **Safety:** Run these only on hardware assigned to you in a dedicated lab. Never change power limits,
> QoS, or routing on shared or production systems.

### L2: one HX8-class host

```bash
nvidia-smi topo -m                                   # GPU↔NIC affinity: expect PIX between GPU i and NIC i
lstopo --of txt                                      # sockets, NUMA nodes, PCIe switches, NIC placement
ibv_devinfo                                          # RDMA devices, firmware version, port state, link layer
nvidia-smi -q -d POWER                               # per-GPU power draw and enforced limit
ipmitool dcmi power reading                          # chassis power from the BMC (where DCMI is supported)
```

Run a sustained single-node load (for example `all_reduce_perf` from nccl-tests across the 8 local GPUs
plus a long-running training proxy) and log chassis power every second for at least 30 minutes. Record
the median and maximum. Replace the `watts_sustained` and `watts_max` assumptions in your assumptions
register with these `[MEASURED]` values, and recompute the 2N check for rack-05.

### L2 on a single GPU host: the packaged experiment

`l2/experiment.py` runs the parts of this procedure that one GPU host can support:

- It probes the topology the design relies on: `nvidia-smi topo -m`, NUMA nodes, the GPU's PCIe link, RDMA NICs and the BMC.
- It measures GPU board power at idle and under a sustained GEMM load, sampled every 200 ms through nvidia-smi together
  with SM clock, temperature and clock-event reasons. It reports the sustained (median) and maximum power and their ratio.
- It reruns the L1 `rack_power()` 2N check with `watts_sustained` rescaled by the measured ratio. This is a `[MODELED]`
  sensitivity analysis, not an HX8 measurement.

GPU<->NIC affinity, `lstopo`, chassis power from `ipmitool`/Redfish, and the 8-GPU load are recorded as **not runnable**,
each with its probe result.

```bash
python scripts/hw_labs.py build capstone-a                 # from the repository root: the ai-infra-gpu:capstone-a image
python scripts/hw_labs.py run capstone-a --device gpu      # measure on the GPU      -> l2/results/gpu-<model>/
python scripts/hw_labs.py run capstone-a --device cpu      # CPU fallback            -> l2/results/cpu-fallback/
python scripts/hw_labs.py test capstone-a                  # quick run now + checks on the committed evidence
```

Without a GPU (`--device auto` on a host with no NVIDIA driver) the same experiment runs its CPU fallback automatically, and the GPU-only invariants are skipped and named in the report. Each run writes `environment.json`, `results.json` (raw repetitions, invariants) and `report.md`. The CPU fallback runs the topology probe and a sustained CPU GEMM load. CPU package power is not readable in the
container (no RAPL powercap), so the CPU fallback records power as not runnable and runs the rack-power check with the
design's own values.

**Observed on the reference run:** the committed bundles in `l2/results/` (`gpu-rtx-4060-laptop-gpu/`, a laptop GPU, and
`cpu-fallback/`) show the GPU pinned at its enforced board limit under load, with the SW power cap active and the SM clock
well below `clocks.max.sm`. The sustained/maximum ratio is therefore close to 1. With a ratio that high, the rescaled 2N check flips rack-05's
sustained verdict. That is a laptop at its power limit, not an H100 node. Replace the ratio with your chassis measurement.

### L3: two or more nodes on a rail-optimized fabric

```bash
# Per-rail point-to-point RDMA bandwidth between ring neighbours (perftest). Server side first, then client.
ib_write_bw -d mlx5_0 --report_gbits -D 10 -F                      # on node A
ib_write_bw -d mlx5_0 --report_gbits -D 10 -F <node-A-rail0-ip>    # on node B
# Add -x <gid-index> on RoCEv2 if the default GID is not the RoCEv2 one (check: show_gids, where installed).

# Collective bandwidth across nodes (nccl-tests), one process per GPU:
mpirun -np 16 -H nodeA:8,nodeB:8 ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1

# Optic health on each link end (module DDM: Tx/Rx power, temperature):
ethtool -m <ifname>
```

To reproduce the oversubscription experiment on real hardware, run `all_reduce_perf` twice with the
same nodes: once with ranks ordered rack-contiguously and once with the shuffled order from
`hostfile_job4471.txt`, on a fabric where cross-rack traffic must traverse the spine. Record at least five
runs of each after warm-up and report median bus bandwidth with min/max. Record in the manifest:
switch model and OS version, NIC firmware, MTU, PFC/ECN configuration, ECMP hash fields, rank-to-node
map, optic part numbers and cable lengths, NCCL and nccl-tests versions, run count and warm-up policy.

## 9. Deliverable

Your filled templates in [`../templates/`](../templates/) plus the outputs of this model, assembled into
the design pack described in [../README.md](../README.md). Planted issues in the dataset are documented
for instructors only.
