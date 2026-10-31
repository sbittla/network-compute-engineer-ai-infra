#!/usr/bin/env python3
"""3.12: build the host inventory of orion-n01 from its snapshot, with provenance per value.

Usage: python solve.py --out DIR
Reads lab/data/snapshots/orion-n01.json [SIMULATED].
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def house(line: str) -> str:
    """Apply the book's copyedit house style to generated Markdown (x -> ×, ~ -> ≈, '40 %', µs)."""
    line = re.sub(r"(\d)%", r"\1 %", line)
    line = line.replace(" x ", " × ")
    line = re.sub(r"(\d)x\b", r"\1×", line)
    line = re.sub(r"~ ?", "≈ ", line)
    line = re.sub(r"(\d) us\b", r"\1 µs", line)
    return line.replace("scaleout", "scale-out").replace("scaleup", "scale-up")

SNAP = Path(__file__).resolve().parents[4] / "lab" / "data" / "snapshots" / "orion-n01.json"
CLASSES = {"0x030200": "gpu", "0x010802": "nvme", "0x030000": "vga"}
NIC_DEVICES = {"0x1021": "rail_nic", "0x101d": "fe_nic"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    s = {k: v["stdout"] for k, v in json.loads(SNAP.read_text(encoding="utf-8"))["sections"].items()}
    inv: dict[str, dict] = {}
    lscpu = {k.strip(): v.strip() for k, _, v in (l.partition(":") for l in s["lscpu"].splitlines())}
    inv["cpu"] = {"value": {"model": lscpu["Model name"], "sockets": int(lscpu["Socket(s)"]),
                            "cores_per_socket": int(lscpu["Core(s) per socket"]),
                            "threads_per_core": int(lscpu["Thread(s) per core"]), "cpus": int(lscpu["CPU(s)"])},
                  "section": "lscpu"}
    sizes = {int(n): int(mb) for n, mb in re.findall(r"node (\d+) size: (\d+) MB", s["numactl_hardware"])}
    inv["numa"] = {"value": {f"node{n}": {"cpus": lscpu[f"NUMA node{n} CPU(s)"], "mb": mb} for n, mb in sizes.items()},
                   "section": "numactl_hardware, lscpu"}
    inv["memory"] = {"value": {"free_total_mib": int(next(l for l in s["free"].splitlines() if l.startswith("Mem:")).split()[1])},
                     "section": "free"}
    devs = []
    for line in s["pcie_sysfs"].splitlines():
        bdf, *kv = line.split(";")
        f = dict(x.split("=", 1) for x in kv)
        kind = CLASSES.get(f["class"]) or NIC_DEVICES.get(f["device"], "other")
        devs.append({"bdf": bdf[5:], "kind": kind, "numa": int(f["numa_node"]),
                     "speed": f["current_link_speed"].split()[0], "width": int(f["current_link_width"]),
                     "max_speed": f["max_link_speed"].split()[0], "max_width": int(f["max_link_width"])})
    by = {}
    for d in devs:
        by.setdefault(d["kind"], []).append(d)
    gpus_smi = [l.split(",")[1].strip().lower()[9:] for l in s["nvidia_smi"].splitlines()[1:] if l.strip()]
    inv["gpus"] = {"value": [{"bdf": d["bdf"], "numa": d["numa"], "link": f"{d['speed']} GT/s x{d['width']}"} for d in by["gpu"]],
                   "section": "nvidia_smi, pcie_sysfs"}
    for kind in ("rail_nic", "fe_nic", "nvme", "vga"):
        links = sorted({f"{d['speed']} GT/s x{d['width']}" for d in by[kind]})
        inv[kind] = {"value": {"count": len(by[kind]), "links": links,
                               "all_at_capability": all(d["speed"] == d["max_speed"] and d["width"] == d["max_width"] for d in by[kind])},
                     "section": "pcie_sysfs"}
    mtus = dict(re.findall(r"^\d+: (\S+): <[^>]*> mtu (\d+)", s["ip_link"], re.M))
    speeds = {k.split(":", 1)[1]: int(re.search(r"Speed: (\d+)Mb/s", v).group(1)) for k, v in s.items() if k.startswith("ethtool:")}
    inv["interfaces"] = {"value": {i: {"mtu": int(mtus[i]), "speed_mbps": speeds[i]} for i in sorted(speeds)},
                         "section": "ip_link, ethtool:*"}
    inv["kernel"] = {"value": s["uname"].split()[2], "section": "uname"}
    inv["drivers"] = {"value": {"nvidia": re.search(r"Kernel Module\s+(\S+)", s["kernel_log"]).group(1),
                                "mlx5_fw": re.search(r"mlx5_core \S+ firmware version: (\S+)", s["kernel_log"]).group(1)},
                      "section": "kernel_log"}
    cf = dict(re.findall(r"^(scaling_\w+): (\S+)", s["cpufreq"], re.M))
    inv["cpufreq"] = {"value": {"driver": cf["scaling_driver"], "governor": cf["scaling_governor"]}, "section": "cpufreq"}

    c = inv["cpu"]["value"]
    assert c["model"] == "Intel(R) Xeon(R) Platinum 8480+" and (c["sockets"], c["cores_per_socket"], c["threads_per_core"], c["cpus"]) == (2, 56, 2, 224)
    assert sizes == {0: 1031868, 1: 1032151} and inv["memory"]["value"]["free_total_mib"] == 2064019
    gpu_bdfs = [g["bdf"] for g in inv["gpus"]["value"]]
    assert sorted(gpu_bdfs) == sorted(gpus_smi) == ["18:00.0", "2a:00.0", "3a:00.0", "5d:00.0", "9a:00.0", "ab:00.0", "ba:00.0", "db:00.0"]
    assert [g["numa"] for g in inv["gpus"]["value"]] == [0, 0, 0, 0, 1, 1, 1, 1]
    assert all(g["link"] == "32.0 GT/s x16" for g in inv["gpus"]["value"])
    assert inv["rail_nic"]["value"] == {"count": 8, "links": ["32.0 GT/s x16"], "all_at_capability": True}
    assert inv["fe_nic"]["value"] == {"count": 2, "links": ["16.0 GT/s x16"], "all_at_capability": True}
    assert inv["nvme"]["value"] == {"count": 8, "links": ["16.0 GT/s x4"], "all_at_capability": True}
    ifs = inv["interfaces"]["value"]
    assert all(v["mtu"] == 9000 for v in ifs.values())
    assert all(ifs[f"rail{i}"]["speed_mbps"] == 400000 for i in range(8)) and all(ifs[f"fe{i}"]["speed_mbps"] == 200000 for i in range(2))
    assert inv["kernel"]["value"] == "5.15.0-122-generic"
    assert inv["drivers"]["value"] == {"nvidia": "550.127.05", "mlx5_fw": "28.39.1002"}
    assert inv["cpufreq"]["value"] == {"driver": "intel_pstate", "governor": "performance"}
    result = {"evidence": "[SIMULATED] snapshot orion-n01", "answer": inv, "units": {"memory": "MB / MiB", "speed": "Mb/s"}}
    md = ["# 3.12 — orion-n01 inventory `[SIMULATED]`", "", "| Category | Value | Section |", "|---|---|---|"]
    for k, v in inv.items():
        md.append(f"| {k} | {json.dumps(v['value'], sort_keys=True)} | {v['section']} |")
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
