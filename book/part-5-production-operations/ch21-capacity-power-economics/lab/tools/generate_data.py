#!/usr/bin/env python3
"""Generate the Chapter 21 capacity / power / economics inputs (all [MODELED] / [ILLUSTRATIVE]).

Files written to ../data (or --out):
  quarterly_plan.csv   supply (deliveries, decommissions), energized facility IT power, demand (2027Q1-2029Q4)
  assumptions.yaml     reserves, utilization, goodput, power, prices, lead times
  designs.yaml         two candidate expansion designs (A: H100-class air-cooled; B: next-gen liquid-cooled)
  power_cap_curve.csv  GPU power cap vs relative training throughput
  power_cap_case.yaml  rack/facility constraints for the power-capping trade-off

The plan contains planted data-quality problems and planning traps (see solutions/).
Deterministic; regenerating produces byte-identical files.
"""
from __future__ import annotations

import argparse
from pathlib import Path

PLAN = """\
quarter,gpus_delivered,gpus_decommissioned,facility_it_kw,demand_train_gpus,demand_infer_gpus,notes
2027Q1,0,0,420,125,35,ORION-256 installed base
2027Q2,0,0,420,135,40,
2027Q3,256,0,800,155,45,expansion 1 (32 nodes); facility upgrade energized
2027Q3,256,0,800,155,45,expansion 1 (32 nodes); facility upgrade energized
2027Q4,0,0,800,180,50,
2028Q1,0,0,800,208,57,
2028Q2,512,0,800,240,65,expansion 2 (64 nodes) delivered; facility phase 2 not yet energized
2028Q3,0,0,800,345,75,new 405B-class pretraining program starts
2028Q4,0,0,1500,395,85,facility phase 2 energized
2029Q1,0,0,1500,455,95,
2029Q2,256,0,1500,525,105,expansion 3 (32 nodes)
2029Q3,0,256,1500,605,115,retire original 256 GPUs (end of 5-year life)
2029Q4,0,0,1500,690,130,
"""

ASSUMPTIONS = """\
# Capacity and cost assumptions for ORION (all [ILLUSTRATIVE] unless noted)
initial_installed_gpus: 256
gpus_per_node: 8
provisioned_it_kw_per_node: 10.2        # HX8 max node power (Reference Cluster)
sustained_it_kw_per_node: 8.5           # training average (8-9 kW)
network_storage_overhead: 0.12          # extra IT power for fabric, storage, management, as a fraction of node power
reserves:
  maintenance: 0.03                     # nodes drained for planned maintenance / upgrades
  failure_repair: 0.078                 # nodes in repair: 5-day MTTR x 24/1,536 per node-day = 7.8 % (canon; Ch 16)
  fragmentation: 0.05                   # GPUs free but unusable for gang-scheduled jobs (Chapter 17)
target_allocation: 0.85                 # plan so that demand <= 85 % of usable GPUs (queueing headroom)
goodput: 0.88                           # useful fraction of allocated GPU time (Chapters 18-19)
lead_time_quarters: {gpus: 2, network: 1, facility_power: 4}
prices:
  amortization_years: 4
  electricity_usd_per_kwh: 0.09
  pue: 1.25                             # canonical ORION hall (liquid-assisted)
  colo_usd_per_kw_month: 130            # on provisioned IT kW
  support_fraction_of_hw_capex: 0.08    # per year
  staff_usd_per_year: 960000            # 4 FTE x $240k for ORION-256
"""

DESIGNS = """\
# Two candidate designs for the next 1.0 MW (IT) facility hall. Per-node values. [ILLUSTRATIVE]
facility_it_kw: 1000
liquid_cooling_kw_available: 1000       # CDU capacity in the hall (kW of heat to liquid)
designs:
  - name: A-air-H100class
    gpus_per_node: 8
    rel_throughput_per_gpu: 1.0         # W-TRAIN step throughput relative to an HX8 GPU
    comm_efficiency: 1.00               # 1:1 rail-optimized fabric
    provisioned_it_kw_per_node: 10.2
    sustained_it_kw_per_node: 8.5
    node_capex_usd: 320000
    network_capex_per_node_usd: 85000
    cooling_capex_per_node_usd: 0
    liquid_fraction: 0.0                # fraction of node heat removed by liquid
    nodes_per_rack: 4
    pue: 1.35                           # variation: air-cooled hall (higher fan/chiller overhead)
  - name: B-liquid-nextgen
    gpus_per_node: 8
    rel_throughput_per_gpu: 2.2
    comm_efficiency: 0.93               # 2:1 oversubscribed spine to save cost: comm-bound phases slower
    provisioned_it_kw_per_node: 14.3
    sustained_it_kw_per_node: 12.0
    node_capex_usd: 700000
    network_capex_per_node_usd: 70000
    cooling_capex_per_node_usd: 30000   # CDU + manifold share
    liquid_fraction: 0.80
    nodes_per_rack: 8
    pue: 1.20                           # variation: mostly-liquid hall (warm-water, less chiller work)
"""

CURVE = """\
gpu_power_cap_w,rel_throughput
350,0.700
400,0.790
450,0.855
500,0.905
550,0.945
600,0.972
650,0.990
700,1.000
"""

CAP_CASE = """\
# Power-capping case (declared variation): 64 HX8 nodes must fit into 16 racks of a LEGACY hall whose racks
# have ONE canonical 415 V / 60 A circuit per side (32.78 kW, PF 0.95, 80 % continuous), 2N A/B. [ILLUSTRATIVE]
nodes: 64
racks: 16
rack_slots: 4                    # physical node slots per rack
rack_limit_kw: 32.78             # one side must carry the whole rack (2N): one circuit's continuous limit
transient_margin: 0.10           # keep planned peak <= limit x (1 - margin) for synchronized power swings
node_base_peak_kw: 4.6           # canonical: 10.2 kW max = 4.6 kW base + 8 x 700 W
gpus_per_node: 8
"""


def write_all(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, text in (("quarterly_plan.csv", PLAN), ("assumptions.yaml", ASSUMPTIONS), ("designs.yaml", DESIGNS),
                       ("power_cap_curve.csv", CURVE), ("power_cap_case.yaml", CAP_CASE)):
        (out / name).write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    write_all(p.parse_args().out)
    print("ok")


if __name__ == "__main__":
    main()
