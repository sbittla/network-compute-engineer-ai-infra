"""O1 — Label each congestion episode in the lab's synthetic time series and quote discriminating rates.

Usage: python solve.py --out DIR

Independent of the lab code: converts cumulative counters to per-second rates (dividing by the true
elapsed time, NaN on the first sample and on negative deltas, i.e. the counter reset on
orion-be-leaf-r4:eth1/2 and the spine-2 telemetry gap), finds hot windows with the lab README Task 2
rule (TC3 watermark >= 1,000 KB or pause tx/rx >= 100 frames/s, merged across <= 6 s gaps), and
reports per-episode medians on the ports that discriminate. Data: lab/data/ (seed-generated,
[SIMULATED / SYNTHETIC]).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
SW_CTRS = ["ecn_marked_tc3", "pfc_tx_p3", "pfc_rx_p3", "discards_tc3"]
NIC_CTRS = ["cnp_sent", "pfc_tx_p3", "pfc_rx_p3"]


def rates(df: pd.DataFrame, keys: list[str], ctrs: list[str]) -> pd.DataFrame:
    df = df.sort_values(keys + ["ts_s"]).reset_index(drop=True).copy()
    g = df.groupby(keys, sort=False)
    dt = g["ts_s"].diff()
    for c in ctrs:
        d = g[c].diff()
        r = d / dt
        r[d < 0] = np.nan
        df[c + "_rate"] = r
    return df


def episodes(sw: pd.DataFrame, gap: int = 6) -> list[tuple[int, int]]:
    hot = (sw["q_tc3_max_kb"] >= 1000) | (sw["pfc_tx_p3_rate"] >= 100) | (sw["pfc_rx_p3_rate"] >= 100)
    eps: list[list[int]] = []
    for t in sorted(sw.loc[hot.fillna(False), "ts_s"].unique()):
        if eps and t - eps[-1][1] <= gap:
            eps[-1][1] = int(t)
        else:
            eps.append([int(t), int(t)])
    return [tuple(e) for e in eps]


def med(df: pd.DataFrame, win: tuple[int, int], **sel) -> dict:
    w = df[(df.ts_s >= win[0]) & (df.ts_s <= win[1])]
    for k, v in sel.items():
        w = w[w[k] == v]
    cols = [c for c in ("tx_gbps", "rx_gbps", "q_tc3_max_kb", "ecn_marked_tc3_rate", "pfc_tx_p3_rate",
                        "pfc_rx_p3_rate", "cnp_sent_rate") if c in w]
    return {c: round(float(w[c].median()), 2) for c in cols}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    sw = rates(pd.read_csv(DATA / "switch_ports.csv"), ["switch", "port"], SW_CTRS)
    nic = rates(pd.read_csv(DATA / "nic_counters.csv"), ["node", "nic"], NIC_CTRS)
    eps = episodes(sw)
    assert eps == [(100, 158), (250, 318), (400, 468)], eps        # 520-558 is busy but NOT an episode
    inc, prop, storm = eps
    L3, L4, S1, S2 = "orion-be-leaf-r3", "orion-be-leaf-r4", "orion-be-spine-1", "orion-be-spine-2"

    v = {
        "incast": {
            "root leaf-r3 eth1/5": med(sw, inc, switch=L3, port="eth1/5"),
            "sender port leaf-r3 eth1/1": med(sw, inc, switch=L3, port="eth1/1"),
            "leaf-r3 uplink eth1/33": med(sw, inc, switch=L3, port="eth1/33"),
            "orion-n05 mlx5_3 (NP)": med(nic, inc, node="orion-n05", nic="mlx5_3"),
        },
        "pause_propagation": {
            "root leaf-r3 eth1/10": med(sw, prop, switch=L3, port="eth1/10"),
            "leaf-r3 uplink eth1/33 (to spine-1)": med(sw, prop, switch=L3, port="eth1/33"),
            "spine-1 eth1/25 (to leaf-r3)": med(sw, prop, switch=S1, port="eth1/25"),
            "spine-2 eth1/25 (to leaf-r3)": med(sw, prop, switch=S2, port="eth1/25"),
            "leaf-r4 uplink eth1/33 (to spine-1)": med(sw, prop, switch=L4, port="eth1/33"),
            "leaf-r4 eth1/1 (to orion-n01)": med(sw, prop, switch=L4, port="eth1/1"),
        },
        "pfc_storm": {
            "leaf-r3 eth1/12 (to orion-n12)": med(sw, storm, switch=L3, port="eth1/12"),
            "orion-n12 mlx5_3 (storm source)": med(nic, storm, node="orion-n12", nic="mlx5_3"),
            "leaf-r3 eth1/3 (to orion-n03)": med(sw, storm, switch=L3, port="eth1/3"),
        },
        "not_an_episode_520_558": {
            "leaf-r4 eth1/7 (to orion-n07)": med(sw, (520, 558), switch=L4, port="eth1/7"),
        },
    }

    # Key (solutions/exercises-key.md, H1/O1 table), tolerances stated per value.
    r = v["incast"]["root leaf-r3 eth1/5"]
    # As-found leaf-r3: PFC holds the queue near the 1,000 KB Xoff-equivalent; marks only on peaks.
    assert r["tx_gbps"] > 390 and 1300 <= r["q_tc3_max_kb"] <= 1550 and r["pfc_rx_p3_rate"] == 0
    assert r["ecn_marked_tc3_rate"] < 50e3                        # median 0: sporadic marking
    assert 14000 <= v["incast"]["sender port leaf-r3 eth1/1"]["pfc_tx_p3_rate"] <= 21000
    assert v["incast"]["leaf-r3 uplink eth1/33"]["pfc_tx_p3_rate"] < 100   # no fabric-port pause
    assert v["incast"]["orion-n05 mlx5_3 (NP)"]["cnp_sent_rate"] < 5e3          # little DCQCN feedback
    p = v["pause_propagation"]
    assert p["root leaf-r3 eth1/10"]["tx_gbps"] > 390 and p["root leaf-r3 eth1/10"]["pfc_rx_p3_rate"] == 0
    assert 1050 <= p["root leaf-r3 eth1/10"]["q_tc3_max_kb"] <= 1700
    assert 6000 <= p["leaf-r3 uplink eth1/33 (to spine-1)"]["pfc_tx_p3_rate"] <= 10000
    sp = p["spine-1 eth1/25 (to leaf-r3)"]
    assert sp["pfc_rx_p3_rate"] > 1000 and sp["ecn_marked_tc3_rate"] > 5e6 and sp["q_tc3_max_kb"] > 1500
    assert p["leaf-r4 eth1/1 (to orion-n01)"]["pfc_tx_p3_rate"] > 1000
    s = v["pfc_storm"]
    st = s["leaf-r3 eth1/12 (to orion-n12)"]
    assert abs(st["pfc_rx_p3_rate"] - 23750) < 250 and st["tx_gbps"] < 1 and st["q_tc3_max_kb"] > 3900
    assert st["ecn_marked_tc3_rate"] == 0
    assert abs(s["orion-n12 mlx5_3 (storm source)"]["pfc_tx_p3_rate"] - 23750) < 250
    b = v["not_an_episode_520_558"]["leaf-r4 eth1/7 (to orion-n07)"]
    assert 375 <= b["tx_gbps"] <= 392 and 150 <= b["q_tc3_max_kb"] <= 250 and b["pfc_rx_p3_rate"] == 0
    assert 40e3 <= b["ecn_marked_tc3_rate"] <= 60e3

    labels = {"incast": {"window_s": list(inc), "root": f"{L3}:eth1/5"},
              "pause_propagation": {"window_s": list(prop), "root": f"{L3}:eth1/10"},
              "pfc_storm": {"window_s": list(storm), "source": "orion-n12:mlx5_3"}}
    result = {"exercise": "O1", "evidence_label": "[SIMULATED]", "inputs": {"data": "lab/data/switch_ports.csv, nic_counters.csv"},
              "answer": {"episodes": labels, "median_rates": v},
              "units": "Gb/s, KB, marks/s, pause frames/s, CNPs/s (medians over the episode)",
              "tolerance": "ranges stated in the assertions (key values are approximate)"}
    rows = ["episode,port,metric,median"]
    for ep, ports in v.items():
        for port, ms in ports.items():
            for m, x in ms.items():
                rows.append(f"{ep},{port},{m},{x}")
    md = ["# O1 — result `[SIMULATED]`", "", "Episodes found: " + ", ".join(f"{a}–{z} s" for a, z in eps) +
          " (520–558 s is busy but not an episode).", ""]
    for ep, ports in v.items():
        md.append(f"## {ep}")
        md.append("")
        for port, ms in ports.items():
            md.append(f"- {port}: " + ", ".join(f"{k} {x:,.2f}" for k, x in ms.items()))
        md.append("")
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    (out / "episode_values.csv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print("O1 ok")


if __name__ == "__main__":
    main()
