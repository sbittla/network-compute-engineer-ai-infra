"""17-T1 — Reconcile the inference pool's free-GPU dashboard (Chapter 17).

Usage: python solve.py --out DIR
Writes result.json and result.md; asserts the answer key (solutions/exercises-key.md).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8", newline="\n")


def close(value: float, key: float, tol: float, what: str) -> None:
    assert abs(value - key) <= tol, f"{what}: computed {value} vs key {key} (tol {tol})"


# Evidence from the prompt [ILLUSTRATIVE]
ALLOCATABLE = {"orion-n25": 8, "orion-n26": 8, "orion-n27": 8, "orion-n28": 0, "orion-n29": 8,
               "orion-n30": 0, "orion-n31": 8, "orion-n32": 8}
ALLOCATED = {"orion-n25": 8, "orion-n26": 4, "orion-n27": 3, "orion-n29": 4, "orion-n32": 8}
PHYSICAL_PER_NODE = 8
DEDICATED = {"orion-n31"}
QUOTA_USED, QUOTA_HARD, REQUEST = 27, 48, 8


def main(out: Path) -> None:
    allocated = sum(ALLOCATED.values())
    free = {n: ALLOCATABLE[n] - ALLOCATED.get(n, 0) for n in ALLOCATABLE}
    dashboard = sum(free.values())
    physical_idle = PHYSICAL_PER_NODE * len(ALLOCATABLE) - allocated
    hidden = {n: PHYSICAL_PER_NODE - ALLOCATED.get(n, 0) for n, a in ALLOCATABLE.items() if a == 0}
    usable = {n: f for n, f in free.items() if f > 0 and n not in DEDICATED}
    fits = [n for n, f in usable.items() if f >= REQUEST]
    assert allocated == 27 == QUOTA_USED
    assert dashboard == 21
    assert physical_idle == 37 and sum(hidden.values()) == 16
    assert sorted(usable.values()) == [4, 4, 5] and sum(usable.values()) == 13 and not fits
    assert QUOTA_USED + REQUEST <= QUOTA_HARD          # quota hypothesis rejected
    result = {"exercise": "17-T1", "evidence_label": "[ILLUSTRATIVE]",
              "inputs": {"allocatable": ALLOCATABLE, "allocated": ALLOCATED},
              "answer": {"allocated": allocated, "dashboard_free": dashboard, "free_by_node": free,
                         "physically_idle": physical_idle, "hidden_by_zero_allocatable": hidden,
                         "usable_after_dedication": usable, "nodes_fitting_8": fits,
                         "quota_after_request": QUOTA_USED + REQUEST},
              "units": {"gpus": "GPUs"}}
    md = f"""
# 17-T1 reconciliation `[ILLUSTRATIVE]`

- allocated = {allocated} (= quota used {QUOTA_USED})
- dashboard free = {dashboard} = {', '.join(f'{n} {f}' for n, f in free.items() if f)}
- physically idle = 64 − {allocated} = {physical_idle}; hidden by allocatable 0: {hidden}
- usable for the inference replica (minus dedicated n31): {usable} → no node fits {REQUEST}
- quota after request: {QUOTA_USED + REQUEST} ≤ {QUOTA_HARD} (not the cause)
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
