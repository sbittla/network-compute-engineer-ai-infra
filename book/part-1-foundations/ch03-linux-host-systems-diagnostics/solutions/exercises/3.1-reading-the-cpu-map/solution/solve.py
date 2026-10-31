#!/usr/bin/env python3
"""3.1: SMT siblings on socket 1 and the NUMA node of GPU 2, from the reference snapshot.

Usage: python solve.py --out DIR
Reads lab/data/snapshots/orion-n01.json [SIMULATED] from this package.
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
BAD_BINDING = "56-63"          # from the prompt
KEY = {"socket1_first": (56, 111), "socket1_siblings": (168, 223), "gpu2_bdf": "3a:00.0", "gpu2_node": 0}


def cpu_list(text: str) -> list[int]:
    cpus: list[int] = []
    for part in text.split(","):
        a, _, b = part.strip().partition("-")
        cpus += list(range(int(a), int(b or a) + 1))
    return cpus


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    sec = json.loads(SNAP.read_text(encoding="utf-8"))["sections"]
    lscpu = {k.strip(): v.strip() for k, _, v in (l.partition(":") for l in sec["lscpu"]["stdout"].splitlines())}
    sockets, cores, tpc = int(lscpu["Socket(s)"]), int(lscpu["Core(s) per socket"]), int(lscpu["Thread(s) per core"])
    physical = sockets * cores
    node1 = cpu_list(lscpu["NUMA node1 CPU(s)"])
    first = [c for c in node1 if c < physical]
    siblings = [c for c in node1 if c >= physical]
    assert siblings == [c + physical for c in first]           # sibling of k is k + 112
    gpu_line = next(l for l in sec["nvidia_smi"]["stdout"].splitlines() if l.startswith("2,"))
    bdf = gpu_line.split(",")[1].strip().lower()[-7:]
    m = re.search(rf"0000:{re.escape(bdf)};[^\n]*?numa_node=(\d+)", sec["pcie_sysfs"]["stdout"])
    gpu_node = int(m.group(1))
    node_of = {n: set(cpu_list(lscpu[f"NUMA node{n} CPU(s)"])) for n in range(int(lscpu["NUMA node(s)"]))}
    binding = set(cpu_list(BAD_BINDING))
    binding_node = next(n for n, s in node_of.items() if binding <= s)
    assert (first[0], first[-1]) == KEY["socket1_first"] and (siblings[0], siblings[-1]) == KEY["socket1_siblings"]
    assert bdf == KEY["gpu2_bdf"] and gpu_node == KEY["gpu2_node"] and binding_node != gpu_node and tpc == 2
    ans = {"socket1_first_threads": f"{first[0]}-{first[-1]}", "socket1_smt_siblings": f"{siblings[0]}-{siblings[-1]}",
           "gpu2_bdf": bdf, "gpu2_numa_node": gpu_node, "binding_numa_node": binding_node,
           "verdict": "wrong socket: bind rank 2 to socket-0 cores (0-55, siblings 112-167)"}
    result = {"evidence": "[SIMULATED] snapshot orion-n01", "answer": ans, "units": "logical CPU ids"}
    md = ["# 3.1", "", f"- socket 1: first threads {ans['socket1_first_threads']}, SMT siblings {ans['socket1_smt_siblings']}",
          f"- GPU 2 = {bdf}, NUMA node {gpu_node}; taskset {BAD_BINDING} is on node {binding_node}: {ans['verdict']}"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
