# Capstone G Starter Kit — ORION-XL Incident Workbench

## 1. Goal and the real-world task it mirrors

When a 3,840-GPU job hangs, the on-call engineer has to answer three questions fast, from evidence
scattered across hosts, switches and logs: *what broke, what else is broken, and where can the job
safely restart?* `starter/ftops.py` is the core of that workbench: inventory, correlation, scoring,
classification, quarantine, checkpoint selection, restart planning, metrics and resume validation.

## 2. Tier and realism boundary

**Tier L1**, evidence class `[SIMULATED]`. The dataset is synthetic and seeded (the generator is an instructor copy only). Log lines imitate the shape of real messages; they are not captures, and counter
names such as `link_down_events_phy` and `rx_crc_errors_phy` must be checked against `ethtool -S`
on your NIC and driver before you rely on them. Nothing in the kit touches a real system.

## 3. Setup

```bash
cd capstones/capstone-g-fault-tolerant-512-node-training/starter-kit
python -m pip install -r ../../../requirements.txt     # numpy, pandas, pyyaml
python check.py                                        # 1/11 PASS at the start
```

## 4. Data dictionary

| File | Contents |
|---|---|
| `inventory.csv` | 4,096 GPU rows (512 nodes × 8): rank (empty on spare nodes), TP/PP/DP coordinates, GPU UUID/BDF, NUMA, HCA, NIC BDF, rail, leaf and port **as observed by LLDP** |
| `cabling_plan.csv` | The DCIM cable plan (node, HCA → leaf, port) |
| `clock_offsets.csv` | Per-host offset reported by chrony: host clock − true time (s) |
| `events.jsonl` | 652 events: `kernel` (Xid, AER, mlx5 link), `dcgm` (field, value), `nic` (counter, value), `switch` (port, counter, value), `job` (rank errors and watchdog timeouts), `scheduler`; timestamps are **host** clocks |
| `progress.csv` | Per rank: last completed step, last enqueued collective sequence number, last-progress host timestamp |
| `step_times.csv` | Global step durations for the last 600 steps |
| `checkpoints.json` | Async sharded checkpoints: step, start, metadata committed, missing shards, checksum failures |
| `quarantine_db.csv`, `spares.csv` | Health database and spare-pool state before the incident |
| `ops_log.jsonl` | What the recovery automation did, on the controller's (true) clock |
| `loss_pre.csv`, `resume_validated.csv`, `resume_unvalidated.csv`, `resume_dataloader_not_restored.csv` | Loss, grad norm and data-loader sample index: before the fault; after this restart; after an earlier drill that restored the newest-looking checkpoint; after a restore that reloaded weights but not the data-loader/RNG state |
| `config.yaml` | Job parameters, targets, scoring thresholds |

## 5. Tasks

| Task | Function(s) | Acceptance criterion | Points |
|---|---|---|---|
| **T1** Topology inventory | `build_maps`, `cabling_discrepancies` | Correct rank→device chain for all 3,840 ranks; port map from LLDP; both DCIM mismatches found | 12 |
| **T2** Correlation | `normalize_events` | One row per event on true time; Xid/AER/link lines mapped to GPU/HCA via BDF; DCGM via UUID; switch ports via LLDP; skewed host corrected | 14 |
| **T3** Health scoring | `health_scores` | Exactly the documented policy; background correctable ECC scores 0 | 10 |
| **T4** Classification | `classify` | First-stalled rank from collective sequence; proven cause vs independent fault vs watch | 14 |
| **T5** Quarantine | `quarantine_plan` | GPU and HCA quarantined; their nodes drained; Fabric ticket on the LLDP peer port; red herrings untouched | 10 |
| **T6** Checkpoint selection | `select_checkpoint` | Newest *restorable* checkpoint; reasons for rejecting newer ones; error when none qualifies | 10 |
| **T7** Restart orchestration | `restart_plan` | Only eligible spares; GPU index (rail) preserved; error when spares run out | 12 |
| **T8** RTO/RPO | `recovery_metrics` | Detect, isolate, RTO, RPO, lost GPU-h and target verdicts | 8 |
| **T9** Resume validation | `validate_resume` | Validated restart passes at a 1e-3 tolerance with identical sample indices; the corrupt-checkpoint restore and the data-loader-not-restored resume both fail, with the reason | 10 |
| | | **Total** | **100** |

Hints: sort the watchdog timeouts by host timestamp and ask why one host is first; look up the switch
port in both the plan and the inventory; read `spares.csv` *and* `quarantine_db.csv`; count the
shards before trusting a checkpoint.

## 6. Running the checker

```bash
python check.py      # ≈ 2 s; PASS/FAIL/TODO per check; exit 0 only at 11/11
```

## Troubleshooting

- **`ModuleNotFoundError` for `numpy`, `pandas` or `yaml`** (a traceback, or a `FAIL  import` line).
  From `starter-kit/`, run `python -m pip install -r ../../../requirements.txt` with the interpreter you
  run `check.py` with. Use Python 3.10 or newer.
- **`FAIL  import -- SyntaxError: ...` and no check lines.** The checker could not import
  `starter/ftops.py`. `python -m py_compile starter/ftops.py` shows the line.
- **`TODO ... -- not implemented: TODO: implement <name>()`.** That function still raises
  `NotImplementedError`. The line names it, for example `validate_resume()`.
- **`FAIL ... orionxl-n042 still reports the earliest timeout`.** You ordered events by their raw
  timestamps. Apply `data/clock_offsets.csv` first (that node's clock is 180 s behind), then correlate.
- **The dataset check FAILs** (instructor copy only), or loading fails. A file in `data/` was edited.
  Restore it with `git checkout -- data/`.
- **The L2 `scripts/hw_labs.py` commands print `FAIL build` or `FAIL run`.** Run them from the
  repository root with Docker running (`docker info` must succeed). `--device gpu` also needs the NVIDIA
  Container Toolkit; without it, use `--device cpu`.

## 7. Deliverable

`starter/ftops.py` passing 11/11 plus the templates in [../templates/](../templates/), with the
checker output pasted into the results table as `[SIMULATED]`.

## 8. L2/L3 extension

> **Safety:** Dedicated lab only. Do not attempt to induce real ECC or PCIe errors. Inject faults by
> killing a rank's process, draining a node, or taking down a dedicated lab interface — each with
> a rehearsed rollback.

**L2 — collect real evidence on one host (read-only):**

```bash
nvidia-smi --query-gpu=index,uuid,pci.bus_id --format=csv
nvidia-smi -q -d ECC                       # volatile/aggregate correctable and uncorrectable counts
nvidia-smi -q -d ROW_REMAPPER              # pending / failed remaps (recent drivers; verify)
sudo journalctl -k | grep -E 'NVRM: Xid|AER:|mlx5_core .* Link'
rdma link show
ethtool -S <rail_iface> | grep -E 'link_down_events_phy|rx_crc_errors_phy'   # names vary by driver
lldpctl                                    # observed switch and port per interface (lldpd)
chronyc tracking                           # clock offset of this host
dcgmi discovery -l
```

Feed the outputs through your parsers (write small adapters into the `events.jsonl` schema) and
record where real formats differ from the synthetic ones.

**L2 — the packaged experiment (one GPU host, read-only plus a local drill).** `l2/experiment.py` has three parts.

1. It runs the command list above, records which commands exist, converts what does exist (nvidia-smi inventory and row
   remapping) into the `events.jsonl` schema, and passes it through your `normalize_events` and `health_scores`. A healthy
   host must score nothing, and a labelled synthetic positive control must score something. It also records the real
   format differences.
2. It trains a small MLP on the GPU with an index-addressed data loader. It measures the replay noise by restoring one
   checkpoint twice, sets the tolerance from that noise, and gates three resumes with your `validate_resume`: correct,
   data loader not restored, and optimizer not restored.
3. It writes sharded checkpoints with the checksummed metadata last, SIGKILLs one save mid-write, corrupts one committed
   shard, scans the directory into the `checkpoints.json` form, and checks that your `select_checkpoint` picks the newest
   restorable checkpoint with the right rejection reasons. Save and restore throughput are measured too.

DCGM, ECC, the kernel log, rdma, ethtool, lldpctl, chrony and the L3 drill are recorded as **not runnable**, each with its
probe result.

```bash
python scripts/hw_labs.py build capstone-g                 # from the repository root: the ai-infra-gpu:capstone-g image
python scripts/hw_labs.py run capstone-g --device gpu      # measure on the GPU      -> l2/results/gpu-<model>/
python scripts/hw_labs.py run capstone-g --device cpu      # CPU fallback            -> l2/results/cpu-fallback/
python scripts/hw_labs.py test capstone-g                  # quick run now + checks on the committed evidence
```

Without a GPU (`--device auto` on a host with no NVIDIA driver) the same experiment runs its CPU fallback automatically, and the GPU-only invariants are skipped and named in the report. Each run writes `environment.json`, `results.json` (raw repetitions, invariants) and `report.md`. The CPU fallback runs parts 2 and 3 on the CPU.

**Observed on the reference run:** the committed bundles in `l2/results/` (`gpu-rtx-4060-laptop-gpu/`, `cpu-fallback/`)
show only the nvidia-smi commands available inside the container, and a healthy host that scores nothing while its
positive control is flagged. Replay noise is zero on this deterministic job, so the tolerance sits at its 1e-5 floor. The
correct resume passes, and both broken resumes fail: one on the sample index, one on continuity. The selector rejects the
killed save (metadata not committed) and the corrupted one (checksum failure). The host is a laptop container, not an
ORION-XL node.

**L3 — controlled drill on ≥ 2 RDMA-connected GPU nodes:** run a small PyTorch DDP or FSDP job with
asynchronous sharded checkpoints (for example DCP async save) and a deliberately short process-group
timeout. Then:

1. Kill one rank's process (`kill -9 <pid>`) and record the watchdog timing on the other ranks. PyTorch's
   desync debugging and NCCL flight recorder (`TORCH_NCCL_DESYNC_DEBUG`, `TORCH_NCCL_TRACE_BUFFER_SIZE`;
   verify names against your PyTorch version) report which rank never entered the collective.
2. Separately, `sudo ip link set dev <lab_rail_iface> down` for 30 s on one node, then `up`; record
   counters and job behaviour.
3. Drain with `scontrol update NodeName=<node> State=DRAIN Reason="<ticket>"`, restart from the
   checkpoint your `select_checkpoint()` picks, and run `validate_resume()` on the real loss log.
4. Kill the job *during* an async save at least once and confirm your selector rejects the
   incomplete checkpoint.

Record (copy `manifest.yaml`, `tier: L3`, `evidence_class: MEASURED`): GPU, driver, CUDA, NCCL and
PyTorch versions; process-group timeout and `NCCL_IB_TIMEOUT` (state the NCCL version, because the
default changed in 2.23); checkpoint mechanism, size and upload rate; storage; injection commands and
rollbacks; repetitions (≥ 3 per fault); measured detect/isolate/RTO/RPO.

## 9. Files

```text
starter-kit/
├── README.md  manifest.yaml  check.py
├── data/                 generated (do not edit)
├── tools/                     generator: instructor copy only (removed from the student release)
└── starter/ftops.py      implement here
```
