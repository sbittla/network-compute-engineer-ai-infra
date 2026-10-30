#!/usr/bin/env python3
"""Generate the Chapter 24 lab datasets (deterministic, seeded).

Outputs (written to ../data/):
  competency_matrices.yaml  role competency matrices, competency catalog, evidence rules
  learner_evidence.yaml     one learner's evidence portfolio (fictional person)
  job_register.csv          a SYNTHETIC job-posting register (fictional employers, example.com URLs)
  register_meta.yaml        register as-of date, allowed values, required fields

Every employer, job ID, and URL in the register is fictional. URLs use the reserved
``example.com`` domain (RFC 2606) so that nothing resolves to a real careers site.

Usage:
    python generate_data.py            # writes into ../data
    python generate_data.py --out DIR
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import random
from pathlib import Path

import yaml

SEED = 24
AS_OF = "2026-10-15"

CAPSTONES = {
    "A": "capstone-a-256-gpu-training-cluster",
    "B": "capstone-b-network-telemetry-troubleshooting",
    "C": "capstone-c-distributed-training-performance",
    "D": "capstone-d-llm-inference-platform",
    "E": "capstone-e-fleet-lifecycle-automation",
    "F": "capstone-f-reliability-game-day",
    "G": "capstone-g-fault-tolerant-512-node-training",
    "H": "capstone-h-disaggregated-llm-serving",
}

# id: (name, chapters, capstone letters)
CATALOG = {
    "dc_architecture": ("AI data-center architecture and capacity", [1, 2, 21], ["A"]),
    "linux_host": ("Linux host, NUMA and PCIe diagnostics", [3, 5], ["A", "C"]),
    "gpu_compute": ("GPU architecture, CUDA execution and profiling", [4, 6], ["C"]),
    "host_topology": ("GPU/NIC topology, NVLink and GPUDirect RDMA", [5, 13], ["A", "C"]),
    "l3_fabric": ("Ethernet, BGP/ECMP and leaf-spine design", [7], ["A", "B"]),
    "rdma_fabrics": ("RDMA, RoCEv2, InfiniBand and multi-rail", [8, 13], ["A", "B"]),
    "congestion": ("Congestion control, ECN/PFC and fabric telemetry", [9], ["B"]),
    "physical_layer": ("Switch ASICs, optics, cabling and commissioning", [10], ["B"]),
    "collectives": ("Distributed training and NCCL collectives", [11, 12], ["C", "G"]),
    "storage_ckpt": ("Storage, data pipelines and checkpointing", [14], ["C", "G"]),
    "inference": ("LLM inference and serving infrastructure", [15], ["D", "H"]),
    "fleet_lifecycle": ("Bare-metal GPU fleet lifecycle", [16], ["E"]),
    "scheduling": ("Kubernetes, Slurm and topology-aware scheduling", [17], ["E", "G"]),
    "observability": ("Observability, SLOs and incident response", [18], ["B", "F"]),
    "reliability_security": ("Reliability, security and multi-tenancy", [19], ["F", "G"]),
    "automation": ("Infrastructure automation and safe change", [20], ["E"]),
    "performance_method": ("Cross-layer performance method and benchmark discipline", [6, 22], ["C"]),
    "hw_validation": ("Hardware validation and interoperability testing", [10, 16], ["B"]),
    "communication": ("Design docs, design reviews and case studies", [23, 24], ["A", "F"]),
}

# role: (title, outline emphasis, [(competency, weight, [junior, mid, senior, staff])])
ROLES = {
    "ai_network": ("AI Network Engineer",
                   "BGP, Ethernet, RoCEv2, InfiniBand, RDMA, congestion, optics and switch telemetry", [
                       ("l3_fabric", 3, [2, 3, 3, 4]),
                       ("rdma_fabrics", 3, [1, 2, 3, 4]),
                       ("congestion", 3, [1, 2, 3, 4]),
                       ("physical_layer", 2, [1, 2, 3, 3]),
                       ("host_topology", 2, [1, 2, 3, 3]),
                       ("observability", 2, [1, 2, 3, 3]),
                       ("automation", 1, [1, 2, 2, 3]),
                       ("communication", 1, [1, 2, 3, 4]),
                   ]),
    "gpu_hpc": ("GPU Compute / HPC Engineer",
                "CUDA, GPU architecture, PCIe, NVLink/NVSwitch, NUMA and NCCL", [
                    ("gpu_compute", 3, [2, 3, 3, 4]),
                    ("host_topology", 3, [1, 2, 3, 4]),
                    ("collectives", 3, [1, 2, 3, 4]),
                    ("linux_host", 2, [2, 2, 3, 3]),
                    ("performance_method", 2, [1, 2, 3, 4]),
                    ("rdma_fabrics", 1, [1, 1, 2, 3]),
                    ("communication", 1, [1, 2, 3, 4]),
                ]),
    "cluster_platform": ("AI Cluster / Platform Engineer",
                         "Bare metal, fleet lifecycle, Kubernetes, Slurm, scheduling and tenant operations", [
                             ("fleet_lifecycle", 3, [1, 2, 3, 4]),
                             ("scheduling", 3, [1, 2, 3, 4]),
                             ("automation", 3, [2, 3, 3, 4]),
                             ("linux_host", 2, [2, 2, 3, 3]),
                             ("reliability_security", 2, [1, 2, 3, 3]),
                             ("observability", 1, [1, 2, 2, 3]),
                             ("communication", 1, [1, 2, 3, 4]),
                         ]),
    "performance": ("AI Performance Engineer",
                    "Workload characterization, profiling, benchmarking and optimization", [
                        ("performance_method", 3, [2, 3, 3, 4]),
                        ("gpu_compute", 2, [1, 2, 3, 3]),
                        ("collectives", 3, [1, 2, 3, 4]),
                        ("inference", 2, [1, 2, 3, 3]),
                        ("storage_ckpt", 1, [1, 1, 2, 3]),
                        ("host_topology", 2, [1, 2, 3, 3]),
                        ("communication", 1, [1, 2, 3, 4]),
                    ]),
    "sre_ops": ("AI Infrastructure SRE / Operations",
                "Observability, SLOs, incidents, reliability, remediation and safe change", [
                    ("observability", 3, [2, 3, 3, 4]),
                    ("reliability_security", 3, [1, 2, 3, 4]),
                    ("automation", 2, [2, 2, 3, 3]),
                    ("scheduling", 2, [1, 2, 3, 3]),
                    ("storage_ckpt", 1, [1, 2, 2, 3]),
                    ("linux_host", 2, [2, 2, 3, 3]),
                    ("communication", 2, [1, 2, 3, 4]),
                ]),
    "hw_vendor": ("Network Hardware / Vendor Engineer",
                  "Switch ASICs, buffers, queues, optics, NICs, validation and interoperability", [
                      ("physical_layer", 3, [2, 3, 3, 4]),
                      ("hw_validation", 3, [1, 2, 3, 4]),
                      ("congestion", 2, [1, 2, 3, 4]),
                      ("rdma_fabrics", 2, [1, 2, 3, 3]),
                      ("linux_host", 1, [1, 2, 2, 3]),
                      ("communication", 1, [1, 2, 3, 4]),
                  ]),
}

EVIDENCE_RULES = {
    "proficiency_scale": {
        0: "No evidence",
        1: "Aware: can explain the concept and vocabulary",
        2: "Working: completes defined tasks with guidance; reproduces a lab result",
        3: "Independent: designs, diagnoses and defends decisions without guidance",
        4: "Expert: owns it in production, sets direction, teaches others",
    },
    "seniority_levels": ["junior", "mid", "senior", "staff"],
    "type_caps": {
        "self_assessment": 1,
        "course": 1,
        "lab_l1": 2,
        "lab_hw": 3,
        "capstone": 3,
        "case_study": 3,
        "production": 4,
    },
    "no_artifact_cap": 1,
    "simulation_claimed_as_measured_cap": 1,
    "production_unverified_cap": 3,
    "stale_after_days": 1095,
    "stale_penalty": 1,
    "ready_min_score": 85.0,
    "near_min_score": 70.0,
    "ready_max_gap": 1,
}


def write_matrices(out: Path) -> None:
    doc = {
        "version": "2026-10",
        "note": ("Teaching matrices derived from the course outline role table. Weights 1-3; targets on the "
                 "0-4 proficiency scale per seniority level (junior, mid, senior, staff/principal)."),
        "capstones": CAPSTONES,
        "catalog": {cid: {"name": n, "chapters": ch, "capstones": cp} for cid, (n, ch, cp) in CATALOG.items()},
        "roles": {
            rid: {
                "title": title,
                "emphasis": emph,
                "competencies": [
                    {"id": c, "weight": w, "targets": dict(zip(EVIDENCE_RULES["seniority_levels"], t))}
                    for c, w, t in comps
                ],
            }
            for rid, (title, emph, comps) in ROLES.items()
        },
        "evidence_rules": EVIDENCE_RULES,
    }
    (out / "competency_matrices.yaml").write_text(
        yaml.safe_dump(doc, sort_keys=False, width=110, allow_unicode=False), encoding="utf-8", newline="\n")


def write_evidence(out: Path) -> None:
    items = [
        ("E01", "l3_fabric", "production", 4, "portfolio/case-studies/bgp-underlay-migration.md",
         "2025-06-01", "Former manager (reference available)", False,
         "Led eBGP underlay migration for a 40-leaf DC fabric; zero customer-impacting incidents."),
        ("E02", "l3_fabric", "course", 2, "certs/dc-routing-course.pdf", "2024-03-15", "", False,
         "Completed a vendor data-center routing course."),
        ("E03", "rdma_fabrics", "lab_l1", 3, "book/ch08 lab report", "2026-08-20", "", False,
         "RoCEv2 vs InfiniBand comparison and readiness checklist."),
        ("E04", "rdma_fabrics", "capstone", 3, "portfolio/capstone-b/report.md", "2026-09-30", "", False,
         "Capstone B: RoCE telemetry pipeline with injected-fault scenarios."),
        ("E05", "congestion", "lab_l1", 3, "book/ch09 lab report", "2026-08-28", "", True,
         "ECN/PFC time-series diagnosis on synthetic counters; report states results were 'measured'."),
        ("E06", "congestion", "case_study", 3, "portfolio/case-studies/storage-incast.md", "2022-08-01", "", False,
         "Diagnosed storage incast on a TCP fabric (pre-RDMA role)."),
        ("E07", "physical_layer", "production", 4, "portfolio/runbooks/optics-commissioning.md", "2021-03-01",
         "", False, "Wrote optics commissioning runbook at a previous employer."),
        ("E08", "host_topology", "lab_l1", 2, "book/ch05 lab mapping CSV", "2026-07-30", "", False,
         "GPU-to-NIC mapping CSV and aligned/misaligned model."),
        ("E09", "observability", "self_assessment", 3, "", "2026-10-01", "", False,
         "Self-rated: comfortable with Prometheus and Grafana."),
        ("E10", "observability", "case_study", 3, "", "2026-06-12", "", False,
         "Postmortem for a fabric-wide throughput regression (document not yet published)."),
        ("E11", "automation", "production", 3, "portfolio/code/config-validator/", "2024-01-10",
         "Peer reviewer: tech lead (reference available)", False,
         "Python config validator in CI for switch configs."),
        ("E12", "communication", "case_study", 3, "portfolio/case-studies/ecmp-polarization.md", "2026-09-10",
         "", False, "Performance case study: ECMP hash polarization on rail uplinks."),
        ("E04", "rdma_fabrics", "capstone", 3, "portfolio/capstone-b/report.md", "2026-09-30", "", False,
         "Capstone B (pasted twice in the portfolio index)."),
        ("E14", "bgp_evpn", "production", 4, "portfolio/case-studies/evpn.md", "2025-02-01",
         "Former manager", False, "EVPN-VXLAN tenant overlay design."),
        ("E15", "collectives", "lab_l1", 2, "book/ch12 lab report", "2026-09-05", "", False,
         "NCCL test result analysis: latency vs bandwidth regions."),
        ("E16", "storage_ckpt", "lab_l1", 1, "book/ch14 lab report", "2026-09-15", "", False,
         "Checkpoint write-time model."),
        ("E17", "linux_host", "production", 3, "portfolio/scripts/host-snapshot.sh", "2023-02-01",
         "Team lead", False, "Host diagnostic snapshot script used by the NOC."),
        ("E18", "scheduling", "course", 2, "certs/k8s-admin-course.pdf", "2025-11-20", "", False,
         "Kubernetes administration course."),
        ("E19", "gpu_compute", "self_assessment", 2, "", "", "", False,
         "Self-rated: read about CUDA warps and SMs."),
        ("E20", "reliability_security", "lab_l1", 2, "book/ch19 lab report", "2026-09-25", "", False,
         "Failure-mode analysis and quarantine decision exercise."),
    ]
    doc = {
        "learner": {
            "name": "R. Okafor (fictional learner)",
            "background": "Six years of data-center network engineering; moving into AI networking.",
            "target_role": "ai_network",
            "target_seniority": "senior",
            "as_of": AS_OF,
        },
        "evidence": [
            {"id": i, "competency": c, "type": t, "claimed_level": lvl, "artifact": a, "date": d,
             "verifier": v, "measured_on_hardware": m, "summary": s}
            for i, c, t, lvl, a, d, v, m, s in items
        ],
    }
    (out / "learner_evidence.yaml").write_text(
        yaml.safe_dump(doc, sort_keys=False, width=110), encoding="utf-8", newline="\n")


# ----------------------------------------------------------------------------------------------
# Synthetic job-posting register
# ----------------------------------------------------------------------------------------------
EMPLOYERS = [  # (name, slug, group) -- ALL FICTIONAL
    ("Vantor Cloud", "vantor", "hyperscaler"),
    ("Pelagic Cloud", "pelagic", "hyperscaler"),
    ("Brightwater GPU Cloud", "brightwater", "neocloud"),
    ("Corvid Compute", "corvid", "neocloud"),
    ("Larkspur AI Cloud", "larkspur", "neocloud"),
    ("Quillon Labs", "quillon", "frontier_lab"),
    ("Halcyon AI", "halcyon", "frontier_lab"),
    ("Meridian Silicon", "meridian", "vendor"),
    ("Tessellate Networks", "tessellate", "vendor"),
    ("Aldermoor Optics", "aldermoor", "vendor"),
]
LOCATIONS = ["Austin, US", "Seattle, US", "Remote (US)", "Dublin, IE", "London, UK", "Toronto, CA",
             "Bengaluru, IN", "Singapore, SG", "Tel Aviv, IL", "Amsterdam, NL"]
SENIORITIES = ["junior", "mid", "senior", "senior", "staff", "principal"]
ROLE_TEMPLATES = [
    ("AI Network Engineer", ["bgp", "ecmp", "rocev2", "rdma", "ecn/pfc", "python"],
     ["infiniband", "optics", "switch telemetry", "sonic"]),
    ("GPU Cluster Engineer", ["linux", "nvidia gpus", "pcie/numa", "nccl", "python"],
     ["cuda", "gpudirect rdma", "slurm"]),
    ("AI Infrastructure Platform Engineer", ["kubernetes", "slurm", "bare-metal provisioning", "go", "python"],
     ["terraform", "gpu operator", "firmware lifecycle"]),
    ("AI Performance Engineer", ["profiling", "nccl", "benchmarking", "python", "cuda"],
     ["roofline", "inference serving", "pytorch distributed"]),
    ("AI Infrastructure SRE", ["observability", "slos", "incident response", "kubernetes", "python"],
     ["prometheus", "chaos engineering", "checkpointing"]),
    ("Network Hardware Validation Engineer", ["switch asics", "optics", "traffic generators", "python"],
     ["rdma", "buffer tuning", "interoperability"]),
    ("Inference Infrastructure Engineer", ["inference serving", "kv cache", "kubernetes", "python"],
     ["rdma", "speculative decoding", "load testing"]),
]
FIELDS = ["employer", "employer_group", "title", "job_id", "location", "seniority", "url", "date_checked",
          "required_skills", "preferred_skills", "status"]


def _base_postings(rng: random.Random, n: int) -> list[dict]:
    as_of = dt.date.fromisoformat(AS_OF)
    rows: list[dict] = []
    used: set[str] = set()
    for _ in range(n):
        emp, slug, group = rng.choice(EMPLOYERS)
        title, req, pref = rng.choice(ROLE_TEMPLATES)
        sen = rng.choice(SENIORITIES)
        while True:
            jid = f"SYN-{slug[:3].upper()}-{rng.randint(1000, 8999)}"
            if jid not in used:
                used.add(jid)
                break
        date = as_of - dt.timedelta(days=rng.randint(0, 25))
        prefix = {"junior": "", "mid": "", "senior": "Senior ", "staff": "Staff ", "principal": "Principal "}[sen]
        rows.append({
            "employer": emp, "employer_group": group, "title": prefix + title, "job_id": jid,
            "location": rng.choice(LOCATIONS), "seniority": sen.capitalize() if rng.random() < 0.3 else sen,
            "url": f"https://careers.example.com/{slug}/jobs/{jid}", "date_checked": date.isoformat(),
            "required_skills": ";".join(rng.sample(req, k=min(len(req), rng.randint(3, 5)))),
            "preferred_skills": ";".join(rng.sample(pref, k=rng.randint(1, 2))),
            "status": "active" if rng.random() < 0.8 else "archived",
        })
    return rows


def build_register(rng: random.Random) -> list[dict]:
    base = _base_postings(rng, 50)
    planted: list[dict] = []

    def clone(i: int, **changes: str) -> dict:
        r = dict(base[i])
        r.update(changes)
        return r

    def shift(date: str, days: int) -> str:
        return (dt.date.fromisoformat(date) + dt.timedelta(days=days)).isoformat()

    # P1 exact duplicates (pasted twice from a spreadsheet)
    planted += [clone(0), clone(1), clone(2)]
    # P2 normalisation duplicates: case/whitespace variants, one re-checked later (newer -> representative)
    planted.append(clone(3, employer="  " + base[3]["employer"].upper() + " ", job_id=base[3]["job_id"].lower(),
                         date_checked=shift(base[3]["date_checked"], 1)))
    planted.append(clone(4, employer=base[4]["employer"] + "  ", title=base[4]["title"] + " "))
    # P3 re-posts: same posting URL (tracking query / trailing slash / host case) under a new job ID
    planted.append(clone(5, job_id=base[5]["job_id"] + "-R", url=base[5]["url"] + "/?utm_source=jobboard"))
    planted.append(clone(6, job_id=base[6]["job_id"] + "-R2",
                         url=base[6]["url"].replace("careers.example.com", "Careers.Example.COM")))
    # P4 chain: B shares A's key, C shares B's URL -> A, B, C are one posting
    b = clone(7, url=f"https://careers.example.com/req/{base[7]['job_id']}-77", date_checked=shift(base[7]["date_checked"], -2))
    c = dict(b, job_id=base[7]["job_id"] + "-X", date_checked=shift(base[7]["date_checked"], -3))
    planted += [b, c]
    # P5 missing job ID: one is a copy of an existing posting (same URL), one is a new posting
    planted.append(clone(8, job_id="", date_checked=shift(base[8]["date_checked"], -1)))
    planted.append({
        "employer": "Corvid Compute", "employer_group": "neocloud", "title": "Staff AI Network Engineer",
        "job_id": "", "location": "Remote (US)", "seniority": "staff",
        "url": "https://careers.example.com/corvid/jobs/network-staff-2026", "date_checked": "2026-10-10",
        "required_skills": "bgp;rocev2;ecn/pfc;python", "preferred_skills": "infiniband", "status": "active"})
    # Missing required fields in otherwise-unique postings
    base[10]["date_checked"] = ""
    base[11]["url"] = ""
    base[12]["required_skills"] = ""
    base[13]["seniority"] = ""
    base[14]["location"] = ""
    # Invalid values
    base[15]["date_checked"] = "15/09/2026"
    base[16]["date_checked"] = "2026-11-20"
    base[17]["url"] = base[17]["url"].replace("https://", "http://")
    base[18]["seniority"] = "Sr."
    base[19]["status"] = "open"
    # Stale actives: checked long ago but still marked active
    for i in (20, 21, 22):
        base[i]["date_checked"] = "2026-06-01"
        base[i]["status"] = "active"
    # A stale *archived* posting is fine (should NOT be flagged)
    base[23]["date_checked"] = "2026-05-01"
    base[23]["status"] = "archived"

    rows = base + planted
    rng.shuffle(rows)
    return rows


def write_register(out: Path) -> None:
    rng = random.Random(SEED)
    rows = build_register(rng)
    with (out / "job_register.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    meta = {
        "as_of": AS_OF,
        "synthetic": True,
        "note": ("SYNTHETIC register for teaching. All employers, job IDs and URLs are fictional; URLs use the "
                 "reserved example.com domain. It is not a census of real job postings."),
        "required_fields": ["employer", "title", "job_id", "location", "seniority", "url", "date_checked",
                            "required_skills", "status"],
        "allowed_seniority": ["junior", "mid", "senior", "staff", "principal"],
        "allowed_status": ["active", "archived"],
        "stale_active_after_days": 30,
    }
    (out / "register_meta.yaml").write_text(yaml.safe_dump(meta, sort_keys=False, width=110),
                                            encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    write_matrices(args.out)
    write_evidence(args.out)
    write_register(args.out)
    print(f"wrote datasets to {args.out}")


if __name__ == "__main__":
    main()
