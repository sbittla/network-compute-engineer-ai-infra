# Lab 2 — ORION Capacity, BOM, Power/Cooling, and Failure-Domain Model

## 1. Goal and the real-world task it mirrors

Before a GPU cluster is ordered, somebody has to turn a design intent ("32 eight-GPU nodes on a
rail-optimized 400G fabric") into numbers that procurement, the network team, and the facilities
(MEP: mechanical, electrical, plumbing) engineer can all sign: how many servers, rack units, switches,
ports, links, and optics; how many kilowatts per rack feed; how many litres per minute of coolant; how
much storage bandwidth per GPU; and what single failure takes the whole cluster down.

The inputs never arrive clean. They come from different people, in different units, at different
stages of the design, and some of them are wrong. In this lab you build the model that a capacity or
deployment engineer builds in the first week of a cluster project:

1. **Validate** six input sheets and report every inconsistency as a structured finding.
2. **Compute a bill of materials (BOM)** for the compute, backend fabric, frontend, and out-of-band
   (OOB) management layers.
3. **Compute a rack power and heat-removal budget**, including branch-circuit headroom, transient
   margin, coolant flow from `Q = ṁ · cp · ΔT`, residual airflow, and coolant distribution unit (CDU)
   loading — plus a cluster energy figure.
4. **Compute a capacity summary**: accelerators, high-bandwidth memory (HBM), per-GPU training state,
   injection and bisection bandwidth, storage throughput per GPU, checkpoint write time, and allocated
   GPU-hours.
5. **Find the single points of failure (SPOFs)** by simulating the loss of each component in a
   dependency model, including SPOFs that are not visible from any one sheet.

## 2. Tier and realism boundary

**Tier L1** (laptop; Python 3.10+, `pyyaml`; no GPU, no root, no network). Runtime < 5 s.

Everything this lab produces is `[MODELED]`: computed from stated formulas and stated assumptions.
Nothing here is a measurement of any server, PDU, CDU, or building. The electrical, cooling, and
structural parameters in `data/facility_envelope.yaml` are teaching assumptions; a real design uses
the site's electrical one-line, the local electrical code, the cooling vendor's performance curves,
and a structural engineer's floor rating. The L2/L3 extensions in Section 8 show how to replace the
key assumptions with measurements.

## 3. Setup

```bash
cd book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/lab
python -m pip install -r ../../../../requirements.txt   # once, from any venv
python check.py                                          # your progress meter
```

Your code goes in `starter/capacity_model.py`. `load_inputs()` and three small helpers
(`circuit_usable_kw`, `gpu_rack_max_kw`, `to_gbytes_per_s`) are already implemented.

## 4. Background you need

| Topic | Manuscript section |
|---|---|
| ORION's node, rack, and fabric structure; BOM arithmetic | Sections 2.2–2.4 and 2.10 |
| Power chain, three-phase circuits, derating, redundancy, PSU feeds | Section 2.5 |
| TDP, transients, power capping | Section 2.6 |
| Air vs liquid cooling, `Q = ṁ · cp · ΔT`, CDUs | Section 2.7 |
| Floor loading and MEP interfaces | Section 2.8 |
| Capacity, utilization, and failure domains | Section 2.9 |

### Input sheets (`data/`)

| File | Source it imitates | Notes |
|---|---|---|
| `design_intent.yaml` | Architecture team's design intent | Treat as the baseline for the BOM, power and capacity tasks. Not beyond question (Task 1). |
| `facility_envelope.yaml` | MEP engineer of record | Circuit voltage, derating, power factor, transient margin, coolant and air properties, CDU, floor rating |
| `rack_plan.csv` | Deployment planner | One row per rack, with planned IT load, circuits per side, breaker size, estimated weight |
| `fabric_plan.csv` | Network team | One row per backend switch: ports, downlinks, uplinks |
| `storage_plan.yaml` | Storage vendor sizing sheet | Per-server and quoted aggregate throughput |
| `cluster_design.yaml` | Reliability review | Components, redundancy groups (`members`, `min_required`), and services |

## 5. Tasks

### Task 1 — Validate the input sheets (`validate_inputs`) — 30 points

Return a list of findings, each a dict `{"code", "item", "message"}`. Apply these rules:

| Code | Rule | `item` |
|---|---|---|
| `DUPLICATE_RACK` | A `rack_id` appears more than once (report once; skip further checks on the duplicate row) | rack id |
| `POWER_BASIS` | `power_basis` is not `max` | rack id |
| `CIRCUIT_OVERLOAD` | Per-side load × (1 + `transient_margin`) exceeds `circuits_per_side` × usable circuit power. GPU-rack load = `node_count × node_max_kw + gpu_rack_aux_kw` (recompute it — do not trust `planned_it_kw`); other racks use `planned_it_kw`. | rack id |
| `FLOOR_LOAD` | `est_weight_kg / rack_footprint_m2` > `floor_rating_kg_per_m2` | rack id |
| `PORT_OVERCOMMIT` | `downlinks + uplinks > port_count` | switch id |
| `OVERSUBSCRIBED_LEAF` | leaf `downlinks / uplinks` > `target_oversubscription` | switch id |
| `UPLINK_MISMATCH` | Σ leaf uplinks ≠ Σ spine downlinks | `fabric` |
| `UNIT_MISMATCH` | A quoted storage aggregate, converted to GB/s, differs by > 5 % from `servers ×` the per-server figure | `storage.<key>` |
| `PSU_FEED_LOSS` | `(psu_count / psu_feeds) × psu_rating_kw < node_dc_peak_kw`: PSU ratings are DC output, so compare with the node's DC peak load, not the 10.2 kW AC input | `node_model` |

**Acceptance:** every real flaw detected and no false positives. Write one sentence per finding in
your report explaining the consequence if nobody caught it.

### Task 2 — Bill of materials (`compute_bom`) — 15 points

Return a dict with these integer keys: `gpu_nodes`, `gpus`, `gpu_racks`, `gpu_node_rack_units`,
`rack_units_per_gpu_rack`, `backend_leaves`, `backend_spines`, `backend_switches`,
`host_backend_links`, `leaf_spine_links`, `backend_links_total`, `backend_switch_ports`,
`transceivers_single_port` (one module per link end, all links optical), `switch_side_twin_port_modules`
(switch ports ÷ 2, if switches use two-port 2×400G modules), `frontend_node_ports`,
`frontend_leaves`, `gpu_rack_pdus`, `oob_ports` (nodes + backend switches + frontend leaves + storage
servers + GPU-rack PDUs), `total_racks`.

**Acceptance:** 256 GPUs, 12 backend switches, 512 backend links, 1,024 single-port transceivers.

### Task 3 — Power and heat-removal budget (`compute_power_cooling`) — 20 points

Return a dict with: `rack_it_max_kw`, `rack_design_kw` (max × (1 + transient margin)), `circuit_kva`
(one 60 A circuit), `usable_per_side_kw` (two circuits), `headroom_per_side_kw`, `rack_liquid_kw`,
`rack_air_kw`, `coolant_mass_flow_kg_s`, `coolant_flow_lpm`, `rack_air_cfm`, `all_air_rack_cfm`,
`cdu_load_kw`, `cdu_utilization`, `cluster_it_max_kw`, `facility_max_kw` (× PUE),
`cluster_it_sustained_kw`, `annual_energy_mwh` (sustained × PUE × 8,760 h), `annual_energy_cost_usd`.

**Acceptance:** 41.0 kW rack maximum, ≈ 46 L/min coolant per rack, CDU ≈ 82 % loaded.

### Task 4 — Capacity summary (`compute_capacity`) — 15 points

Return a dict with: `gpus`, `total_hbm_gb`, `training_state_tb`, `training_state_per_gpu_gb` (state
÷ (TP × PP)), `injection_tbps`, `bisection_tbps_per_direction`, `leaf_oversubscription`,
`storage_read_gbytes_s`, `storage_write_gbytes_s`, `storage_read_per_gpu_gbytes_s`, `checkpoint_gb`,
`checkpoint_write_s` (lower bound: size ÷ aggregate write), `allocated_gpu_hours_per_year`.

**Acceptance:** 51.2 Tb/s bisection per direction; 35 GB training state per GPU.

### Task 5 — Failure domains and SPOFs (`failed_set`, `find_spofs`) — 20 points

Implement failure propagation to a fixed point, then fail each component alone and record which
services are lost. **Acceptance:** the exact SPOF set and correct service impact. In your report, draw
the failure-domain diagram and propose a mitigation for each SPOF, stating which ones you would
*accept* as a documented risk and why.

## 6. Running the checker

```bash
python check.py                    # starter: TODO lines until you implement each function
python check.py --impl solution    # instructors: reference must print 14/14 and exit 0
```

Each line is `PASS`, `FAIL` (with a reason), or `TODO` (function still raises `NotImplementedError`).
The first check confirms that `data/` regenerates byte-identically. It needs the instructor-only
generator, so in the student edition it prints `SKIP`, which does not count against you.

## 7. Deliverable and grading rubric

Deliverable (the Chapter 2 course deliverable): a **cluster BOM**, a **capacity spreadsheet** (export
your dicts to CSV, or paste into a spreadsheet with formulas visible), a **findings list** for the
input sheets, and a **failure-domain diagram** with mitigations.

| Item | Points |
|---|---|
| Task 1: all flaws found, no false positives, consequence sentence for each | 30 |
| Task 2: BOM correct and presented as a table with assumptions (optics type, twin-port option) | 15 |
| Task 3: power and cooling budget correct; assumptions register attached | 20 |
| Task 4: capacity summary correct; one paragraph interpreting storage per GPU and checkpoint time | 15 |
| Task 5: SPOF set correct; failure-domain diagram; mitigations with accept/fix decision | 20 |
| **Total** | **100** |

Passing `check.py` earns the computational part of each task (about 60 % of the points); the rest is
the written interpretation, which instructors grade from `solutions/exercises-key.md` guidance.

## 8. Extensions (L2/L3, hardware-backed)

> **Safety:** These extensions are **read-only** unless you have written authorisation for the
> specific machine. Never change power limits, PDU settings, or CDU setpoints on shared or production
> equipment. Power-capping experiments belong on a dedicated lab server with the owner's approval.

### L2 — Replace the node power assumption with a measured profile (one GPU server)

Goal: measure idle, sustained, and peak power of one server under a defined workload and compare with
the 10.2 kW / 8.5 kW assumptions.

```bash
# Server-level power from the BMC (DCMI); repeat at a fixed interval during the run
ipmitool -I lanplus -H "$BMC" -U "$BMC_USER" -E dcmi power reading
ipmitool -I lanplus -H "$BMC" -U "$BMC_USER" -E sdr type "Power Supply"

# Redfish (read-only GETs). Credentials come from a 0600 netrc file and the BMC's CA certificate
# is verified; do not use -k or put passwords on the command line.
#   ~/.bmc-netrc:  machine <bmc-host> login <user> password <password>
R="curl -s --netrc-file $HOME/.bmc-netrc --cacert $HOME/bmc-ca.pem"
$R "https://$BMC/redfish/v1/Chassis"
# Current schema (DMTF 2020.4 and later):
$R "https://$BMC/redfish/v1/Chassis/<chassis-id>/PowerSubsystem"
$R "https://$BMC/redfish/v1/Chassis/<chassis-id>/ThermalSubsystem"
$R "https://$BMC/redfish/v1/Chassis/<chassis-id>/EnvironmentMetrics"   # PowerWatts, PowerLimitWatts
$R "https://$BMC/redfish/v1/Chassis/<chassis-id>/Controls"             # power-limit controls, if exposed
# Deprecated since 2020.4 but still common on older BMC firmware:
$R "https://$BMC/redfish/v1/Chassis/<chassis-id>/Power"
$R "https://$BMC/redfish/v1/Chassis/<chassis-id>/Thermal"

# GPU-level power, temperature, clocks, and clock-event (throttle) reasons
nvidia-smi -q -d POWER,TEMPERATURE,PERFORMANCE
nvidia-smi --query-gpu=index,power.draw,power.limit,temperature.gpu,clocks.sm --format=csv -l 1
nvidia-smi dmon -s pucv            # power/temp, utilization, clocks, violations, 1 s samples
dcgmi dmon -l                      # list field IDs available on your DCGM version, then:
dcgmi dmon -e 155,150,100 -d 1000  # power usage, GPU temperature, SM clock (verify IDs with -l)
```

Generate load with an approved stress workload on that server — for example the DCGM diagnostic
(`dcgmi diag -r 3`, which includes stress tests; check the duration for your version) or your own GEMM
loop — and sample for at least 10 minutes after a 5-minute warm-up. Repeat ≥ 5 runs. Report median,
p95, p99, and max of server power; the ratio of p99 to sustained; and whether any GPU reported a
power or thermal clock-event reason.

### L3 — Rack and CDU budget validation (lab hall, with facilities sign-off)

With the facilities team present, run the same workload on every node in one rack and record per-feed
power from the metered rack PDUs (through the PDU's web/SNMP/Redfish interface as supported by its
vendor), plus CDU secondary-loop (TCS) supply and return temperature and flow. Compute the measured
heat to liquid as `ṁ · cp · (T_return − T_supply)` and compare with your modeled `rack_liquid_kw`; the
difference is the real air-side heat. Record every field listed under `extensions` in
`manifest.yaml`. Never trip a breaker on purpose: single-feed tests are tabletop exercises unless the
facilities team runs them as part of formal commissioning.

## 9. Instructor notes

The planted flaws, why each was chosen, the complete expected findings, and model answers to the
written parts are documented in `../solutions/exercises-key.md` (section "Lab 2 answer key").
