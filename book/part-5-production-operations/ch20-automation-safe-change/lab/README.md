# Lab 20 — Safe-Change Automation on ORION

## 1. Goal and the real-world task it mirrors

Automation is how a team of a few people changes 256 GPUs and 8 rail leaves without typing on 40
consoles. That leverage cuts both ways. In this lab you build the three pieces that stop automation
from turning one bad change into a fleet-wide outage:

1. **Part 1 — Idempotent validator and reconciler.** Validate a desired-state file for ORION's RoCE
   settings (MTU, PFC priority, DSCP maps, approved NIC firmware) with schema and policy rules.
   Compute a dry-run plan against the observed fleet. Apply it in capped batches to a simulated
   fleet with an audit trail. Show that a second run is a no-op. This is the core loop of every
   reconciler: Terraform `plan`/`apply`, a GitOps controller, or a Kubernetes operator.
2. **Part 2 — Canary rollout controller.** Given per-wave health evidence from a NIC firmware
   rollout (baseline and post-change samples per node), apply pre-declared prechecks, bake-time
   rules, and abort conditions. Decide *proceed*, *hold*, or *abort* for each wave, and compute the
   rollback set.
3. **Part 3 — Change-plan review.** Review a change plan that a well-meaning engineer submitted,
   and record each missing control as a structured finding. Senior engineers do this in change
   review every week.

The deliverable for the chapter, an **automation sample and a safe-change runbook**, is built from
Parts 1–2 (the automation sample) and Part 3 plus Exercise 20.10 (the runbook).

## 2. Tier and realism boundary

**Tier L1** (laptop, Python only). All data is synthetic `[SIMULATED]`, generated with seed 20 and
modeled on ORION-256 ([REFERENCE_CLUSTER.md](../../../../docs/REFERENCE_CLUSTER.md)). The fleet API
is an in-memory object (`SimFleet`). It always answers instantly and never half-applies a change.

> **Realism boundary:** The lab cannot show the hard parts of real fleet APIs. It has no timeouts,
> partial writes, eventual consistency, or settings that only take effect after a reboot or a link
> retrain. It also cannot show whether an MTU or QoS change actually changes NCCL bandwidth. The
> rollout metrics are synthetic. They teach the *decision logic*, not the physics. Section 8 gives
> the L2/L3 procedure for real evidence.

`rdma_path_mtu` models the NIC's RoCE MTU cap; on hardware the observed value is the derived `active_mtu`; SimFleet does not recompute it when `host_mtu` changes.

The data generator (`tools/generate_data.py`) is an instructor copy only and is not part of
the learner release; `data/` is committed.

## 3. Setup

```bash
cd book/part-5-production-operations/ch20-automation-safe-change/lab
python -m pip install -r ../../../../requirements.txt     # needs pyyaml
python check.py                                            # progress meter for your starter code
```

Python 3.10 or later. You edit `starter/safe_change.py` and `starter/findings.yaml`.

## 4. Background you need

| Topic | Manuscript section |
|---|---|
| Desired state, reconciliation, idempotency | §20.3, §20.4 |
| Schema and policy-as-code validation, MTU budget | §20.5 |
| Canary, waves, bake time, abort conditions | §20.7 |
| Rollback and rollback scope | §20.8 |
| Dry-run, blast-radius caps, rate limits, kill switches | §20.9 |
| Audit evidence | §20.10 |
| Worked example (MTU 1024 → 4096 change, rollout decision log) | §20.11 |

## 5. Tasks

### Part 1 — Validator and reconciler (`starter/safe_change.py`)

| # | Function | Acceptance criterion |
|---|---|---|
| 1.1 | `resolve_desired` | Every target in `desired["targets"]` gets defaults plus its overrides |
| 1.2 | `_schema_violations`, `validate_desired` | Finds every invalid desired value. Reports no false positives. Clean defaults validate with zero violations |
| 1.3 | `compute_plan` | Invalid targets are *blocked*; `None` targets are *unreachable*; only differing keys produce actions |
| 1.4 | `apply_plan` | Dry-run by default (zero writes). `max_targets` caps distinct targets per call. One audit record per action, with `before` read at apply time |
| 1.5 | Idempotency | After capped batches converge, `compute_plan` returns no actions. Re-applying the old plan writes nothing and records `noop` |

Expected output of `python starter/safe_change.py` once Part 1 works: a short list of violations,
then a one-line plan summary with the action count, blocked targets, and unreachable targets. Read
each violation and explain to yourself *why* it would hurt RoCE traffic.

### Part 2 — Rollout controller

| # | Function | Acceptance criterion |
|---|---|---|
| 2.1 | `check_condition` | Implements `relative_drop`, `relative_rise` (with absolute floor) and `sum_gt` with the declared aggregation. Reasons start with the condition ID |
| 2.2 | `evaluate_wave` | Precheck failures are skipped, not changed or evaluated; insufficient bake → `hold`; any breach → `abort`; else `proceed` |
| 2.3 | `run_rollout` | Stops at the first abort or hold; rollback set follows `rollback_scope`; later waves are reported as not started |

Write down your decision log (wave → decision → reasons). Then answer: *would a controller that used
`min` instead of `median` for bandwidth (try it: `_aggregate` supports `min`), or that ignored prechecks, have made a different decision?*

### Part 3 — Review the unsafe change plan

Read `data/unsafe_change_plan.md` (`cat -n` gives line numbers). Fill in `starter/findings.yaml`
with one entry per gap, using IDs from `data/gap_catalog.json`. Some catalogue entries are *not*
gaps in this plan. Citing one that the plan already covers is a false positive. Each finding needs
the plan line(s) that show the gap, the risk on ORION, and a concrete fix.

## 6. Running the checker

```bash
python check.py                    # your starter: TODO / FAIL / PASS per check, exit 1 until done
python check.py --impl solution    # instructors only (needs ../solutions/)
```

The checker runs 13 checks (6 for Part 1, 4 for Part 2, 3 for Part 3) in well under a second. The
Part 3 checks score coverage of the real gaps (at least 13 of them), false positives (at most 1),
and evidence quality: valid line citations, and a fix that names a concrete control. The keyword
check is a progress meter, not a substitute for instructor review of your reasoning.

## 7. Deliverable and grading rubric (100 points)

| Item | Points |
|---|---|
| Part 1: validation finds every planted defect, with a one-line explanation of each | 15 |
| Part 1: plan, dry-run, capped apply, audit trail, and idempotency demonstrated (paste the checker lines and a second-run plan of size 0) | 20 |
| Part 2: correct decision log, with a written explanation of the two traps a naive controller falls into | 20 |
| Part 2: rollback set and justification of `rollback_scope: all_changed` vs failing wave only | 5 |
| Part 3: findings coverage and precision (checker) | 15 |
| Part 3: quality of fixes (specific numbers, ORION context) — instructor-graded | 10 |
| Safe-change runbook (Exercise 20.10) built from your lab outputs | 15 |

## 8. Extensions (L2/L3)

> **Safety:** Run these only on a dedicated lab host or lab fabric that you own. Never point the
> reconciler at production or shared switches. Changing MTU or QoS on a live RoCE fabric can drop
> traffic for every tenant on it.

**L2 — one host, real config, real idempotency.** On a lab VM with an RDMA NIC, or a soft-RoCE
device, extend `SimFleet` into a `LinuxHost` adapter. Its `get` reads the real state and its `set`
changes it:

```bash
ip -d link show dev eth1                    # read IP MTU (look for "mtu 9000")
sudo ip link set dev eth1 mtu 9000          # the only mutating call your adapter makes
sudo rdma link add rxe0 type rxe netdev eth1   # soft-RoCE if no RDMA NIC (lab VM only)
rdma link show                              # RDMA link state and netdev mapping
ibv_devinfo -d rxe0 | grep -E "active_mtu|max_mtu|state"   # RDMA MTU actually negotiated
```

Run your reconciler twice and keep both audit logs. The second run must plan zero actions. Record
the `L2` fields in `manifest.yaml`: OS, kernel, NIC, firmware, driver, rdma-core version, MTU
before and after, and the size of the second-run plan.

**L3 — real canary on a lab fabric.** On ≥ 2 GPU nodes with RoCEv2 NICs and a lab leaf, build the
evidence the rollout controller consumes:

```bash
# Baseline and post-change pair test (nccl-tests), 8 GPUs per node, fixed 8 GiB message:
mpirun -np 16 -H nodeA:8,nodeB:8 ./build/all_reduce_perf -b 8G -e 8G -f 2 -g 1 -n 50 -w 10
# busbw_GBps in rollout.json is per rail: the reported busbw (all 8 rails) divided by 8
ethtool -S eth1 | grep -iE "pause|cnp|ecn"     # counter names vary by NIC vendor and driver
nvidia-smi -q -d ECC,PERFORMANCE               # Xid events appear in the kernel log: dmesg | grep -i xid
```

Switch-side reads through the device's gNMI/OpenConfig interface (paths vary by platform; verify
against your switch OS documentation):

```bash
gnmic -a leaf-lab:57400 -u admin -p "$GNMI_PASSWORD" --skip-verify get \
  --path "/interfaces/interface[name=Ethernet1/1]/state/counters"
```

Record the `L3` fields. Follow LAB_STANDARDS §5: at least 5 repetitions per sample point, median and
p95, warm-up iterations stated, and one change at a time. Feed the samples into your
`evaluate_wave` and compare its decision with your own judgement.

> **Vendor implementation note (NVIDIA):** On ConnectX-class NICs the firmware version is reported
> by `ethtool -i <netdev>` (`firmware-version`), and by `mlxfwmanager --query` from the Mellanox
> Firmware Tools (MFT) package. Use the vendor's documented burn-and-reset procedure only in the
> lab, never ad hoc.

## 9. Intentionally flawed inputs

The dataset contains planted defects in Parts 1 and 2, and the plan in Part 3 contains deliberate
gaps. They are documented for instructors in `../solutions/exercises-key.md` (Lab section). Do not
look there until you have finished.
