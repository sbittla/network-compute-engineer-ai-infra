# M1 — Failure-mode analysis (risk register): reference solution

**Relies on:** Section 19.2 (Table 19.1 fault domains, "FMEA and the risk register", Table 19.2);
Sections 19.3–19.7 for the failure mechanisms; lab `data/fmea.csv` and `fmea_score()` (Task 5). Scores
are `[ILLUSTRATIVE]` judgments, justified per row.

## Scales

Severity S (impact), Occurrence O (likelihood), Detection D (how *unlikely* we are to detect the failure
before impact; 10 = undetectable), each 1–10. RPN = S × O × D. RPN is ordinal, so priority also uses an
**action-priority** rule: act on RPN ≥ 200 **or** S ≥ 9, as `fmea_score(rpn_threshold=200,
severity_override=9)` does. Every detection score must be consistent with the stated control. A control
of "none" forces D = 10.

## Register (14 rows, all six domains)

| ID | Domain | Failure mode | Effect: training | Effect: inference | S | O | D | RPN | Justification | Detection control | Mitigation | Owner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N1 | GPU node | Uncorrectable ECC / remap failure | Rank crash → job restart | One replica lost | 7 | 6 | 3 | 126 | Common at fleet scale; Xid 48/64 detected immediately | DCGM health + Xid alert | Row-remap policy (K2); fast restart | Platform |
| N2 | GPU node | Intermittent HCA link flap | 10-min hang, then restart (INC-3107) | Usually none (TP inside node) | 8 | 7 | 6 | **336** | Two attempts lost in one night; only raw link-down logs, no flap-rate alert | Link-down log only | Flap-rate alert; quarantine after 2 flaps/24 h; DOM warn at −4 dBm | Fabric |
| N3 | GPU node | PCIe link downtrained after reboot | Whole job slower (T1) | One slow replica, p99 latency up | 6 | 4 | 8 | 192 | Silent: no errors, only step-time drift | None until drift noticed | `LnkSta` = `LnkCap` check on every boot | Platform |
| N4 | GPU node | GPU off the bus (Xid 79) | Rank loss → restart | Replica lost | 7 | 4 | 2 | 56 | Loud failure, detected at once | Xid alert + health check | Cold reboot, diagnostics, RMA | Platform |
| R1 | Rack | PDU breaker trip / feed loss | 4 nodes lost; restart inrush may re-trip | Replicas in that rack lost | 8 | 3 | 4 | 96 | 2N feeds make it rare; PDU telemetry alerts | PDU telemetry alert | Spread replicas across racks; staged restart | Facilities |
| R2 | Rack | CDU pump failure (row loop) | Thermal throttle, then shutdown of many nodes | Many replicas | 10 | 2 | **10** (was 2) | **200** | Control is "none", so D = 2 was inconsistent | None → add pump-state alarm | Pump telemetry and alarm; redundant pump | Facilities |
| L1 | Leaf switch | Reboot / ASIC fault | 32 nodes lose a rail; all jobs on them stall | Minimal | **9** | 3 | 3 | 81 | Low RPN but severity override | gNMI oper-status ON_CHANGE | Spare switch on site; runbook; placement | Fabric |
| L2 | Leaf switch | QoS change puts PFC on the wrong priority | Rail-wide drops; bus bandwidth collapse | Frontend unaffected | **9** | 3 | 6 | 162 | Valid values, wrong relationship; seen only after the change | Post-change counters | Cross-object policy validation; one-leaf canary (Chapter 20) | Fabric |
| S1 | Storage | Metadata server failover | Checkpoint stalls; RPO grows | Model loads stall | 7 | 4 | 5 | 140 | Checkpoint-duration SLO catches it late | Checkpoint SLO alert | HA metadata; two-tier checkpoints | Storage |
| S2 | Storage | Checkpoint "complete" but metadata uncommitted | Restore fails or falls back (ckpt-0085) | — | 8 | 3 | 7 | 168 | Async saves make it plausible; only a log line | Trainer log | Validate metadata commit and checksums in selection | Training Infra |
| C1 | Scheduler | slurmctld failover | No new starts or requeues for minutes | — | 4 | 3 | 3 | 36 | Running jobs continue | HA heartbeat | Active/standby controller | Platform |
| C2 | Scheduler | Auto-requeue onto the same faulty nodes | Repeat hang: 5,530 GPU-h in the lab | — | 8 | 5 | 6 | **240** | Happened in INC-3107; nothing gates it | Job-failure alert only | Retry gate: exclude implicated nodes; ≤ 2 restarts/6 h | Platform |
| P1 | Control plane | etcd quorum loss | — (Slurm) | Rollouts, scaling, self-healing blocked | 8 | 2 | 4 | 64 | 3/5-member etcd makes it rare | etcd health alert | Members across fault domains; backups | Platform |
| P2 | Control plane | API server overload from restart storm | — | Deploys and autoscaling slow | 6 | 3 | 5 | 90 | Seen in containment exercises (M3) | API latency alert | Per-tenant rate limits; priority and fairness | Platform |

Running the lab's `fmea_score()` on this register sorts it as N2 336, C2 240, R2 200
(DETECTION_INCONSISTENT, re-scored), N3 192, S2 168, L2 162 …. `action_required` is true for N2, C2,
R2 (RPN ≥ 200) and L1, L2 (S = 9 override).

## Top-5 actions with owners

1. **N2 (336):** flap-rate alert and auto-quarantine after 2 flaps in 24 h; DOM threshold tickets. Owner: Fabric.
2. **C2 (240):** retry-loop gate that excludes implicated nodes before any automatic restart and blocks
   repeat offenders. Owner: Platform.
3. **R2 (200, S = 10):** pump-state telemetry with alarm, and a redundant pump. Owner: Facilities.
4. **L1 (S = 9 override):** spare leaf on site, a replacement runbook, and placement that minimizes jobs per leaf. Owner: Fabric.
5. **L2 (S = 9 override):** cross-object policy validation and one-leaf-first canary for QoS changes. Owner: Fabric with Platform CI.

Next in line: N3 (boot-time link-width check) and S2 (checkpoint metadata validation). Both are cheap,
and S2 directly cost about 30 minutes of extra RPO (31 min instead of ≈ 1 min) in INC-3107.

## Common wrong answers

- Fewer than six domains (scheduler and control plane are often missing).
- Low D with a control of "none" (the F07 trap).
- Ranking by RPN alone, so severity-9 leaf failures drop out.
- Generic owners ("ops") instead of a named team.
