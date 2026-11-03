#!/usr/bin/env python3
"""Generate the Chapter 23 design-review bundles (deterministic, seeded).

Two capstone design bundles are written under ``lab/data/``:

* ``bundle_orion_reference/`` -- a consistent ORION-256 design (Capstone A style). A correct
  linter reports zero findings on it (it is the false-positive control).
* ``bundle_kestrel_capA/`` -- a submission by the fictional learner team "Kestrel". It looks
  plausible but contains planted completeness and consistency flaws. The list of planted flaws is
  documented only in ``solutions/``.

Each bundle contains seven files: ``design.md``, ``assumptions.yaml``, ``bom.yaml``,
``topology.yaml``, ``failure_domains.yaml``, ``slos.yaml`` and ``benchmarks.md``, plus the
environment manifests its MEASURED rows cite under ``manifests/``.

All values are [ILLUSTRATIVE] H100-class approximations from docs/REFERENCE_CLUSTER.md.

Usage:
    python tools/generate_bundles.py            # writes ../data/
    python tools/generate_bundles.py --out DIR
"""
from __future__ import annotations

import argparse
import copy
import random
from pathlib import Path

import yaml

SEED = 23


# --------------------------------------------------------------------------------------------
# Reference (consistent) bundle content
# --------------------------------------------------------------------------------------------

def reference_assumptions() -> dict:
    """Assumptions register for the consistent ORION-256 design."""
    rows = [
        ("A-01", "Dense BF16 tensor peak per GPU", 989, "TFLOP/s", "VENDOR-SPEC, 2026-10",
         "Training Infra", "Re-verify against the current datasheet before procurement sign-off"),
        ("A-02", "HBM capacity per GPU", 80, "GB", "VENDOR-SPEC, 2026-10",
         "Training Infra", "Confirm with nvidia-smi --query-gpu=memory.total on acceptance"),
        ("A-03", "Node maximum power", 10.2, "kW", "VENDOR-SPEC, 2026-10",
         "Facilities", "Measure PDU draw during burn-in (Chapter 16 acceptance)"),
        ("A-04", "Model FLOPs utilization (MFU) for W-TRAIN", 0.40, "ratio", "ILLUSTRATIVE",
         "Training Infra", "Measure on a 64-GPU slice before full-scale launch"),
        ("A-05", "Parallel file system aggregate write bandwidth", 80, "GB/s", "ILLUSTRATIVE",
         "Platform", "IOR-style write test from 32 clients at acceptance"),
        ("A-06", "Achievable all-reduce busbw per 400G rail at 32 nodes (node busbw / 8, i.e. ~320 GB/s per node)", 40, "GB/s", "MODELED",
         "Fabric", "all_reduce_perf on 2 and 32 nodes, 5 runs each, L3"),
        ("A-07", "Mean time between job-interrupting failures for a 256-GPU job", 48, "h",
         "ILLUSTRATIVE", "SRE", "Compute from 90 days of incident and Xid history"),
        ("A-08", "Blocking checkpoint time (synchronous save to the PFS, conservative)", 60, "s", "MODELED",
         "Training Infra", "Time the sync save on 32 nodes, then validate async save to NVMe, L2/L3"),
        ("A-09", "Planned rack power budget after PDU derating and the Chapter 21 10 % transient "
         "margin (declared variation: an existing row limited to 50 kW continuous per rack per "
         "2N side; 50 x 0.9 = 45)", 45, "kW", "ILLUSTRATIVE",
         "Facilities", "Facilities sign-off against the as-built PDU one-line"),
        ("A-10", "RoCE path MTU", 4096, "B", "ILLUSTRATIVE",
         "Fabric", "Check active_mtu with ibv_devinfo on every NIC at acceptance"),
    ]
    keys = ["id", "statement", "value", "unit", "label", "owner", "validation"]
    return {
        "bundle": "orion-256-reference",
        "assumptions": [dict(zip(keys, r)) for r in rows],
        "workload": {"name": "W-TRAIN", "total_gpus": 256,
                     "parallelism": {"tp": 8, "pp": 4, "dp": 8}},
    }


def reference_bom() -> dict:
    return {
        "bundle": "orion-256-reference",
        "gpu_nodes": {"model": "HX8", "count": 32, "gpus_per_node": 8, "spares": 0},
        "total_gpus": 256,
        "node_power_kw": {"max": 10.2, "sustained": 8.5, "assumption": "A-03"},
        "racks": {"budget_kw": 45, "budget_assumption": "A-09",
                  "gpu_racks": {f"rack-{i:02d}": 4 for i in range(1, 9)}},
        "switches": {"rail_leaf": {"count": 8, "radix": 64},
                     "spine": {"count": 4, "radix": 64}},
        "cables": {"backend_400g": 512, "note": "256 host-leaf + 256 leaf-spine links"},
    }


def reference_topology() -> dict:
    return {
        "bundle": "orion-256-reference",
        "backend": {
            "transport": "RoCEv2",
            "rails": 8,
            "rail_leaf": {"count": 8, "radix": 64, "downlinks": 32, "uplinks": 32,
                          "uplinks_per_spine": 8},
            "spine": {"count": 4, "radix": 64},
            "claimed_oversubscription": "1:1",
        },
        "frontend": {"ports_per_node": 2, "speed_gbps": 200, "claimed_oversubscription": "1.5:1",
                     "oversubscription_basis": "bandwidth (48 x 200G down : 16 x 400G up); "
                                               "3:1 by port count"},
    }


def reference_failure_domains() -> dict:
    rows = [
        ("FD-01", "gpu", "1 GPU (1/256 of capacity); the whole job stalls until restart",
         "none (no spares, as in the reference cluster)",
         "Drain node (stops new placement only); checkpoint, then wait for repair or restart at DP=7 (224 GPUs, batch adjusted)",
         "DCGM Xid/ECC alerts; NCCL watchdog timeout"),
        ("FD-02", "node", "8 GPUs (3.1 % of capacity)",
         "none (no spares, as in the reference cluster)",
         "Slurm drains node (job not moved); restart from checkpoint after repair or at DP=7 (224 GPUs, batch adjusted)",
         "Node health check; BMC Redfish events"),
        ("FD-03", "nic", "1 rail on 1 node; job stalls or runs degraded",
         "none", "Drain node; NIC replaced under Chapter 16 RMA flow",
         "RDMA link-down and port error counters"),
        ("FD-04", "rail_leaf", "Rail r on all 32 nodes; every multi-node job is affected",
         "none", "Fail jobs fast, checkpoint restart; spare leaf pre-staged; 4 h RMA target",
         "Switch link-down on 32 host ports; spine BGP sessions to the leaf drop"),
        ("FD-05", "spine", "1/4 of leaf-spine bandwidth; ECMP reconverges",
         "N-1: 3 of 4 spines -> 1.33:1 (75 % of leaf-spine bandwidth)", "ECMP removes failed spine",
         "BGP session loss; spine port counters"),
        ("FD-06", "rack_power", "4 nodes (32 GPUs, 12.5 % of capacity)",
         "dual PDU A/B feeds", "Place DP replicas across racks; restart from checkpoint",
         "PDU and BMC power alarms"),
        ("FD-07", "storage", "Checkpoint writes and dataloader reads for all jobs",
         "replicated metadata servers (active/standby)",
         "Fail over metadata service; jobs retry checkpoint", "PFS health probes; I/O latency SLO"),
        ("FD-08", "scheduler", "No new job placement; running jobs unaffected",
         "slurmctld primary/backup", "Fail over to backup controller",
         "Synthetic sbatch probe every 5 min"),
    ]
    keys = ["id", "class", "scope", "redundancy", "mitigation", "detection"]
    return {"bundle": "orion-256-reference", "domains": [dict(zip(keys, r)) for r in rows]}


def reference_slos() -> dict:
    rows = [
        ("SLO-01", "Training goodput",
         "productive step-seconds / allocated GPU-seconds", ">= 0.90", "ratio", "30d",
         "Slurm accounting + step logs"),
        ("SLO-02", "Training job start latency",
         "p95 time from submit to first step for <= 256-GPU jobs", "<= 15", "min", "7d",
         "Slurm accounting"),
        ("SLO-03", "Checkpoint completion",
         "fraction of checkpoints durable within 10 min of trigger", ">= 0.99", "ratio", "7d",
         "Checkpoint manager events"),
        ("SLO-04", "Inference TTFT",
         "p95 time to first token, 2k-token prompts", "<= 800", "ms", "28d",
         "Gateway histograms"),
        ("SLO-05", "Backend fabric health",
         "fraction of 5-min intervals with zero rail-leaf link-down events", ">= 0.999", "ratio",
         "30d", "Switch streaming telemetry"),
    ]
    keys = ["id", "name", "sli", "target", "unit", "window", "source"]
    return {"bundle": "orion-256-reference", "slos": [dict(zip(keys, r)) for r in rows]}


def benchmark_rows(rng: random.Random) -> list[dict]:
    """Benchmark evidence rows. MEASURED rows carry plausible run-to-run spread from the RNG."""
    busbw = 8 * (44.0 + rng.uniform(-0.6, 0.6))   # node busbw over 8 rails; per rail = busbw / 8
    return [
        {"id": "B-01", "metric": "W-TRAIN step time at 40 % MFU", "value": "17.4", "unit": "s",
         "label": "MODELED", "tier": "L1", "manifest": "model: 6*N*tokens / (256*989e12*0.40)"},
        {"id": "B-02", "metric": "all_reduce_perf busbw, 8 GiB, 2 nodes x 8 GPUs, 8 rails (median of 5; per rail = busbw/8)",
         "value": f"{busbw:.1f}", "unit": "GB/s", "label": "ILLUSTRATIVE", "tier": "L3",
         "manifest": "manifests/l3-2node-2026-10-12.yaml"},     # format template; no run produced the value
        {"id": "B-03", "metric": "Checkpoint write, 980 GB at 80 GB/s", "value": "12.3", "unit": "s",
         "label": "MODELED", "tier": "L1", "manifest": "model: 980 GB / 80 GB/s"},
        {"id": "B-04", "metric": "DP gradient all-reduce per step (4.375 GB/GPU, ring)",
         "value": "0.19", "unit": "s", "label": "MODELED", "tier": "L1",
         "manifest": "model: 2*(7/8)*4.375 GB / 40 GB/s per rail"},
        {"id": "B-05", "metric": "Checkpoint + rework waste at Young interval (excl. restart R)",
         "value": "2.6",
         "unit": "%", "label": "MODELED", "tier": "L1",
         "manifest": "model: delta/tau + tau/(2M), delta=60 s, M=48 h"},
        {"id": "B-06", "metric": "Design-lint CLI wall time on this bundle (median of 7)", "value": "0.17",
         "unit": "s",
         "label": "MEASURED", "tier": "L1", "manifest": "manifests/l1-laptop.yaml"},
    ]


def manifest_l3_2node(busbw: float) -> str:
    """Example L3 manifest cited by B-02. ORION is fictional, so this file is ILLUSTRATIVE."""
    return f"""# ILLUSTRATIVE example manifest for a fictional cluster (ORION-256).
# It shows the fields a MEASURED L3 benchmark row must cite. No run produced these values,
# so row B-02 is labelled ILLUSTRATIVE; a real 2-node run would make it MEASURED with this manifest.
lab: ch23-capstone-reference-bundle
tier: L3
row: B-02
date: 2026-10-12
nodes: [orion-n01, orion-n02]
node_image_id: orion-hx8-2026.10.1 (both nodes)
hardware: 8 x H100-SXM-class per node; 8 x 400G RoCEv2 NICs (one per rail), PIX GPU-NIC affinity
nic_firmware: 28.39.1002 (both nodes)
software: {{driver: 570-series, cuda: 12.x, nccl: 2.2x, nccl_tests: built with MPI=1}}
fabric: {{rails: 8, rdma_path_mtu: 4096, isolated: true, note: no other tenant on the rail leaves}}
gdr_evidence: every network channel line ends in /GDRDMA on both nodes
command: srun -N 2 --ntasks-per-node=8 --gpus-per-node=8 --mpi=pmix all_reduce_perf -b 8G -e 8G -g 1 -w 5 -n 20
warm_up: 5 iterations per run (-w 5), discarded
repetitions: 5 runs
result: {{metric: busbw, unit: GB/s, median: {busbw:.1f}, min: 353.0, max: 359.0}}
"""


MANIFEST_L1_LAPTOP = """# MEASURED: environment manifest for B-06 (design-lint wall time). A real run; re-run on yours.
lab: ch23-capstone-reference-bundle
tier: L1
row: B-06
date: 2026-11-01
host: {cpu: Intel Core i7-13700HX, gpu: none used, os: Windows 11 (10.0.26200)}
software: {python: 3.13.14, pyyaml: 6.0.2}
command: python solutions/lab/design_lint.py lab/data/bundle_orion_reference
timing: wall clock of the whole process, including interpreter start-up
warm_up: 3 runs, discarded
repetitions: 7 runs
result: {metric: wall time, unit: s, median: 0.169, min: 0.163, max: 0.193}
"""


def render_benchmarks(rows: list[dict], title: str) -> str:
    cols = ["id", "metric", "value", "unit", "label", "tier", "manifest"]
    lines = [f"# Benchmark evidence -- {title}", "",
             "Every row states its evidence label, tier and manifest (or model formula).", "",
             "| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    lines.append("")
    return "\n".join(lines)


REFERENCE_DESIGN = """# ORION-256 capstone design (reference bundle)

## Problem statement

Halcyon AI needs a cluster that trains W-TRAIN (70B dense, 4.19 M tokens per step) and serves
W-INFER from the same hardware estate. Success means a step time near 17.4 s [MODELED] (B-01) and a
training goodput SLO of 0.90 (SLO-01).

## Assumptions

All load-bearing numbers live in assumptions.yaml. The decision-critical ones are MFU (A-04),
job MTBF (A-07) and blocking checkpoint time (A-08).

## Architecture

32 HX8 nodes give 256 GPUs; TP=8 stays inside each NVLink domain, PP=4 and DP=8 cross nodes.
The backend is a rail-optimized RoCEv2 leaf-spine: 8 rail leaves of radix 64 with 32 downlinks and
32 uplinks each, and 4 spines, for 1:1 subscription (see topology.yaml).
Each GPU node draws up to 10.2 kW [VENDOR-SPEC, 2026-10] so a 4-node rack needs 40.8 kW [MODELED]
against the 45 kW planned budget (A-09: 50 kW rack limit less the 10 % transient margin).

## Failure domains

The rail leaf (FD-04) is the largest single-component blast radius: it touches every node.
Rack power (FD-06) is mitigated by spreading DP replicas across racks.

## Benchmark evidence

B-02 is the only fabric benchmark row; everything else is modeled. ORION is fictional and no run
produced B-02, so it is labelled ILLUSTRATIVE; a real 2-node run would make it MEASURED with its manifest.
Checkpoint plus rework waste at the Young interval is about 2.6 % [MODELED] (B-05), excluding restart.

## Failure exercise

A tabletop of a rail-leaf failure during a 256-GPU run: expected detection within 2 min
[ILLUSTRATIVE] via NCCL watchdog and switch link-down alerts. The job must restart from the last
checkpoint; the plan assumes it waits for the pre-staged spare leaf rather than relying on
untested 7-rail operation.

## Next-step backlog

1. Measure A-04 on a 64-GPU slice (highest decision value).
2. Validate A-08 at 32-node scale.
3. Pre-stage a spare rail leaf to cut FD-04 recovery time.
"""


# --------------------------------------------------------------------------------------------
# Flawed bundle: start from the reference and plant flaws
# --------------------------------------------------------------------------------------------

KESTREL_DESIGN = """# ORION-256 capstone design -- Team Kestrel (Capstone A)

## Problem statement

Halcyon AI wants one cluster for W-TRAIN pretraining and W-INFER serving. Our target is a step time
of 17.4 s [MODELED] (B-01) and training goodput of at least 0.90 (SLO-01).

## Assumptions

See assumptions.yaml. We treat MFU (A-04) and job MTBF (A-07) as the decision-critical inputs,
and we assume the storage tier sustains the dataloader read rate (A-12).

## Architecture

We deploy 34 HX8 nodes (two extra for headroom) giving 256 training GPUs plus spare capacity.
TP=8 stays inside the NVLink domain; PP=4 and DP cross nodes.
The backend is a rail-optimized RoCEv2 leaf-spine with 8 rail leaves and 4 spines (topology.yaml).
Each rail leaf carries 400 Gb/s per port and the fabric is non-blocking.
Racks rack-01..rack-06 hold 4 nodes and rack-07..rack-08 hold 5 nodes; each node draws up to 10.2 kW [VENDOR-SPEC, 2026-10].
Rack power fits comfortably inside the facility envelope (A-09).

## Failure domains

The rail leaf (FD-04) is the largest blast radius. Storage metadata (FD-06) is shared by all jobs.

## Benchmark evidence

Our two-node NCCL run reached 356 GB/s busbw (B-02) and the eight-node run reached 328 GB/s (B-04).
Checkpoints should cost under 6 % of wall-clock time once asynchronous saves land.

## Next-step backlog

1. Measure A-04 on a 64-GPU slice.
2. Re-run B-04 on L3 hardware.
3. Add a spare rail leaf.
"""


def kestrel_bundle(rng: random.Random) -> dict[str, object]:
    asm = copy.deepcopy(reference_assumptions())
    asm["bundle"] = "kestrel-capstone-a"
    for row in asm["assumptions"]:
        if row["id"] == "A-07":
            del row["validation"]                      # planted: missing validation plan
    asm["workload"]["parallelism"] = {"tp": 8, "pp": 4, "dp": 16}   # planted: 512 != 256

    bom = copy.deepcopy(reference_bom())
    bom["bundle"] = "kestrel-capstone-a"
    bom["gpu_nodes"]["count"] = 34                     # planted: spares not declared
    bom["racks"]["gpu_racks"] = {"rack-01": 4, "rack-02": 4, "rack-03": 4, "rack-04": 4, "rack-05": 4,
                                 "rack-06": 4, "rack-07": 5, "rack-08": 5}    # planted: 5 x 10.2 kW > 45 kW
    # cables left at 512 although 34 nodes need 8 x (34 + 32) = 528 links (planted)

    topo = copy.deepcopy(reference_topology())
    topo["bundle"] = "kestrel-capstone-a"
    topo["backend"]["rail_leaf"]["downlinks"] = 34     # planted: 34 + 32 = 66 > radix 64
    # claimed_oversubscription stays "1:1" although 34:32 (planted)

    fd = copy.deepcopy(reference_failure_domains())
    fd["bundle"] = "kestrel-capstone-a"
    fd["domains"] = [d for d in fd["domains"] if d["class"] != "scheduler"]  # planted: missing
    for d in fd["domains"]:  # the learner's own design: it declares no spares of its own
        if d["redundancy"] == "none (no spares, as in the reference cluster)":
            d["redundancy"] = "none (no spares declared)"
    for d in fd["domains"]:
        if d["id"] == "FD-06":                          # planted: SPOF with no mitigation
            d.update({"class": "storage", "scope": "Metadata service for all jobs",
                      "redundancy": "none", "mitigation": "",
                      "detection": "PFS health probes"})
        if d["id"] == "FD-07":                          # rack power, redundancy none, mitigated
            d.update({"class": "rack_power", "scope": "4-5 nodes (up to 40 GPUs)",
                      "redundancy": "none",
                      "mitigation": "Place DP replicas across racks; restart from checkpoint",
                      "detection": "PDU and BMC power alarms"})

    slos = copy.deepcopy(reference_slos())
    slos["bundle"] = "kestrel-capstone-a"
    for s in slos["slos"]:
        if s["id"] == "SLO-03":
            del s["window"]                             # planted: no window
        if s["id"] == "SLO-04":
            s["target"] = "low"                         # planted: not measurable

    rows = benchmark_rows(rng)
    by_id = {r["id"]: r for r in rows}
    by_id["B-02"].update({"label": "MEASURED", "manifest": "-"})   # planted: MEASURED without manifest
    by_id["B-03"]["label"] = ""                         # planted: missing label
    by_id["B-04"].update({"metric": "all_reduce_perf busbw, 8 GiB, 8 nodes x 8 GPUs",
                          "value": "328.0", "unit": "GB/s", "label": "MEASURED",
                          "tier": "L1", "manifest": "manifests/l1-laptop.yaml"})  # planted
    by_id["B-05"]["label"] = "ESTIMATED"                # planted: not in vocabulary
    return {
        "design.md": KESTREL_DESIGN,
        "assumptions.yaml": asm,
        "bom.yaml": bom,
        "topology.yaml": topo,
        "failure_domains.yaml": fd,
        "slos.yaml": slos,
        "benchmarks.md": render_benchmarks(rows, "Team Kestrel"),
        "manifests/l1-laptop.yaml": MANIFEST_L1_LAPTOP,
    }


def reference_bundle(rng: random.Random) -> dict[str, object]:
    rows = benchmark_rows(rng)
    busbw = float(next(r["value"] for r in rows if r["id"] == "B-02"))
    return {
        "design.md": REFERENCE_DESIGN,
        "assumptions.yaml": reference_assumptions(),
        "bom.yaml": reference_bom(),
        "topology.yaml": reference_topology(),
        "failure_domains.yaml": reference_failure_domains(),
        "slos.yaml": reference_slos(),
        "benchmarks.md": render_benchmarks(rows, "ORION-256 reference"),
        "manifests/l3-2node-2026-10-12.yaml": manifest_l3_2node(busbw),
        "manifests/l1-laptop.yaml": MANIFEST_L1_LAPTOP,
    }


def write_bundle(files: dict[str, object], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        text = content if isinstance(content, str) else yaml.safe_dump(
            content, sort_keys=False, allow_unicode=True, width=100)
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = parser.parse_args()
    # Separate RNG streams so each bundle is independent and byte-stable.
    write_bundle(reference_bundle(random.Random(SEED)), args.out / "bundle_orion_reference")
    write_bundle(kestrel_bundle(random.Random(SEED)), args.out / "bundle_kestrel_capA")
    print(f"wrote bundles to {args.out}")


if __name__ == "__main__":
    main()
