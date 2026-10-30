# Capstone F Starter Kit — Game Day on a Simulated ORION

## 1. Goal and the real-world task it mirrors

SRE teams prepare game days by writing a plan, predicting outcomes, deciding which alerts should
fire, and afterwards reconstructing what happened from logs and alerts. This kit gives you a
seeded discrete-event simulator of ORION (`sim/cluster_sim.py`, fully implemented), the recording
of Halcyon's first game day, and a module (`starter/gameday.py`) in which you implement the plan,
the alert rules and the analysis.

## 2. Tier and realism boundary

**Tier L1** — laptop, Python 3.10+, no GPU, no root, no network. Evidence class `[SIMULATED]`.
Read the simulator's module docstring: it lists what the model includes and, more importantly,
what it does **not** capture. Quote that list in your report.

> **Safety:** Nothing in this kit touches a real system. Keep it that way: do not add code that
> shells out to `ip`, `systemctl`, `scontrol` or any other real tool.

## 3. Setup

```bash
cd capstones/capstone-f-reliability-game-day/starter-kit
python -m pip install -r ../../../requirements.txt     # numpy, pandas, pyyaml
python check.py                                        # 2/11 PASS at the start
```

## 4. Using the simulator

```python
import sys; sys.path.insert(0, ".")            # run from starter-kit/
from sim import cluster_sim
faults = [{"id": "X1", "kind": "node_loss", "target": "orion-n09", "start_s": 3000}]
rules  = [{"name": "NodeDown", "metric": "sim_node_up", "op": "==", "threshold": 0,
           "for_s": 60, "severity": "critical", "detects": ["node_loss"]}]
res = cluster_sim.run(faults, rules)                       # 6 h horizon, deterministic
res = cluster_sim.run(faults, rules, {"fast_fail": True})  # what-if: change a parameter
for e in res.events[:5]: print(e)                          # {'t': ..., 'kind': ..., ...}
print(res.alerts)                                          # rule, labels, t_fire, t_resolve, detects
```

**Fault kinds** (`kind` field): `link_down` (`target` node, `rail` 0–7, optional `duration_s`),
`node_loss` (`target`; permanent unless `duration_s`), `storage_slow` (`factor` multiplies storage
bandwidth, `duration_s`), `scheduler_outage` (`duration_s`). Times are seconds from the start of
the run.

**Series** scraped every 15 s: `sim_node_up{node}`, `sim_nic_link_up{node,rail}` (absent while the
node is down), `sim_job_progress_age_seconds{job}`, `sim_job_running{job}`,
`sim_checkpoint_age_seconds{job}`, `sim_storage_write_GBps`, `sim_scheduler_heartbeat` (absent
while the scheduler is down), `sim_inference_ready_replicas`.

**Rules:** `{"name", "metric", "op": "<"|">"|"=="|"!="|"absent", "threshold", "for_s", "severity",
"detects": [fault kinds]}` — evaluated per series at each scrape; `for_s` must hold continuously.

**Event kinds** you will meet: `fault_start/end`, `job_hung`, `job_failed`, `job_requeued`,
`requeue_blocked`, `job_restarted` (`from_step`, `steps_lost`), `job_resumed`, `node_drained`,
`drain_pending`, `ckpt_started`, `ckpt_durable`, `ckpt_aborted`, `ckpt_skipped`,
`alert_firing/resolved`.

## 5. The dataset

| File | Contents |
|---|---|
| `data/default_alert_rules.yaml` | The four rules Halcyon ran game day 1 with |
| `data/gameday_constraints.yaml` | Horizon, warm-up, protected nodes, max concurrent faults, detection targets, false-alert budget |
| `data/gameday1_plan.yaml` | The five faults injected on game day 1 |
| `data/gameday1_events.jsonl`, `gameday1_alerts.jsonl`, `gameday1_final.json` | The recording |
| `data/backlog_candidates.csv` | Six candidate reliability improvements with `[ILLUSTRATIVE]` frequency and impact estimates |

## 6. Tasks

| Task | Function | Acceptance criterion | Points |
|---|---|---|---|
| **T1** Fault-injection plan | `fault_plan` | ≥ 5 scenarios; all four fault kinds; ≥ 1 overlapping pair; no protected targets; after warm-up; ≤ 2 concurrent; hypothesis, expected numbers, abort conditions, blast radius and rollback for each; executes in the simulator | 18 |
| **T2** Alert rules | `alert_rules` | Zero alerts in a fault-free 6 h run; node loss, link loss and scheduler outage detected ≤ 120 s, storage degradation ≤ 300 s, in the checker's canonical scenarios | 18 |
| **T3** Detection time | `detection_time` | Correct per-fault detection on the recorded game day, including *undetected* faults; only alerts inside [onset, onset + 2 × target] count | 10 |
| **T4** Recovery metrics | `recovery_metrics` | Mitigation, recovery and lost GPU-hours on the recorded game day; restore point from the last *durable* checkpoint; unrecovered faults reported as such | 22 |
| **T5** Incident timeline | `build_timeline` | Sorted, windowable, noise-free timeline with UTC and `T+` offsets | 12 |
| **T6** Hypothesis evaluation | `evaluate_hypotheses` | Correct held/failed verdicts; an undetected fault never meets a detection target | 8 |
| **T7** Backlog prioritisation | `prioritize_backlog` | Correct scores and order; your report must then critique the formula | 12 |
| | | **Total** | **100** |

Hints:

- Run the default rules on an empty fault list first. Count what fires and ask why.
- On the recorded game day, find every `ckpt_aborted` event before you compute lost work.
- One fault on the recorded day never recovers. Find out why before you write the postmortem —
  the failed component is not the cause.
- Re-run the recorded plan with *your* rules and with `{"fast_fail": True}`; compare.

## 7. Running the checker

```bash
python check.py            # ≈ 9 s; prints PASS/FAIL/TODO per check; exit 0 only when 11/11
```

The checker runs a dataset-integrity check (instructor copy only; `SKIP` in the student release),
confirms the simulator is deterministic, runs your plan and rules through the simulator, and compares your
analysis of the recorded game day with the expected values.

## 8. L2/L3 extension: safe fault injection in a dedicated lab

Outline Section 16: *conduct safe fault injection in a dedicated non-production lab with explicit
rollback and isolation.*

> **Safety:** Proceed only with written authorisation for a dedicated lab whose hosts, fabric and
> storage are not shared with any other user or workload. Before each injection, write the abort
> condition and rehearse the rollback. Keep an out-of-band path (BMC console) to every host you
> disrupt. Never run these commands on production or shared systems.

| Fault | Inject (lab only) | Roll back | Observe |
|---|---|---|---|
| Backend link down | `sudo ip link set dev <rail_iface> down` | `sudo ip link set dev <rail_iface> up` | `rdma link show`, `ip -s link show <rail_iface>`, job logs for the collective timeout |
| Node loss | `ipmitool -I lanplus -H <bmc> -U <user> -P <pass> chassis power off` (or a Redfish `ComputerSystem.Reset` action) | `... chassis power on`, then re-run acceptance before undrain | `sinfo -R`, `scontrol show node <node>`, job requeue in `squeue` |
| Storage slow | `sudo tc qdisc add dev <storage_iface> root netem delay 20ms rate 1gbit` on the lab client only | `sudo tc qdisc del dev <storage_iface> root` | Checkpoint write duration in job logs; PFS client stats |
| Scheduler outage | `sudo systemctl stop slurmctld` on the lab controller | `sudo systemctl start slurmctld` | `scontrol ping`, `journalctl -u slurmctld`, absence alert firing |

For Kubernetes-based labs, chaos frameworks (for example Chaos Mesh or LitmusChaos) provide
equivalent injections with built-in duration limits; use their documented experiment types only.

Run a real multi-node job (for example a small PyTorch DDP model with periodic checkpoints across
two nodes) and measure, over at least 3 repetitions per fault: time to first alert, time to drain,
time to job failure (record the configured process-group/NCCL timeout), time to resume, steps
lost, and the restore step. Compare with your simulator predictions and explain every difference.

What to record (copy `manifest.yaml`, set `tier: L3`, `evidence_class: MEASURED`): node and GPU
models, driver/CUDA/NCCL/PyTorch versions, scheduler and version, configured collective timeout,
checkpoint mechanism and size, storage system, monitoring stack and versions, alert rules used,
injection tool and exact command, repetitions, and the rollback verification for every injection.

## 9. Files

```text
starter-kit/
├── README.md
├── manifest.yaml
├── check.py
├── sim/cluster_sim.py      given simulator
├── data/                   generated (do not edit)
├── tools/                     generator: instructor copy only (removed from the student release)
└── starter/gameday.py      implement here
```
