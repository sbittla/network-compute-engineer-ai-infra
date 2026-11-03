# M3 — Misleading nominal counts: model answer

Sources: manuscript Sections 21.2 (nominal versus usable, ORION-XL waterfall), 21.3 (onboarding), 21.5
(oversubscription), 21.7 (cooling), 21.9 and 21.11; lab Task 6 covers stranded GPUs, reserve shortfall
and per-GPU cost. Examples `[MODELED]` from `[ILLUSTRATIVE]` inputs.

| Bottleneck | Mechanism | Quantified ORION / ORION-XL example | Telemetry that reveals it |
|---|---|---|---|
| **Energized power** | Delivered GPUs wait for facility power | 2028Q2–Q3: 1,024 installed, 560 energized → 464 stranded ≈ $3.05M per quarter at $3.00/GPU-h | Installed versus energized node counts; PDU/EPMS load against budget; nodes in a "racked, unpowered" lifecycle state |
| **Cooling** | CDU heat capacity or supply temperature limits nodes or forces caps | Design B with half the CDU capacity: ⌊500 / 11.44⌋ = 43 nodes instead of 62; 2 % of GPUs 10 % slower → whole job ≈ 10 % slower | CDU heat load, supply/return ΔT, pump redundancy; `HW_THERMAL_SLOWDOWN` clock-event reasons per row |
| **Maintenance reserve** | Rolling firmware/OS work drains nodes | 3 % of ORION-XL = 123 GPUs (16 nodes/day rollout keeps ≈ 3 % out for a month) | Scheduler drain reasons "maintenance"; change calendar |
| **Repair (failure reserve)** | Failed nodes wait out the MTTR | 5-day MTTR × 0.5 failures/day = 2.5 of 32 nodes = 7.8 %; ORION-XL 40 nodes. Spares outside the partition are *extra* capex | Nodes in `repair` state, age in repair, RMA queue |
| **Fragmentation** | Gang jobs need whole nodes; free GPUs are scattered over part-used nodes | 5 % reserve; Section 21.11: 44 GPUs free but only 2 whole nodes while a 4-node job queued for 4 days | Whole-free-node count and free-GPU histogram per node at queue-head wait times; queue wait by job size |
| **Allocation headroom** | Queues explode near 100 %, so plan ≤ 85 % | 420 demand needs 494.1 usable GPUs | Allocated/usable GPU-hours; queue wait p50/p95 |
| **Goodput** | Failures and restarts redo work | 512-node job: ≈ 81 % at τ = 19 min; ORION-XL 2,958 allocated → 2,396 effective | Step records, checkpoint/restart logs, lost GPU-hours per incident |
| **Network oversubscription** | Cross-spine collectives slow at 2:1 | Comm efficiency 1 / (1 + 0.15 × 0.5) = 0.93; checkpoint storms limited by the 1.5:1 frontend | Spine utilization and ECN/PFC counters; exposed-comm fraction from profiles |
| **Storage** | Concurrent checkpoints share ≈ 80 GB/s | 980 GB checkpoint ≥ 12 s alone, ≈ 24 s with twice the jobs; every blocking second is paid by every GPU | PFS write throughput, checkpoint duration per job |
| **Onboarding** | Dock ≠ in service | 64-node expansion: 2–3 weeks to schedulable, 95 % first-pass yield → ≈ 3 nodes trailing 1–2 weeks | Lifecycle state counts; acceptance failure rate; days from delivery to `IDLE` |
| **Peak-sized inference pools** | Sized for peak + N+2, average load low | `chat-70b`: 96 GPUs, ≈ 4 of 12 replicas busy on average (33 %) | Per-pool allocation by hour of day |

**Putting it together.** The ORION-XL waterfall: 4,096 nominal → 3,480 usable → 2,958 allocated →
2,396 GPU-equivalents of retained progress, ≈ 58 % of nominal before MFU (Section 21.2).

**Marking notes.** At least six rows, which must include power, cooling, reserves, fragmentation,
network, storage and onboarding. Each row needs a number and a signal. Deduct for rows with no number,
or for treating `GPU_UTIL` as the signal for any of these.
