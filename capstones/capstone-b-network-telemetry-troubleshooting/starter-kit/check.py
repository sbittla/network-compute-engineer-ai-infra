#!/usr/bin/env python3
"""Capstone B starter-kit checker — ORION backend telemetry and troubleshooting pipeline.

Usage:
    python check.py                    # check your starter/telemetry.py (default)
    python check.py --impl solution    # check the instructor reference (instructor edition only)

Prints one line per check (PASS / FAIL / TODO). Exits 0 only when every check passes.
Detection is scored against data/ground_truth.sha256 (hashed fault keys), so the checker can report
precision and recall without printing the answers.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MODULE = "telemetry"

LEAF_SAMPLE = """orion-be-leaf-r9# show interfaces counters
Timestamp: 2026-10-12T09:00:00Z
Port                    InOctets         OutOctets        InDiscards       OutDiscards         FCSErrors      FECCorrected         FECUncorr          RxPause3          TxPause3        EcnMarked3
Ethernet1/1                 1000              2000                 0                 1                 0               500                 0        4294967000                10               100
Ethernet1/33                3000              4000                 0                 0                 2               600                 0                 5                 6               700

orion-be-leaf-r9# show interfaces counters
Timestamp: 2026-10-12T09:01:00Z
Port                    InOctets         OutOctets        InDiscards       OutDiscards         FCSErrors      FECCorrected         FECUncorr          RxPause3          TxPause3        EcnMarked3
Ethernet1/1              6001000           8002000                 0                 1                 0               800                 0               200                70               400
Ethernet1/33             3003000           4004000                 0                 0                 2               900                 0                 5                 6               760
"""
SPINE_SAMPLE = (
    '{"timestamp_ns":1791795600500000000,"device":"orion-be-spine-9","updates":['
    '{"path":"/interfaces/interface[name=Ethernet1/7]/state/counters","values":{"in-octets":11,"out-octets":22,'
    '"in-discards":0,"out-discards":3,"in-fcs-errors":0}},'
    '{"path":"/qos/interfaces/interface[name=Ethernet1/7]/ext/pfc-ecn","values":{"rx-pause-3":4,"tx-pause-3":5,'
    '"ecn-marked-3":6}}]}\n'
)
NIC_SAMPLE = """### collected_at=1791795600 host=orion-n99 dev=mlx5_3 netdev=ens3np0 rail=3
NIC statistics:
     rx_vport_rdma_unicast_bytes: 1000
     tx_vport_rdma_unicast_bytes: 2000
     rx_prio3_pause: 3
     tx_prio3_pause: 4
     rx_discards_phy: 0
     rx_crc_errors_phy: 1
     rx_unrelated_counter_we_ignore: 77
RDMA hw_counters (/sys/class/infiniband/mlx5_3/ports/1/hw_counters):
     np_cnp_sent: 5
     rp_cnp_handled: 6
     np_ecn_marked_roce_packets: 7
     out_of_sequence: 8
     local_ack_timeout_err: 9
"""


def load(impl: str) -> ModuleType | None:
    if impl == "solution":
        path = HERE.parent / "instructor" / "reference" / f"{MODULE}.py"
    else:
        path = HERE / "starter" / f"{MODULE}.py"
    if not path.exists():
        print(f"Implementation not found: {path}")
        if impl == "solution":
            print("The instructor reference is not shipped in the student edition.")
        return None
    spec = importlib.util.spec_from_file_location(f"{MODULE}_{impl}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CHECKS: list[tuple[str, Callable[[ModuleType], str]]] = []
_C: dict[str, object] = {}


def check(name: str):
    def deco(fn: Callable[[ModuleType], str]):
        CHECKS.append((name, fn))
        return fn
    return deco


def truth() -> list[tuple[str, "pd.Timestamp", float]]:
    import pandas as pd
    out = []
    for ln in (DATA / "ground_truth.sha256").read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#"):
            h, onset, tol = ln.split()
            out.append((h, pd.Timestamp(onset), float(tol)))
    return out


def key(device: str, interface: str, cls: str) -> str:
    return hashlib.sha256(f"{device}:{interface}|{cls}".encode()).hexdigest()


def indep_score(alerts) -> dict[str, object]:
    """Time-aware scoring (docs/VERIFIED_FACTS.md): a root page matches a fault only if it FIRES within
    [onset, onset + tolerance]; earlier or non-matching pages are FPs; re-pages of a matched fault are
    duplicates."""
    import pandas as pd
    assert "fired_ts" in alerts.columns, "detect() must report fired_ts (when persistence is satisfied)"
    t = {h: (o, tol) for h, o, tol in truth()}
    matched: dict[str, float] = {}
    fp = 0
    for r in alerts[alerts["role"] == "root"].sort_values("fired_ts").itertuples(index=False):
        h = key(r.device, r.interface, r.fault_class)
        f = pd.Timestamp(r.fired_ts)
        if h in t and h not in matched and t[h][0] <= f <= t[h][0] + pd.Timedelta(seconds=t[h][1]):
            matched[h] = (f - t[h][0]).total_seconds()
        elif h in matched and f > t[h][0]:
            continue
        else:
            fp += 1
    tp = len(matched)
    return {"tp": tp, "fp": fp, "fn": len(t) - tp, "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / len(t), "latency": matched}


def frame(m):
    if "df" not in _C:
        _C["df"] = m.load_all(DATA)
    return _C["df"]


def ctx(m):
    if "ctx" not in _C:
        _C["ctx"] = m.load_context(DATA)
    return _C["ctx"]


def rates(m):
    if "rates" not in _C:
        _C["rates"] = m.compute_rates(frame(m), ctx(m)["profiles"])
    return _C["rates"]


def alerts(m, persistence=None):
    k = f"alerts_{persistence}"
    if k not in _C:
        c = ctx(m)
        _C[k] = m.detect(rates(m), c["topology"], c["maintenance"], persistence=persistence)
    return _C[k]


def cols_ok(df, need: list[str]) -> None:
    missing = [c for c in need if c not in df.columns]
    assert not missing, f"missing columns {missing}"


SCHEMA = ["ts", "device", "interface", "counter", "native", "value", "source"]


# ---- checks ---------------------------------------------------------------------------------------

@check("01 parse leaf CLI text")
def _c01(m):
    df = m.parse_leaf_cli(LEAF_SAMPLE)
    cols_ok(df, SCHEMA)
    assert len(df) == 40, f"{len(df)} rows; expected 2 snapshots x 2 ports x 10 counters = 40"
    assert str(df["ts"].dt.tz) == "UTC", "ts must be tz-aware UTC"
    row = df[(df["interface"] == "Ethernet1/1") & (df["counter"] == "pfc_rx_pause_p3")].sort_values("ts")
    assert list(row["value"]) == [4294967000, 200], f"RxPause3 -> pfc_rx_pause_p3 values {list(row['value'])}"
    assert set(df["counter"]) <= set(m.CANONICAL_COUNTERS), f"non-canonical names {set(df['counter']) - set(m.CANONICAL_COUNTERS)}"
    assert (df["device"] == "orion-be-leaf-r9").all() and (df["source"] == "leaf_cli").all()
    return "40 rows, canonical names, UTC timestamps"


@check("02 parse spine JSON lines")
def _c02(m):
    df = m.parse_spine_jsonl(SPINE_SAMPLE)
    cols_ok(df, SCHEMA)
    assert len(df) == 8, f"{len(df)} rows; expected 8 counters for one interface"
    ts = df["ts"].iloc[0]
    assert str(ts) == "2026-10-12 09:00:00.500000+00:00", f"timestamp_ns decoded as {ts} (nanoseconds since epoch, UTC)"
    got = dict(zip(df["counter"], df["value"]))
    assert got.get("rx_bytes") == 11 and got.get("tx_bytes") == 22 and got.get("ecn_marked_p3") == 6, f"{got}"
    assert set(df["interface"]) == {"Ethernet1/7"}, f"interface from path: {set(df['interface'])}"
    return "OpenConfig-style paths and ns timestamps normalized"


@check("03 parse NIC ethtool + hw_counters")
def _c03(m):
    df = m.parse_nic_ethtool(NIC_SAMPLE)
    cols_ok(df, SCHEMA)
    assert len(df) == 11, f"{len(df)} rows; expected 11 known counters (unknown ones ignored)"
    assert set(df["device"]) == {"orion-n99"} and set(df["interface"]) == {"mlx5_3"}, "device=host, interface=RDMA dev"
    got = dict(zip(df["counter"], df["value"]))
    assert got.get("fcs_errors") == 1 and got.get("cnp_sent") == 5 and got.get("pfc_tx_pause_p3") == 4, f"{got}"
    assert str(df["ts"].iloc[0]) == "2026-10-12 09:00:00+00:00", f"collected_at decoded as {df['ts'].iloc[0]}"
    return "mlx5 counter names mapped to canonical schema"


@check("04 load full bundle")
def _c04(m):
    df = frame(m)
    cols_ok(df, SCHEMA)
    counts = df["source"].value_counts().to_dict()
    exp = {"leaf_cli": 158720, "spine_stream": 63488, "nic_ethtool": 45056}
    assert counts == exp, f"rows per source {counts}, expected {exp}"
    assert df["device"].nunique() == 44, f"{df['device'].nunique()} devices, expected 8 leaves + 4 spines + 32 hosts"
    assert str(df["ts"].dt.tz) == "UTC", "all timestamps must be UTC"
    return "267,264 samples from 3 formats and 44 devices"


@check("05 counter_delta: wrap vs reset")
def _c05(m):
    cases = [((100, 250, 64), 150), ((4294967000, 200, 32), 496), ((5_000_000_000, 10, 64), None),
             ((1000, 10, 32), None), ((7, 7, 64), 0)]
    for (p, c, w), exp in cases:
        got = m.counter_delta(p, c, w)
        assert got == exp, f"counter_delta({p}, {c}, {w}) = {got}, expected {exp}"
    got = m.counter_delta(3_000_000_000, 5, 32, max_delta=120_000_000)
    assert got is None, (f"counter_delta(3e9, 5, 32, max_delta=1.2e8) = {got}: a 'wrap' of ~1.3e9 exceeds the "
                         "plausibility bound, so it is a clear, not a wrap")
    return "32-bit wrap recovered; 64-bit decrease and implausible 'wrap' treated as reset (None)"


@check("06 rates: resets and wraps in the bundle")
def _c06(m):
    r = rates(m)
    cols_ok(r, ["ts", "device", "interface", "counter", "rate", "valid"])
    bad = set(r.loc[~r["valid"].astype(bool), "device"])
    assert bad == {"orion-n30", "orion-be-leaf-r7", "orion-be-spine-2"}, (
        f"devices with invalid (reset) intervals {sorted(bad)}; three counter resets are in the capture")
    assert (r.loc[r["valid"].astype(bool), "rate"] >= 0).all(), "negative rates on valid intervals"
    w = r[(r["device"] == "orion-be-leaf-r4") & (r["interface"] == "Ethernet1/7") & (r["counter"] == "pfc_tx_pause_p3")]
    assert w["valid"].astype(bool).all(), "the 32-bit pause counter on orion-be-leaf-r4 Ethernet1/7 wraps; that is not a reset"
    assert w["rate"].max() < 3000, f"wrap handled wrongly: max pause rate {w['rate'].max():.3g}/s"
    assert r["rate"].max() < 1e11, f"implausible max rate {r['rate'].max():.3g}/s (unhandled reset?)"
    return "3 resets marked invalid; 32-bit wrap recovered; no negative or absurd rates"


@check("07 in_maintenance")
def _c07(m):
    import pandas as pd
    w = [{"device": "x", "start": "2026-10-12T10:00:00Z", "end": "2026-10-12T10:05:00Z"}]
    t = lambda s: pd.Timestamp(s)  # noqa: E731
    assert m.in_maintenance("x", t("2026-10-12T10:00:00Z"), w) is True, "start is inclusive"
    assert m.in_maintenance("x", t("2026-10-12T10:05:00Z"), w) is False, "end is exclusive"
    assert m.in_maintenance("y", t("2026-10-12T10:02:00Z"), w) is False, "other device"
    return "start-inclusive, end-exclusive, per device"


@check("08 detection recall")
def _c08(m):
    s = indep_score(alerts(m))
    assert s["recall"] == 1.0, f"recall {s['recall']:.2f}: {s['fn']} injected fault(s) not paged within their window"
    worst = max(s["latency"].values())
    return f"all {s['tp']} faults paged in-window at root-cause granularity; worst latency {worst:.0f} s from onset"


@check("09 detection precision")
def _c09(m):
    s = indep_score(alerts(m))
    assert s["precision"] >= 0.9, (f"precision {s['precision']:.2f} ({s['fp']} false-positive pages); with 5 "
                                   "positives, >= 0.9 means zero FPs")
    return f"precision {s['precision']:.2f} ({s['fp']} FP)"


@check("10 persistence reduces false positives")
def _c10(m):
    base, naive = indep_score(alerts(m)), indep_score(alerts(m, persistence=1))
    a1 = alerts(m, persistence=1)
    early = a1[(a1["role"] == "root") & (a1["device"] == "orion-n17") & (a1["interface"] == "mlx5_5")]
    assert (early["fired_ts"] < "2026-10-12T10:15:00Z").any(), "persistence=1 should page n17 mlx5_5 during the 10:12 burst"
    assert naive["fp"] >= 50 and naive["fp"] > base["fp"], (
        f"with persistence=1 expected many FPs (benign burst, glitches); got {naive['fp']} vs {base['fp']}")
    return f"persistence=1 -> {naive['fp']} FP; tuned -> {base['fp']} FP"


@check("10b separated glitches do not page")
def _c10b(m):
    import pandas as pd
    T = pd.Timestamp("2026-10-12T11:00:00Z")
    ts = [T + pd.Timedelta(minutes=k) for k in range(1, 11)]
    fcs = [0, 1, 0, 0, 1, 0, 0, 0, 0, 0]            # two isolated FCS increments, 3 intervals apart
    rows = [{"ts": t, "device": "orion-be-leaf-r9", "interface": "Ethernet1/1", "counter": "fcs_errors",
             "source": "leaf_cli", "dt_s": 60.0, "delta": f, "rate": f / 60.0, "valid": True, "reason": ""}
            for t, f in zip(ts, fcs)]
    topo = pd.DataFrame(columns=["a_device", "a_interface", "b_device", "b_interface", "rail", "link_role"])
    a = m.detect(pd.DataFrame(rows), topo, [])
    pages = a[(a["role"] == "root") & (a["device"] == "orion-be-leaf-r9")] if len(a) else a
    assert len(pages) == 0, (f"two separated single-interval glitches paged: {pages[['fault_class', 'fired_ts']].to_dict('records')}; "
                             "open an episode only on `persistence` consecutive true intervals before bridging gaps")
    return "isolated glitches never open an episode (hysteresis applies only after opening)"


@check("11 maintenance suppression (incl. link peers)")
def _c11(m):
    a = alerts(m)
    roots = a[a["role"] == "root"]
    down = roots[roots["fault_class"] == "link_down"]
    assert down.empty, f"link_down alerts that maintenance should suppress: {sorted(set(down['device']))}"
    c = ctx(m)
    raw = m.detect(rates(m), c["topology"], [], persistence=None)
    raw_down = raw[(raw["role"] == "root") & (raw["fault_class"] == "link_down")]
    assert not raw_down.empty, "with an empty change calendar the leaf-r7 optic swap should raise link_down"
    return f"{len(raw_down)} link_down alerts suppressed by the change calendar"


@check("12 score()")
def _c12(m):
    import pandas as pd
    T = pd.Timestamp
    t = [{"hash": key("a", "p1", "pfc_storm"), "onset": T("2026-10-12T10:10:00Z"), "tolerance_s": 300},
         {"hash": key("b", "*", "ecn_misconfig"), "onset": T("2026-10-12T10:00:00Z"), "tolerance_s": 300}]
    al = pd.DataFrame([
        {"device": "a", "interface": "p1", "fault_class": "pfc_storm", "role": "root", "fired_ts": T("2026-10-12T10:08:00Z")},
        {"device": "a", "interface": "p1", "fault_class": "pfc_storm", "role": "root", "fired_ts": T("2026-10-12T10:12:00Z")},
        {"device": "a", "interface": "p1", "fault_class": "pfc_storm", "role": "root", "fired_ts": T("2026-10-12T10:13:00Z")},
        {"device": "c", "interface": "p9", "fault_class": "link_down", "role": "root", "fired_ts": T("2026-10-12T10:12:00Z")},
        {"device": "b", "interface": "*", "fault_class": "ecn_misconfig", "role": "symptom", "fired_ts": T("2026-10-12T10:01:00Z")},
    ])
    s = m.score(al, t)
    got = (s["tp"], s["fp"], s["fn"], s["duplicates"])
    assert got == (1, 2, 1, 1), (f"tp/fp/fn/dup {got}, expected (1, 2, 1, 1): the 10:08 page precedes onset (FP), "
                                 "10:12 matches, 10:13 is a duplicate, c:p9 is a FP, symptoms are not scored")
    assert math.isclose(s["latency_s"][key("a", "p1", "pfc_storm")], 120.0), f"latency {s['latency_s']}"
    return "time-aware matching: pre-onset FP, in-window TP, duplicates, latency from onset"


@check("13 leaf health table (report)")
def _c13(m):
    h = m.leaf_health_table(rates(m), ctx(m)["topology"]).set_index("device")
    assert len(h) == 8, f"{len(h)} leaves"
    assert h.loc["orion-be-leaf-r6", "ecn_per_s"] < 1, "a leaf with ECN marking disabled should stand out"
    assert h.loc["orion-be-leaf-r1", "uplink_cv"] > 0.5 and h.drop("orion-be-leaf-r1")["uplink_cv"].max() < 0.2, \
        f"uplink CV: {h['uplink_cv'].round(2).to_dict()}"
    gbps = h.drop("orion-be-leaf-r5")["host_rx_gbps"]
    assert ((gbps > 170) & (gbps < 200)).all(), (
        f"host_rx_gbps (Gb/s, mean over all 32 host ports: 24 training ~240 + 8 inference ~16) ~184: {gbps.round(1).to_dict()}")
    return "per-leaf summary separates r1, r2, r5, r6 from the healthy rails"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    try:
        mod = load(args.impl)
    except Exception as e:  # syntax error etc. in learner code
        print(f"FAIL import  {type(e).__name__}: {e}")
        return 1
    if mod is None:
        return 2
    counts = {"PASS": 0, "FAIL": 0, "TODO": 0}
    for name, fn in CHECKS:
        try:
            msg = fn(mod)
            status = "PASS"
        except NotImplementedError as e:
            status, msg = "TODO", str(e) or "not implemented yet"
        except AssertionError as e:
            status, msg = "FAIL", str(e) or "assertion failed"
        except Exception as e:  # noqa: BLE001 - report, never crash
            status, msg = "FAIL", f"{type(e).__name__}: {e}"
        counts[status] += 1
        print(f"{status:4} {name:<46} {msg}")
    total = len(CHECKS)
    print(f"\n{counts['PASS']}/{total} checks pass ({counts['TODO']} TODO, {counts['FAIL']} FAIL) [impl={args.impl}]")
    return 0 if counts["PASS"] == total else 1


if __name__ == "__main__":
    sys.exit(main())
