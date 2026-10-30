#!/usr/bin/env python3
"""Checker for the Chapter 7 lab (fabric design and validation tool).

    python check.py                    # check lab/starter/fabric_lab.py (your work)
    python check.py --impl solution    # check the reference implementation (instructors)

Prints one line per check (PASS / FAIL / TODO / SKIP) and exits non-zero if any check does not pass.
Pure Python, no network, no hardware; runs in well under 60 s.
"""
from __future__ import annotations

import argparse
import importlib.util
import ipaddress
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # keep starter/ and solutions/ free of __pycache__

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMPLS = {
    "starter": HERE / "starter" / "fabric_lab.py",
    "solution": HERE.parent / "solutions" / "lab" / "fabric_lab.py",
}

EXPECTED_FINDINGS = {
    ("DUP_P2P", "10.101.3.72/31"),
    ("ASN_COLLISION", "65107"),
    ("MTU_MISMATCH", "F-r3-s2-k6"),
    ("ECMP_MAXPATHS", "orion-be-leaf-r2"),
    ("BAD_ORIGIN", "orion-be-leaf-r1 10.100.6.0/24"),
    ("ASYM_ADVERT", "orion-be-leaf-r5 10.100.5.0/24"),
}
HINTS = {
    "DUP_P2P": "group every link by the /31 network of its endpoints",
    "ASN_COLLISION": "compare leaf ASNs with each other (spines may share 65100)",
    "MTU_MISMATCH": "compare a_mtu and b_mtu on fabric links",
    "ECMP_MAXPATHS": "a leaf with 32 uplinks needs max-paths >= 32",
    "BAD_ORIGIN": "a leaf owns only 10.100.<rail>.0/24 and its loopback",
    "ASYM_ADVERT": "each owned prefix must reach every spine the leaf is linked to",
}


def load(impl: str):
    path = IMPLS[impl]
    spec = importlib.util.spec_from_file_location(f"fabric_lab_{impl}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CheckFailed(Exception):
    pass


class Skipped(Exception):
    """A check that cannot run in this distribution (e.g. generator absent in the student release)."""


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise CheckFailed(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = parser.parse_args()
    m = load(args.impl)
    results: list[tuple[str, str, str]] = []
    cache: dict = {}

    def run(name: str, fn) -> None:
        try:
            fn()
            results.append(("PASS", name, ""))
        except NotImplementedError as exc:
            results.append(("TODO", name, f"{exc} not implemented yet"))
        except Skipped as exc:
            results.append(("SKIP", name, str(exc)))
        except CheckFailed as exc:
            results.append(("FAIL", name, str(exc)))
        except Exception as exc:  # learner bugs must not crash the checker
            results.append(("FAIL", name, f"{type(exc).__name__}: {exc}"))

    # ---- Data integrity: committed dataset == seeded generator output ---------------------
    def t_regen() -> None:
        gen = HERE / "tools" / "generate_intent.py"
        if not gen.exists():
            raise Skipped("generator not shipped in student release")
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, str(gen), "--out", tmp],
                           check=True, capture_output=True)
            for name in ("devices.csv", "links.csv", "advertisements.csv"):
                expect((Path(tmp) / name).read_bytes() == (DATA / name).read_bytes(),
                       f"data/{name} differs from generator output (seed 7) -- do not edit data/ by hand")

    run("T0  dataset regenerates byte-identically (seed 7)", t_regen)

    # ---- Task 1: sizing -------------------------------------------------------------------
    def t_orion() -> None:
        r = m.size_two_tier(256, 64, 64, 1.0)
        want = {"down_per_leaf": 32, "up_per_leaf": 32, "leaves": 8, "spines": 4,
                "links_per_leaf_spine": 8, "host_cables": 256, "fabric_cables": 256,
                "total_cables": 512, "transceivers": 1024, "max_endpoints_two_tier": 2048,
                "leaf_uplink_gbps": 12800}
        for k, v in want.items():
            expect(r.get(k) == v, f"{k}={r.get(k)!r}, expected {v}")
        expect(abs(r["oversubscription"] - 1.0) < 1e-9 and r["feasible"] is True, "oversub/feasible wrong")

    def t_frontend() -> None:
        r = m.size_two_tier(64, 64, 64, 3.0, down_gbps=200)
        want = {"down_per_leaf": 48, "up_per_leaf": 16, "leaves": 2, "spines": 2,
                "links_per_leaf_spine": 8, "fabric_cables": 32, "total_cables": 96}
        for k, v in want.items():
            expect(r.get(k) == v, f"3:1 frontend: {k}={r.get(k)!r}, expected {v}")
        expect(abs(r["oversubscription"] - 3.0) < 1e-9, "port-count oversubscription should be 3.0")
        bw = r.get("bandwidth_oversubscription")
        expect(bw is not None and abs(bw - 1.5) < 1e-9,
               f"bandwidth_oversubscription={bw!r}: 48 x 200G down vs 16 x 400G up is 9.6 : 6.4 = 1.5")

    def t_xl() -> None:
        r64 = m.size_two_tier(4096, 64, 64, 1.0)
        expect(r64["feasible"] is False, "4,096 endpoints exceed a 64-port two-tier Clos (max 2,048)")
        r128 = m.size_two_tier(4096, 128, 128, 1.0)
        want = {"feasible": True, "leaves": 64, "spines": 32, "links_per_leaf_spine": 2,
                "max_endpoints_two_tier": 8192, "total_cables": 8192}
        for k, v in want.items():
            expect(r128.get(k) == v, f"128-port radix: {k}={r128.get(k)!r}, expected {v}")

    run("T1a size ORION-256 backend (64-port, 1:1)", t_orion)
    run("T1b size frontend pair (3:1 ports, 1.5:1 bandwidth)", t_frontend)
    run("T1c ORION-XL radix limit (64- vs 128-port)", t_xl)

    # ---- Task 2: addressing ---------------------------------------------------------------
    def plan():
        if "plan" not in cache:
            cache["plan"] = m.build_addressing_plan()
        return cache["plan"]

    def t_plan_shape() -> None:
        p = plan()
        expect(len(p) == 512, f"{len(p)} rows, expected 256 host + 256 fabric = 512")
        subnets = [r["subnet"] for r in p]
        expect(len(set(subnets)) == 512, "subnets are not unique")
        for r in p:
            a, b = ipaddress.ip_interface(r["a_ip"]), ipaddress.ip_interface(r["b_ip"])
            expect(a.network == b.network == ipaddress.ip_network(r["subnet"]) and a.ip != b.ip,
                   f"{r['link_id']}: ends not in the same /31")
            expect(a.network.prefixlen == 31, f"{r['link_id']}: not a /31")

    def t_plan_values() -> None:
        rows = {r["link_id"]: r for r in plan()}
        h = rows.get("H-r3-n05")
        expect(h is not None, "missing H-r3-n05")
        expect((h["a_ip"], h["b_ip"], h["a_port"]) == ("10.100.3.10/31", "10.100.3.11/31", "Ethernet5"),
               f"H-r3-n05 got {h['a_ip']}, {h['b_ip']}, {h['a_port']}")
        f = rows.get("F-r2-s3-k1")
        expect(f is not None, "missing F-r2-s3-k1")
        expect((f["b_ip"], f["a_ip"], f["a_port"], f["b_port"]) ==
               ("10.101.3.34/31", "10.101.3.35/31", "Ethernet50", "Ethernet18"),
               f"F-r2-s3-k1 got spine {f['b_ip']} leaf {f['a_ip']} ports {f['a_port']}/{f['b_port']}")

    run("T2a addressing plan: 512 unique /31s", t_plan_shape)
    run("T2b addressing plan: spot values", t_plan_values)

    # ---- Task 3: BGP ----------------------------------------------------------------------
    def t_bgp() -> None:
        n = m.build_bgp_neighbors(plan())
        expect(len(n) == 256, f"{len(n)} sessions, expected 256 (one per fabric link)")
        per_leaf: dict[str, int] = {}
        per_spine: dict[str, int] = {}
        for s in n:
            per_leaf[s["leaf"]] = per_leaf.get(s["leaf"], 0) + 1
            per_spine[s["spine"]] = per_spine.get(s["spine"], 0) + 1
            expect(s["spine_asn"] == 65100, "spine ASN must be 65100")
            expect(s["leaf_asn"] == 65101 + int(s["leaf"].removeprefix("orion-be-leaf-r")), f"bad ASN for {s['leaf']}")
            expect("/" not in s["leaf_ip"] and "/" not in s["spine_ip"], "IPs must not carry a prefix length")
        expect(set(per_leaf.values()) == {32} and len(per_leaf) == 8, "each leaf needs 32 sessions")
        expect(set(per_spine.values()) == {64} and len(per_spine) == 4, "each spine needs 64 sessions")
        expect(len({(s["leaf_ip"], s["spine_ip"]) for s in n}) == 256, "duplicate sessions")

    run("T3  BGP neighbor table (256 sessions, ASNs)", t_bgp)

    # ---- Task 4: validation ---------------------------------------------------------------
    def findings():
        if "findings" not in cache:
            fs = m.validate_intent(m.load_intent(DATA))
            cache["findings"] = {(f["code"], f["subject"]) for f in fs}
        return cache["findings"]

    for code, subject in sorted(EXPECTED_FINDINGS):
        def t(code=code, subject=subject) -> None:
            expect((code, subject) in findings(), f"not found -- hint: {HINTS[code]}")
        run(f"T4  detect planted {code}", t)

    def t_no_fp() -> None:
        extra = findings() - EXPECTED_FINDINGS
        expect(not extra, f"{len(extra)} false positive(s), e.g. {sorted(extra)[:3]}")

    run("T4  no false positives (shared spine ASN, host MTU 9000 are legal)", t_no_fp)

    # ---- Task 5: capacity -----------------------------------------------------------------
    def cap_case(label, counts, adv, leaf, uplink, ingress, bis) -> None:
        def t() -> None:
            c = m.fabric_capacity(counts, 400, adv)
            got = (c["uplink_gbps"][leaf], c["ecmp_ingress_gbps"][leaf], c["bisection_gbps"])
            expect(tuple(round(x) for x in got) == (uplink, ingress, bis),
                   f"leaf {leaf}: uplink/ingress/bisection = {got}, expected {(uplink, ingress, bis)}")
        run(f"T5  capacity: {label}", t)

    lm = m.link_matrix
    cap_case("baseline", lm(8, 4, 8), None, 0, 12800, 12800, 51200)
    cap_case("one orion-be-leaf-r0/orion-be-spine-1 link down", lm(8, 4, 8, failed_links=((0, 0),)), None, 0, 12400, 11200, 50800)
    cap_case("orion-be-spine-2 down", lm(8, 4, 8, failed_spines=(1,)), None, 3, 9600, 9600, 38400)
    adv = [[True] * 4 for _ in range(8)]
    adv[5][3] = False
    cap_case("orion-be-leaf-r5 prefix not sent to orion-be-spine-4", lm(8, 4, 8), adv, 5, 12800, 9600, 51200)
    cap_case("orion-be-leaf-r3 down (rail 3 isolated)", lm(8, 4, 8, failed_leaves=(3,)), None, 3, 0, 0, 38400)

    # ---- report ---------------------------------------------------------------------------
    width = max(len(n) for _, n, _ in results)
    for status, name, why in results:
        print(f"{status:4s}  {name:<{width}}  {why}".rstrip())
    passed = sum(1 for s, _, _ in results if s == "PASS")
    skipped = sum(1 for s, _, _ in results if s == "SKIP")
    counted = len(results) - skipped
    note = f", {skipped} skipped" if skipped else ""
    print(f"\n{passed}/{counted} checks passed ({args.impl}{note})")
    return 0 if passed == counted else 1


if __name__ == "__main__":
    sys.exit(main())
