#!/usr/bin/env python3
"""Chapter 10 lab checker: link-health analyzer, commissioning report, BOM/spares, cabling.

Usage:
    python check.py                    # check starter/linkhealth.py (your work)
    python check.py --impl solution    # check the reference solution (instructors)

Prints one line per check (PASS / FAIL / TODO). Exit 0 only if every check passes.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
import tempfile
import traceback
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True  # keep lab/ and solutions/ free of __pycache__

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
LEAF = "orion-be-leaf-r3"

# Expected outcome on the supplied dataset. Per-port answers are stored only as a digest so the
# checker does not give the diagnosis away; the counts below are hints you may use.
EXPECTED_LAYER_COUNTS = {"healthy": 55, "physical": 7, "higher_layer": 2}
EXPECTED_PRIMARY_COUNTS = {
    "HEALTHY": 55, "MISCABLED": 2, "OPTIC_MISMATCH": 1, "LINK_FLAP": 1, "CRC_ERRORS": 1,
    "RX_POWER_LOW": 1, "PRE_FEC_BER_HIGH": 1, "CONGESTION": 1, "OVERSIZE_FRAMES": 1,
}
EXPECTED_DIGEST = "e4c73a2d39db8da50081e0b5a1cd49758f67c20eb8a4bb9aa98ef99dc79e1e40"


def load_impl(impl: str):
    path = HERE / "starter" / "linkhealth.py" if impl == "starter" else \
        HERE.parent / "solutions" / "lab" / "linkhealth.py"
    spec = importlib.util.spec_from_file_location(f"linkhealth_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_generator():
    spec = importlib.util.spec_from_file_location("ch10_gen", HERE / "tools" / "generate_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Ctx:
    def __init__(self, m):
        self.m = m
        self._res = None

    def inputs(self):
        m = self.m
        return (m.load_snapshot(DATA / "snapshot_t0.csv"), m.load_snapshot(DATA / "snapshot_t1.csv"),
                m.load_schedule(DATA / "cabling_schedule.csv"), m.load_yaml(DATA / "thresholds.yaml"))

    def results(self):
        if self._res is None:
            self._res = self.m.analyze(*self.inputs())
        return self._res

    def fabrics(self):
        return self.m.load_yaml(DATA / "fabrics.yaml")


# ----------------------------------------------------------------------------------- checks
def c_dataset(ctx):
    if not (HERE / "tools" / "generate_data.py").exists():
        return "SKIP", "generator not shipped in student release"
    gen = load_generator()
    with tempfile.TemporaryDirectory() as td:
        gen.write_all(Path(td))
        for name in ("snapshot_t0.csv", "snapshot_t1.csv", "cabling_schedule.csv",
                     "thresholds.yaml", "fabrics.yaml"):
            if (Path(td) / name).read_bytes() != (DATA / name).read_bytes():
                return False, f"{name} differs from a fresh regeneration (do not edit data/)"
    size = sum(p.stat().st_size for p in DATA.iterdir())
    return size < 2_000_000, f"dataset regenerates byte-identically ({size} bytes)"


def c_counter_delta(ctx):
    f = ctx.m.counter_delta
    cases = [((100, 250), 150), ((0, 0), 0), ((5000, 1200), 1200), ((7, 7), 0)]
    for (a, b), want in cases:
        got = f(a, b)
        if got != want:
            return False, f"counter_delta({a},{b}) = {got}, expected {want}"
    return True, "normal, zero and counter-reset cases"


def c_line_rate(ctx):
    v = ctx.m.pcs_fec_line_rate_gbps(400)
    v2 = ctx.m.pcs_fec_line_rate_gbps(100)
    ok = abs(v - 425.0) < 1e-6 and abs(v2 - 106.25) < 1e-6
    return ok, f"400G -> {v:.4f} Gb/s, 100G -> {v2:.4f} Gb/s (expect 425, 106.25)"


def c_fec_margin(ctx):
    f = ctx.m.fec_margin_decades
    a = f(2.4e-6)
    b = f(2.4e-4)
    c = f(float("nan"))
    d = f(1.6e-4)
    ok = abs(a - 2.0) < 1e-9 and abs(b) < 1e-9 and math.isinf(c) and abs(d - math.log10(1.5)) < 1e-9
    return ok, f"margin(2.4e-6)={a:.3f}, margin(2.4e-4)={b:.3f}, margin(1.6e-4)={d:.3f} decades"


def c_deltas(ctx):
    t0, t1, _, _ = ctx.inputs()
    d = ctx.m.compute_deltas(t0, t1)
    if len(d) != 64:
        return False, f"expected 64 ports, got {len(d)}"
    missing = [c for c in ["dt_s", "pre_fec_ber_t0"] + [f"d_{c}" for c in ctx.m.COUNTERS]
               if c not in d.columns]
    if missing:
        return False, f"missing columns: {missing[:4]}"
    if set(d["dt_s"].round(3)) != {600.0}:
        return False, f"dt_s should be 600 s for every port, got {sorted(set(d['dt_s']))[:3]}"
    neg = int((d[[f"d_{c}" for c in ctx.m.COUNTERS]] < 0).to_numpy().sum())
    if neg:
        return False, f"{neg} negative deltas (counter resets not handled)"
    return True, "64 ports, dt = 600 s, no negative deltas"


def c_layers(ctx):
    r = ctx.results()
    got = dict(Counter(r["layer"]))
    return got == EXPECTED_LAYER_COUNTS, f"layer counts {got} (expect {EXPECTED_LAYER_COUNTS})"


def c_primary(ctx):
    r = ctx.results()
    got = dict(Counter(r["primary"]))
    if got != EXPECTED_PRIMARY_COUNTS:
        diff = {k: (got.get(k, 0), v) for k, v in EXPECTED_PRIMARY_COUNTS.items() if got.get(k, 0) != v}
        extra = {k: v for k, v in got.items() if k not in EXPECTED_PRIMARY_COUNTS}
        return False, f"primary-code counts differ (got, expected): {diff} extra={extra}"
    return True, "primary-code counts match"


def c_digest(ctx):
    r = ctx.results()
    if list(r.columns[:6]) != ["port", "layer", "primary", "severity", "findings", "action"]:
        return False, f"columns should start port,layer,primary,severity,findings,action; got {list(r.columns)}"
    if list(r["port"]) != [f"Ethernet{i}" for i in range(1, 65)]:
        return False, "rows must be sorted by port number"
    dig = ctx.m.classification_digest(r)
    return dig == EXPECTED_DIGEST, "per-port classification matches reference" if dig == EXPECTED_DIGEST \
        else "counts may match but at least one port has the wrong primary/layer"


def c_severity(ctx):
    r = ctx.results()
    bad = r[(r["layer"] == "healthy") & (r["severity"] != "ok")]
    bad2 = r[(r["layer"] == "higher_layer") & (r["severity"] != "refer")]
    crit = int((r["severity"] == "critical").sum())
    ok = bad.empty and bad2.empty and crit == 7
    return ok, f"critical={crit} (expect 7); healthy->ok, higher_layer->refer"


def c_report(ctx):
    r = ctx.results()
    rep = ctx.m.commissioning_report(r, LEAF)
    phys = list(r.loc[r["layer"] == "physical", "port"])
    ok = (rep["overall"] == "FAIL" and rep["ports_total"] == 64 and rep["ports_accepted"] == 57
          and rep["physical_failures"] == phys and len(rep["higher_layer_referrals"]) == 2)
    if ok:
        md = rep["markdown"]
        named = all(p in md for p in phys + rep["higher_layer_referrals"])
        ok = named and LEAF in md
    return ok, f"overall={rep['overall']}, accepted={rep['ports_accepted']}/64, " \
               f"failures={len(rep['physical_failures'])}, referrals={len(rep['higher_layer_referrals'])}"


def c_link_budget(ctx):
    a = ctx.m.link_budget(0.0, -5.9, 0.5, 0.4, 4, 0.5)
    b = ctx.m.link_budget(-2.9, -5.9, 0.05, 0.4, 2, 0.75, 0, 0.0, 1.0)
    ok = a == {"loss_db": 2.2, "rx_dbm": -2.2, "margin_db": 3.7} and \
        b == {"loss_db": 2.52, "rx_dbm": -5.42, "margin_db": 0.48}
    return ok, f"DR4 0.5 km, 4 MPO pairs, Tx 0 dBm: {a}; 50 m, 2 pairs, Tx -2.9 dBm, 1 dB penalty: {b}"


def c_bom(ctx):
    f = ctx.fabrics()
    s = ctx.m.estimate_fabric_bom(f["fabrics"]["small"], f["spares_policy"])
    o = ctx.m.estimate_fabric_bom(f["fabrics"]["orion"], f["spares_policy"])
    want_s = {"leaves": 8, "spines": 2, "total_links": 256, "cables": 256, "spare_cables": 6,
              "uplinks_per_leaf_per_spine": 8}
    want_o = {"leaves": 8, "spines": 4, "total_links": 512, "cables": 512, "spare_cables": 11,
              "uplinks_per_leaf_per_spine": 8}
    for name, got, want, opt, sp in (("small", s, want_s, 512, 16), ("orion", o, want_o, 1024, 31)):
        for k, v in want.items():
            if got.get(k) != v:
                return False, f"{name}: {k}={got.get(k)} expected {v}"
        if got["optics"] != {"400G-DR4": opt} or got["spare_optics"] != {"400G-DR4": sp}:
            return False, f"{name}: optics {got['optics']} spares {got['spare_optics']}"
    return True, "small: 8 leaves/2 spines/256 links/512 optics; ORION: 8/4/512/1024 (matches the ORION reference)"


def c_cabling(ctx):
    f = ctx.fabrics()
    spec = f["fabrics"]["small"]
    rows = ctx.m.generate_cabling_schedule(spec)
    bom = ctx.m.estimate_fabric_bom(spec, f["spares_policy"])
    if len(rows) != bom["total_links"]:
        return False, f"{len(rows)} rows, expected {bom['total_links']}"
    ids = [r["cable_id"] for r in rows]
    if len(set(ids)) != len(ids):
        return False, "duplicate cable_id"
    ends = [(r["a_device"], r["a_port"]) for r in rows] + [(r["b_device"], r["b_port"]) for r in rows]
    dup = [e for e, n in Counter(ends).items() if n > 1]
    if dup:
        return False, f"endpoint used twice: {dup[0]}"
    spines = {r["b_device"] for r in rows if "spine" in r["b_device"]}
    pairs = Counter((r["a_device"], r["b_device"]) for r in rows if r["b_device"] in spines)
    if len(spines) != bom["spines"] or set(pairs.values()) != {bom["uplinks_per_leaf_per_spine"]}:
        return False, f"leaf->spine link counts uneven: {set(pairs.values())}"
    for r in rows:
        if not (r["cable_id"] in r["label_a"] and r["b_port"] in r["label_a"] and r["a_port"] in r["label_b"]):
            return False, f"label for {r['cable_id']} must name cable ID and both endpoints"
    return True, f"{len(rows)} cables, unique endpoints, {bom['uplinks_per_leaf_per_spine']} links per leaf-spine pair"


CHECKS = [
    ("dataset_reproducible", c_dataset),
    ("counter_delta", c_counter_delta),
    ("pcs_fec_line_rate", c_line_rate),
    ("fec_margin_decades", c_fec_margin),
    ("compute_deltas", c_deltas),
    ("layer_classification", c_layers),
    ("primary_findings", c_primary),
    ("per_port_digest", c_digest),
    ("severity_policy", c_severity),
    ("commissioning_report", c_report),
    ("link_budget", c_link_budget),
    ("bom_and_spares", c_bom),
    ("cabling_schedule", c_cabling),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    ap.add_argument("--report", type=Path, help="also write the commissioning report Markdown here")
    args = ap.parse_args()
    try:
        mod = load_impl(args.impl)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL import {args.impl}: {exc}")
        return 2
    ctx = Ctx(mod)
    passed = skipped = 0
    for name, fn in CHECKS:
        try:
            ok, msg = fn(ctx)
            if ok == "SKIP":
                print(f"SKIP {name}: {msg}")
                skipped += 1
                continue
            print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}")
            passed += bool(ok)
        except NotImplementedError as exc:
            print(f"TODO {name}: implement {exc.args[0] if exc.args else 'function'}()")
        except Exception as exc:  # noqa: BLE001
            last = traceback.extract_tb(exc.__traceback__)[-1]
            print(f"FAIL {name}: {type(exc).__name__}: {exc} (at {Path(last.filename).name}:{last.lineno})")
    required = len(CHECKS) - skipped
    print(f"\n{passed}/{required} checks passed ({args.impl})" + (f", {skipped} skipped" if skipped else ""))
    if args.report and passed == required:
        args.report.write_text(mod.commissioning_report(ctx.results(), LEAF)["markdown"], encoding="utf-8")
        print(f"commissioning report written to {args.report}")
    return 0 if passed == required else 1


if __name__ == "__main__":
    sys.exit(main())
