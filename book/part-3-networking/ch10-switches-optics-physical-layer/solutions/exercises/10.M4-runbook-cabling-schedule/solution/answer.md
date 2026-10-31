# 10.M4 — Physical-layer runbook and port/cabling schedule (model answer)

**(a) Port/cabling schedule.** `generate_cabling_schedule()` for the lab's `small` fabric (16 nodes,
8 rails, 64-port switches, 1:1) yields 8 leaves × 16 host links = 128 host cables and 8 leaves × 16
uplinks = 128 fabric cables: **256 rows**, unique cable IDs and endpoints, 8 links per leaf–spine pair
(2 spines × 8 leaves). The checks `cabling_schedule` and `bom_and_spares` in `outputs/lab_checks.json`
confirm this. Each row: cable ID, both endpoints, optic at each end (400G-DR4), media (SMF MPO-12),
`length_m`, and label text naming the cable ID and both ends, e.g.
`H-r0-n01 | lab-leaf-r0:Ethernet1 -> lab-n01:nic0` (fabric cables `F-r0-0-s1-1` …).

Model rack layout for lengths `[ILLUSTRATIVE]`: one network rack holds 8 leaves and 2 spines; GPU racks
at 2 nodes per rack in a row, rack pitch 0.6 m, network rack 6 m from the first GPU rack. Host-link
length = 6 m + 0.6 m × (rack index) + 3 m vertical/slack, rounded up to a stocked length (10, 15 m);
leaf–spine = 3 m in-rack. Lengths must come from such a stated layout, not be invented per row.

**(b) Runbook (≤ 3 pages) — required content**

| Signal | Warning | Critical | First safe action | Escalate to |
|---|---|---|---|---|
| FEC uncorrectable | — | > 0 in 5 min | Correlate with host CRC/RDMA counters; prepare drain | Fabric on-call |
| FCS with uncorrectables | — | > 0 in 5 min | Drain; inspect/clean; swap cable, then optic | Fabric on-call |
| FCS without uncorrectables, clean BER | > 0 | > 15 min | Look one hop upstream (stomped frames) | Fabric on-call |
| Pre-FEC BER | ≥ 10⁻⁵ or ≥ 10× vs 7-day baseline | ≥ 10⁻⁴ | Warn: cleaning ticket; critical: drain and clean/replace now | Fabric |
| Rx power per lane | < −4.0 dBm or > 3 dB below siblings | < −5.9 dBm | Compare far-end Tx; inspect/clean both ends | Fabric |
| Link-down events | ≥ 2 in 10 min | error-disabled | Keep down; reseat/inspect; firmware; replace optic | Fabric on-call |
| Discards/PFC/ECN, giants | per Chapter 9 / > 0 | — | Not physical: congestion workflow / MTU check | Fabric, Platform |

Threshold provenance: −5.9 dBm DR4 receiver minimum and 3.0 dB channel loss `[VENDOR-SPEC, 2026-10]`
(IEEE 802.3bs); 2.4 × 10⁻⁴ KP4 design point `[VENDOR-SPEC, 2026-10]`; every warn/critical value above
is `[ILLUSTRATIVE]` ORION policy (Table 10.10).

**Drain before touch.** Host link: drain the node through the scheduler (Slurm/Kubernetes), confirm
no job, then work. Uplink: routing-policy drain (e.g. AS-path prepend or BGP shutdown on that
session), confirm zero traffic, then admin-down; one link per leaf at a time; record before/after DOM
and counters; return to service only through the commissioning gates.

**Commissioning gates** (Figure 10.7): Installed → Inspected → Configured → LinkUp → Verified (part =
BOM, LLDP = schedule, DOM within policy) → Soaked (≥ 30 min, zero uncorrectables) → InService.

**Cleaning/inspection.** Inspect before cleaning and after every mating (IEC 61300-3-35 pass/fail);
dry one-click clean, re-inspect, wet-dry only if needed; cap every unused port and jumper.

**Sparing** `[MODELED]` from the lab policy: optics ⌈512 × 0.03⌉ = ⌈15.36⌉ = **16**; cables
⌈256 × 0.02⌉ = ⌈5.12⌉ = **6**; **1** spare switch.
