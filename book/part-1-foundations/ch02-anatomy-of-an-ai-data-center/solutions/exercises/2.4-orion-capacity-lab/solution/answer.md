# 2.4 — ORION capacity, BOM, power and SPOF lab: reference solution

Reference implementation: `solutions/lab/capacity_model.py`. Rubric: `lab/README.md` Section 7. Methods:
manuscript Sections 2.4–2.10. All values `[MODELED]` from `[ILLUSTRATIVE]` input sheets (seed 2).

## Checker

`python check.py --impl solution` prints 14/14 PASS (committed as `solutions/lab/outputs/check_solution.txt`).
The first check (`data_regenerates_identically`) needs the instructor-only generator and prints SKIP in the
student edition; that does not count against the learner. Check names print with a trailing colon, so the
`lab_checks` list in `meta.yaml` keeps the colon.

## Task 1: the nine findings (and no others)

| Code | Item | Consequence sentence |
|---|---|---|
| `DUPLICATE_RACK` | rack-05 | The sheet totals 36 nodes, so procurement would order 4 extra servers and Facilities would plan a ninth rack's power. |
| `POWER_BASIS` | rack-03 | Planned at sustained 34.2 kW instead of 41.0 kW maximum, 16.6 % under-sized; breakers trip at burn-in. |
| `CIRCUIT_OVERLOAD` | rack-07 | One circuit per side gives 32.78 kW against 45.1 kW needed: the rack cannot survive a feed loss at load. |
| `FLOOR_LOAD` | rack-08 | 1,000 kg / 0.72 m² = 1,389 kg/m² > 1,200: structural review required. |
| `PORT_OVERCOMMIT` | orion-be-spine-2 | 72 downlinks on a 64-port switch: the cable plan cannot be built. |
| `OVERSUBSCRIBED_LEAF` | orion-be-leaf-r5 | 24 uplinks for 32 downlinks = 1.33:1 on rail 5; collectives run at the slowest rail's pace. |
| `UPLINK_MISMATCH` | fabric | Σ leaf uplinks 248 ≠ Σ spine downlinks 264: the sheet is internally inconsistent. |
| `UNIT_MISMATCH` | storage.aggregate_read | "160 Gb/s" where 8 × 20 GB/s = 160 GB/s: an 8× bits-for-bytes error. |
| `PSU_FEED_LOSS` | HX8 | 3 × 3.0 kW = 9.0 kW DC per feed < 9.59 kW DC peak: needs a feed-loss policy (570 W GPU cap). |

Non-findings learners sometimes report: the 13U of empty space (by design), storage racks on 32 A
(17.48 kW ≥ 9.9 kW needed), network racks on one 60 A circuit per side (32.78 kW ≥ 17.6 kW), and
`aggregate_write` 80 GB/s (= 8 × 10). Compare DC with DC for the PSU rule (PSU ratings are DC output).

## Tasks 2–4: expected values

- **BOM:** 32 nodes, 256 GPUs, 8 GPU racks (256U of nodes), 8 leaves + 4 spines, 512 backend links, 768
  switch ports, 1,024 single-port transceivers (or 640 with twin-port switch optics), 64 frontend ports,
  2 frontend leaves, 32 GPU-rack PDUs, 86 OOB ports, 13 racks.
- **Power and cooling:** 41.0 kW rack maximum, 45.1 kW design per side against 65.55 kW usable (20.45 kW
  headroom); liquid 30.75 kW and air 10.25 kW per rack; 46.4 L/min PG25 and 1,199 CFM; CDU 246 kW = 82 %
  (capacity ✓, redundancy ✗); cluster 382.0 kW IT, 477.5 kW facility; 3,587 MWh/yr, ≈ $287k/yr.
- **Capacity:** 20,480 GB HBM; 35.0 GB training state per GPU; 102.4 Tb/s injection and 51.2 Tb/s
  bisection per direction; 160/80 GB/s storage, 0.625 GB/s read per GPU; 980 GB checkpoint ≥ 12.25 s;
  1,906,176 allocated GPU-hours.

## Task 5: SPOFs (15)

`cdu-1`, `pdu-net-A`, `busway-A`, `ups-A`, `mds-1`, `slurmctld-1`, `oob-sw-1` and the eight rail leaves
`orion-be-leaf-r0` … `r7`. The key teaching point: `ups-A` and `busway-A` are SPOFs in a 2N electrical
design only because both dual-homed frontend leaves are single-corded to `pdu-net-A` (feed A). Re-cording
them across A and B removes three SPOFs at almost no cost. Fix: CDU (N+1), frontend-leaf cording, MDS HA,
backup Slurm controller. Accept with documentation: rail leaves (inherent to rail-optimized design; spare
on site, pre-staged config) and the OOB switch (spare on site, fix at next expansion). Not SPOFs: any
single spine (3 of 4 suffice), any chiller (2 of 3), any GPU-rack PDU (2N), any single node.

**Common mistakes:** listing only the singleton groups (missing the power-path SPOFs); comparing PSU DC
rating with AC input; reporting the empty 13U as a finding.

## Hardware run (L2 harness)

The L2 extension on the course harness (`python scripts/hw_labs.py run ch02`) replaces the GPU share of
the node power assumption with measured idle, sustained and peak GPU power under a defined GEMM and copy
load. It sets the measured sustained-to-limit and peak-to-sustained ratios next to the 8.5 kW / 10.2 kW
model and its transient margin. Server-level (BMC) power is recorded as not runnable on that host. A
submission using it should keep the model's maximum for rack sizing and quote the measured ratios as
`[MEASURED]` on the named GPU, not as HX8 figures. CPU fallback: throughput only, no power.
