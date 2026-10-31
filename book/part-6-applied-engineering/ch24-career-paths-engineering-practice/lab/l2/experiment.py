"""Ch 24 L2: turn one lab_l1 evidence item into lab_hw evidence on this host, and score what changes.

The chapter's L2 extension asks the learner to take one ``lab_l1`` evidence item and back it with a
hardware run on one GPU host: record GPU model, driver, CUDA, NCCL, kernel, the commands, >= 5
repetitions, the warm-up policy and the raw output paths, then change the item to ``type: lab_hw``,
``measured_on_hardware: true`` with an ``artifact`` that points at the raw results.

This experiment does exactly that for the fictional learner's item **E08** (``host_topology``,
"GPU-to-NIC mapping CSV and aligned/misaligned model", Chapter 5):

1. **Hardware run.** It captures the Chapter 5 evidence on this host (``nvidia-smi -q`` header,
   ``nvidia-smi topo -m``, PCIe link state, NUMA layout, and an RDMA/NIC probe) and measures pinned
   host-to-device bandwidth against the negotiated link (3 warm-ups, >= 5 repetitions). The raw command
   output is stored in ``results.json``. The README's intra-node ``all_reduce_perf -g <ngpus>`` needs
   >= 2 GPUs and is recorded as not runnable.
2. **The L2 manifest record.** Every field the lab's ``manifest.yaml`` lists under the L2 extension,
   filled from this run.
3. **The evidence conversion, scored with the lab's own model** (``effective_level``,
   ``demonstrated_levels``, ``readiness``). It scores the original item, the converted ``lab_hw`` item,
   and the two classic mistakes: flipping ``measured_on_hardware`` on a ``lab_l1`` item
   (SIMULATION_CLAIMED_AS_MEASURED) and a ``lab_hw`` item with no artifact (NO_ARTIFACT). Then it
   recomputes the learner's readiness for their target role with the converted item.

The run also states what it does *not* prove: there is no NIC on this host, so the GPU-NIC half of
E08's claim is still unevidenced. The converted item's summary says so.

CPU fallback: the hardware run is the host half only (NUMA layout, host memory copy bandwidth, the
RDMA probe); the GPU fields are recorded as absent, and the converted item keeps its claimed level at 2,
because a CPU-only run does not show GPU topology skills.
"""
from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXPERIMENT = {
    "id": "ch24-l2",
    "title": "Lab 24 L2: converting a lab_l1 evidence item into lab_hw evidence (host topology, Chapter 5)",
    "evidence": "MEASURED",
    "cpu_fallback": ("the host half of the topology run (NUMA layout, host memory copy bandwidth, RDMA probe), with the "
                     "converted item's claim kept at level 2 because no GPU was measured"),
}

PKG = Path(__file__).resolve().parents[2]
ITEM_ID = "E08"
PCIE_GBPS_PER_LANE = {1: 0.25, 2: 0.5, 3: 0.985, 4: 1.969, 5: 3.938, 6: 7.563}
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def sh(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, ANSI.sub("", (p.stdout + p.stderr).strip("\n"))
    except FileNotFoundError:
        return 127, f"{cmd[0]}: command not found"
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)


def read(path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def load_l1(name: str):
    """The L1 module: the reference solution if present, else the learner's starter (student release)."""
    for d in (PKG / "solutions" / "lab", PKG / "lab" / "starter"):
        p = d / f"{name}.py"
        if p.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            try:
                spec.loader.exec_module(mod)
                return mod, p.relative_to(PKG).as_posix()
            except Exception:  # noqa: BLE001
                continue
    return None, None


def hardware_run(ctx) -> dict:
    torch = ctx.torch
    import hwlab  # noqa: PLC0415 - /opt/hwlab is on sys.path inside the image

    raw, cmds = {}, []

    def capture(cmd: list[str], lines: int | None = None) -> str:
        rc, out = sh(cmd)
        text = "\n".join(out.splitlines()[:lines]) if lines else out
        raw[" ".join(cmd)] = text
        cmds.append(" ".join(cmd) + (f" | head -{lines}" if lines else ""))
        return text

    numa = {d.name: read(d / "cpulist") for d in sorted(Path("/sys/devices/system/node").glob("node[0-9]*"))}
    raw["/sys/devices/system/node/*/cpulist"] = "\n".join(f"{k}: {v}" for k, v in numa.items())
    cmds.append("cat /sys/devices/system/node/node*/cpulist   # lstopo / numactl are not installed in the image")
    ib = Path("/sys/class/infiniband")
    rdma = sorted(p.name for p in ib.iterdir()) if ib.is_dir() else []
    raw["ls /sys/class/infiniband"] = "\n".join(rdma) or "ls: cannot access '/sys/class/infiniband': No such file or directory"
    cmds.append("ls /sys/class/infiniband")
    out = {"numa_nodes": numa, "rdma_devices": rdma, "tools": {t: bool(shutil.which(t)) for t in
                                                             ("nvidia-smi", "lstopo", "numactl", "all_reduce_perf", "ibv_devinfo")}}
    mib = 64 if ctx.quick else 256
    n = mib << 20
    if ctx.is_gpu:
        header = capture(["nvidia-smi", "-q"], 40)
        topo = capture(["nvidia-smi", "topo", "-m"])
        link = capture(["nvidia-smi", "--query-gpu=name,driver_version,pcie.link.gen.max,pcie.link.width.max,"
                        "pcie.link.gen.gpucurrent,pcie.link.width.current", "--format=csv"])
        vals = [v.strip() for v in link.splitlines()[-1].split(",")]
        name, driver, gmax, wmax = vals[0], vals[1], int(vals[2]), int(vals[3])
        cuda_ver = re.search(r"CUDA Version\s*:\s*(\S+)", header)
        src = torch.empty(n, dtype=torch.uint8).pin_memory()
        dev = torch.empty(n, dtype=torch.uint8, device="cuda")
        st = ctx.bench(lambda: dev.copy_(src, non_blocking=True), warmup=3, reps=ctx.reps(10))
        cmds.append(f"python: torch dev.copy_(pinned {mib} MiB, non_blocking=True), CUDA events, 3 warm-ups + {st['n']} reps")
        ceiling = PCIE_GBPS_PER_LANE[gmax] * wmax
        try:
            v = torch.cuda.nccl.version()
            nccl = ".".join(map(str, v)) if isinstance(v, tuple) else str(v)
        except Exception:  # noqa: BLE001 - NCCL not built in
            nccl = None
        out.update({"gpu_model": name, "driver_version": driver, "cuda_driver_api": cuda_ver.group(1) if cuda_ver else None,
                    "cuda_runtime": torch.version.cuda, "nccl_version": nccl, "link": f"Gen{gmax} x{wmax}",
                    "link_current": f"Gen{vals[4]} x{vals[5]}", "ceiling_gbs": ceiling,
                    "h2d_gbs_median": n / st["median"] / 1e9, "h2d_gbs_at_p95_time": n / st["p95"] / 1e9, "reps": st["n"],
                    "topo_lists_nic": "NIC0" in topo, "gpu_count": torch.cuda.device_count()})
    else:
        a = torch.empty(n, dtype=torch.uint8)
        b = torch.empty_like(a)
        st = ctx.bench(lambda: b.copy_(a), warmup=3, reps=ctx.reps(10))
        cmds.append(f"python: torch host copy_ {mib} MiB, perf_counter, 3 warm-ups + {st['n']} reps")
        out.update({"gpu_model": None, "driver_version": None, "cuda_runtime": torch.version.cuda, "nccl_version": None,
                    "host_copy_gbs_median": n / st["median"] / 1e9, "reps": st["n"], "gpu_count": 0, "topo_lists_nic": False})
    out.update({"kernel": os.uname().release, "commands": cmds, "raw_outputs": raw, "size_mib": mib,
                "label": hwlab.label_for({"device": ctx.device, "gpus": [],
                                          "gpu0": {"name": out.get("gpu_model") or ""} if ctx.is_gpu else {}})})
    return out


def run(ctx) -> dict:
    import yaml  # noqa: PLC0415
    hw = hardware_run(ctx)
    data = PKG / "lab" / "data"
    manifest_fields = next(e for e in yaml.safe_load((PKG / "lab" / "manifest.yaml").read_text(encoding="utf-8"))["extensions"]
                           if e["tier"] == "L2")["record"]
    artifact = f"lab/l2/results/{hw['label']}/results.json"
    record = {
        "gpu_model": hw["gpu_model"] or "none (CPU fallback)", "driver_version": hw["driver_version"] or "n/a",
        "cuda_version": f"driver API {hw.get('cuda_driver_api')}, runtime {hw['cuda_runtime']}" if ctx.is_gpu else "n/a",
        "nccl_version": hw["nccl_version"] or "n/a", "os_kernel": hw["kernel"], "commands_run": hw["commands"],
        "run_count": hw["reps"], "warmup_policy": "3 warm-up transfers discarded before timing",
        "raw_output_paths": [f"{artifact} (tables.hardware[0].raw_outputs)"],
    }
    today = dt.date.today()
    mod, src = load_l1("career_lab")
    ev = yaml.safe_load((data / "learner_evidence.yaml").read_text(encoding="utf-8"))
    mats = yaml.safe_load((data / "competency_matrices.yaml").read_text(encoding="utf-8"))
    original = next(e for e in ev["evidence"] if e["id"] == ITEM_ID)
    claim = 3 if ctx.is_gpu else 2
    converted = {**copy.deepcopy(original), "type": "lab_hw", "measured_on_hardware": True, "claimed_level": claim,
                 "artifact": artifact, "date": today.isoformat(),
                 "summary": (original["summary"] + f" Hardware run on {hw['gpu_model'] or 'a CPU-only host'}: topo -m, PCIe link "
                             f"state, NUMA layout and {hw['reps']}-rep pinned H2D bandwidth [MEASURED]. Not shown: GPU-NIC "
                             "alignment (no NIC on this host).")}
    variants = {
        "original lab_l1": original,
        "mistake: lab_l1 with measured_on_hardware: true": {**original, "measured_on_hardware": True, "claimed_level": claim},
        "converted lab_hw": converted,
        "mistake: lab_hw without artifact": {**converted, "artifact": ""},
    }
    scored, readiness, err = [], {}, None
    if mod is not None:
        try:
            rules, known = mats["evidence_rules"], set(mats["catalog"])
            for name, item in variants.items():
                lvl, flags = mod.effective_level(item, rules, today, known)
                scored.append({"variant": name, "type": item["type"], "claimed": item["claimed_level"],
                               "measured_on_hardware": item["measured_on_hardware"], "artifact": bool(item["artifact"]),
                               "effective_level": lvl, "flags": flags, "type_cap": rules["type_caps"][item["type"]]})
            role_id, sen = ev["learner"]["target_role"], ev["learner"]["target_seniority"]
            role = mats["roles"][role_id]
            for label, items in (("before", ev["evidence"]),
                                 ("after", [converted if e["id"] == ITEM_ID else e for e in ev["evidence"]])):
                levels, _ = mod.demonstrated_levels(items, mats["catalog"], rules, today)
                r = mod.readiness(role, sen, levels, rules)
                readiness[label] = {**r, "host_topology_level": levels.get("host_topology")}
            readiness["role"], readiness["seniority"] = role.get("title", role_id), sen
        except Exception as exc:  # noqa: BLE001 - starter TODOs
            err = f"{type(exc).__name__}: {exc}"
    metrics = {
        "item": ITEM_ID, "competency": original["competency"], "claimed_after": claim,
        "effective_before": next((s["effective_level"] for s in scored if s["variant"] == "original lab_l1"), None),
        "effective_after": next((s["effective_level"] for s in scored if s["variant"] == "converted lab_hw"), None),
        "readiness_before": readiness.get("before", {}).get("score"), "readiness_after": readiness.get("after", {}).get("score"),
        "manifest_fields_filled": sum(1 for f in manifest_fields if record.get(f) not in (None, "", [])),
        "manifest_fields_required": len(manifest_fields), "run_count": hw["reps"],
    }
    if ctx.is_gpu:
        metrics.update({"h2d_gbs_median": round(hw["h2d_gbs_median"], 2), "link": hw["link"], "ceiling_gbs": round(hw["ceiling_gbs"], 2)})
    else:
        metrics["host_copy_gbs_median"] = round(hw["host_copy_gbs_median"], 2)
    not_runnable = [{"part": "Intra-node nccl-tests all_reduce_perf -b 8 -e 4G -f 2 -g <ngpus> (Chapter 12 evidence)",
                     "needs": [">= 2 GPUs in one host", "nccl-tests built against the installed NCCL"],
                     "probe": {"gpu_count": hw["gpu_count"], "all_reduce_perf": hw["tools"]["all_reduce_perf"]}},
                    {"part": "GPU-NIC alignment half of E08 (topo -m GPU-NIC relation, ibdev2netdev)",
                     "needs": ["an RDMA NIC on the GPU host"], "probe": {"rdma_devices": hw["rdma_devices"],
                                                                        "topo_lists_nic": hw["topo_lists_nic"]}}]
    notes = [f"Item converted: {ITEM_ID} ({original['competency']}). Its artifact points at {artifact}, the results.json this "
             "run writes; raw command output is stored inside it.",
             "Scoring uses the lab's own effective_level / demonstrated_levels / readiness with as_of = the run date."]
    if err:
        notes.append(f"Scoring not run: {err} (implement lab/starter/career_lab.py Part A).")
    yaml_item = yaml.safe_dump([converted], sort_keys=False, allow_unicode=True, width=100)
    return {"metrics": metrics, "tables": {"hardware": [hw], "manifest_record": [record], "scored": scored,
                                           "readiness": [readiness], "converted_item_yaml": yaml_item},
            "notes": notes, "not_runnable_parts": not_runnable}


def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    fails = []
    if m["manifest_fields_filled"] != m["manifest_fields_required"]:
        fails.append(f"only {m['manifest_fields_filled']} of {m['manifest_fields_required']} L2 manifest fields filled: evidence "
                     "without a complete manifest is not lab_hw evidence")
    if m["run_count"] < 5:
        fails.append("fewer than 5 repetitions")
    by = {s["variant"]: s for s in t["scored"]}
    if by:
        conv = by["converted lab_hw"]
        if conv["effective_level"] != min(conv["claimed"], conv["type_cap"]) or conv["flags"]:
            fails.append(f"converted item scored {conv['effective_level']} with flags {conv['flags']}: expected "
                         f"min(claimed, lab_hw cap) and no flags")
        mis = by["mistake: lab_l1 with measured_on_hardware: true"]
        if "SIMULATION_CLAIMED_AS_MEASURED" not in mis["flags"] or mis["effective_level"] > 1:
            fails.append("flipping measured_on_hardware on a lab_l1 item must be flagged and capped")
        if "NO_ARTIFACT" not in by["mistake: lab_hw without artifact"]["flags"]:
            fails.append("a lab_hw item without an artifact must be flagged NO_ARTIFACT")
        r = t["readiness"][0]
        if r and r["after"]["score"] < r["before"]["score"]:
            fails.append("readiness fell after replacing an item with stronger evidence: check demonstrated_levels")
    if env["device"] == "cuda":
        hw = t["hardware"][0]
        if hw["h2d_gbs_median"] > 1.05 * hw["ceiling_gbs"]:
            fails.append(f"H2D {hw['h2d_gbs_median']:.1f} GB/s exceeds the {hw['link']} ceiling {hw['ceiling_gbs']:.1f} GB/s")
        if not hw["raw_outputs"].get("nvidia-smi topo -m"):
            fails.append("no raw topo -m output captured")
    return fails


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    hw, rec = t["hardware"][0], t["manifest_record"][0]
    gpu = env["device"] == "cuda"
    lines = ["## Hardware run backing the evidence", ""]
    if gpu:
        lines += [f"{hw['gpu_model']}, driver {hw['driver_version']}, link {hw['link']} (now {hw['link_current']}), NUMA nodes "
                  f"{list(hw['numa_nodes'])}, RDMA devices {hw['rdma_devices'] or 'none'}. Pinned H2D {hw['size_mib']} MiB: "
                  f"**{hw['h2d_gbs_median']:.2f} GB/s** median ({hw['h2d_gbs_at_p95_time']:.2f} at the p95 time, {hw['reps']} reps) "
                  f"of a {hw['ceiling_gbs']:.2f} GB/s link ceiling `[MEASURED]`."]
    else:
        lines += [f"CPU fallback: NUMA nodes {list(hw['numa_nodes'])}, RDMA devices {hw['rdma_devices'] or 'none'}, host copy "
                  f"{hw['size_mib']} MiB **{hw['host_copy_gbs_median']:.2f} GB/s** ({hw['reps']} reps) `[MEASURED]`."]
    lines += ["", "## L2 manifest record (lab/manifest.yaml, extension L2)", "", "| Field | Value |", "|---|---|"]
    for k, v in rec.items():
        val = "<br>".join(f"`{x}`" for x in v) if isinstance(v, list) else str(v)
        lines.append(f"| {k} | {val.replace('|', chr(92) + '|')} |")
    lines += ["", "## The converted evidence item", "", "```yaml", t["converted_item_yaml"].rstrip(), "```", "",
              "## Scored with the lab's model", "", "| Variant | Type | Claimed | measured_on_hardware | Artifact | Cap | Effective | Flags |",
              "|---|---|---|---|---|---|---|---|"]
    for s in t["scored"]:
        lines.append(f"| {s['variant']} | {s['type']} | {s['claimed']} | {s['measured_on_hardware']} | {'yes' if s['artifact'] else 'no'} | "
                     f"{s['type_cap']} | **{s['effective_level']}** | {', '.join(s['flags']) or '-'} |")
    r = t["readiness"][0]
    if r:
        lines += ["", f"Readiness for **{r['role']} ({r['seniority']})**: {r['before']['score']} ({r['before']['status']}) before, "
                  f"{r['after']['score']} ({r['after']['status']}) after; host_topology level {r['before']['host_topology_level']} -> "
                  f"{r['after']['host_topology_level']}."]
    lines += ["", "What to conclude:", "",
              "- Hardware evidence raises the ceiling (lab_l1 caps at 2, lab_hw at 3); it does not raise the level by itself. "
              "The claim must still be defended, and here the GPU-NIC half of the claim has no evidence because there is no NIC.",
              "- The cheap shortcut, setting `measured_on_hardware: true` on a lab_l1 item, is caught and capped at 1, and a "
              "lab_hw item without an artifact is capped at 1 too. The manifest and the raw output are what make it evidence.",
              "- This is a laptop Ada GPU in a WSL2 container. The evidence is honest about that, which is what a reviewer "
              "checks first."]
    if not gpu:
        lines += ["", "_CPU fallback: no GPU was measured, so the converted item keeps claimed level 2 and the GPU fields of the "
                  "manifest are recorded as n/a._"]
    lines += ["", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}.")
    return "\n".join(lines)
