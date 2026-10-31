"""D1 — Page-load estimate for ORION-XL's single rotation (Chapter 18).

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


JOBS, PAGES_PER_JOB_MONTH = 40, 0.5            # [ILLUSTRATIVE] historical burn-page rate
SERVICES, PAGES_PER_SERVICE_MONTH = 3, 6.0      # [ILLUSTRATIVE]
SHIFT_H, DAYS, BUDGET_PER_SHIFT = 12, 30, 2


def main(out: Path) -> None:
    shifts = DAYS * 24 // SHIFT_H
    training = JOBS * PAGES_PER_JOB_MONTH / shifts
    inference = SERVICES * PAGES_PER_SERVICE_MONTH / shifts
    total = training + inference
    ungrouped_incident = JOBS
    assert shifts == 60
    close(training, 0.33, 0.005, "training pages per shift")
    close(inference, 0.30, 1e-9, "inference pages per shift")
    assert total < BUDGET_PER_SHIFT
    result = {"exercise": "D1", "evidence_label": "[ILLUSTRATIVE]",
              "inputs": {"jobs": JOBS, "pages_per_job_month": PAGES_PER_JOB_MONTH, "services": SERVICES,
                         "pages_per_service_month": PAGES_PER_SERVICE_MONTH, "shift_h": SHIFT_H},
              "answer": {"shifts_per_month": shifts, "training_per_shift": round(training, 3),
                         "inference_per_shift": round(inference, 3), "total_per_shift": round(total, 3),
                         "budget_per_shift": BUDGET_PER_SHIFT, "pages_one_incident_without_grouping": ungrouped_incident,
                         "pages_one_incident_with_grouping": 1},
              "units": {"pages": "pages per 12 h shift"}}
    md = f"""
# D1 load estimate `[ILLUSTRATIVE]`

- shifts/month = {DAYS} × 24 / {SHIFT_H} = {shifts}
- training = {JOBS} × {PAGES_PER_JOB_MONTH} / {shifts} = {training:.2f}; inference = {SERVICES} × {PAGES_PER_SERVICE_MONTH:g} / {shifts} = {inference:.2f}
- total = {total:.2f} per shift (budget {BUDGET_PER_SHIFT}); one fabric incident: {ungrouped_incident} pages ungrouped vs 1 grouped
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
