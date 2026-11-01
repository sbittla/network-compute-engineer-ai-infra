# Capstone F L2: contained kill-detect-recover drill with measured detect, resume and steps lost

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:17:32Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

## The drill

Job: a 1024-wide 4-layer MLP with Adam on the GPU, a heartbeat every step, an atomic checkpoint every 25 steps (~50 MB). Injection: SIGKILL at a seeded random time after the first checkpoint. Alert rule: progress age > 0.5 s for 0.25 s, polled every 50 ms.
Same form as the L1 rule `JobStalled` in `instructor/reference/gameday.py` (sim_job_progress_age_seconds > 120 for 60 s), with the threshold scaled from an ORION step (~17 s plus checkpoint stall) to this job's ~19.8 ms mean step (including the first, warm-up step).

| Rep | killed at step | restored | steps lost | heartbeat age at kill (s) | detect (s) | resume (s) | launch (s) | init (s) | ckpt load (ms) | first step (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 43 | 25 | 18 | 0.006 | 0.773 | 4.512 | 0.041 | 2.981 | 160 | 507 |
| 1 | 68 | 50 | 18 | 0.003 | 0.787 | 4.167 | 0.024 | 2.678 | 66 | 561 |
| 2 | 72 | 50 | 22 | 0.002 | 0.775 | 3.633 | 0.022 | 2.283 | 66 | 436 |
| 3 | 99 | 75 | 24 | 0.010 | 0.778 | 3.694 | 0.053 | 2.511 | 66 | 236 |
| 4 | 42 | 25 | 17 | 0.004 | 0.771 | 3.308 | 0.043 | 2.211 | 43 | 189 |

## Measured vs the simulator's recovery model

| Quantity | predicted | measured median | min-max |
|---|---|---|---|
| detect_s | 0.750 (+ up to one poll and one step) | 0.775 | 0.771-0.787 |
| checkpoint load (s) | 0.032 (bytes / 1.60 GB/s read) | 0.066 | 0.043-0.160 |
| resume_s (kill -> first new step) | 3.334 | 3.694 | 3.308-4.512 |
| steps lost | 12.0 mean, max 24 | 18 | 17-24 |

## Not runnable here

- **backend link down / up (ip link set dev <rail_iface> down)**. Probe: interfaces=['lo'], RDMA=none, uid=1000 (not root). Needs: dedicated lab node with a rail interface, root, a multi-node job using it.
- **node loss via BMC (ipmitool chassis power off / Redfish reset)**. Probe: ipmitool=False. Needs: lab BMC, written authorisation.
- **storage slowdown (tc qdisc add ... netem delay 20ms rate 1gbit)**. Probe: tc=True, uid=1000. Needs: root (CAP_NET_ADMIN) on a lab client, network storage.
- **scheduler outage (systemctl stop slurmctld) and drain/requeue**. Probe: scontrol=False, kubectl=False. Needs: lab Slurm or Kubernetes.
- **multi-node DDP with NCCL/process-group timeout**. Probe: GPUs=1. Needs: >= 2 GPU nodes with RDMA.

## What to conclude

- Recovery time is dominated by restart, not by loading the checkpoint: process launch plus framework and CUDA context initialisation take 68 % of resume_s here. A simulator that models restart as checkpoint bytes / bandwidth alone underestimates RTO. Measure launch_s on the real stack.
- Steps lost are bounded by the checkpoint interval only because a checkpoint counts once its rename commits. Kill during a save and the previous checkpoint is the one restored. The restored-step column shows it.
- Detection is threshold + hold + one poll *after the last heartbeat*. Measured from the kill it can be shorter: when the kill lands during a checkpoint write, the job has already been silent for a while (see the heartbeat-age column).
- Tighter thresholds detect faster but page on every checkpoint stall. The L1 rule's 120 s / 60 s exist because ORION's checkpoint stall is ~20 s.
- This is a **laptop Ada GPU in a container, not ORION**: the absolute seconds are not transferable, the decomposition is.

- Abort condition: the drill stops if the worker exits on its own or does not resume within 120 s. Rollback: requeue from the last durable checkpoint, verified by the restored step in the new process's heartbeat.
- Blast radius: one child process in a disposable container (--network none); nothing outside it is touched.
- Repetitions: 5 drills, each with a seeded random kill time; medians reported.
- Times are wall clock (time.time) shared by the monitor and the worker heartbeats.
