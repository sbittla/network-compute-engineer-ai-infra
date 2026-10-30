#!/usr/bin/env python3
"""Generate the Chapter 17 lab datasets (deterministic, seeded).

Outputs (in ../data/):
  cluster_state.json   ORION-256 snapshot: 32 HX8 nodes, lifecycle/health, labels, taints, rails,
                       MIG flags, GPUs already allocated to running jobs, tenant GPU quotas.
  job_queue.json       Pending jobs to place (gang size, pool, tenant, priority, selectors, tolerations).
  pending_cases.json   Evidence bundles for jobs that are pending "despite free GPUs".

All values are [ILLUSTRATIVE]/[SIMULATED]; node names and racks follow docs/REFERENCE_CLUSTER.md
(orion-n01..orion-n32, rack-01..rack-08, 4 nodes per rack). Re-running produces byte-identical files.

Usage:  python tools/generate_data.py [--out DIR] [--seed 17]
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

GPU_PRODUCT = "NVIDIA-H100-80GB-HBM3"


def node_name(i: int) -> str:
    return f"orion-n{i:02d}"


def rack_of(i: int) -> str:
    return f"rack-{(i - 1) // 4 + 1:02d}"


def base_node(i: int) -> dict:
    pool = "train" if i <= 24 else "infer"
    return {
        "name": node_name(i),
        "rack": rack_of(i),
        "lifecycle_state": "schedulable",
        "health": "ok",
        "health_detail": "",
        "labels": {
            "halcyon.ai/pool": pool,
            "halcyon.ai/rack": rack_of(i),
            "nvidia.com/gpu.product": GPU_PRODUCT,
            "nvidia.com/gpu.count": "8",
            "nvidia.com/mig.capable": "true",
            "halcyon.ai/rails-complete": "true",
        },
        "taints": [],
        "mig_enabled": False,
        "rails_up": list(range(8)),
        "gpus_allocated": [],
    }


def build_cluster(rng: random.Random) -> dict:
    nodes = {i: base_node(i) for i in range(1, 33)}

    running = [
        {"job_id": "R-pt-001", "tenant": "pretrain", "nodes": {node_name(i): list(range(8)) for i in range(1, 9)}},
        {"job_id": "R-pt-002", "tenant": "pretrain", "nodes": {node_name(i): list(range(8)) for i in range(9, 13)}},
        {"job_id": "R-rs-001", "tenant": "research", "nodes": {node_name(i): list(range(8)) for i in (15, 16)}},
        {"job_id": "R-ft-001", "tenant": "finetune", "nodes": {node_name(17): list(range(8))}},
        {"job_id": "R-rs-002", "tenant": "research", "nodes": {node_name(20): [0, 1]}},
        {"job_id": "R-ft-002", "tenant": "finetune", "nodes": {node_name(21): [4, 5]}},
        {"job_id": "R-inf-001", "tenant": "inference", "nodes": {node_name(25): list(range(8))}},
        {"job_id": "R-inf-002", "tenant": "inference", "nodes": {node_name(26): [0, 1, 2, 3]}},
        {"job_id": "R-inf-003", "tenant": "inference", "nodes": {node_name(27): [0, 1]}},
        {"job_id": "R-inf-004", "tenant": "inference", "nodes": {node_name(27): [4]}},
        {"job_id": "R-inf-005", "tenant": "inference", "nodes": {node_name(29): [4, 5, 6, 7]}},
        {"job_id": "R-inf-006", "tenant": "inference", "nodes": {node_name(32): list(range(8))}},
    ]
    for r in running:
        for n, idx in r["nodes"].items():
            i = int(n.split("n")[-1])
            nodes[i]["gpus_allocated"] = sorted(nodes[i]["gpus_allocated"] + idx)

    # Node conditions (the interesting ones).
    nodes[14]["health"] = "degraded"
    nodes[14]["health_detail"] = "backend rail 3 link down (NIC3 no carrier); intra-node NVLink healthy"
    nodes[14]["rails_up"] = [0, 1, 2, 4, 5, 6, 7]
    # Not drained: one dead rail is expressed as an attribute (K8s label / Slurm feature rails7 + low Weight).
    nodes[14]["labels"]["halcyon.ai/rails-complete"] = "false"
    nodes[19]["lifecycle_state"] = "repair"
    nodes[19]["health"] = "failed"
    nodes[19]["health_detail"] = "GPU5 uncorrectable ECC; RMA ticket open"
    nodes[23]["lifecycle_state"] = "drained"
    nodes[23]["health_detail"] = "wave-2 firmware upgrade (Chapter 16 staged upgrade)"
    nodes[28]["mig_enabled"] = True
    nodes[28]["labels"]["nvidia.com/mig.config"] = "all-1g.10gb"
    nodes[28]["health_detail"] = "MIG all-1g.10gb: 56 x 1g.10gb instances for small-model serving"
    nodes[31]["taints"] = [{"key": "halcyon.ai/dedicated", "value": "search", "effect": "NoSchedule"}]
    nodes[31]["labels"]["halcyon.ai/dedicated"] = "search"
    # Cosmetic, non-blocking taint (PreferNoSchedule) — a red herring for learners.
    nodes[30]["taints"] = [{"key": "halcyon.ai/canary-driver", "value": "570", "effect": "PreferNoSchedule"}]

    tenants = {
        "pretrain": {"gpu_quota": 160, "description": "foundation-model pretraining"},
        "research": {"gpu_quota": 48, "description": "research experiments"},
        "finetune": {"gpu_quota": 32, "description": "fine-tuning and evaluation"},
        "inference": {"gpu_quota": 48, "description": "production chat serving"},
        "search": {"gpu_quota": 8, "description": "embedding/search serving on a dedicated node"},
    }
    return {
        "cluster": "ORION-256",
        "snapshot": "2026-10-12T09:00:00Z",
        "evidence_class": "SIMULATED",
        "gpus_per_node": 8,
        "nodes": [nodes[i] for i in range(1, 33)],
        "running": running,
        "tenants": tenants,
    }


def build_jobs(rng: random.Random) -> list[dict]:
    def job(jid, tenant, pool, gpus, prio, submit, **kw):
        d = {"job_id": jid, "tenant": tenant, "pool": pool, "gpus": gpus, "priority": prio,
             "submit_time": submit + rng.randint(0, 9), "node_selector": {}, "tolerations": []}
        d.update(kw)
        return d

    sel = {"nvidia.com/gpu.product": GPU_PRODUCT}
    jobs = [
        job("J01", "pretrain", "train", 32, 50, 100, node_selector=dict(sel), note="4-node ablation run"),
        job("J02", "finetune", "train", 8, 50, 120, note="single-node SFT"),
        job("J03", "research", "train", 32, 50, 140, note="4-node sweep"),
        job("J04", "research", "train", 12, 50, 150, note="user asked for 12 GPUs"),
        job("J05", "pretrain", "train", 16, 100, 300, note="urgent 2-node eval of release candidate"),
        job("J06", "research", "train", 8, 10, 40, note="best-effort single-node job"),
        job("J07", "finetune", "train", 4, 50, 200, note="LoRA run"),
        job("J08", "research", "train", 16, 50, 210, note="2-node experiment"),
        job("J09", "finetune", "train", 2, 5, 220, note="scavenger debug job"),
        job("J10", "inference", "infer", 4, 100, 400, note="TP=4 FP8 replica scale-up"),
        job("J11", "inference", "infer", 2, 50, 410, note="small model replica"),
        job("J12", "search", "infer", 8, 50, 420,
            node_selector={"halcyon.ai/dedicated": "search"},
            tolerations=[{"key": "halcyon.ai/dedicated", "operator": "Equal", "value": "search",
                          "effect": "NoSchedule"}],
            note="dedicated search replica"),
        job("J13", "inference", "infer", 8, 50, 430, note="TP=8 BF16 replica"),
        job("J14", "inference", "infer", 8, 10, 440, note="best-effort batch eval replica"),
        job("J15", "inference", "infer", 1, 50, 450, note="1-GPU canary replica"),
    ]
    return jobs


def k8s_node(name, physical=8, allocated=0, allocatable=8, labels=None, taints=None,
             schedulable=True, extra_alloc=None) -> dict:
    lab = {"nvidia.com/gpu.product": GPU_PRODUCT, "halcyon.ai/pool": "infer"}
    lab.update(labels or {})
    alloc = {"nvidia.com/gpu": allocatable}
    alloc.update(extra_alloc or {})
    return {"name": name, "schedulable": schedulable, "physical_gpus": physical,
            "capacity": dict(alloc), "allocatable": alloc,
            "allocated": {"nvidia.com/gpu": allocated}, "labels": lab, "taints": taints or [],
            "conditions": {"Ready": True}}


def slurm_node(name, state, alloc, reason="") -> dict:
    return {"name": name, "slurm_state": state, "physical_gpus": 8,
            "allocatable": {"gres/gpu": 8}, "allocated": {"gres/gpu": alloc},
            "labels": {"feature": "h100,hx8"}, "taints": [], "reason": reason}


def build_cases(rng: random.Random) -> list[dict]:
    cases: list[dict] = []
    ded = [{"key": "halcyon.ai/dedicated", "value": "search", "effect": "NoSchedule"}]

    # P01 — quota exhausted (Kubernetes ResourceQuota / Kueue ClusterQueue)
    cases.append({
        "case_id": "P01", "scheduler": "kubernetes",
        "job": {"name": "chat-70b-replica-7", "tenant": "inference", "resource": "nvidia.com/gpu",
                "gpus_per_node": 8, "nodes": 1, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "ClusterQueue", "name": "inference-cq", "hard": 48, "used": 44},
        "nodes": [k8s_node("orion-n30", allocated=0), k8s_node("orion-n29", allocated=4)],
        "events": ["Workload chat-70b-replica-7 QuotaReserved=False: couldn't assign flavors to pod set "
                   "main: insufficient unused quota for nvidia.com/gpu in flavor h100-sxm, 4 more needed"],
        "dashboard_free_gpus": 12})

    # P02 — untolerated dedicated taint
    cases.append({
        "case_id": "P02", "scheduler": "kubernetes",
        "job": {"name": "rerank-eval", "tenant": "inference", "resource": "nvidia.com/gpu",
                "gpus_per_node": 8, "nodes": 1, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "ResourceQuota", "name": "gpu-quota", "hard": 48, "used": 24},
        "nodes": [k8s_node("orion-n31", allocated=0, labels={"halcyon.ai/dedicated": "search"}, taints=ded),
                  k8s_node("orion-n26", allocated=6), k8s_node("orion-n27", allocated=3)],
        "events": ["0/3 nodes are available: 1 node(s) had untolerated taint {halcyon.ai/dedicated: search}, "
                   "2 Insufficient nvidia.com/gpu. preemption: 0/3 nodes are available: 1 Preemption is not "
                   "helpful for scheduling, 2 No preemption victims found for incoming pod."],
        "dashboard_free_gpus": 15})

    # P03 — fragmentation (Slurm, 4 nodes x 8 GPUs, 34 idle GPUs scattered)
    frag_alloc = [4, 5, 2, 6, 0, 7, 3, 3]  # yields free 4,3,6,2,8,1,5,5 -> only 1 whole-free node
    cases.append({
        "case_id": "P03", "scheduler": "slurm",
        "job": {"name": "jobid=48211 pt-ablation", "tenant": "pretrain", "resource": "gres/gpu",
                "gpus_per_node": 8, "nodes": 4, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "QOS GrpTRES", "name": "pretrain", "hard": 160, "used": 96},
        "nodes": [slurm_node(f"orion-n{13 + k:02d}", "MIXED" if a else "IDLE", a) for k, a in enumerate(frag_alloc)],
        "events": ["squeue: 48211 train pt-ablation PD 0:00 4 (Resources)"],
        "dashboard_free_gpus": sum(8 - a for a in frag_alloc)})

    # P04 — device plugin not advertising (nvidia-smi sees 8 GPUs; allocatable 0)
    cases.append({
        "case_id": "P04", "scheduler": "kubernetes",
        "job": {"name": "chat-70b-replica-8", "tenant": "inference", "resource": "nvidia.com/gpu",
                "gpus_per_node": 8, "nodes": 1, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "ResourceQuota", "name": "gpu-quota", "hard": 48, "used": 8},
        "nodes": [k8s_node("orion-n30", allocated=0, allocatable=0),
                  k8s_node("orion-n32", allocated=8)],
        "events": ["0/2 nodes are available: 2 Insufficient nvidia.com/gpu.",
                   "gpu-operator/nvidia-device-plugin-daemonset-x7k2p on orion-n30: CrashLoopBackOff"],
        "dashboard_free_gpus": 8})

    # P05 — node drained in Slurm after Xid, only place with 8 free
    cases.append({
        "case_id": "P05", "scheduler": "slurm",
        "job": {"name": "jobid=48230 sft-8gpu", "tenant": "finetune", "resource": "gres/gpu",
                "gpus_per_node": 8, "nodes": 1, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "QOS GrpTRES", "name": "finetune", "hard": 32, "used": 10},
        "nodes": [slurm_node("orion-n18", "DRAIN", 0, reason="NHC: GPU Xid 79 (fallen off bus)"),
                  slurm_node("orion-n20", "MIXED", 4), slurm_node("orion-n21", "MIXED", 6)],
        "events": ["squeue: 48230 train sft-8gpu PD 0:00 1 (Resources)"],
        "dashboard_free_gpus": 14})

    # P06 — nodeSelector product mismatch (typo'd product string)
    cases.append({
        "case_id": "P06", "scheduler": "kubernetes",
        "job": {"name": "chat-70b-canary", "tenant": "inference", "resource": "nvidia.com/gpu",
                "gpus_per_node": 4, "nodes": 1,
                "node_selector": {"nvidia.com/gpu.product": "NVIDIA-H100-SXM5-80GB"}, "tolerations": []},
        "quota": {"kind": "ResourceQuota", "name": "gpu-quota", "hard": 48, "used": 20},
        "nodes": [k8s_node("orion-n29", allocated=4), k8s_node("orion-n30", allocated=0)],
        "events": ["0/2 nodes are available: 2 node(s) didn't match Pod's node affinity/selector. preemption: "
                   "0/2 nodes are available: 2 Preemption is not helpful for scheduling."],
        "dashboard_free_gpus": 12})

    # P07 — MIG node exposes mig-1g.10gb slices, job asks for whole nvidia.com/gpu
    cases.append({
        "case_id": "P07", "scheduler": "kubernetes",
        "job": {"name": "embed-batch", "tenant": "inference", "resource": "nvidia.com/gpu",
                "gpus_per_node": 1, "nodes": 1, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "ResourceQuota", "name": "gpu-quota", "hard": 48, "used": 47},
        "nodes": [k8s_node("orion-n28", allocated=0, allocatable=0,
                           labels={"nvidia.com/mig.config": "all-1g.10gb"},
                           extra_alloc={"nvidia.com/mig-1g.10gb": 56}),
                  k8s_node("orion-n25", allocated=8)],
        "events": ["0/2 nodes are available: 2 Insufficient nvidia.com/gpu."],
        "dashboard_free_gpus": 8})

    # P08 — two causes: quota (Kueue) AND the only whole-free node is tainted
    cases.append({
        "case_id": "P08", "scheduler": "kubernetes",
        "job": {"name": "eval-harness-8g", "tenant": "inference", "resource": "nvidia.com/gpu",
                "gpus_per_node": 8, "nodes": 1, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "ClusterQueue", "name": "inference-cq", "hard": 48, "used": 42},
        "nodes": [k8s_node("orion-n31", allocated=0, labels={"halcyon.ai/dedicated": "search"}, taints=ded),
                  k8s_node("orion-n27", allocated=3)],
        "events": ["Workload eval-harness-8g QuotaReserved=False: couldn't assign flavors to pod set main: "
                   "insufficient unused quota for nvidia.com/gpu in flavor h100-sxm, 2 more needed"],
        "dashboard_free_gpus": 13})

    # P09 — control: nothing blocks; job was submitted 3 s ago (scheduling cycle)
    cases.append({
        "case_id": "P09", "scheduler": "kubernetes",
        "job": {"name": "chat-70b-replica-9", "tenant": "inference", "resource": "nvidia.com/gpu",
                "gpus_per_node": 4, "nodes": 1, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "ResourceQuota", "name": "gpu-quota", "hard": 48, "used": 28},
        "nodes": [k8s_node("orion-n29", allocated=4),
                  k8s_node("orion-n30", allocated=0,
                           taints=[{"key": "halcyon.ai/canary-driver", "value": "570",
                                    "effect": "PreferNoSchedule"}])],
        "events": ["pod created 3s ago; no FailedScheduling events yet"],
        "dashboard_free_gpus": 12})

    # P10 — Slurm: drained node hides fragmentation in the rest of the partition
    cases.append({
        "case_id": "P10", "scheduler": "slurm",
        "job": {"name": "jobid=48302 rs-2node", "tenant": "research", "resource": "gres/gpu",
                "gpus_per_node": 8, "nodes": 2, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "QOS GrpTRES", "name": "research", "hard": 48, "used": 20},
        "nodes": [slurm_node("orion-n23", "DRAIN", 0, reason="fw-upgrade wave 2"),
                  slurm_node("orion-n22", "IDLE", 0),
                  slurm_node("orion-n20", "MIXED", 4), slurm_node("orion-n21", "MIXED", 2),
                  slurm_node("orion-n24", "ALLOCATED", 8)],
        "events": ["squeue: 48302 train rs-2node PD 0:00 2 (Resources)"],
        "dashboard_free_gpus": 26})

    # P11 — Kueue gang of 2 pods x 8 GPUs; one whole-free node eligible, second has dedicated taint
    cases.append({
        "case_id": "P11", "scheduler": "kubernetes",
        "job": {"name": "distill-2node", "tenant": "inference", "resource": "nvidia.com/gpu",
                "gpus_per_node": 8, "nodes": 2, "node_selector": {}, "tolerations": []},
        "quota": {"kind": "ClusterQueue", "name": "inference-cq", "hard": 48, "used": 24},
        "nodes": [k8s_node("orion-n30", allocated=0),
                  k8s_node("orion-n31", allocated=0, labels={"halcyon.ai/dedicated": "search"}, taints=ded),
                  k8s_node("orion-n26", allocated=4)],
        "events": ["pod distill-2node-worker-1: 0/3 nodes are available: 1 node(s) had untolerated taint "
                   "{halcyon.ai/dedicated: search}, 2 Insufficient nvidia.com/gpu.",
                   "pod distill-2node-worker-0: Scheduled to orion-n30 (gang not complete; waiting)"],
        "dashboard_free_gpus": 20})

    # P12 — cordoned node (kubectl cordon) after Chapter 16 drain started; plus selector fine
    cases.append({
        "case_id": "P12", "scheduler": "kubernetes",
        "job": {"name": "chat-70b-replica-10", "tenant": "inference", "resource": "nvidia.com/gpu",
                "gpus_per_node": 8, "nodes": 1, "node_selector": {"nvidia.com/gpu.product": GPU_PRODUCT},
                "tolerations": []},
        "quota": {"kind": "ResourceQuota", "name": "gpu-quota", "hard": 48, "used": 32},
        "nodes": [k8s_node("orion-n30", allocated=0, schedulable=False,
                           taints=[{"key": "node.kubernetes.io/unschedulable", "value": "",
                                    "effect": "NoSchedule"}]),
                  k8s_node("orion-n29", allocated=4)],
        "events": ["0/2 nodes are available: 1 Insufficient nvidia.com/gpu, 1 node(s) were unschedulable."],
        "dashboard_free_gpus": 12})

    rng.shuffle(cases)  # order in the file must not leak the case design
    return cases


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "data"))
    ap.add_argument("--seed", type=int, default=17)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    write_json(out / "cluster_state.json", build_cluster(rng))
    write_json(out / "job_queue.json", build_jobs(rng))
    write_json(out / "pending_cases.json", build_cases(rng))
    print(f"wrote 3 files to {out}")


if __name__ == "__main__":
    main()
