"""14.7 -- Tail at scale: P(at least one read beyond a per-read percentile) = 1 - q^N. [MODELED]

Usage: python solve.py --out DIR
Inputs (prompt): N = 256 and 4,096 ranks; per-read p99 and p99.9 (q = 0.99, 0.999); independence.
"""
import argparse
import json
from pathlib import Path

RANKS = (256, 4096)
QS = {"p99": 0.99, "p99.9": 0.999}
KEY = {(256, "p99"): 0.92, (256, "p99.9"): 0.23, (4096, "p99"): 1.0, (4096, "p99.9"): 0.98}


def sig2(x: float) -> float:
    return float(f"{x:.2g}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    table = {}
    for n in RANKS:
        for name, q in QS.items():
            p = 1 - q ** n
            table[f"N={n},{name}"] = round(p, 4)
            # Key 14.7 values to two significant figures (tolerance: exact match at 2 s.f.).
            assert sig2(p) == KEY[(n, name)], (n, name, p)

    result = {
        "inputs": {"ranks": list(RANKS), "q": QS},
        "steps": {"formula": "1 - q^N", "q^N": {f"N={n},{k}": round(q ** n, 4) for n in RANKS for k, q in QS.items()}},
        "answer": table,
        "units": {"probability": "fraction of steps"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# 14.7 result `[MODELED]`", "", "| N | beyond p99 | beyond p99.9 |", "|---|---|---|"]
    for n in RANKS:
        lines.append(f"| {n:,} | {sig2(1 - 0.99 ** n)} | {sig2(1 - 0.999 ** n)} |")
    lines += ["", "At scale the per-read p99.9 is the typical step's experience.", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
