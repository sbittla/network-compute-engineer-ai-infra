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
