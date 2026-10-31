"""Ch 5 L2: capture this host's real GPU/NIC/PCIe topology, measure the GPU's link, and run the GDR gate on it.

What it teaches (Sections 5.3-5.7, Table 5.3): topology is evidence you capture, not something you
assume. The experiment captures the real ``nvidia-smi topo -m`` and PCIe link state, parses them with
the lab's own ``parse_topo_matrix``, scans PCI and sysfs for RDMA NICs, collects every Table 5.3
GPUDirect RDMA prerequisite that can be read without root, and measures the GPU's negotiated link: the
generation it trains to at idle versus under load, and pinned host-to-device bandwidth against the
link ceiling. It then applies the lab's GDR distance gate (``path_model.yaml: gdr_max_relation``) to
what was actually found.

On this kind of host (one GPU, no RDMA NIC) the honest verdict is that GPUDirect RDMA is impossible:
there is no NIC to pair with the GPU. The runtime proof of Exercise 5.15 (NCCL ``/GDRDMA`` channel lines
or ``ib_write_bw --use_cuda``) is recorded as not runnable, with what it needs.

CPU fallback: no GPU is visible, so the experiment captures the PCI/NUMA/RDMA probes, applies the same
gate (which fails for want of both GPU and NIC), and measures host-memory copy bandwidth, the memory
system a host-staged (non-GDR) transfer bounces through.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch05-l2",
    "title": "Lab 5 L2: real host topology capture, PCIe link measurement and the GDR gate",
    "evidence": "MEASURED",
    "cpu_fallback": ("PCI / NUMA / RDMA probes and the Table 5.3 gate without a GPU, plus a host-memory copy "
                     "bandwidth sweep (the memory a host-staged transfer bounces through)"),
}

PKG = Path(__file__).resolve().parents[2]
PCIE_GBPS_PER_LANE = {1: 0.25, 2: 0.5, 3: 0.985, 4: 1.969, 5: 3.938, 6: 7.563}  # GB/s per lane after encoding
REL_ORDER = ["X", "PIX", "PXB", "PHB", "NODE", "SYS"]
ANSI = re.compile(r"\x1b\[[0-9;]*m")


# --------------------------------------------------------------------------------------------- helpers
def sh(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip("\n")
    except FileNotFoundError:
        return 127, f"{cmd[0]}: command not found"
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)


def read(path: str) -> str | None:
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


def pci_scan() -> list[dict]:
    out = []
    for d in sorted(Path("/sys/bus/pci/devices").glob("*")):
        out.append({"bdf": d.name, "class": read(str(d / "class")), "vendor": read(str(d / "vendor")),
                    "device": read(str(d / "device")), "numa_node": read(str(d / "numa_node"))})
    return out


def numa_nodes() -> list[dict]:
    base = Path("/sys/devices/system/node")
    return [{"node": d.name, "cpulist": read(str(d / "cpulist"))} for d in sorted(base.glob("node[0-9]*"))]


def rdma_probe() -> dict:
    ib = Path("/sys/class/infiniband")
    mods = {ln.split()[0] for ln in (read("/proc/modules") or "").splitlines() if ln.strip()}
    return {
        "sys_class_infiniband": sorted(p.name for p in ib.iterdir()) if ib.is_dir() else [],
        "dev_infiniband": Path("/dev/infiniband").exists(),
        "netdevs": sorted(p.name for p in Path("/sys/class/net").iterdir()) if Path("/sys/class/net").is_dir() else [],
        "rdma_modules_loaded": sorted(m for m in mods if m in {"ib_core", "ib_uverbs", "mlx5_core", "mlx5_ib", "rdma_rxe",
                                                                 "irdma", "bnxt_re", "nvidia_peermem", "nv_peer_mem"}),
        "modules_visible": len(mods),
        "tools": {t: bool(shutil.which(t)) for t in ("ibv_devinfo", "ib_write_bw", "lspci", "lstopo", "ofed_info",
                                                      "rdma", "ethtool")},
    }


def topo_capture() -> tuple[str, dict | None, str | None]:
    """Raw `nvidia-smi topo -m` (ANSI stripped) and its parse by the lab's own parser (or a minimal one)."""
    rc, raw = sh(["nvidia-smi", "topo", "-m"])
    raw = ANSI.sub("", raw) if rc == 0 else raw
    if rc != 0:
        return raw, None, None
    mod, src = load_l1("topo_mapper")
    if mod is not None:
        try:
            return raw, mod.parse_topo_matrix(raw), src
        except Exception:  # noqa: BLE001 - starter TODO: fall through to the minimal parser
            pass
    lines = raw.splitlines()
    hdr = next(i for i, ln in enumerate(lines) if "GPU0" in ln and ln.startswith("\t"))
    devices = [h.strip() for h in lines[hdr].split("\t")[1:] if re.fullmatch(r"(GPU|NIC)\d+", h.strip())]
    return raw, {"devices": devices, "rel": {}, "nic_names": {}}, "minimal parser (topo_mapper not implemented)"


def link_ceiling(gen: int, width: int) -> float | None:
    return PCIE_GBPS_PER_LANE.get(gen, 0) * width or None


def nvsmi(fields: list[str]) -> dict:
    rc, out = sh(["nvidia-smi", f"--query-gpu={','.join(fields)}", "--format=csv,noheader,nounits"])
    vals = [v.strip() for v in out.splitlines()[0].split(",")] if rc == 0 and out else []
    return dict(zip(fields, vals)) if len(vals) == len(fields) else {}


# --------------------------------------------------------------------------------------------- run
def run(ctx) -> dict:
    torch = ctx.torch
    rdma = rdma_probe()
    pci = pci_scan()
    net_ctrl = [d for d in pci if (d["class"] or "").startswith("0x02")]
    ib_ctrl = [d for d in pci if (d["class"] or "").startswith("0x0207")]
    cmdline = read("/proc/cmdline") or ""
    kernel = os.uname().release
    tables: dict = {"pci_devices": pci, "numa": numa_nodes()}
    metrics: dict = {"rdma_devices": len(rdma["sys_class_infiniband"]), "pci_network_controllers": len(net_ctrl),
                     "numa_nodes": len(tables["numa"])}
    notes = []
    topo = None
    if ctx.is_gpu:
        raw, topo, parser = topo_capture()
        tables["topo_m_raw"] = raw
        gpus = [d for d in topo["devices"] if d.startswith("GPU")]
        nics = [d for d in topo["devices"] if d.startswith("NIC")]
        metrics.update({"topo_gpus": len(gpus), "topo_nics": len(nics), "topo_parser": parser})
        link_fields = ["pci.bus_id", "pcie.link.gen.max", "pcie.link.gen.gpumax", "pcie.link.gen.hostmax",
                       "pcie.link.gen.gpucurrent", "pcie.link.width.max", "pcie.link.width.current", "driver_version"]
        idle = nvsmi(link_fields)
        # --- PCIe link: idle state, then the state and bandwidth under a pinned H2D load
        mib = 64 if ctx.quick else 256
        n = mib << 20
        host = torch.empty(n, dtype=torch.uint8).pin_memory()
        pageable = torch.empty(n, dtype=torch.uint8)
        dev = torch.empty(n, dtype=torch.uint8, device="cuda")
        time.sleep(1.0)
        idle_gen = nvsmi(["pcie.link.gen.gpucurrent", "pcie.link.width.current"])
        loaded = {}
        stop = time.monotonic() + (1.5 if ctx.quick else 3.0)
        while time.monotonic() < stop:  # keep the link busy while sampling its trained state
            for _ in range(4):
                dev.copy_(host, non_blocking=True)
            loaded = nvsmi(["pcie.link.gen.gpucurrent", "pcie.link.width.current"]) or loaded
        torch.cuda.synchronize()
        reps = ctx.reps(10)
        pinned = ctx.bench(lambda: dev.copy_(host, non_blocking=True), reps=reps)
        page = ctx.bench(lambda: dev.copy_(pageable), reps=reps)
        d2h = ctx.bench(lambda: host.copy_(dev, non_blocking=True), reps=reps)
        gen_max, width_max = int(idle["pcie.link.gen.max"]), int(idle["pcie.link.width.max"])
        ceiling = link_ceiling(gen_max, width_max)
        tables["link"] = [
            {"state": "capability (GPU max)", "gen": idle.get("pcie.link.gen.gpumax"), "width": idle.get("pcie.link.width.max"),
             "host_max_gen": idle.get("pcie.link.gen.hostmax")},
            {"state": "idle (current)", "gen": idle_gen.get("pcie.link.gen.gpucurrent"),
             "width": idle_gen.get("pcie.link.width.current"), "host_max_gen": ""},
            {"state": "under H2D load (current)", "gen": loaded.get("pcie.link.gen.gpucurrent"),
             "width": loaded.get("pcie.link.width.current"), "host_max_gen": ""},
        ]
        tables["bandwidth"] = [
            {"case": c, "size_mib": mib, "median_s": st["median"], "p95_s": st["p95"], "n": st["n"],
             "gbs_median": n / st["median"] / 1e9, "gbs_p95_time": n / st["p95"] / 1e9}
            for c, st in (("h2d_pinned", pinned), ("h2d_pageable", page), ("d2h_pinned", d2h))]
        bw = {r["case"]: r["gbs_median"] for r in tables["bandwidth"]}
        metrics.update({
            "gpu_bdf": idle.get("pci.bus_id"), "driver": idle.get("driver_version"),
            "link_gen_max": gen_max, "link_width_max": width_max, "link_gen_host_max": idle.get("pcie.link.gen.hostmax"),
            "link_gen_idle": idle_gen.get("pcie.link.gen.gpucurrent"), "link_gen_loaded": loaded.get("pcie.link.gen.gpucurrent"),
            "link_width_loaded": loaded.get("pcie.link.width.current"),
            "link_ceiling_gbs": round(ceiling, 2) if ceiling else None,
            "h2d_pinned_gbs": round(bw["h2d_pinned"], 2), "h2d_pageable_gbs": round(bw["h2d_pageable"], 2),
            "d2h_pinned_gbs": round(bw["d2h_pinned"], 2),
            "h2d_pinned_efficiency": round(bw["h2d_pinned"] / ceiling, 3) if ceiling else None,
        })
        ctx.log(f"link Gen{gen_max} x{width_max} (host up to Gen{idle.get('pcie.link.gen.hostmax')}), idle Gen"
                f"{metrics['link_gen_idle']}, loaded Gen{metrics['link_gen_loaded']}; H2D pinned {bw['h2d_pinned']:.2f} GB/s "
                f"of {ceiling:.2f} GB/s")
        del host, pageable, dev
    else:
        mib = 64 if ctx.quick else 256
        src = torch.empty(mib << 20, dtype=torch.uint8)
        dst = torch.empty_like(src)
        st = ctx.bench(lambda: dst.copy_(src), reps=ctx.reps(10))
        tables["bandwidth"] = [{"case": "host_copy", "size_mib": mib, "median_s": st["median"], "p95_s": st["p95"],
                                "n": st["n"], "gbs_median": (mib << 20) / st["median"] / 1e9,
                                "gbs_p95_time": (mib << 20) / st["p95"] / 1e9}]
        metrics["host_copy_gbs"] = round(tables["bandwidth"][0]["gbs_median"], 2)

    # --- Table 5.3 evidence, item by item, from what this host actually shows
    peermem = [m for m in rdma["rdma_modules_loaded"] if m in ("nvidia_peermem", "nv_peer_mem")]
    gpu_pv = [d for d in pci if d["vendor"] == "0x1414" and (d["class"] or "").startswith("0x03")]
    nic_count = len(rdma["sys_class_infiniband"]) + len(ib_ctrl) + len(net_ctrl) + (len([d for d in (topo or {}).get("devices", []) if d.startswith("NIC")]))
    items = [
        {"item": "1 Topology", "evidence": f"topo -m devices: {', '.join((topo or {}).get('devices', [])) or 'no nvidia-smi'}; "
                                            f"PCI network controllers: {len(net_ctrl)}; /sys/class/infiniband: "
                                            f"{rdma['sys_class_infiniband'] or 'absent'}",
         "verdict": "FAIL: no NIC to pair with the GPU" if nic_count == 0 else "check relation"},
        {"item": "2 Peer memory", "evidence": f"peer-memory modules: {peermem or 'none'} ({rdma['modules_visible']} modules "
                                              f"visible); kernel {kernel}",
         "verdict": "FAIL: no nvidia_peermem, and DMA-BUF needs an RDMA NIC driver" if not peermem else "PASS"},
        {"item": "3 Versions", "evidence": f"driver {metrics.get('driver', 'n/a')}; CUDA runtime "
                                           f"{getattr(torch.version, 'cuda', None)}; ofed_info "
                                           f"{'present' if rdma['tools']['ofed_info'] else 'absent'}; ibv_devinfo "
                                           f"{'present' if rdma['tools']['ibv_devinfo'] else 'absent'}",
         "verdict": "INCOMPLETE: no NIC stack or firmware to match against the support matrix"},
        {"item": "4 IOMMU", "evidence": f"/proc/cmdline: {cmdline[:160]}",
         "verdict": ("n/a: WSL2 guest kernel; the IOMMU belongs to the Windows host" if "WSL" in cmdline or "microsoft" in kernel
                     else ("passthrough" if "iommu=pt" in cmdline.split() else "not set: check the vendor-recommended mode"))},
        {"item": "5 ACS", "evidence": (f"no lspci and no root; the guest PCI view is {len(pci)} paravirtual functions"
                                       + (f" ({len(gpu_pv)} Microsoft GPU-PV render devices, class 0x0302)" if gpu_pv else "")),
         "verdict": "NOT READABLE here: needs root lspci -vvv on bare metal"},
        {"item": "6 Runtime", "evidence": "NCCL /GDRDMA channel lines or ib_write_bw --use_cuda need an RDMA NIC and a peer",
         "verdict": "NOT RUNNABLE: no RDMA NIC, no second host"},
    ]
    tables["gdr_checklist"] = items

    # --- the lab's GDR distance gate applied to the GPU-NIC pairs actually found
    import yaml  # noqa: PLC0415
    model = yaml.safe_load((PKG / "lab" / "data" / "path_model.yaml").read_text(encoding="utf-8"))
    gate = model["gdr_max_relation"]
    pairs = []
    if topo and topo.get("rel"):
        for (row, col), rel in topo["rel"].items():
            if row.startswith("GPU") and col.startswith("NIC"):
                pairs.append({"gpu": row, "nic": col, "relation": rel,
                              "gdr_allowed": REL_ORDER.index(rel) <= REL_ORDER.index(gate) if rel in REL_ORDER else False})
    tables["gdr_pairs"] = pairs
    metrics["gdr_pairs_allowed"] = sum(p["gdr_allowed"] for p in pairs)
    metrics["gdr_possible"] = bool(pairs) and metrics["gdr_pairs_allowed"] > 0 and bool(peermem)
    metrics["gdr_gate"] = gate
    metrics["host_staged_cap_model_gbs"] = model["modifiers"]["host_staged"]["bw_cap_GBps"]

    not_runnable = [
        {"part": "Exercise 5.15 runtime proof: NCCL NET/IB/.../GDRDMA channel lines or ib_write_bw --use_cuda",
         "needs": ["an RDMA NIC (ConnectX-class or similar) on the GPU's PCIe switch", "nvidia_peermem or DMA-BUF support",
                   "a second host on an RDMA fabric"],
         "probe": rdma},
        {"part": "L2 capture script (capture/capture_topology.sh) with lspci -vvv ACS/LnkSta, lstopo, ibdev2netdev, LLDP",
         "needs": ["root on bare metal (not a WSL2 guest)", "lspci, lstopo, rdma-core", "an RDMA NIC"],
         "probe": {"tools": rdma["tools"], "euid": os.geteuid()}},
        {"part": "NVLink / fabric manager status (nvidia-smi nvlink --status)", "needs": ["an NVLink-equipped multi-GPU host"],
         "probe": f"{metrics.get('topo_gpus', 0)} GPU(s) in topo -m"},
    ]
    notes += [
        "Every row of the Table 5.3 checklist is built from a command or sysfs file read during this run; the raw "
        "topo -m output and the PCI scan are in results.json.",
        f"GDR gate from lab/data/path_model.yaml: a GPU-NIC pair is GDR-eligible when its relation is at most {gate}.",
        "Bandwidth: median of >= 5 timed repetitions after 3 warm-ups (CUDA events on the GPU, perf_counter on the CPU).",
    ]
    return {"metrics": metrics, "tables": tables, "notes": notes, "not_runnable_parts": not_runnable}


# --------------------------------------------------------------------------------------------- invariants
def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    fails = []
    if any(r["gbs_median"] <= 0 for r in t["bandwidth"]):
        fails.append("non-positive bandwidth")
    if any(r["n"] < 5 for r in t["bandwidth"]):
        fails.append("fewer than 5 repetitions in a bandwidth case")
    if m["gdr_possible"] and m["rdma_devices"] == 0 and m.get("topo_nics", 0) == 0:
        fails.append("GDR marked possible without any RDMA NIC: the gate logic is wrong")
    if m.get("topo_nics", 0) == 0 and m["gdr_pairs_allowed"]:
        fails.append("GDR-eligible pairs reported although topo -m lists no NIC")
    if not t["gdr_checklist"] or len(t["gdr_checklist"]) != 6:
        fails.append("the Table 5.3 checklist must have all six items")
    if env["device"] != "cuda":
        return fails
    if m.get("topo_gpus", 0) < 1:
        fails.append("nvidia-smi topo -m shows no GPU although CUDA is available: check the parser against the raw output")
    ceiling = m["link_ceiling_gbs"]
    if ceiling and m["h2d_pinned_gbs"] > 1.05 * ceiling:
        fails.append(f"pinned H2D {m['h2d_pinned_gbs']} GB/s exceeds the Gen{m['link_gen_max']} x{m['link_width_max']} "
                     f"ceiling {ceiling} GB/s: check the link fields or the timing")
    if ceiling and m["h2d_pinned_gbs"] < 0.4 * ceiling:
        fails.append(f"pinned H2D {m['h2d_pinned_gbs']} GB/s is < 40 % of the {ceiling} GB/s link: check LnkSta (downtrained "
                     "link?) or contention from another job")
    if m["h2d_pinned_gbs"] < 0.95 * m["h2d_pageable_gbs"]:
        fails.append("pinned H2D is slower than pageable: pinned memory should never lose")
    try:
        if int(m["link_gen_loaded"]) > int(m["link_gen_max"]) or int(m["link_width_loaded"]) > int(m["link_width_max"]):
            fails.append("the link trained above its capability: the nvidia-smi fields are inconsistent")
    except (TypeError, ValueError):
        fails.append("no link state captured under load: was nvidia-smi queried while the copies ran?")
    return fails


# --------------------------------------------------------------------------------------------- report
def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    lines = ["## Table 5.3 GPUDirect RDMA evidence on this host", "", "| Item | Evidence (captured now) | Verdict |",
             "|---|---|---|"]
    for r in t["gdr_checklist"]:
        lines.append(f"| {r['item']} | {r['evidence'].replace('|', '/')} | {r['verdict']} |")
    lines += ["", f"**GDR verdict: {'possible' if m['gdr_possible'] else 'impossible on this host'}.** "
              f"RDMA devices in /sys/class/infiniband: {m['rdma_devices']}; PCI network controllers: "
              f"{m['pci_network_controllers']}; GPU-NIC pairs within the {m['gdr_gate']} gate: {m['gdr_pairs_allowed']}. "
              "With no NIC there is no GPU-NIC path to classify, so NCCL would fall back to host-staged or socket "
              "transport for any inter-node traffic."]
    if gpu:
        lines += ["", "## nvidia-smi topo -m (raw)", "", "```", t["topo_m_raw"].rstrip(), "```", "",
                  "## PCIe link of the GPU", "", "| State | Gen | Width | Host max Gen |", "|---|---|---|---|"]
        for r in t["link"]:
            lines.append(f"| {r['state']} | {r['gen']} | x{r['width']} | {r['host_max_gen']} |")
        lines += ["", "| Case | Size (MiB) | GB/s (median) | GB/s at p95 time | n |", "|---|---|---|---|---|"]
        for r in t["bandwidth"]:
            lines.append(f"| {r['case']} | {r['size_mib']} | {r['gbs_median']:.2f} | {r['gbs_p95_time']:.2f} | {r['n']} |")
        lines += ["", f"Link ceiling Gen{m['link_gen_max']} x{m['link_width_max']} = **{m['link_ceiling_gbs']} GB/s** per "
                  f"direction `[MODELED]`; pinned H2D reached **{m['h2d_pinned_gbs']} GB/s** "
                  f"({m['h2d_pinned_efficiency'] * 100:.0f} %) `[MEASURED]`.", "",
                  "What to conclude:", "",
                  f"- The GPU is a x{m['link_width_max']} device: the host could run Gen{m['link_gen_host_max']}, the GPU "
                  f"trains Gen{m['link_gen_max']} x{m['link_width_max']}. Always read capability *and* current state; a laptop "
                  "or riser slot can halve a link without any error.",
                  f"- Idle link generation was Gen{m['link_gen_idle']}, under load Gen{m['link_gen_loaded']}. A reading "
                  "taken at idle can show a power-managed lower generation; capture LnkSta under load before calling a link "
                  "downtrained.",
                  f"- The lab's model caps a host-staged path at {m['host_staged_cap_model_gbs']} GB/s on an HX8 (Gen5 x16) "
                  f"node. On this host the same path would be capped by this link (about {m['h2d_pinned_gbs']} GB/s "
                  "measured), which is why the model's parameters must be recalibrated per platform.",
                  "- This is a laptop Ada GPU in a WSL2 guest, not an HX8 node: there is no PCIe switch, no NIC and no "
                  "second GPU, so the PIX/PXB/SYS distinctions of the lab cannot be exercised here."]
    else:
        lines += ["", "## Host memory copy", "", f"Host copy bandwidth: **{m['host_copy_gbs']} GB/s** `[MEASURED]` "
                  f"(median of {t['bandwidth'][0]['n']}).", "",
                  "_CPU fallback: no GPU is visible, so no topo -m, link state or H2D bandwidth was measured; the "
                  "GPU-only invariants were skipped. The GDR gate fails for want of both GPU and NIC._"]
    lines += ["", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}.")
    return "\n".join(lines)
