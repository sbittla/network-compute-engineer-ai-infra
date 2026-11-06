# Lab 19 — ORION-XL Incident: Isolate, Contain, Recover — then Score the Risks and Audit the Tenants

Tier **L1** (laptop). Evidence class: `[SIMULATED]`.

## 1. Goal and the real-world task it mirrors

At 03:52 UTC Slurm marks job 900211 — a 4,096-GPU pretraining run on ORION-XL — `FAILED (NCCL
watchdog timeout)`. It is the job's **second** failure tonight; the first was auto-restarted on the
same nodes. Auto-requeue is now held pending review. You are the on-call reliability engineer. Before
anyone presses "restart" you must answer, with evidence:

1. Which ranks stopped first, and what hardware do they share?
2. Which component caused the hang — and which alarming-looking events are *real faults that did not
   cause it*, or merely correlated noise?
3. What is the **smallest defensible failure domain** to quarantine, and which spares replace it?
4. Which checkpoint is safe to restore, what are RPO, RTO, and lost accelerator-hours, and is an
   automatic restart allowed under the retry policy?

Then, as the post-incident work every reliability team does: score the platform's **FMEA risk
register** (catching its data-quality errors) and audit the **tenant-isolation configuration** against
policy.

## 2. Tier and realism boundary

Everything runs on synthetic data in a few seconds. The dataset mimics real artifacts — kernel `Xid`
and `mlx5_core` lines, NCCL `NET/IB` warnings, PyTorch watchdog messages, a flight-recorder summary,
switch-port counters, DCGM/`nvidia-smi` row-remapper state — but message formats are `[ILLUSTRATIVE]`
and vary by driver/NCCL/PyTorch version. It cannot reproduce real timing races, partial log loss,
clock skew, or the behaviour of elastic training frameworks.

## 3. Setup

```bash
cd book/part-5-production-operations/ch19-reliability-security-multitenancy/lab
python -m pip install -r ../../../../requirements.txt
python check.py                    # progress on starter/incident_toolkit.py
```

## 4. Background

| Topic | Manuscript section |
|---|---|
| Error taxonomy (ECC, row remapping, Xid, AER, links, firmware) | 19.3 |
| Distributed failure signatures (timeouts, hangs, stragglers) | 19.4 |
| Fast isolation workflow and rank → switch-port correlation | 19.5 |
| Containment, quarantine, smallest failure domain | 19.6 |
| Recovery, checkpoint selection, retry policy, RTO/RPO | 19.7 |
| FMEA and risk registers | 19.2 |
| Tenant isolation | 19.9–19.10 |
| Worked example (same incident) | 19.11 |

## 5. Data

| File | Contents |
|---|---|
| `rank_map.csv` | 4,096 ranks → node, local rank, pp stage, dp index, GPU UUID, GPU BDF, NUMA, HCA, HCA BDF, rail, leaf switch, leaf port, backend IP |
| `rank_progress.csv` | Flight-recorder summary per rank: blocked process group, last completed / enqueued collective sequence number, watchdog time |
| `gpu_health.csv` | Per-GPU ECC and row-remapper state for all job nodes and the spare pool |
| `host_nic_snapshot.csv` | HCA counters and transceiver DOM for pipeline stage 3 nodes (and orionxl-n451) |
| `switch_port_counters.csv` | Cumulative per-port counters every 10 min for three leaves |
| `events.jsonl` | Kernel, NCCL, PyTorch, switch, scheduler, and checkpoint events |
| `checkpoints.csv`, `restart_history.csv`, `spares.csv` | Recovery inputs. The spare pool is a declared variation (55 nodes, Poisson p99 at 5-day MTTR, outside the partition); `spares.csv` lists the 8 not already standing in for nodes in repair |
| `hypotheses.yaml` | Six hypotheses raised in the incident channel |
| `fmea.csv` | The platform risk register |
| `tenants.yaml`, `isolation_policy.yaml` | Tenant configuration and the policy it must satisfy |

## 6. Tasks

| # | Task | Functions | Acceptance criterion (checked) |
|---|---|---|---|
| 1 | Parse evidence; map ranks to hardware | `parse_xid`, `parse_netib`, `rank_to_hardware`, `gpu_bdf_to_rank` | Parsers handle real-format lines and reject others; full rank → switch-port path; Xid PCI address → rank |
| 2 | Localize | `stuck_ranks`, `common_hardware`, `implicate_links`, `bad_ports`, `gpu_actions` | The lagging group, its shared rail/stage, the implicated endpoint, the faulty port, and a health decision per affected GPU |
| 3 | Cause vs correlation | `classify_hypotheses` | Each hypothesis H1–H6 classified proven_cause / real_fault_not_cause / correlation_only / refuted |
| 4 | Contain and recover | `select_checkpoint`, `recovery_metrics`, `repeat_offenders`, `auto_restart_allowed`, `restart_plan` | Restorable checkpoint; RPO/RTO/lost GPU-hours; retry policy blocks restart until the repeat offender is excluded; healthy spares chosen; ranks remapped with coordinates preserved |
| 5 | Risk register | `fmea_score` | RPN ranking; data-quality issues detected; action-required set |
| 6 | Tenant isolation | `check_isolation` | Exactly the policy violations present, including device access outside the device plugin (`pod_security`, Section 19.9.1) |

For Task 4 assume the job resumes at **04:31:00** with the plan you produce.

## 7. Running the checker

```bash
python check.py                    # starter
python check.py --impl solution    # instructors
python check.py -v                 # tracebacks
```

## 8. Deliverable and grading rubric (100 points)

Submit `incident_toolkit.py` plus a short incident packet (`incident_packet.md`):

| Item | Points |
|---|---|
| Checker Tasks 1–2 and a **failure timeline** (01:12 → 04:31) built from the events | 15 |
| **Rank-to-hardware table** for every implicated rank (rank, node, GPU UUID, BDF, NUMA, HCA, rail, leaf port) | 10 |
| Task 3 plus a **proven vs correlated** table: for each hypothesis, the evidence for, against, and the test that would settle any remaining doubt | 20 |
| **Health decision and quarantine** for each component, naming the smallest defensible failure domain *and* the scheduling unit actually removed | 15 |
| **Safe restart plan**: checkpoint choice and restore validation steps, spares, rank remap, pre-restart checks, post-restart validation, retry policy | 15 |
| Recovery metrics (RPO, RTO, lost GPU-hours for both attempts) and what the first auto-restart cost | 5 |
| **Risk register** (top-5 risks with corrected scores, owners, mitigations) | 10 |
| **Isolation model** and remediation for every violation | 10 |

## 9. Extensions (L2 / L3)

> **Safety:** Run these only on a dedicated lab host or lab partition. Never reset GPUs, disable
> links, or inject faults on nodes carrying user jobs or on shared fabrics.

**L2 — one GPU host (read-only first):**

```bash
nvidia-smi -q -d ECC                     # volatile/aggregate correctable and uncorrectable counts
nvidia-smi -q -d ROW_REMAPPER            # remapped rows (correctable/uncorrectable), pending, failure
nvidia-smi --query-gpu=index,uuid,pci.bus_id,serial --format=csv
journalctl -k | grep -E 'NVRM: Xid|AER'
dcgmi diag -r 2                          # medium diagnostic; -r 3 for long (lab host only)
lspci -vvv -s <gpu-bdf> | grep -A3 'Advanced Error Reporting'
```

Build a real `rank_map.csv` for one host with `nvidia-smi topo -m`, `ibdev2netdev` (where available)
or `rdma link show`, and `lldpctl` / switch LLDP neighbours.

**L2 on any single GPU (scripted, read-only, with CPU fallback).** `lab/l2/experiment.py` runs the read-only
queries above that a container can run. They cover identity (UUID, BDF, serial, VBIOS, InfoROM), ECC mode,
row-remapper state and bank histogram, retired pages, the driver's recovery action, the PCIe link (device and host
maximum) with replays since reset, and `nvidia-smi topo -m`. The real row goes through the lab's `gpu_actions`.
The run then samples clock-event reasons every 200 ms through idle, GEMM, memory-copy and idle phases, reads the
per-reason counters around each phase, and classifies every phase with the chapter's rules (normal, investigate,
drain). Nothing is reset or reconfigured. Kernel Xid/AER logs, `lspci` AER, DCGM, RDMA HCAs and the L3 link-flap
trials are probed and recorded as not runnable.

```bash
python scripts/hw_labs.py build ch19
python scripts/hw_labs.py run ch19 --device gpu   # needs the NVIDIA container runtime
python scripts/hw_labs.py run ch19 --device cpu   # host health queries + /proc/pressure/cpu phases
```

Without a GPU (`--device auto` on a host with no NVIDIA driver) the CPU fallback runs automatically. It runs the
host-side read-only queries (CPU, memory, EDAC, kernel-log access) and the same phases, read through
pressure-stall information. GPU-only invariants are skipped. **Observed on the reference run:** the committed
bundles in `lab/l2/results/` (`gpu-rtx-4060-laptop-gpu/` and `cpu-fallback/`) show `GPU_IDLE` at idle,
`SW_POWER_CAP` at the enforced limit under GEMM (normal; see Section 19.3, "Thermal and power events", and Chapter 18), no limiting reason in the memory-bound copy,
and whether the driver's reason counters kept up with the sampled bitmask on that platform `[MEASURED]`.
*One stale cross-reference.* In the committed `lab/l2/results/gpu-rtx-4060-laptop-gpu/report.md`, the first
bullet under "What to conclude" (the GEMM soak at the 80 W limit) ends with "(exercise K4)". That pointer is
wrong: this chapter's K4 is about PCIe evidence. Read it as Section 19.3, "Thermal and power events", which is
what `experiment.py` now prints. Only that pointer is stale; every measured value in the report, and its other
pointers (K2, T1), are correct. Your own run writes a fresh report without the error.

**L3 — two RDMA nodes, dedicated partition.** Run `all_reduce_perf` (or a small PyTorch DDP loop) and,
with authorization, administratively disable one backend port for 3 s, 8 s, and 15 s on separate
trials. Before each trial, record the port's state and counters; after it, re-enable the port and
confirm link up at full speed with no new FEC-uncorrectable or flap counts before the next trial. When
done, leave both nodes drained until a pair test passes. Record whether the job survives, the NCCL warnings, and time to watchdog. Record in the
manifest: NIC firmware, RDMA stack, NCCL and PyTorch versions, `NCCL_IB_TIMEOUT`, `NCCL_IB_RETRY_CNT`,
watchdog timeout, link-down duration, outcome per trial, number of trials. Compare with the retry
budget computed in Section 19.4 (`[MODELED]` vs `[MEASURED]`).

## 10. Intentionally flawed inputs

The dataset contains planted traps (a misleading first reporter, a real-but-unrelated GPU fault, a
background AER stream, a downstream PFC spike, an unsafe "complete" checkpoint, an unhealthy spare,
FMEA scoring errors, and several isolation violations, one of them a GPU device-injection bypass). They are documented for instructors in
`../solutions/exercises-key.md`.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'pandas'`** (or `yaml`) → run
  `python -m pip install -r ../../../../requirements.txt` from this `lab/` folder, with the same `python`
  you run `check.py` with.
- **`FAIL import/load: ...` and no check lines** → `starter/incident_toolkit.py` has a syntax or import
  error. Fix the line it names.
- **`TODO <check>: implement <function>()`** → that function still raises `NotImplementedError`. Expected
  until you implement it. Each check names the task (T1–T6) it tests; work through them in order.
- **A `FAIL` line whose cause is not obvious** → rerun with `python check.py -v` to print the traceback.
  To try `check_isolation()` on your own tenant files, use the snippet in exercise
  [M2](../exercises/M2-tenant-isolation-boundaries/README.md).
- **`SKIP dataset reproducible`** → expected in the learner release, which ships without the data
  generator. If checks fail after you edited `data/`, restore it with `git checkout -- data/`.
- **`python scripts/hw_labs.py run ch19` fails** → run it from the repository root with Docker running, and
  run `build ch19` first. If the GPU run cannot start the container, the NVIDIA container runtime is
  missing; use `--device cpu`. A run overwrites the committed bundles in `lab/l2/results/`;
  `git checkout -- lab/l2/results` restores them.
