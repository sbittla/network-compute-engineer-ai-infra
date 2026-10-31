"""W1 — Error budget, burn rates, and multiwindow alert evaluation for chat-70b (Chapter 18).

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


SLO, WINDOW_MIN, RPM = 0.999, 30 * 24 * 60, 3000
BUDGET = 1 - SLO
POLICY = [("page 1h/5m", 60, 5, 14.4), ("page 6h/30m", 360, 30, 6.0), ("ticket 3d/6h", 4320, 360, 1.0)]
FOR_MIN = 2


def window_burn(err: float, dur_min: float, t_min: float, window_min: float) -> float:
    """Burn rate of a trailing window ending at t for an error ratio err during [0, dur]."""
    bad = max(0.0, min(t_min, dur_min) - max(0.0, t_min - window_min))
    return err * bad / window_min / BUDGET


def evaluate(err: float, dur: float) -> dict:
    out = {}
    for name, long_w, short_w, thr in POLICY:
        first = None
        for tenth in range(0, int(dur * 10) + 1):        # 0.1-minute resolution over the incident
            t = tenth / 10
            if window_burn(err, dur, t, long_w) > thr and window_burn(err, dur, t, short_w) > thr:
                first = t
                break
        out[name] = {"long": round(window_burn(err, dur, dur, long_w), 4),
                     "short": round(window_burn(err, dur, dur, short_w), 4),
                     "first_true_min": first, "fires": first is not None}
    return out


def main(out: Path) -> None:
    requests = RPM * WINDOW_MIN
    budget_req = BUDGET * requests
    budget_min = BUDGET * WINDOW_MIN
    b = evaluate(0.006, 90)
    c = evaluate(0.02, 90)
    burn_b, burn_c = 0.006 / BUDGET, 0.02 / BUDGET
    consumed_b = burn_b * 90 / WINDOW_MIN
    consumed_c = burn_c * 90 / WINDOW_MIN
    exhaust_days = 30 / burn_b
    t_long = BUDGET * 14.4 / 0.02 * 60
    close(budget_req, 129600, 1e-6, "budget requests")
    close(budget_min, 43.2, 1e-9, "budget minutes")
    close(burn_b, 6, 1e-9, "burn (b)")
    close(consumed_b, 0.0125, 1e-9, "consumed (b)")
    assert not any(v["fires"] for v in b.values()), b
    close(b["page 6h/30m"]["long"], 1.5, 1e-6, "6 h burn (b)")
    close(b["ticket 3d/6h"]["long"], 0.125, 1e-6, "3 d burn (b)")
    close(burn_c, 20, 1e-9, "burn (c)")
    close(t_long, 43.2, 1e-9, "1 h window crossing (c)")
    close(c["page 1h/5m"]["first_true_min"], 43.3, 0.11, "condition true (c)")
    assert not c["page 6h/30m"]["fires"] and not c["ticket 3d/6h"]["fires"]
    close(t_long + FOR_MIN, 45.2, 1e-9, "page time with for: 2m")
    close(consumed_c, 0.0417, 0.00005, "consumed (c)")
    close(exhaust_days, 5, 1e-9, "days to exhaustion")
    result = {"exercise": "W1", "evidence_label": "[MODELED]",
              "inputs": {"slo": SLO, "window_min": WINDOW_MIN, "requests_per_min": RPM, "policy": POLICY},
              "answer": {"a_budget_requests": round(budget_req), "a_budget_min": budget_min,
                         "b_burn": burn_b, "b_consumed": consumed_b, "b_windows_at_90min": b,
                         "c_burn": burn_c, "c_long_window_crossing_min": t_long, "c_page_min": t_long + FOR_MIN,
                         "c_consumed": round(consumed_c, 5), "c_windows": c, "d_exhaustion_days": exhaust_days},
              "units": {"time": "min / days", "burn": "x budget rate"}}
    md = f"""
# W1 result `[MODELED]`

- (a) budget {budget_req:,.0f} failed requests = {budget_min:.1f} min of total outage
- (b) burn {burn_b:g}, consumed {consumed_b * 100:.2f} %; windows at 90 min: {b}
- (c) burn {burn_c:g}; 1 h window > 1.44 % after {t_long:.1f} min; page ≈ {t_long + FOR_MIN:.1f} min; consumed {consumed_c * 100:.2f} %
- (d) exhaustion at burn 6: {exhaust_days:g} days
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
