"""Exercise 5.11: shortest GPU-NIC pairing per GPU on orion-n01, from the nvidia-smi topo -m capture.

Usage: python solve.py --out DIR
Reads lab/data/hosts/orion-n01/nvidia-smi_topo_m.txt (a [SIMULATED] capture) of this package.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TOPO = Path(__file__).resolve().parents[4] / "lab" / "data" / "hosts" / "orion-n01" / "nvidia-smi_topo_m.txt"
RANK = {"PIX": 0, "PXB": 1, "PHB": 2, "NODE": 3, "SYS": 4}
# exercises-key.md 5.11: GPUi -> mlx5_i PIX; examples PXB GPU0-NIC2, PHB GPU0-NIC0, NODE GPU0-NIC3, SYS GPU0-NIC6
KEY_EXAMPLES = {"PXB": ("GPU0", "NIC2"), "PHB": ("GPU0", "NIC0"), "NODE": ("GPU0", "NIC3"), "SYS": ("GPU0", "NIC6")}


def parse(text: str) -> tuple[dict, dict]:
    lines = text.splitlines()
    header = lines[0].split("\t")[1:]
    cells: dict[tuple[str, str], str] = {}
    for line in lines[1:]:
        if not line.startswith("GPU"):
            continue
        parts = line.split("\t")
        for col, val in zip(header, parts[1:]):
            if col.startswith("NIC"):
                cells[(parts[0].strip(), col)] = val.strip()
    legend = dict(re.findall(r"^\s*(NIC\d+):\s*(\S+)", text, re.M))
    return cells, legend


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    cells, legend = parse(TOPO.read_text(encoding="utf-8"))
    gpus = sorted({g for g, _ in cells}, key=lambda g: int(g[3:]))
    rows = []
    for g in gpus:
        best = min((n for gg, n in cells if gg == g), key=lambda n: (RANK[cells[(g, n)]], int(n[3:])))
        rows.append({"gpu": g, "nic_column": best, "hca": legend[best], "relation": cells[(g, best)]})
    for r in rows:
        assert r["relation"] == "PIX" and r["hca"] == f"mlx5_{r['gpu'][3:]}", r
    examples = {}
    for cls, (g, n) in KEY_EXAMPLES.items():
        assert cells[(g, n)] == cls, (cls, cells[(g, n)])
        examples[cls] = {"gpu": g, "nic_column": n, "hca": legend[n], "relation": cells[(g, n)]}
    res = {"exercise": "5.11", "evidence_label": "SIMULATED capture; relations read from it",
           "inputs": {"capture": "lab/data/hosts/orion-n01/nvidia-smi_topo_m.txt", "nic_legend": legend},
           "answer": {"shortest": rows, "examples": examples}, "units": {}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 5.11 — shortest GPU–NIC pairings on `orion-n01`", "",
          "| GPU | topo -m column | HCA | Relation |", "|---|---|---|---|"]
    md += [f"| {r['gpu']} | {r['nic_column']} | `{r['hca']}` | {r['relation']} |" for r in rows]
    md += ["", "| Class | Example (matrix cell) |", "|---|---|"]
    md += [f"| {c} | {e['gpu']} ↔ {e['nic_column']} (`{e['hca']}`) = {e['relation']} |" for c, e in examples.items()]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
