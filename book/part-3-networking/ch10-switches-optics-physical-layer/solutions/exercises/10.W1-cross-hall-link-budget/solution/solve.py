"""10.W1 — Link budget for a cross-hall 400G-DR4 link.

Usage: python solve.py --out DIR      Evidence label: [MODELED] (inputs [ILLUSTRATIVE] / [VENDOR-SPEC, 2026-10])
Inputs are the prompt's stated parameters (exercises.md, 10.W1); method Section 10.6.2.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LENGTH_KM = 0.420          # 420 m SMF
FIBER_DB_PER_KM = 0.4
MPO_PAIRS = 4
MPO_DB = 0.5               # per mated MPO pair
SPLICES = 2
SPLICE_DB = 0.1
TX_MIN_DBM = -2.9          # DR4 worst-case Tx per lane
RX_MIN_DBM = -5.9          # DR4 receiver minimum per lane
MAX_CHANNEL_DB = 3.0       # DR4 maximum channel insertion loss
DIRTY_EXTRA_DB = 1.0       # (b)
MEAS_RX_DBM = -4.1         # (d) all lanes
MEAS_FAR_TX_DBM = 0.6      # (d) far-end Tx all lanes
TYPICAL_TX_DBM = 0.5       # typical module, for the (b) commentary


def r3(x: float) -> float:
    return round(x, 3)


def solve() -> dict:
    fiber = LENGTH_KM * FIBER_DB_PER_KM
    conn = MPO_PAIRS * MPO_DB
    spl = SPLICES * SPLICE_DB
    channel = fiber + conn + spl
    rx = TX_MIN_DBM - channel
    margin = rx - RX_MIN_DBM
    # (b)
    channel_b = channel + DIRTY_EXTRA_DB
    rx_b = TX_MIN_DBM - channel_b
    # (c)
    rx_mw = 10 ** (rx / 10)
    # (d)
    measured = MEAS_FAR_TX_DBM - MEAS_RX_DBM
    excess = measured - channel
    return {
        "inputs": {"length_km": LENGTH_KM, "fiber_db_per_km": FIBER_DB_PER_KM, "mpo_pairs": MPO_PAIRS,
                   "mpo_db": MPO_DB, "splices": SPLICES, "splice_db": SPLICE_DB, "tx_min_dbm": TX_MIN_DBM,
                   "rx_min_dbm": RX_MIN_DBM, "max_channel_db": MAX_CHANNEL_DB},
        "a": {"fiber_db": r3(fiber), "connectors_db": r3(conn), "splices_db": r3(spl),
              "channel_db": r3(channel), "rx_worst_dbm": r3(rx), "margin_db": r3(margin),
              "within_channel_budget": channel <= MAX_CHANNEL_DB},
        "b": {"channel_db": r3(channel_b), "over_budget_db": r3(channel_b - MAX_CHANNEL_DB),
              "rx_worst_dbm": r3(rx_b), "below_rx_min_db": r3(RX_MIN_DBM - rx_b),
              "meets_channel_budget": channel_b <= MAX_CHANNEL_DB, "meets_rx_min": rx_b >= RX_MIN_DBM,
              "rx_typical_tx_dbm": r3(TYPICAL_TX_DBM - channel_b),
              "decision": "Reject: clean or re-terminate and re-measure before acceptance"},
        "c": {"rx_mw": round(rx_mw, 4)},
        "d": {"measured_loss_db": r3(measured), "excess_db": r3(excess),
              "decision": "Equal excess on all lanes -> shared element (MPO end-face at a mated pair, "
                          "splice or trunk bend); drain, inspect jumpers and panel interfaces first"},
        "units": {"loss": "dB", "power": "dBm", "rx_mw": "mW"},
        "evidence_label": "[MODELED]",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    r = solve()
    # Answer key 10.W1: 2.37 dB, -5.27 dBm, 0.63 dB; (b) 3.368 dB / -6.27 dBm fail; (c) 0.297 mW;
    # (d) 4.7 dB measured, 2.33 dB excess. Tolerance 0.01 dB / 0.001 mW (key rounds to 2-3 digits).
    assert abs(r["a"]["channel_db"] - 2.37) < 0.01 and abs(r["a"]["rx_worst_dbm"] + 5.27) < 0.01
    assert abs(r["a"]["margin_db"] - 0.63) < 0.01
    assert abs(r["b"]["channel_db"] - 3.368) < 0.001 and abs(r["b"]["rx_worst_dbm"] + 6.27) < 0.01
    assert not r["b"]["meets_channel_budget"] and not r["b"]["meets_rx_min"]
    assert abs(r["c"]["rx_mw"] - 0.297) < 0.001
    assert abs(r["d"]["measured_loss_db"] - 4.7) < 0.001 and abs(r["d"]["excess_db"] - 2.33) < 0.01
    (out / "result.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    a, b, c, d = r["a"], r["b"], r["c"], r["d"]
    md = f"""# 10.W1 — Cross-hall DR4 link budget `[MODELED]`

## (a)
- fiber = {LENGTH_KM} km x {FIBER_DB_PER_KM} dB/km = {a['fiber_db']} dB
- connectors = {MPO_PAIRS} x {MPO_DB} dB = {a['connectors_db']} dB; splices = {SPLICES} x {SPLICE_DB} dB = {a['splices_db']} dB
- channel = {a['channel_db']} dB (limit {MAX_CHANNEL_DB} dB)
- Rx worst = {TX_MIN_DBM} dBm - {a['channel_db']} dB = {a['rx_worst_dbm']} dBm
- margin = {a['rx_worst_dbm']} - ({RX_MIN_DBM}) = {a['margin_db']} dB

## (b) one dirty MPO pair (+{DIRTY_EXTRA_DB} dB)
- channel = {b['channel_db']} dB, {b['over_budget_db']} dB over budget
- Rx worst = {b['rx_worst_dbm']} dBm, {b['below_rx_min_db']} dB below the receiver minimum
- with typical Tx {TYPICAL_TX_DBM} dBm the link would still show {b['rx_typical_tx_dbm']} dBm
- decision: {b['decision']}

## (c)
- 10^({a['rx_worst_dbm']}/10) = {c['rx_mw']} mW

## (d)
- measured loss = {MEAS_FAR_TX_DBM} - ({MEAS_RX_DBM}) = {d['measured_loss_db']} dB
- excess = {d['measured_loss_db']} - {a['channel_db']} = {d['excess_db']} dB
- decision: {d['decision']}
"""
    (out / "result.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
