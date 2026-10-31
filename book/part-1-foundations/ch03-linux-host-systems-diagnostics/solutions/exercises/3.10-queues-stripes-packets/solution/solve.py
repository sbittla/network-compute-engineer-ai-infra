#!/usr/bin/env python3
"""3.10: Little's law, md0 throughput, concurrency limit, iowait check and packet rates.

Usage: python solve.py --out DIR
Reads the live iostat/vmstat sections of lab/data/snapshots/orion-n12.json [SIMULATED].
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
CPUS, OUTSTANDING, HEALTHY_LAT_S, REQ_B = 224, 41, 0.25e-3, 512 * 1024
GEN4X4_GBPS, MEMBERS = 16 * 4 * 128 / 130 / 8, 4
FE_BPS, WIRE_OVERHEAD_B = 200e9, 38
KEY = {"q_nvme3": 40.3, "q_md0": 40.8, "md0_MBps": 435.2, "allowed_GBps": 86.0, "iowait_from_b": 6.8,
       "pps_9000_M": 2.77, "pps_1500_M": 16.3, "ratio": 5.9}


def last_report(text: str) -> dict:
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
    devs["_cpu"] = dict(zip(lines[cpu_i].split()[1:], map(float, lines[cpu_i + 1].split())))
    return devs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    sec = json.loads(SNAP.read_text(encoding="utf-8"))["sections"]
    d = last_report(sec["iostat"]["stdout"])
    n3, md0 = d["nvme3n1"], d["md0"]
    rows = [l.split() for l in sec["vmstat"]["stdout"].splitlines()[2:] if l.strip()]
    b = [int(r[1]) for r in rows[1:]]
    members_kBps = sum(d[f"nvme{i}n1"]["r/s"] * d[f"nvme{i}n1"]["rareq-sz"] for i in range(MEMBERS))
    ans = {"q_nvme3": n3["r/s"] * n3["r_await"] / 1e3, "q_md0": md0["r/s"] * md0["r_await"] / 1e3,
           "md0_MBps": md0["r/s"] * md0["rareq-sz"] * 1024 / 1e6, "members_kBps": members_kBps,
           "md0_rkBps": md0["rkB/s"], "allowed_GBps": OUTSTANDING / HEALTHY_LAT_S * REQ_B / 1e9,
           "member_links_GBps": MEMBERS * GEN4X4_GBPS, "b_live": b, "b_mean": sum(b) / len(b),
           "iowait_from_b": 100 * sum(b) / len(b) / CPUS, "iowait_reported": d["_cpu"]["%iowait"],
           "pps_9000_M": FE_BPS / 8 / (9000 + WIRE_OVERHEAD_B) / 1e6,
           "pps_1500_M": FE_BPS / 8 / (1500 + WIRE_OVERHEAD_B) / 1e6}
    ans["ratio"] = ans["pps_1500_M"] / ans["pps_9000_M"]
    for k, v in KEY.items():
        assert abs(ans[k] - v) <= 0.01 * v, (k, ans[k], v)
    assert abs(ans["members_kBps"] - ans["md0_rkBps"]) < 1e-6
    assert ans["allowed_GBps"] > ans["member_links_GBps"]
    assert abs(ans["iowait_from_b"] - ans["iowait_reported"]) < 0.2
    result = {"evidence": "[SIMULATED] snapshot; derived values [MODELED]",
              "answer": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in ans.items()},
              "units": {"queue": "requests", "throughput": "MB/s or GB/s (SI)", "rate": "Mpps", "iowait": "%"}}
    md = ["# 3.10 `[MODELED]`", "",
          f"- (a) Little: nvme3n1 {ans['q_nvme3']:.1f} (aqu-sz {n3['aqu-sz']}), md0 {ans['q_md0']:.1f} (aqu-sz {md0['aqu-sz']})",
          f"- (b) md0 {ans['md0_MBps']:.1f} MB/s; members sum {members_kBps:.0f} kB/s = md0 rkB/s",
          f"- (c) {OUTSTANDING} outstanding / 0.25 ms x 512 KiB = {ans['allowed_GBps']:.0f} GB/s > drive links {ans['member_links_GBps']:.1f} GB/s",
          f"- (d) b mean {ans['b_mean']} / 224 = {ans['iowait_from_b']:.2f} % vs %iowait {ans['iowait_reported']}",
          f"- (e) {ans['pps_9000_M']:.2f} Mpps at 9000, {ans['pps_1500_M']:.1f} Mpps at 1500, ratio {ans['ratio']:.2f}"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
