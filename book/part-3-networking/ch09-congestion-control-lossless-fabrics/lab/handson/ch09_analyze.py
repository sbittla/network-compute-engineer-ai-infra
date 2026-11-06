#!/usr/bin/env python3
"""Chapter 9 hands-on lab: turn the raw outputs of a run into summary.json and report.md.

    python3 ch09_analyze.py results/<run-id>

Standard library only. check.py imports the parsers below, re-derives every number from the raw files and
compares it with summary.json.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

RATE_BPS = 100e6                 # bottleneck drain rate (net.sh RATE)
FRAME, PAYLOAD = 1514, 1448      # bytes the queue holds per full-size TCP segment, and its payload (timestamps on)
CEILING_MBPS = RATE_BPS * PAYLOAD / FRAME / 1e6   # best possible TCP goodput through the bottleneck: 95.6 Mbit/s
BUF, KMIN, KMAX, PMAX = 500_000, 18_750, 187_500, 0.2
KMIN_AF, KMAX_AF = 187_500, 750_000
STEADY_FROM_S = 1.0              # queue and ping statistics skip the first second (connection setup, slow start)
CONFIGS = {   # name: (queue profile, tcp_ecn on the senders, congestion control) -- the order run.sh uses
    "droptail": ("droptail", 1, "cubic"),
    "red-ecn": ("red", 1, "cubic"),
    "red-nonect": ("red", 0, "cubic"),
    "asfound": ("asfound", 1, "cubic"),
    "dctcp": ("dctcp", 1, "dctcp"),
}


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def child_qdisc(path: Path) -> dict:
    for q in json.loads(path.read_text()):
        if q.get("handle") == "10:":
            return q
    raise ValueError(f"{path}: no child qdisc with handle 10:")


def netstat(path: Path) -> dict[str, int]:
    """Parse /proc/net/netstat + /proc/net/snmp (header line, value line per protocol) into {'IpExt.InCEPkts': n}."""
    out: dict[str, int] = {}
    lines = path.read_text().splitlines()
    for a, b in zip(lines, lines[1:]):
        ka, kb = a.split(), b.split()
        if ka and kb and ka[0] == kb[0] and not ka[1].lstrip("-").isdigit() and kb[1].lstrip("-").isdigit():
            for k, v in zip(ka[1:], kb[1:]):
                out[f"{ka[0].rstrip(':')}.{k}"] = int(v)
    return out


def iperf_client(path: Path) -> dict:
    d = json.loads(path.read_text())
    if "error" in d:
        raise ValueError(f"{path.name}: iperf3 error: {d['error']}")
    e = d["end"]
    return {"goodput_mbps": e["sum_received"]["bits_per_second"] / 1e6, "bytes": e["sum_received"]["bytes"],
            "seconds": e["sum_received"]["seconds"], "retransmits": e["sum_sent"].get("retransmits", 0),
            "cc": e.get("sender_tcp_congestion")}


def ping(path: Path) -> dict:
    t, rtt = [], []
    sent = recv = None
    for line in path.read_text().splitlines():
        m = re.match(r"\[(\d+\.\d+)\].*time=([\d.]+) ms", line)
        if m:
            t.append(float(m.group(1)))
            rtt.append(float(m.group(2)))
        m = re.match(r"(\d+) packets transmitted, (\d+) received", line)
        if m:
            sent, recv = int(m.group(1)), int(m.group(2))
    if not rtt:
        raise ValueError(f"{path}: no echo replies")
    steady = [r for ti, r in zip(t, rtt) if ti - t[0] >= STEADY_FROM_S] or rtt
    return {"sent": sent, "received": recv, "rtt_ms_p50": pct(steady, 50), "rtt_ms_p99": pct(steady, 99),
            "rtt_ms_min": min(rtt), "rtt_ms_max": max(rtt), "samples": len(rtt)}


def queue_csv(path: Path) -> dict:
    rows = [ln.split(",") for ln in path.read_text().splitlines()[1:] if ln.strip()]
    if len(rows) < 10:
        raise ValueError(f"{path}: only {len(rows)} queue samples")
    t = [float(r[0]) for r in rows]
    b = [int(r[1]) for r in rows]
    steady = [x for ti, x in zip(t, b) if ti >= STEADY_FROM_S] or b
    return {"samples": len(rows), "backlog_bytes_p50": pct(steady, 50), "backlog_bytes_p99": pct(steady, 99),
            "backlog_bytes_max": max(b), "backlog_bytes_mean": statistics.mean(steady),
            "queue_delay_ms_p50": pct(steady, 50) * 8 / RATE_BPS * 1e3,
            "queue_delay_ms_p99": pct(steady, 99) * 8 / RATE_BPS * 1e3}


def jain(xs: list[float]) -> float:
    return sum(xs) ** 2 / (len(xs) * sum(x * x for x in xs)) if xs and any(xs) else float("nan")


def run_metrics(d: Path) -> dict:
    """Every number one incast run reports, from its raw files."""
    clients = sorted(d.glob("client_h*.json"), key=lambda p: int(re.search(r"h(\d+)", p.name).group(1)))
    if not clients:
        raise ValueError(f"{d}: no client_h*.json")
    fl = [iperf_client(p) for p in clients]
    q0, q1 = child_qdisc(d / "qdisc_before.json"), child_qdisc(d / "qdisc_after.json")
    n0, n1 = netstat(d / "rx_netstat_before.txt"), netstat(d / "rx_netstat_after.txt")
    dq = {k: q1.get(k, 0) - q0.get(k, 0) for k in ("packets", "bytes", "drops", "marked", "early", "pdrop", "overlimits")}
    dn = {k: n1.get(f"IpExt.{k}", 0) - n0.get(f"IpExt.{k}", 0) for k in ("InNoECTPkts", "InECT0Pkts", "InECT1Pkts", "InCEPkts")}
    gp = [f["goodput_mbps"] for f in fl]
    # Aggregate goodput is every byte delivered over the incast's wall-clock window. Summing per-flow rates
    # would overstate it: each flow's rate uses its own 15 s, and staggered starts make the union longer.
    t0, t1 = (float(x) for x in (d / "window.txt").read_text().split()[:2])
    agg = sum(f["bytes"] for f in fl) * 8 / (t1 - t0) / 1e6
    m = {"senders": len(fl), "cc": sorted({f["cc"] for f in fl if f["cc"]}), "window_s": t1 - t0,
         "goodput_mbps": agg, "utilization": agg / CEILING_MBPS, "per_flow_mbps": gp, "jain": jain(gp),
         "retransmits": sum(f["retransmits"] for f in fl),
         "queue_sent_pkts": dq["packets"], "drops": dq["drops"], "marks": dq["marked"], "early_drops": dq["early"],
         "tail_drops": dq["pdrop"], "overlimits": dq["overlimits"],
         "mark_rate": dq["marked"] / dq["packets"] if dq["packets"] else 0.0,
         "drop_rate": dq["drops"] / (dq["packets"] + dq["drops"]) if dq["packets"] else 0.0,
         "rx_ce_pkts": dn["InCEPkts"], "rx_ect0_pkts": dn["InECT0Pkts"], "rx_noect_pkts": dn["InNoECTPkts"],
         "qdisc_kind": q1.get("kind")}
    m.update({f"queue_{k}" if not k.startswith(("backlog", "queue")) else k: v for k, v in queue_csv(d / "queue.csv").items()})
    p = ping(d / "ping.txt")
    m.update({f"ping_{k}": v for k, v in p.items()})
    return m


def med(runs: list[dict], key: str) -> float:
    return statistics.median(r[key] for r in runs)


KEYS = ["goodput_mbps", "utilization", "jain", "retransmits", "drops", "marks", "early_drops", "tail_drops",
        "mark_rate", "drop_rate", "rx_ce_pkts", "backlog_bytes_p50", "backlog_bytes_p99", "backlog_bytes_max",
        "queue_delay_ms_p50", "queue_delay_ms_p99", "ping_rtt_ms_p50", "ping_rtt_ms_p99"]


def analyze(run: Path) -> dict:
    s: dict = {"lab": "ch09-handson", "run_id": run.name,
               "params": {"rate_mbps": RATE_BPS / 1e6, "base_delay_ms_one_way": 2.0, "buffer_bytes": BUF,
                          "template": {"kmin": KMIN, "kmax": KMAX, "pmax": PMAX},
                          "as_found": {"kmin": KMIN_AF, "kmax": KMAX_AF, "pmax": PMAX},
                          "goodput_ceiling_mbps": CEILING_MBPS, "steady_from_s": STEADY_FROM_S}}
    s1 = run / "step1-fabric"
    idle = ping(s1 / "ping_idle.txt")
    single = run_metrics(s1 / "single-flow")
    base = idle["rtt_ms_p50"]
    s["step1"] = {"idle_ping": idle, "base_rtt_ms": base, "bdp_bytes": RATE_BPS / 8 * base / 1e3, "single_flow": single}
    s["configs"] = {}
    for name, (prof, ecn, cc) in CONFIGS.items():
        dirs = sorted((run / "step2-incast").glob(f"{name}_rep*"))
        if not dirs:
            s["configs"][name] = {"skipped": True}
            continue
        runs = [dict(run_metrics(d), rep=d.name) for d in dirs]
        s["configs"][name] = {"queue": prof, "tcp_ecn": ecn, "cc": cc, "runs": runs,
                              "median": {k: med(runs, k) for k in KEYS},
                              "min": {k: min(r[k] for r in runs) for k in KEYS},
                              "max": {k: max(r[k] for r in runs) for k in KEYS}}
    order = (run / "step2-incast" / "order.txt")
    s["step2_order"] = order.read_text().split() if order.exists() else []
    s["fanin"] = {}
    for d in sorted((run / "step7-fanin").glob("*_n*")):
        name, n = d.name.rsplit("_n", 1)
        s["fanin"].setdefault(name, {})[n] = {k: v for k, v in run_metrics(d).items() if k in KEYS + ["senders", "per_flow_mbps"]}
    return s


def f0(x) -> str:
    return f"{x:,.0f}"


def report(s: dict) -> str:
    p, st = s["params"], s["step1"]
    L = [f"# Chapter 9 hands-on: ECN and incast with `tc` — `{s['run_id']}`", "",
         "Every number is `[MEASURED]` on the machine in `environment.json`, in the step named; medians over the "
         "repetitions, with the range in brackets.", "",
         "## Step 1: the fabric", "",
         f"- Bottleneck {p['rate_mbps']:.0f} Mbit/s; best TCP goodput through it {p['goodput_ceiling_mbps']:.1f} Mbit/s "
         f"(1,448 payload bytes per 1,514-byte frame).",
         f"- Idle RTT probe → receiver: p50 **{st['base_rtt_ms']:.2f} ms** (min {st['idle_ping']['rtt_ms_min']:.2f}) "
         f"`[MEASURED, step 1]`, so BDP = {f0(st['bdp_bytes'])} B `[MEASURED, step 1]`.",
         f"- One cubic flow into the drop-tail queue: **{st['single_flow']['goodput_mbps']:.1f} Mbit/s** "
         f"({100 * st['single_flow']['utilization']:.0f} % of the ceiling), queue p50 {f0(st['single_flow']['backlog_bytes_p50'])} B, "
         f"{st['single_flow']['drops']} drops `[MEASURED, step 1]`.", "",
         "## Steps 2–6: 8:1 incast, one queue profile at a time", "",
         f"Order of the interleaved runs: {' '.join(s['step2_order'])}.", "",
         "| Config | Goodput (Mbit/s) | Jain | Queue p50 (B) | Queue p99 (B) | Queue delay p50 (ms) | Probe RTT p50 / p99 (ms) | Drops | Marks | CE at receiver | Retransmits |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, c in s["configs"].items():
        if c.get("skipped"):
            L.append(f"| {name} | skipped (not available on this kernel) |||||||||| ")
            continue
        m, lo, hi = c["median"], c["min"], c["max"]
        L.append(f"| {name} | {m['goodput_mbps']:.1f} [{lo['goodput_mbps']:.1f}–{hi['goodput_mbps']:.1f}] | {m['jain']:.3f} | "
                 f"{f0(m['backlog_bytes_p50'])} [{f0(lo['backlog_bytes_p50'])}–{f0(hi['backlog_bytes_p50'])}] | {f0(m['backlog_bytes_p99'])} | "
                 f"{m['queue_delay_ms_p50']:.1f} | {m['ping_rtt_ms_p50']:.1f} / {m['ping_rtt_ms_p99']:.1f} | "
                 f"{f0(m['drops'])} [{f0(lo['drops'])}–{f0(hi['drops'])}] | {f0(m['marks'])} [{f0(lo['marks'])}–{f0(hi['marks'])}] | "
                 f"{f0(m['rx_ce_pkts'])} | {f0(m['retransmits'])} |")
    L += ["", "All `[MEASURED, step 2–6]`. Queue figures are the bottleneck's backlog sampled every 20 ms after the first "
          "second; queue delay = backlog / drain rate.", ""]
    rn = s["configs"].get("red-nonect", {})
    if rn and not rn.get("skipped"):
        m = rn["median"]
        L += [f"red-nonect: senders with `tcp_ecn=0` into the same RED+ECN queue: {f0(m['early_drops'])} early drops, "
              f"{f0(m['marks'])} marks (the ECT(0) ping probe only) `[MEASURED, step 4]`.", ""]
    if s["fanin"]:
        L += ["## Step 7: fan-in", "", "| Config | N | Goodput (Mbit/s) | Jain | Queue p50 (B) | Drops | Marks | Retransmits |",
              "|---|---|---|---|---|---|---|---|"]
        for name, by_n in s["fanin"].items():
            for n in sorted(by_n, key=int):
                m = by_n[n]
                L.append(f"| {name} | {n} | {m['goodput_mbps']:.1f} | {m['jain']:.3f} | {f0(m['backlog_bytes_p50'])} | "
                         f"{f0(m['drops'])} | {f0(m['marks'])} | {f0(m['retransmits'])} |")
        L += ["", "All `[MEASURED, step 7]`, one run each (N = 8 is in the table above).", ""]
    return "\n".join(L) + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run = Path(sys.argv[1])
    s = analyze(run)
    (run / "summary.json").write_text(json.dumps(s, indent=2))
    (run / "report.md").write_text(report(s), encoding="utf-8")
    print(f"wrote {run / 'summary.json'} and {run / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
