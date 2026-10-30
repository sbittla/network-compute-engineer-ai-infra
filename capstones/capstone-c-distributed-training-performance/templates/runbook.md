# Runbook Excerpts — Training Performance Guardrails (Capstone C)

> **Safety:** These procedures act on job submission and on the scheduler, not on the fabric. Never
> change NCCL, NIC or switch settings on shared production systems as a "fix". Changes go through the
> platform's change process.

## RB-1: Launcher transport preflight

**Purpose:** stop a multi-node job before it burns GPU-hours on a host-staged or socket path.

| Step | Check (read-only, inside the job's own container) | Pass | On failure | Owner |
|---|---|---|---|---|
| 1 | `ls /dev/infiniband/` and `ibv_devinfo` list the 8 backend HCAs | 8 devices, ports ACTIVE | Fail the job with "RDMA devices not visible in container"; page Platform | Platform |
| 2 | `nvidia-smi topo -m` matches the golden topology (GPU *i* PIX NIC *i*) | identical | Fail; open a Fleet ticket for the node | Fleet |
| 3 | Rank-0 NCCL INFO log after init: `Using network IB`; channel lines contain `/GDRDMA` | both present | Fail on `Using network Socket`; warn if `/GDRDMA` is absent (host-staged) | Training Infra |
| 4 | <fill: short `all_reduce_perf` smoke test across the allocation (≤ 60 s)> | busbw ≥ <fill> GB/s | Fail; list the slowest node pair | Training Infra |

**Approvals:** turning the preflight off for a job needs Training Infra lead approval, recorded in the job metadata.

## RB-2: Scaling-regression alert

**Signal:** the job's weak-scaling efficiency E(N) or tokens/s per GPU drops by more than 3 % from its recorded
baseline for the same configuration, over ≥ 30 steady-state steps.

| Step | Action | Owner | Approval |
|---|---|---|---|
| 1 | Compare the job manifest with the baseline manifest (image digest, NCCL version, NCCL env, node set) | Training Infra on-call | none |
| 2 | Read rank-0 NCCL log for transport and GDR; check per-node step-time skew (straggler) and DCGM clock-event reasons | Training Infra on-call | none |
| 3 | <fill: if one node is the straggler, drain it in Slurm (stops new placement only), then checkpoint and restart without it. There are no spares, so the restart runs at reduced DP; the restart costs ≈ 900 s> | Training Infra lead | Platform |
| 4 | <fill: if the environment drifted, roll the image or configuration back to the baseline digest> | Platform | Change advisory |
| 5 | Validate: ≥ 8 runs or ≥ 200 steady steps back within the baseline CI | Training Infra | none |

**Escalation:** <fill>.
