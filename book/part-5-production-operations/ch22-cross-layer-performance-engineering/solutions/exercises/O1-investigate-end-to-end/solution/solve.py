#!/usr/bin/env python3
"""O1 — corroboration measurements and the two-interaction refit on the lab bundle.

Usage: python solve.py --out DIR   (writes result.json and result.md; asserts the answer key)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def r(x: float, nd: int = 4) -> float:
    return round(float(x), nd)


def write(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    (out / "result.md").write_text(md.rstrip() + "\n", encoding="utf-8")


# Lab bundle and reference implementation of this package (instructor image only).
PKG = Path(__file__).resolve().parents[4]
DATA = PKG / "lab" / "data"
sys.path.insert(0, str(PKG / "solutions" / "lab"))
import numpy as np  # noqa: E402
import regression_lab as ref  # noqa: E402


def ols(ft, terms):
    """OLS of per-job mean step time on an intercept plus `terms`; returns coef, classical SE, R^2."""
    X = np.column_stack([np.ones(len(ft))] + [ft[t].to_numpy(float) for t in terms])
    y = ft["mean_step_s"].to_numpy(float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    n, p = X.shape
    se = np.sqrt(np.diag(float(res @ res) / (n - p) * np.linalg.inv(X.T @ X)))
    r2 = 1 - float(res @ res) / float(((y - y.mean()) ** 2).sum())
    names = ["intercept"] + list(terms)
    return dict(zip(names, map(float, beta))), dict(zip(names, map(float, se))), r2


KEY_CORR = {"tx_packed": 6.06, "tx_split": 95.93, "sm_packed": 0.57, "sm_split": 0.40, "iowait_hot": 1.52,
            "iowait_cap": 6.03, "bounce_before": 0.4, "bounce_after": 9.5, "sbe_before": 0.7, "sbe_after": 152,
            "temp_before": 67.4, "temp_after": 68.1, "dw_delta": 1.46, "p99_hot": 18.8, "p99_cap": 35.0,
            "p50_hot": 18.17, "p50_cap": 18.24}                 # exercises-key.md O1 (b)
KEY_INT = {"tp_x_storage": (-1.30, 0.15), "tp_x_driver": (0.03, 0.13)}   # exercises-key.md O1 (c)
ALERT_NODE = "orion-n13"


def close(got, want):
    nd = len(str(want).split(".")[1]) if "." in str(want) else 0
    return abs(got - want) <= 0.5 * 10 ** (-nd) + 1e-9


def main(out: Path) -> None:
    b = ref.load_bundle(DATA)
    ft = ref.job_factor_table(b)
    jobs = b["jobs"].set_index("job_id")
    nm = b["node_metrics"].join(ft[["period", "tp_split"]], on="job_id").join(jobs[["dataset_tier"]], on="job_id")
    aft = nm[nm["period"] == "after"]
    new_nodes = set(b["inventory"].loc[b["inventory"]["driver_branch"] == "R570", "node"])
    nm["new_node"] = nm["node"].isin(new_nodes)
    nn = nm[nm["new_node"]].groupby("period")["host_bounce_copy_GBps"].mean()
    n13 = nm[nm["node"] == ALERT_NODE].groupby("period")[["gpu_ecc_sbe_count", "gpu_temp_c_mean"]].mean()
    tx = aft.groupby("tp_split")["backend_tx_GBps_mean"].mean()
    sm = aft.groupby("tp_split")["sm_active_mean"].mean()
    io = aft.groupby("dataset_tier")["cpu_iowait_pct"].mean()
    pk = ft[(ft["period"] == "after") & (ft["tp_split"] == 0)].groupby("storage_new")[["p50_step_s", "p99_step_s"]].mean()
    cross = ref.storage_crosscheck(ft, ref.estimate_effects(ft))
    corr = {"tx_packed": tx[0], "tx_split": tx[1], "sm_packed": sm[0], "sm_split": sm[1],
            "iowait_hot": io["hot"], "iowait_cap": io["capacity"], "bounce_before": nn["before"],
            "bounce_after": nn["after"], "sbe_before": n13.loc["before", "gpu_ecc_sbe_count"],
            "sbe_after": n13.loc["after", "gpu_ecc_sbe_count"], "temp_before": n13.loc["before", "gpu_temp_c_mean"],
            "temp_after": n13.loc["after", "gpu_temp_c_mean"], "dw_delta": cross["data_wait_delta_s"],
            "p99_hot": pk.loc[0, "p99_step_s"], "p99_cap": pk.loc[1, "p99_step_s"],
            "p50_hot": pk.loc[0, "p50_step_s"], "p50_cap": pk.loc[1, "p50_step_s"]}
    corr = {k: float(v) for k, v in corr.items()}
    for k, v in KEY_CORR.items():
        assert close(corr[k], v), (k, corr[k], v)

    ft2 = ft.copy()
    ft2["tp_x_driver"] = ft2["tp_split"] * ft2["driver_new"]
    terms = list(ref.TERMS) + ["tp_x_driver"]
    coef, se, r2 = ols(ft2, terms)
    for k, (c, s) in KEY_INT.items():
        assert abs(coef[k] - c) <= 0.01 and abs(se[k] - s) <= 0.01, (k, coef[k], se[k])
    z = {k: abs(coef[k]) / se[k] for k in KEY_INT}
    assert z["tp_x_storage"] > 3 and z["tp_x_driver"] < 1, z
    result = {"id": "O1", "evidence_label": "SIMULATED", "units": "GB/s; fraction; %; s; count; degC",
              "inputs": {"bundle": "lab/data (seed 2214)", "alert_node": ALERT_NODE,
                         "r570_nodes": sorted(new_nodes)},
              "steps": {"corroboration": {k: r(v, 3) for k, v in corr.items()},
                        "two_interaction_model": {"coef_s": {k: r(v, 3) for k, v in coef.items()},
                                                  "se_s": {k: r(v, 3) for k, v in se.items()}, "r2": r(r2, 4)}},
              "answer": {"tp_x_storage": [r(coef["tp_x_storage"], 2), r(se["tp_x_storage"], 2)],
                         "tp_x_driver": [r(coef["tp_x_driver"], 2), r(se["tp_x_driver"], 2)],
                         "z": {k: r(v, 1) for k, v in z.items()},
                         "judgment": "keep tp_x_storage, drop tp_x_driver"}}
    md = ["# O1 — corroboration and interactions `[SIMULATED]`", "",
          "| Cause | Measurement | Value |", "|---|---|---|",
          f"| TP split | backend tx per node, packed → split (after) | {corr['tx_packed']:.2f} → {corr['tx_split']:.2f} GB/s |",
          f"| TP split | SM active, packed → split (after) | {corr['sm_packed']:.2f} → {corr['sm_split']:.2f} |",
          f"| Capacity tier | data-wait delta, TP-packed (after) | {corr['dw_delta']:+.2f} s |",
          f"| Capacity tier | CPU iowait hot → capacity (after) | {corr['iowait_hot']:.2f} → {corr['iowait_cap']:.2f} % |",
          f"| Capacity tier | per-job p99 (p50) hot → capacity | {corr['p99_hot']:.1f} → {corr['p99_cap']:.1f} s "
          f"({corr['p50_hot']:.2f} → {corr['p50_cap']:.2f} s) |",
          f"| R570 / GDR | host bounce copy on R570 nodes, before → after | {corr['bounce_before']:.2f} → {corr['bounce_after']:.2f} GB/s |",
          f"| ECC alert | orion-n13 SBE; temperature | {corr['sbe_before']:.1f} → {corr['sbe_after']:.0f}; "
          f"{corr['temp_before']:.1f} → {corr['temp_after']:.1f} °C |", "",
          f"tp_x_storage {coef['tp_x_storage']:+.2f} ± {se['tp_x_storage']:.2f} s ({z['tp_x_storage']:.1f} SE): keep.",
          f"tp_x_driver {coef['tp_x_driver']:+.2f} ± {se['tp_x_driver']:.2f} s ({z['tp_x_driver']:.1f} SE): drop."]
    write(out, result, "\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
