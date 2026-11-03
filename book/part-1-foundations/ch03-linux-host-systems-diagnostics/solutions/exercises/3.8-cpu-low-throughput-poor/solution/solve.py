#!/usr/bin/env python3
"""3.8: quantify the orion-n12 signals from its snapshot.

Usage: python solve.py --out DIR
Reads lab/data/snapshots/orion-n12.json [SIMULATED]. The 40 % shortfall and the peers' ≈ 725 MB/s
md0 rate are from the prompt; the script checks that they agree (435 / 0.60 ≈ 725 MB/s).
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

SNAP = Path(__file__).resolve().parents[4] / "lab" / "data" / "snapshots" / "orion-n12.json"
SHORTFALL = 0.40
CPUS = 224
KEY = {"md0_MBps": 435.2, "remote_fraction": 0.989, "b_mean": 15.25, "member_ratio": 231.0,
       "delivered_fraction": 0.60, "required_MBps": 725.0}


def last_iostat(text: str) -> tuple[dict, dict]:
    lines = text.splitlines()
    start = max(i for i, l in enumerate(lines) if l.startswith("Device"))
    cols = lines[start].split()
    devs = {}
    for l in lines[start + 1:]:
        if not l.strip():
            break
        f = l.split()
        devs[f[0]] = dict(zip(cols[1:], map(float, f[1:])))
    cpu_i = max(i for i, l in enumerate(lines) if l.startswith("avg-cpu"))
    cpu = dict(zip(lines[cpu_i].split()[1:], map(float, lines[cpu_i + 1].split())))
    return devs, cpu


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    sec = json.loads(SNAP.read_text(encoding="utf-8"))["sections"]
    devs, cpu = last_iostat(sec["iostat"]["stdout"])
    md0, n3 = devs["md0"], devs["nvme3n1"]
    siblings = [devs[d]["r_await"] for d in ("nvme0n1", "nvme1n1", "nvme2n1")]
    md0_bps = md0["r/s"] * md0["rareq-sz"] * 1024
    rows = [l.split() for l in sec["vmstat"]["stdout"].splitlines()[2:] if l.strip()]
    b_live = [int(r[1]) for r in rows[1:]]                 # drop the since-boot row
    b_mean = sum(b_live) / len(b_live)
    total = next(l for l in sec["numastat_pid"]["stdout"].splitlines() if l.startswith("Total")).split()
    node0, node1, tot = map(float, total[1:4])
    affinity = sec["taskset_pid"]["stdout"].split(":")[-1].strip()
    remote = node1 / tot if affinity.startswith("0-55") else node0 / tot
    gpu_util = [int(l.rsplit(",", 1)[1].strip(" %")) for l in sec["nvidia_smi"]["stdout"].splitlines()[1:] if l.strip()]
    ans = {"nvme3n1_r_await_ms": n3["r_await"], "sibling_r_await_ms": max(siblings),
           "member_ratio": n3["r_await"] / max(siblings), "md0_r_await_ms": md0["r_await"],
           "md0_MBps": md0_bps / 1e6, "required_MBps": md0_bps / 1e6 / (1 - SHORTFALL),
           "delivered_fraction": 1 - SHORTFALL, "littles_law_nvme3": n3["r/s"] * n3["r_await"] / 1e3,
           "aqu_sz_nvme3": n3["aqu-sz"], "iowait_pct": cpu["%iowait"], "b_live": b_live, "b_mean": b_mean,
           "b_over_cpus_pct": 100 * b_mean / CPUS, "remote_fraction": remote, "pid_affinity": affinity,
           "gpu_util_min": min(gpu_util), "gpu_util_max": max(gpu_util)}
    for k in ("md0_MBps", "remote_fraction", "b_mean", "member_ratio", "required_MBps"):
        assert abs(ans[k] - KEY[k]) <= 0.005 * KEY[k], (k, ans[k])
    assert abs(ans["littles_law_nvme3"] - ans["aqu_sz_nvme3"]) < 0.1
    assert abs(ans["b_over_cpus_pct"] - ans["iowait_pct"]) < 0.2
    assert 55 <= ans["gpu_util_min"] and ans["gpu_util_max"] <= 60
    result = {"evidence": "[SIMULATED] snapshot; derived values [MODELED]",
              "answer": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in ans.items()},
              "units": {"latency": "ms", "throughput": "MB/s (SI)", "fraction": "0-1"}}
    md = ["# 3.8 — orion-n12 `[MODELED]` from `[SIMULATED]` data", "",
          f"- nvme3n1 r_await {n3['r_await']} ms vs siblings {max(siblings)} ms ({ans['member_ratio']:.0f}x)",
          f"- md0 delivers {ans['md0_MBps']:.1f} MB/s; at a 40 % shortfall the loader needs ~{ans['required_MBps']:.0f} MB/s",
          f"- Little's law nvme3n1: {n3['r/s']:.0f}/s x {n3['r_await'] / 1e3} s = {ans['littles_law_nvme3']:.2f} (aqu-sz {n3['aqu-sz']})",
          f"- vmstat b live {b_live}, mean {b_mean}; {ans['b_over_cpus_pct']:.2f} % of 224 CPUs vs %iowait {cpu['%iowait']}",
          f"- PID memory remote to its CPUs: {remote:.1%} (affinity {affinity})",
          f"- GPU utilization {min(gpu_util)}-{max(gpu_util)} %"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
