# Capstone E Starter Kit — Fleet Lifecycle Controller Prototype

## 1. Goal and the real-world task it mirrors

You are building the decision core of a bare-metal lifecycle controller: the code that a Fleet
team runs between the provisioner, the acceptance runner, the scheduler and the audit store. In
production this logic sits behind a queue and an API; here it is a pure Python module (`fleet.py`)
that you drive with a week of synthetic ORION evidence. Every function you write has a direct
production counterpart:

| Function | Production counterpart |
|---|---|
| `lifecycle_spec()` | The state machine definition reviewed by the change-advisory board |
| `evaluate_acceptance()` | The admission gate run after every (re)image |
| `check_compatibility()` | The firmware/driver drift detector |
| `apply_event()` / `replay()` | The controller's event handler, fed by an at-least-once queue |
| `plan_waves()` | The rollout planner for a new bundle |
| `canary_decision()` | The automated promote/abort gate after soak |
| `plan_remediation()` | The reconciliation loop (desired vs observed) |
| `audit_append()` / `audit_verify()` | The tamper-evident change log and Security's verifier |

## 2. Tier and realism boundary

**Tier L1** — laptop, Python 3.10+, no GPU, no root, no network. Evidence class `[SIMULATED]`: all
inputs are synthetic (seeded; the generator is an instructor copy only) and resemble the outputs of real tools.
The kit proves your *decision logic*; it cannot prove that the thresholds suit your hardware or
that a firmware procedure is safe (see [the brief, Section 7](../README.md#7-realism-and-simulation-boundary-what-to-state-in-your-report)).

## 3. Setup

```bash
cd capstones/capstone-e-fleet-lifecycle-automation/starter-kit
python -m pip install -r ../../../requirements.txt      # numpy, pandas, pyyaml
python check.py                                         # your progress: 1/17 PASS at the start
```

## 4. The dataset

| File | Contents |
|---|---|
| `data/inventory.csv` | 41 nodes: ORION racks `rack-01`–`rack-08` (`role` = training or inference partition), expansion racks `rack-09`–`rack-10`, retired `orion-lab-n01`. One row per node with current state and the installed version of every bundle component; `gpu_vbios` lists all eight GPUs separated by `;` |
| `data/compat_matrix.csv` | Four bundles: `B-2026.04` (deprecated), `B-2026.07` (golden), `B-2026.10` (canary), `BLK-0001` (blocked) |
| `data/acceptance_policy.yaml` | Versioned thresholds (`acceptance-2026.10`) |
| `data/acceptance_results.json` | Acceptance evidence for the ten nodes (re)imaged this week |
| `data/events.jsonl` | 36 lifecycle events as delivered by the queue — **not** in time order, and the queue is at-least-once |
| `data/rollout_constraints.yaml` | Canary size, wave caps, per-partition capacity floors, expiring-bundle priority, canary soak thresholds |
| `data/canary_metrics.csv` | Soak results for four canary scenarios `S1`–`S4`: two canaries on `B-2026.10` (orion-n01 training, orion-n25 inference — the planner's canary) and two golden-bundle baselines per partition. Training rows carry step time; inference rows carry serving TPOT p95 |
| `data/audit_log.jsonl` | 40 records exported from the controller's hash-chained audit log |

All version strings and measurements are `[ILLUSTRATIVE]`; they are not statements about any
vendor's real compatibility.

## 5. Tasks

Implement the functions in `starter/fleet.py`. Each task lists the acceptance criterion the checker
applies; your design document must also *explain* each decision.

| Task | Function(s) | Acceptance criterion | Points |
|---|---|---|---|
| **T1** State machine | `lifecycle_spec` | Seven outline states; `discovered` initial; `retired` terminal; every state reachable and able to reach `retired`; no path to `schedulable` that avoids `validated`; no `repair`/`retired` directly from `schedulable` | 12 |
| **T2** Acceptance gate | `evaluate_acceptance` | Exact failure set for every node imaged this week; thresholds read from the policy (the checker changes the policy and expects your verdicts to change) | 16 |
| **T3** Compatibility | `check_compatibility` | Correct status for all 41 nodes, including per-GPU firmware uniformity and an explanation for stacks that match no bundle | 12 |
| **T4** Event handling | `apply_event`, `replay` | Idempotent noop vs rejection; guards on `acceptance_complete`, `admit`, `undrain`; time-ordered, at-most-once replay; expected final states; no admission without passing both gates | 18 |
| **T5** Rollout waves | `plan_waves` | Every eligible node exactly once; canary on distinct racks; per-rack and per-partition floors respected (pending drains excluded); the minimum number of waves; expiring bundle first; refuses impossible constraints | 12 |
| **T6** Canary gate | `canary_decision` | `S1` promote, `S2` abort, `S3` extend, `S4` abort, with reasons naming node and metric | 10 |
| **T7** Remediation | `plan_remediation` | Drain-before-reimage for a schedulable node on a bad stack; deprecated nodes scheduled, not drained; converged fleet → empty plan | 10 |
| **T8** Audit trail | `audit_append`, `audit_verify` | Detects the tampered record in the export; detects edits and deletions in a fresh chain; hashes match the controller's format | 10 |
| | | **Total** | **100** |

Hints that save hours:

- Read the docstrings: they are the specification. Where a docstring and your intuition differ,
  the docstring wins — and your design document may argue for a change.
- Look at *every* field of the acceptance evidence for every node before writing the gate. At least
  one node fails on something other than a measured value, and at least one alarming-looking
  number is not a failure.
- `replay()` receives events in delivery order. Ask what happens if you apply them as delivered.
- A canary gate that averages the canaries hides exactly the regression it exists to catch.

## 6. Running the checker

```bash
python check.py                    # checks starter/fleet.py
```

Each line reads `PASS`, `FAIL` or `TODO` followed by the check name and a short reason. The exit
code is 0 only when all 17 checks pass. The checker runs in about 2 s and touches no hardware or
network. The first check is a dataset-integrity check that only runs in the instructor copy; in
the student release it prints `SKIP` and counts as passed.

## 7. Deliverable

Your repository with `starter/fleet.py` passing 17/17, plus the design artifacts in
[../templates/](../templates/). Paste the checker output into your results table with evidence class
`[SIMULATED]`.

## 8. L2/L3 extension: real provisioning and health checks

The advanced extension (outline Section 16: *integrate a lab provisioning system and real hardware
health checks*) replaces the synthetic producers in Figure E.1 with real ones. Do this **only on
dedicated lab hardware you are authorised to reimage**.

> **Safety:** Every command below either reads state or changes state on the lab node it targets.
> Commands that drain, reimage or flash are labelled. Never run them against shared or production
> systems. Firmware flashing follows the vendor's documented procedure only.

### 8.1 Provisioning integration (L3)

Map the provisioning system's node states onto yours and emit `image_complete` from its
"deployment finished" signal. Representative state models (verify against the version you deploy):

| Your state | OpenStack Ironic provision state | MAAS status | Metal3 `BareMetalHost` provisioning state |
|---|---|---|---|
| discovered | `enroll` → `manageable` (after inspection) | New → Commissioning → Ready | `registering` → `inspecting` → `available` |
| imaged | `active` (deploy complete) | Deployed | `provisioned` |
| repair | `manageable` (maintenance flag set) | Broken | (host marked for remediation by your controller) |
| retired | node deleted / retired | Retired (or deleted) | deprovisioned and deleted |

Representative Ironic CLI calls (L3, state-changing): `openstack baremetal node manage <node>`,
`openstack baremetal node inspect <node>`, `openstack baremetal node provide <node>`,
`openstack baremetal node deploy <node>` (verify sub-commands against your client version).
States `validated`, `schedulable` and `drained` live in *your* controller and the scheduler, not in
the provisioner — keep that boundary explicit in your architecture.

### 8.2 Real acceptance evidence (L2 on one host; L3 for cross-node tests)

Read-only inventory and health (L2):

```bash
nvidia-smi --query-gpu=index,uuid,pci.bus_id,vbios_version,driver_version,temperature.gpu,\
ecc.errors.uncorrected.volatile.total,ecc.errors.corrected.volatile.total,\
pcie.link.gen.current,pcie.link.width.current --format=csv
nvidia-smi -q -d ROW_REMAPPER            # pending / failed row remaps (recent drivers; verify)
nvidia-smi topo -m                       # GPU-NIC PCIe relationships (PIX / PXB / SYS)
sudo lspci -vv -s <NIC_BDF> | grep -E 'LnkCap:|LnkSta:'   # negotiated PCIe speed/width
ethtool <iface> | grep -E 'Speed|Link detected'           # 400000Mb/s expected per rail
ibv_devinfo -d <rdma_dev> | grep -E 'state|active_mtu'
sudo dmesg -T | grep -i xid              # any Xid since boot fails the gate
```

> **Pitfall:** GPUs and NICs may downshift PCIe link speed when idle to save power. Read
> `pcie.link.gen.current` / `LnkSta` while the device is busy (during the bandwidth test), or
> compare against the `max` fields, before declaring a downtrained link.

Diagnostics and bandwidth (L2; GPU-intensive, minutes to hours):

```bash
dcgmi diag -r 3                          # DCGM level-3 diagnostics (long run)
./nvbandwidth                            # NVIDIA nvbandwidth: host<->device and device<->device copies
./build/all_reduce_perf -b 8 -e 8G -f 2 -g 8   # nccl-tests, intra-node bus bandwidth
fio --name=seqread --directory=/mnt/pfs/accept --rw=read --bs=1M --direct=1 \
    --numjobs=8 --size=8G --group_reporting
```

Cross-node RDMA (L3; two lab nodes, one rail at a time):

```bash
# server (lab node A, rail r)
ib_write_bw -d <rdma_dev_r> --report_gbits
# client (lab node B, same rail)
ib_write_bw -d <rdma_dev_r> --report_gbits <nodeA_rail_r_ip>
```

Out-of-band inventory via Redfish (read-only; L2/L3):

```bash
curl -sk -u "$BMC_USER:$BMC_PASS" https://<bmc>/redfish/v1/Systems
curl -sk -u "$BMC_USER:$BMC_PASS" https://<bmc>/redfish/v1/UpdateService/FirmwareInventory
```

Use a dedicated read-only BMC account, keep credentials in a secret store, and verify TLS in
anything beyond a throwaway lab (`-k` disables certificate verification).

Scheduler integration (L3, state-changing, lab cluster only):

```bash
scontrol update NodeName=<node> State=DRAIN Reason="lifecycle: <ticket>"
scontrol update NodeName=<node> State=RESUME
kubectl cordon <node>
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
kubectl uncordon <node>
```

Convert each tool's output into the `acceptance_results.json` schema with a small parser, then run
your unchanged `evaluate_acceptance()` over it. Record calibration runs on at least two known-good
nodes (≥ 5 repetitions per bandwidth test; report median and min) before you trust any threshold.

### 8.3 What to record

Copy `manifest.yaml`, set `tier: L3` (or `L2`) and `evidence_class: MEASURED`, and fill
`extensions[*].record`: GPU model and count, driver, VBIOS per GPU, CUDA, NIC model and firmware,
RDMA stack version, BIOS and BMC firmware, kernel, provisioning system and version, test tool
versions, run count and warm-up policy, and the calibration results that justify each threshold.

## 9. Files

```text
starter-kit/
├── README.md            this file
├── manifest.yaml        environment manifest
├── check.py             checker (17 checks)
├── data/                generated dataset (do not edit by hand)
├── tools/                     generator: instructor copy only (removed from the student release)
└── starter/fleet.py     implement here
```
