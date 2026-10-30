# Lab 1 (Chapter 1) — Workload Characterization Model for ORION

## 1. Goal and the real-world task it mirrors

Before Halcyon AI approves new capacity, every team submits a resource profile of its workload: FLOPs,
HBM traffic, NVLink and NIC volumes, storage I/O, and an observed step time. A capacity reviewer must
answer three questions quickly: *Is the data credible? Which resource bounds each workload? Does the
team's own label match the evidence?* You will build the tool that answers them: a ceiling
(roofline-style) model that validates the profile sheet, computes lower-bound times against ORION's
ceilings, classifies each workload as compute-, memory-, communication-, or I/O-bound, flags
suspicious profiles, and generates the one-page training-versus-inference comparison that is part of
the Chapter 1 deliverable.

## 2. Tier and realism boundary

**Tier L1** (laptop, no GPU, no root, < 1 s runtime). Evidence class: `MODELED` (the profiles are
synthetic `[ILLUSTRATIVE]` values derived from W-TRAIN/W-INFER; the ceilings are vendor-class peaks).

> **Realism boundary:** The model computes lower bounds from peak rates. It cannot show achievable
> bandwidth, overlap, latency, contention, or stragglers, and it says nothing about real NVLink, RDMA,
> or HBM behaviour. Use the L2/L3 extension (Section 8) to replace synthetic profiles with measured ones.

## 3. Setup

```bash
cd book/part-1-foundations/ch01-ai-infrastructure-landscape/lab
python --version                      # 3.10 or newer
pip install -r ../../../../requirements.txt   # needs pyyaml (numpy/pandas optional here)
python check.py                       # starter: expect TODO lines and a non-zero exit
```

Files:

| Path | Purpose |
|---|---|
| `data/workload_profiles.csv` | 18 workload profiles as submitted (flaws included — do not edit) |
| `data/platform_orion.yaml` | ORION per-GPU and per-node ceilings and the latency threshold |
| `starter/workload_model.py` | Your implementation (functions raise `NotImplementedError`) |
| `check.py` | Automated checker (`--impl starter` default, `--impl solution` for instructors) |

## 4. Background you need

- Manuscript Section 1.6 (the ceiling model, ceiling fraction, machine balance, Table 1.7 evidence).
- Section 1.5 (why NIC line rate is 400 Gb/s = 50 GB/s and how TP/DP volumes arise).
- Section 1.9 (the worked example; profile W01 is W-TRAIN and W02 is W-INFER decode).

Column units (per GPU per step unless the name says otherwise): `tflop_per_gpu` in TFLOP (10^12 FLOP);
`hbm_gb_per_gpu` in GB (10^9 B) read + written to HBM; `nvlink_gb_per_gpu` in GB sent over NVLink (one
direction); `net_value_per_gpu` is the volume sent through the backend NIC, in the unit named by
`net_unit`; `io_read_gb_per_node` / `io_write_gb_per_node` in GB per node per step from/to shared
storage; `observed_step_s` is wall-clock seconds reported by the workload owner.

## 5. Tasks

1. **Validate and normalize** — implement `normalize_and_validate(rows)`. Reject rows with blank numeric
   fields (`MISSING`), negative values (`NEGATIVE`), non-volume network units (`BAD_UNIT`), and repeated
   IDs (`DUPLICATE`, keep the first). Convert `net_value_per_gpu` to `net_gb_per_gpu` (GB and Gb are
   the only accepted units). *Acceptance:* 4 rejected rows, 14 clean rows; checks
   `validation_issues`, `unit_normalization` pass.
2. **Resource lower bounds** — implement `resource_times(profile, platform)` returning compute, memory,
   scaleup, scaleout, io_read, io_write in seconds. The per-node storage ceiling is
   `min(frontend NICs, PFS aggregate / nodes in the job)`. *Acceptance:* `resource_times_core`,
   `resource_times_io`, `w01_worked_example` pass; W01 compute ≈ 6.95 s, scaleup ≈ 2.67 s.
3. **Classify and flag** — implement `classify(profile, platform)` and `analyze(...)`: dominant
   resource, bound class, lower bound, ceiling fraction, and flags `IMPOSSIBLE`,
   `LATENCY_OR_OVERHEAD`, `MISLABELED`. *Acceptance:* `classification`, `flags` pass.
4. **One-page comparison** — implement `comparison_markdown(a, b)` and run
   `python starter/workload_model.py --compare W01 W02 > comparison.md`. *Acceptance:*
   `comparison_markdown` passes and the page is ≤ 600 words.
5. **Data-quality note** — write `data_quality.md` (not checked automatically): one line per rejected
   or flagged row stating the probable real-world cause of the flaw and who you would ask to fix it.

## 6. Running the checker

```bash
python check.py                  # your starter implementation
python check.py -v               # also print tracebacks for FAIL lines
python check.py --impl solution  # instructors: reference implementation (exit 0)
```

Each line reads `PASS`, `FAIL`, or `TODO` with a reason; the exit code is 0 only when all nine checks
pass. From the repository root, `python scripts/validate_labs.py ch01` runs both modes.

## 7. Deliverable and grading rubric (100 points)

Deliverable: passing `check.py` output, `comparison.md` (W01 vs W02), and `data_quality.md`.

| Item | Points |
|---|---:|
| Task 1 — validation and unit normalization (checks 2–3) | 20 |
| Task 2 — resource lower bounds (checks 4–6) | 20 |
| Task 3 — classification and flags (checks 7–8) | 20 |
| Task 4 — one-page comparison: correct, readable, evidence section meaningful | 15 |
| Task 5 — data-quality note: every flaw explained with a plausible cause and owner | 20 |
| Code quality: type hints, docstrings with units, no hard-coded workload IDs in logic | 5 |
| **Total** | **100** |

## 8. Extensions (L2 / L3)

Replace synthetic rows with profiles you measure. Never run these on shared production nodes; use a
dedicated lab node or an allocation you own.

**L2 — one GPU node.**

```bash
nvidia-smi -q -d PERFORMANCE                 # confirm no active clock-event (throttle) reasons
nvidia-smi dmon -s pucvmet -d 1 -c 60 > dmon.txt   # power, util, clocks, violations, memory, ECC/PCIe, PCIe throughput
dcgmi dmon -e 1002,1004,1005,1011 -d 1000 -c 60 > dcgm.txt
#   1002 SM_ACTIVE, 1004 PIPE_TENSOR_ACTIVE, 1005 DRAM_ACTIVE, 1011 NVLINK_TX_BYTES (verify IDs: `dcgmi dmon -l`)
nsys profile -o step_profile --trace=cuda,nvtx,osrt python train_step.py   # your own workload
./build/all_reduce_perf -b 8M -e 4G -f 2 -g 8   # nccl-tests, intra-node NVLink all-reduce
```

Build a CSV row for your workload: FLOPs from the model formula, HBM bytes from DRAM activity × peak ×
time (an approximation; Nsight Compute gives exact per-kernel bytes), NVLink bytes from DCGM, observed
step time as the **median of ≥ 5 runs after warm-up**. Record p95 and min/max too.

**L3 — two or more nodes with RDMA.**

```bash
ibv_devinfo                                         # RDMA devices, firmware, link layer (Ethernet = RoCE)
ethtool -S <backend-if> | grep -E 'tx_bytes_phy|rx_bytes_phy|discard|pause'   # mlx5-class counter names
mpirun -np 16 -H orion-n01:8,orion-n02:8 -x NCCL_DEBUG=INFO -x NCCL_IB_HCA=<rail-hca-list> \
    ./build/all_reduce_perf -b 8M -e 4G -f 2 -g 1        # -x exports the variables to every rank
NCCL_DEBUG=INFO <your launcher> 2>&1 | grep -E 'via (P2P|NET)'   # which transport each channel uses
```

Compute NIC bytes per GPU per step from counter deltas divided by steps and GPUs, and check that the
implied rate never exceeds line rate (if it does, you summed directions or NICs).

**Record in a copy of `manifest.yaml`:** GPU model and count, driver, CUDA, NCCL and DCGM versions,
NIC model and firmware, link speed and MTU, topology (`nvidia-smi topo -m` output), workload
definition (model, batch, sequence length, parallelism), warm-up policy, number of runs, median and
p95, and which values are `MEASURED` versus `MODELED`.

## 9. Intentionally flawed inputs

The dataset contains planted flaws that mirror real capacity-review mistakes. They are documented for
instructors in `../solutions/lab/README.md`. Learners: find them yourselves; that is the point.
