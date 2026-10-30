# Lab 16 — Fleet Lifecycle Automation (Progressive Lab 7, part 1)

## 1. Goal and the real-world task it mirrors

Halcyon AI's Fleet team owns ORION's 32 HX8 nodes from delivery to retirement. In this lab you write
the four pieces of automation that team runs every day:

1. a **compatibility checker** that tells whether a node's firmware/driver stack is a validated
   bundle (and, if not, what to fix);
2. an **acceptance evaluator** that turns raw per-node acceptance results into PASS / WARN / FAIL
   with reason codes, for the 32-node build-out;
3. a **guarded lifecycle state machine** with an append-only audit log, replayed over a week of
   operational events, some of which are unsafe shortcuts it must refuse;
4. a **staged-upgrade planner** that produces a canary + wave plan with blast-radius caps.

This is the code behind Capstone E, and Chapter 17's scheduler lab (Progressive Lab 7, part 2,
[../../ch17-kubernetes-slurm-scheduling/lab/](../../ch17-kubernetes-slurm-scheduling/lab/)) treats
only `schedulable` nodes as eligible.

## 2. Tier and realism boundary

**Level 1** (laptop, no GPU, no root). Inputs are synthetic but shaped like real tool output
(`nvidia-smi` fields, `ethtool` speeds in Mb/s, DCGM results, `ib_write_bw` Gb/s, NVMe SMART).
The lab proves *logic*: policy evaluation, guards, audit, planning. It cannot prove that any physical
node is healthy; the L2/L3 extension (Section 8) collects the same JSON from real hardware.
All thresholds and version strings are `[ILLUSTRATIVE]`.

## 3. Setup

```bash
cd book/part-5-production-operations/ch16-bare-metal-fleet-lifecycle/lab
python --version                         # 3.10+
pip install -r ../../../../requirements.txt   # needs pyyaml
python check.py                          # progress meter on starter/fleet_lifecycle.py
```

## 4. Background

- Lifecycle states and guards: manuscript Section 16.1 (Figure 16.1) and 16.11.
- Acceptance checks, thresholds, normal-vs-defect behaviours: Section 16.5 (Table 16.4).
- Compatibility bundles and blocked versions: Section 16.7.
- Canary, waves, per-rack caps, lower bound on wave count: Section 16.8.

Data files in `data/` (committed; the generator that produced them is an instructor copy only and is
not part of the student release). The six nodes that fail build-out acceptance in
`acceptance_results.json` were repaired and re-accepted before the ops week, which is why
`inventory.json` lists them as `schedulable` and the planner may place them in waves.

| File | Content |
|---|---|
| `acceptance_policy.yaml` | Expected HX8 configuration and thresholds (policy `acc-2026.10`) |
| `compat_matrix.yaml` | Bundles B-2025.11 (deprecated), B-2026.04 (production), B-2026.10 (production, upgrade target) and a blocked list |
| `acceptance_results.json` | One record per node: firmware, 8 GPUs (PCIe, NVLink, ECC, row remap, burn-in thermals), DCGM, 10 NICs, NVMe, single-node NCCL, Xid events |
| `inventory.json` | CMDB snapshot at the start of the ops week: state, firmware, drain, ticket |
| `lifecycle_events.json` | 36 ordered events (`seq`, `ts`, `node`, `event`, `actor`, `evidence`) |

## 5. Tasks

Implement the functions in `starter/fleet_lifecycle.py`. Each docstring is the exact contract.

**Task 1 — `check_compat` (15 pts).** Classify a firmware dict as OK / DEPRECATED / OFF_MATRIX /
BLOCKED, with closest bundle and mismatching components. A component may be a list (all 8 compute
NICs' firmware). *Accept:* checks `T1.*` pass.

**Task 2 — `evaluate_node` (35 pts).** Apply the policy. Every threshold comes from the policy file —
no hard-coded numbers. Watch for behaviours that look like faults but are not (they are described in
Section 16.5). *Accept:* `T2.*` pass; fleet verdict counts and digest match the reference.

**Task 3 — lifecycle state machine (25 pts).** `transition_table`, `apply_event`, `replay`. Every
event — applied or rejected — appends exactly one audit record; rejected events never change state;
`replay` must not mutate its input. *Accept:* `T3.*` pass, including the invariant that nothing
reaches `schedulable` except from `validated` or a cancelled maintenance drain.

**Task 4 — `plan_upgrade_waves` (15 pts).** Plan the move to B-2026.10: canary of 2 nodes in
different racks, waves of ≤ 4 nodes and ≤ 1 node per rack, minimal number of waves, deterministic.
*Accept:* `T4.*` pass.

**Task 5 — acceptance and lifecycle report (10 pts).** Run `python report.py > acceptance_report.md`
and add, for every non-PASS node, (a) the raw evidence value(s) that triggered each code, (b) the
most likely physical cause, (c) the remediation and the lifecycle event sequence that returns the
node to service. For the rejected lifecycle events, explain in one line each what the guard
prevented. *Accept:* graded by the rubric below.

## 6. Running the checker

```bash
python check.py                     # your starter implementation; exits non-zero until all pass
python check.py --impl solution     # instructor reference (requires solutions/)
```

Output is one line per check: `PASS`, `FAIL` (with the reason), or `TODO` (function still raises
`NotImplementedError`). Dataset-level checks compare a SHA-256 digest of your results with the
reference, so a FAIL tells you *that* something differs; use the fixture checks and `report.py` to
find *what*.

## 7. Deliverable and grading rubric (100 points)

| Item | Points |
|---|---|
| Task 1 `check_compat` (all T1 checks) | 15 |
| Task 2 `evaluate_node` (all T2 checks; policy-driven, no magic numbers) | 35 |
| Task 3 state machine (all T3 checks; guards in one place; audit complete) | 25 |
| Task 4 planner (all T4 checks) | 15 |
| Task 5 report: correct physical cause and remediation for each non-PASS node; guard explanations | 10 |

The report feeds the chapter deliverable (exercise D1: node acceptance automation specification and
lifecycle runbook).

## 8. Extensions (L2 / L3): produce the acceptance JSON from real hardware

> **Safety:** Run only on a dedicated lab node you own or are authorised to test, never on a node
> carrying production work. Burn-in draws full power; tell the facility owner. `fio` below is
> read-only; never run write tests against drives holding data.

**L2 (one GPU host).** Collect each field of an `acceptance_results.json` record:

```bash
nvidia-smi --query-gpu=index,uuid,pci.bus_id,name,memory.total,vbios_version,driver_version --format=csv
nvidia-smi --query-gpu=index,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max --format=csv  # once idle, once under load
nvidia-smi -q -d ECC,ROW_REMAPPER
nvidia-smi nvlink --status
systemctl is-active nvidia-fabricmanager            # NVSwitch systems only
dcgmi diag -r 3 -j > dcgm_r3.json
nvidia-smi --query-gpu=index,temperature.gpu,power.draw,clocks.sm,clocks_event_reasons.active --format=csv -l 60 > burnin.csv   # during burn-in
NCCL_ALGO=NVLS NCCL_DEBUG=INFO ./build/all_reduce_perf -b 8 -e 8G -f 2 -g <num_gpus> 2>&1 | tee nccl_nvls.log
#   confirm in the INFO init log that NVLS initialised; repeat >= 5 times; record median and min/max busbw at 8 GiB
NCCL_ALGO=Ring NCCL_DEBUG=INFO ./build/all_reduce_perf -b 8 -e 8G -f 2 -g <num_gpus> 2>&1 | tee nccl_ring.log
#   Ring baseline, same repetitions; record nccl_version and "algorithm" ("NVLS" or "Ring") in the JSON for each run
sudo nvme list; sudo nvme smart-log /dev/nvme0
sudo fio --name=seqread --rw=read --bs=1M --iodepth=32 --ioengine=libaio --direct=1 --runtime=60 --time_based --filename=/dev/nvme0n1
sudo dmesg -T | grep -i xid
```

Write a small collector that emits the same JSON schema, then run your `evaluate_node` against it
with the lab policy (adjust `expected` for your GPU count/model and say so in the manifest).

**L3 (two or more nodes with RDMA).** Per compute NIC:

```bash
ethtool <netdev> | grep -E 'Speed|Link detected'
ibv_devinfo -d <rdma_dev> | grep -E 'fw_ver|state|active_mtu|link_layer'
show_gids <rdma_dev>        # pick the RoCEv2 GID index (vendor tool; or inspect /sys/class/infiniband/<dev>/ports/1/gids)
# reference node on the same rail (server; flags must match the client): ib_write_bw -d <dev> -x <gid_idx> -F --report_gbits -s 65536 -D 10 -q 4
ib_write_bw -d <dev> -x <gid_idx> -F --report_gbits -s 65536 -D 10 -q 4 <reference_node_ip>
```

Also read the firmware inventory out-of-band (`curl .../redfish/v1/UpdateService/FirmwareInventory`)
and compare with in-band versions. Record everything listed under `extensions` in `manifest.yaml`
(copy it to `manifest.local.yaml` and fill in real values, run counts, and warm-up policy). Label all
resulting numbers `[MEASURED]` with a pointer to that manifest.

## 9. Intentionally flawed inputs

The dataset contains planted acceptance defects, distractors that must *not* fail, and lifecycle
events that must be refused. They are documented for instructors only in
`../solutions/lab/PLANTED_FAULTS.md`.
