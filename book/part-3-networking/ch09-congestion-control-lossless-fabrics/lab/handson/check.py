#!/usr/bin/env python3
"""Check a Chapter 9 hands-on evidence bundle: complete, internally consistent and physically sensible.

    python check.py results/<run-id>

Prints one PASS / FAIL / SKIP line per check and exits 0 only if no check fails. Standard library only. It
re-derives every number from the raw outputs (with ch09_analyze's parsers) instead of trusting
summary.json, then confirms summary.json agrees. It tests mechanisms, not this machine's numbers: a
drop-tail queue drops and never marks; a RED+ECN queue marks, the marks arrive as CE, and the queue stays
short without costing goodput; the same queue drops packets from senders that are not ECN-capable;
thresholds set too high behave like drop-tail.
"""
from __future__ import annotations

import json
import math
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ch09_analyze as A  # noqa: E402

RUN_FILES = ["client_h1.json", "qdisc_before.json", "qdisc_after.json", "qdisc_after.txt", "queue.csv", "ping.txt",
             "rx_netstat_before.txt", "rx_netstat_after.txt", "commands.txt"]
REQUIRED_CFGS = ["droptail", "red-ecn", "red-nonect", "asfound"]
FANIN = [f"{c}_n{n}" for n in (1, 4, 16) for c in ("droptail", "red-ecn")]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    run = Path(sys.argv[1])
    rows: list[tuple[str, str, str]] = []

    def check(name: str, fn) -> None:
        try:
            msg = fn() or ""
            rows.append(("SKIP" if msg.startswith("SKIP:") else "PASS", name, msg.removeprefix("SKIP: ")))
        except AssertionError as e:
            rows.append(("FAIL", name, str(e) or "assertion failed"))
        except Exception as e:  # noqa: BLE001 - a malformed bundle must give a useful line, not a traceback
            tb = traceback.extract_tb(e.__traceback__)[-1]
            rows.append(("FAIL", name, f"{type(e).__name__}: {e} (check.py:{tb.lineno})"))

    def complete():
        missing = [f for f in ("environment.json", "summary.json", "report.md", "step1-fabric/ping_idle.txt",
                               "step1-fabric/fabric.txt", "step2-incast/order.txt") if not (run / f).is_file()]
        missing += [f"step1-fabric/single-flow/{f}" for f in RUN_FILES if not (run / "step1-fabric/single-flow" / f).is_file()]
        for c in REQUIRED_CFGS:
            reps = sorted((run / "step2-incast").glob(f"{c}_rep*"))
            if len(reps) < 2:
                missing.append(f"step2-incast/{c}_rep* (need >= 2 repetitions, found {len(reps)})")
            for r in reps:
                missing += [f"{r.relative_to(run).as_posix()}/{f}" for f in RUN_FILES if not (r / f).is_file()]
        for f in FANIN:
            d = run / "step7-fanin" / f
            missing += [f"step7-fanin/{f}/{x}" for x in RUN_FILES if not (d / x).is_file()]
        assert not missing, f"missing in {run}: {', '.join(missing[:8])}" + (f" (+{len(missing) - 8} more)" if len(missing) > 8 else "")
        return "all raw files, summary.json and report.md present"
    check("bundle complete", complete)
    if rows[-1][0] == "FAIL":
        return report(rows)

    s = A.analyze(run)
    sm = json.loads((run / "summary.json").read_text())
    C = s["configs"]
    med = {k: v["median"] for k, v in C.items() if not v.get("skipped")}

    def env():
        e = json.loads((run / "environment.json").read_text())
        assert e.get("captured_at") and e.get("kernel"), "environment.json lacks the time or the kernel"
        t = e.get("tools", {})
        assert any("iperf 3" in str(v) for v in t.values()), "environment.json does not record the iperf3 version"
        return f"kernel {e['kernel']}, {e.get('cpu')}"
    check("environment.json names kernel, CPU, time and iperf3", env)
    check("report.md labels its numbers [MEASURED]",
          lambda: None if "[MEASURED" in (run / "report.md").read_text(encoding="utf-8") else (_ for _ in ()).throw(
              AssertionError("report.md has no [MEASURED] label")))

    def agree():
        bad = []
        for name, c in s["configs"].items():
            if c.get("skipped"):
                continue
            for k, v in c["median"].items():
                w = sm["configs"][name]["median"][k]
                if not math.isclose(v, w, rel_tol=1e-9, abs_tol=1e-9):
                    bad.append(f"{name}.{k}: raw {v} vs summary {w}")
        if not math.isclose(s["step1"]["base_rtt_ms"], sm["step1"]["base_rtt_ms"], rel_tol=1e-9):
            bad.append("step1.base_rtt_ms")
        assert not bad, "; ".join(bad[:5])
        return "every median re-derived from the raw files matches summary.json"
    check("summary.json agrees with the raw outputs", agree)

    def clients_ok():
        short = []
        for d in sorted((run / "step2-incast").glob("*_rep*")) + sorted((run / "step7-fanin").glob("*_n*")):
            meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
            n_want = meta.get("senders")
            fl = sorted(d.glob("client_h*.json"))
            if n_want and len(fl) != n_want:
                short.append(f"{d.name}: {len(fl)} of {n_want} clients")
            for p in fl:
                c = A.iperf_client(p)
                if c["seconds"] < 0.9 * meta.get("seconds", 0) or c["bytes"] <= 0:
                    short.append(f"{d.name}/{p.name}: {c['seconds']:.1f} s, {c['bytes']} B")
        assert not short, "; ".join(short[:5])
        return "every iperf3 client connected and ran its full duration"
    check("incast runs complete", clients_ok)

    st = s["step1"]
    check("step 1: base RTT shows the 2 ms netem delay", lambda: (
        f"idle probe RTT p50 {st['base_rtt_ms']:.2f} ms, BDP {st['bdp_bytes']:,.0f} B"
        if 1.9 <= st["base_rtt_ms"] <= 4.0 else (_ for _ in ()).throw(AssertionError(f"idle RTT p50 {st['base_rtt_ms']:.2f} ms, expected 2-4 ms"))))

    def single():
        g = st["single_flow"]["goodput_mbps"]
        assert 0.85 * A.CEILING_MBPS <= g <= 1.01 * A.CEILING_MBPS, f"one flow got {g:.1f} Mbit/s; ceiling {A.CEILING_MBPS:.1f}"
        return f"one flow {g:.1f} Mbit/s of a {A.CEILING_MBPS:.1f} Mbit/s ceiling: the bottleneck is the token bucket"
    check("step 1: one flow fills the bottleneck", single)

    def physical():
        bad = []
        for name, c in C.items():
            for r in c.get("runs", []):
                if r["goodput_mbps"] > 1.02 * A.CEILING_MBPS:
                    bad.append(f"{r['rep']}: goodput {r['goodput_mbps']:.1f} above the ceiling")
                if r["backlog_bytes_max"] > A.BUF + 2 * A.FRAME:
                    bad.append(f"{r['rep']}: backlog {r['backlog_bytes_max']} above the {A.BUF} B buffer")
        assert not bad, "; ".join(bad[:5])
        return f"no run beats {A.CEILING_MBPS:.1f} Mbit/s or holds more than the {A.BUF:,} B buffer"
    check("physical limits respected", physical)

    def droptail():
        rs = C["droptail"]["runs"]
        assert all(r["marks"] == 0 and r["rx_ce_pkts"] == 0 for r in rs), \
            f"drop-tail marked: {[(r['marks'], r['rx_ce_pkts']) for r in rs]}"
        assert all(r["drops"] > 0 for r in rs), f"drop-tail never dropped: {[r['drops'] for r in rs]}"
        m = med["droptail"]
        return f"0 marks, 0 CE; median {m['drops']:,.0f} drops, queue p50 {m['backlog_bytes_p50']:,.0f} B"
    check("droptail: drops, never marks", droptail)

    def red_marks():
        rs = C["red-ecn"]["runs"]
        assert all(r["marks"] > 0 for r in rs), f"RED+ECN did not mark: {[r['marks'] for r in rs]}"
        for r in rs:
            assert abs(r["rx_ce_pkts"] - r["marks"]) <= 0.05 * r["marks"] + 10, \
                f"{r['rep']}: {r['marks']} marked at the queue but {r['rx_ce_pkts']} CE packets at the receiver"
        m = med["red-ecn"]
        return f"median {m['marks']:,.0f} marks, {m['rx_ce_pkts']:,.0f} CE packets arrived (mark rate {100 * m['mark_rate']:.1f} %)"
    check("red-ecn: marks, and every mark arrives as CE", red_marks)

    def red_drops():
        d, r = med["droptail"]["drops"], med["red-ecn"]["drops"]
        assert r <= 0.1 * d, f"RED+ECN dropped {r:,.0f} (median) against drop-tail's {d:,.0f}"
        return f"median drops {r:,.0f} against drop-tail's {d:,.0f}"
    check("red-ecn: marks replace drops", red_drops)

    def red_queue():
        d, r = med["droptail"], med["red-ecn"]
        assert r["backlog_bytes_p50"] <= 0.5 * d["backlog_bytes_p50"], \
            f"queue p50 {r['backlog_bytes_p50']:,.0f} B vs drop-tail {d['backlog_bytes_p50']:,.0f} B"
        assert r["ping_rtt_ms_p50"] < d["ping_rtt_ms_p50"], "the probe saw no lower RTT"
        assert A.KMIN / 4 <= r["backlog_bytes_p50"] <= A.KMAX, \
            f"RED queue p50 {r['backlog_bytes_p50']:,.0f} B outside [Kmin/4, Kmax] = [{A.KMIN / 4:,.0f}, {A.KMAX:,}]"
        return (f"queue p50 {r['backlog_bytes_p50']:,.0f} B vs {d['backlog_bytes_p50']:,.0f} B; probe RTT p50 "
                f"{r['ping_rtt_ms_p50']:.1f} vs {d['ping_rtt_ms_p50']:.1f} ms")
    check("red-ecn: short queue, low queueing delay", red_queue)

    def red_goodput():
        d, r = med["droptail"]["goodput_mbps"], med["red-ecn"]["goodput_mbps"]
        assert r >= 0.9 * d, f"RED+ECN goodput {r:.1f} vs drop-tail {d:.1f} Mbit/s"
        return f"{r:.1f} vs {d:.1f} Mbit/s"
    check("red-ecn: the short queue costs little goodput", red_goodput)

    def nonect():
        rs = C["red-nonect"]["runs"]
        for r in rs:
            assert r["early_drops"] > 0, f"{r['rep']}: no early drops"
            assert r["marks"] <= r["ping_sent"], f"{r['rep']}: {r['marks']} marks but only {r['ping_sent']} ECT(0) probes"
            assert r["rx_noect_pkts"] > 20 * max(r["rx_ect0_pkts"], 1), \
                f"{r['rep']}: data arrived ECN-capable ({r['rx_ect0_pkts']} ECT(0) vs {r['rx_noect_pkts']} not-ECT)"
        m = med["red-nonect"]
        return (f"median {m['early_drops']:,.0f} early drops, {m['marks']:,.0f} marks (probe only): the same queue drops "
                f"what it cannot mark")
    check("red-nonect: senders without ECN are dropped, not marked", nonect)

    def asfound():
        a, r, d = med["asfound"], med["red-ecn"], med["droptail"]
        assert a["backlog_bytes_p50"] >= 2 * r["backlog_bytes_p50"], \
            f"as-found queue p50 {a['backlog_bytes_p50']:,.0f} B vs template {r['backlog_bytes_p50']:,.0f} B"
        assert a["backlog_bytes_p50"] >= A.KMIN_AF * 0.5, f"as-found queue p50 {a['backlog_bytes_p50']:,.0f} B below Kmin/2"
        return (f"queue p50 {a['backlog_bytes_p50']:,.0f} B (template {r['backlog_bytes_p50']:,.0f}, drop-tail "
                f"{d['backlog_bytes_p50']:,.0f}); {a['marks']:,.0f} marks, {a['drops']:,.0f} drops")
    check("asfound: thresholds 10x too high give a deep queue", asfound)

    def dctcp():
        if "dctcp" not in med:
            return "SKIP: DCTCP not available on this kernel"
        m, r = med["dctcp"], med["red-ecn"]
        assert m["marks"] > 0, "DCTCP run saw no marks"
        assert all("dctcp" in x["cc"] for x in C["dctcp"]["runs"]), "the flows did not use dctcp"
        assert m["backlog_bytes_p50"] <= 3 * A.KMIN, f"queue p50 {m['backlog_bytes_p50']:,.0f} B, K = {A.KMIN:,}"
        assert m["goodput_mbps"] >= 0.9 * A.CEILING_MBPS, f"goodput {m['goodput_mbps']:.1f} Mbit/s"
        return (f"queue p50 {m['backlog_bytes_p50']:,.0f} B at K = {A.KMIN:,} B, goodput {m['goodput_mbps']:.1f} Mbit/s, "
                f"mark rate {100 * m['mark_rate']:.1f} %")
    check("dctcp: the queue sits at K with the link full", dctcp)

    def interleaved():
        order = s["step2_order"]
        names = [o.rsplit("_rep", 1)[0] for o in order]
        assert len(order) >= 2 * len(REQUIRED_CFGS), f"only {len(order)} runs in order.txt"
        rep_runs = [n for n in names]
        same = [i for i in range(1, len(rep_runs)) if rep_runs[i] == rep_runs[i - 1]]
        assert not same, f"configurations repeated back to back at {same}"
        return " ".join(order)
    check("step 2: repetitions interleaved", interleaved)

    def fanin():
        f = s["fanin"]
        d16, r16 = f["droptail"]["16"], f["red-ecn"]["16"]
        assert all(f["droptail"][n]["marks"] == 0 for n in f["droptail"]), "drop-tail marked in the fan-in sweep"
        assert all(f["red-ecn"][n]["marks"] > 0 for n in ("4", "16")), "RED+ECN did not mark at N = 4 or 16"
        assert d16["drops"] > 0, "drop-tail at N = 16 did not drop"
        assert r16["backlog_bytes_p50"] < d16["backlog_bytes_p50"], "RED+ECN queue not shorter at N = 16"
        return (f"N = 16: drop-tail {d16['drops']:,.0f} drops, queue p50 {d16['backlog_bytes_p50']:,.0f} B; "
                f"RED+ECN {r16['drops']:,.0f} drops, {r16['marks']:,.0f} marks, queue p50 {r16['backlog_bytes_p50']:,.0f} B")
    check("step 7: fan-in", fanin)
    return report(rows)


def report(rows) -> int:
    for st, name, msg in rows:
        print(f"{st}  {name}" + (f"  — {msg}" if msg else ""))
    fails = sum(1 for r in rows if r[0] == "FAIL")
    print(f"\n{sum(1 for r in rows if r[0] == 'PASS')} passed, {fails} failed, {sum(1 for r in rows if r[0] == 'SKIP')} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
