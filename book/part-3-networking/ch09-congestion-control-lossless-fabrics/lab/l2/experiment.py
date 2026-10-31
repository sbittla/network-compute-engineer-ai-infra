"""Ch 9 L2: probe for RDMA congestion counters; measure a host-stack N:1 incast and its real ECN/retransmit counters.

The chapter's L2 extension reads PFC pause, ECN-marked and CNP counters from an RDMA NIC
(``ethtool -S``, ``rdma statistic``, ``/sys/class/infiniband/<dev>/ports/1/hw_counters``) twice, 60 s
apart, and turns them into rates with ``counters_to_rates``. This host has no RDMA NIC, so that part
is probed and recorded as not runnable. What genuinely applies on one host:

1. **The host's real congestion-control configuration.** The TCP congestion-control algorithm, the
   algorithms available and the ECN mode, read from ``/proc/sys/net/ipv4``.
2. **An N:1 incast on loopback, measured with the L3 method of Section 9.9 step 4.** N sender threads
   each push the same burst over TCP into one receiver (N = 1, 2, 4, 8; >= 5 repetitions). The
   experiment reports the median and p95/p99 per-flow bandwidth and flow-completion time, Jain's
   fairness index, and incast completion against the single-flow case. Before and after every run it
   snapshots the network namespace's cumulative counters (``RetransSegs``, ``InCEPkts``,
   ``InECT0Pkts``, ...) and converts them to rates with the lab's own ``counters_to_rates``. This is
   the counter method of the L2 extension, applied to counters that exist here.
3. **The L1 SIMULATED incast for comparison.** The lab's fluid model (``compare_configs`` on
   ``lab/data/sim_configs.yaml``) shows what ECN thresholds change on a 400 Gb/s lossless port.

Loopback has no switch, no egress queue, no ECN marking and no PFC: the bottleneck is the receiver's
CPU and socket stack. The measurement teaches the *method* (one variable at a time, per-flow
percentiles, counters as rates). It does not reproduce fabric congestion; the report says so.

CPU fallback: identical (the experiment does not use the GPU).
"""
from __future__ import annotations

import importlib.util
import shutil
import socket
import statistics
import sys
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch09-l2",
    "title": "Lab 9 L2: RDMA-counter probe, host-stack N:1 incast and real ECN/retransmit counters",
    "evidence": "MEASURED",
    "gpu_optional": True,
    "cpu_fallback": "identical: the loopback incast, counter snapshots and simulation use only the CPU",
}

PKG = Path(__file__).resolve().parents[2]
COUNTERS = {("Tcp", "RetransSegs"), ("Tcp", "OutSegs"), ("Tcp", "InSegs"), ("IpExt", "InCEPkts"),
            ("IpExt", "InECT0Pkts"), ("IpExt", "InECT1Pkts"), ("IpExt", "InNoECTPkts"),
            ("TcpExt", "TCPTimeouts"), ("TcpExt", "TCPFastRetrans"), ("TcpExt", "TCPLossProbes"),
            ("TcpExt", "TCPBacklogDrop"), ("TcpExt", "TCPRcvQDrop"), ("TcpExt", "TCPSpuriousRTOs")}
CHUNK = 1 << 20


def read(path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def load_l1(name: str):
    """The L1 module: the reference solution if present, else the learner's starter (student release)."""
    for d in (PKG / "solutions" / "lab", PKG / "lab" / "starter"):
        p = d / f"{name}.py"
        if p.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            try:
                spec.loader.exec_module(mod)
                return mod, p.relative_to(PKG).as_posix()
            except Exception:  # noqa: BLE001
                continue
    return None, None


def snapshot() -> dict:
    """Cumulative counters of this network namespace from /proc/net/snmp and /proc/net/netstat."""
    out = {}
    for f in ("/proc/net/snmp", "/proc/net/netstat"):
        lines = (read(f) or "").splitlines()
        for hdr, val in zip(lines[::2], lines[1::2]):
            names, vals = hdr.split(), val.split()
            group = names[0].rstrip(":")
            for n, v in zip(names[1:], vals[1:]):
                if (group, n) in COUNTERS:
                    out[f"{group}.{n}"] = int(v)
    out["ts_s"] = time.monotonic()
    return out


def probe() -> dict:
    ib = Path("/sys/class/infiniband")
    devs = sorted(p.name for p in ib.iterdir()) if ib.is_dir() else []
    return {
        "rdma_devices": devs,
        "hw_counters_dirs": [str(p) for p in ib.glob("*/ports/*/hw_counters")] if devs else [],
        "tools": {t: bool(shutil.which(t)) for t in ("ethtool", "rdma", "mlnx_qos", "dcb", "ib_write_bw")},
        "netdevs": sorted(p.name for p in Path("/sys/class/net").iterdir()) if Path("/sys/class/net").is_dir() else [],
        "tcp_congestion_control": read("/proc/sys/net/ipv4/tcp_congestion_control"),
        "tcp_available_congestion_control": read("/proc/sys/net/ipv4/tcp_available_congestion_control"),
        "tcp_ecn": read("/proc/sys/net/ipv4/tcp_ecn"),
    }


def incast_once(n: int, nbytes: int) -> dict:
    """One N:1 incast over loopback TCP. Returns per-flow FCT (s) and bytes, and the incast completion time."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(n)
    port = srv.getsockname()[1]
    go = threading.Event()
    t_go = [0.0]
    recv = {}

    def reader(conn, idx):
        got, buf = 0, bytearray(CHUNK)
        view = memoryview(buf)
        while True:
            k = conn.recv_into(view)
            if not k:
                break
            got += k
        recv[idx] = (got, time.perf_counter())
        conn.close()

    def acceptor():
        threads = []
        for i in range(n):
            conn, _ = srv.accept()
            th = threading.Thread(target=reader, args=(conn, i))
            th.start()
            threads.append(th)
        for th in threads:
            th.join()

    payload = memoryview(bytes(CHUNK))

    def sender(sock):
        go.wait()
        left = nbytes
        while left > 0:
            k = min(left, CHUNK)
            sock.sendall(payload[:k])
            left -= k
        sock.shutdown(socket.SHUT_WR)
        sock.close()

    acc = threading.Thread(target=acceptor)
    acc.start()
    socks = [socket.create_connection(("127.0.0.1", port)) for _ in range(n)]
    senders = [threading.Thread(target=sender, args=(s,)) for s in socks]
    for th in senders:
        th.start()
    time.sleep(0.01)
    t_go[0] = time.perf_counter()
    go.set()
    for th in senders:
        th.join()
    acc.join()
    srv.close()
    fct = [recv[i][1] - t_go[0] for i in range(n)]
    return {"fct_s": fct, "bytes": [recv[i][0] for i in range(n)], "completion_s": max(fct)}


def jain(x: list[float]) -> float:
    return sum(x) ** 2 / (len(x) * sum(v * v for v in x)) if x and any(x) else 0.0


def pct(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, round(q * (len(s) - 1)))]


def run(ctx) -> dict:
    import pandas as pd  # noqa: PLC0415

    pr = probe()
    nbytes = (32 if ctx.quick else 128) << 20
    ns = [1, 2, 4, 8]
    reps = ctx.reps(10)
    rows, snaps, raw = [], [], []
    mod, src = load_l1("congestion_lab")
    for n in ns:
        incast_once(n, nbytes // 8)  # warm-up (connection setup, page cache, thread pools)
        snaps.append({"run": f"N{n}", **snapshot()})
        reps_out = [incast_once(n, nbytes) for _ in range(reps)]
        snaps.append({"run": f"N{n}", **snapshot()})
        flow_gbps = [nbytes * 8 / f / 1e9 for r in reps_out for f in r["fct_s"]]
        fct = [f for r in reps_out for f in r["fct_s"]]
        comp = [r["completion_s"] for r in reps_out]
        agg = [n * nbytes * 8 / r["completion_s"] / 1e9 for r in reps_out]
        jn = [jain([nbytes * 8 / f / 1e9 for f in r["fct_s"]]) for r in reps_out]
        lost = sum(nbytes * n - sum(r["bytes"]) for r in reps_out)
        rows.append({"senders": n, "reps": reps, "flow_gbps_median": statistics.median(flow_gbps),
                     "flow_gbps_p5": pct(flow_gbps, 0.05), "fct_ms_median": statistics.median(fct) * 1e3,
                     "fct_ms_p95": pct(fct, 0.95) * 1e3, "fct_ms_p99": pct(fct, 0.99) * 1e3,
                     "completion_ms_median": statistics.median(comp) * 1e3, "aggregate_gbps_median": statistics.median(agg),
                     "jain_median": statistics.median(jn), "jain_min": min(jn), "bytes_missing": lost})
        raw.append({"senders": n, "fct_s": [r["fct_s"] for r in reps_out]})
        ctx.log(f"N={n}: per-flow {rows[-1]['flow_gbps_median']:.1f} Gb/s, aggregate {rows[-1]['aggregate_gbps_median']:.1f} "
                f"Gb/s, FCT p99 {rows[-1]['fct_ms_p99']:.1f} ms, Jain {rows[-1]['jain_median']:.3f}")

    # counters -> rates with the lab's own function (one group per run, two samples each)
    sdf = pd.DataFrame(snaps)
    counter_cols = [c for c in sdf.columns if c not in ("run", "ts_s")]
    rates_tbl, rate_src = [], None
    if mod is not None:
        try:
            rates = mod.counters_to_rates(sdf, ["run"], counter_cols)
            rate_src = src
            for _, r in rates.dropna(subset=[f"{counter_cols[0]}_rate"]).iterrows():
                rates_tbl.append({"run": r["run"], **{c: round(float(r[f"{c}_rate"]), 2) for c in counter_cols}})
        except Exception as exc:  # noqa: BLE001 - starter TODO
            rate_src = f"counters_to_rates not available ({type(exc).__name__})"
    deltas = {c: int(sdf[c].iloc[-1] - sdf[c].iloc[0]) for c in counter_cols}

    sim_rows, sim_src = [], None
    if mod is not None:
        try:
            import yaml  # noqa: PLC0415
            sim = yaml.safe_load((PKG / "lab" / "data" / "sim_configs.yaml").read_text(encoding="utf-8"))
            t0 = time.perf_counter()
            df = mod.compare_configs(sim)
            sim_src = f"{src}: compare_configs ({time.perf_counter() - t0:.1f} s)"
            for name, r in df.iterrows():
                sim_rows.append({"config": name, "completion_us": float(r["completion_us"]),
                                 "peak_queue_kb": float(r["peak_queue_kb"]), "pause_time_us": float(r["pause_time_us"]),
                                 "dropped_bytes": float(r["dropped_bytes"]), "cnps": float(r["cnps"])})
        except Exception as exc:  # noqa: BLE001
            sim_src = f"simulation not available ({type(exc).__name__})"

    one, big = rows[0], rows[-1]
    metrics = {
        "tcp_congestion_control": pr["tcp_congestion_control"], "tcp_ecn": pr["tcp_ecn"],
        "rdma_devices": len(pr["rdma_devices"]), "burst_mib_per_sender": nbytes >> 20,
        "flow_gbps_n1": round(one["flow_gbps_median"], 2), f"flow_gbps_n{big['senders']}": round(big["flow_gbps_median"], 2),
        "aggregate_gbps_n1": round(one["aggregate_gbps_median"], 2),
        f"aggregate_gbps_n{big['senders']}": round(big["aggregate_gbps_median"], 2),
        f"fct_p99_ms_n{big['senders']}": round(big["fct_ms_p99"], 2),
        f"jain_median_n{big['senders']}": round(big["jain_median"], 4),
        "retrans_segs_delta": deltas.get("Tcp.RetransSegs"), "ce_marked_pkts_delta": deltas.get("IpExt.InCEPkts"),
        "ect0_pkts_delta": deltas.get("IpExt.InECT0Pkts"),
    }
    not_runnable = [
        {"part": "RDMA NIC congestion counters (PFC pause, np_cnp_sent, rp_cnp_handled, np_ecn_marked_roce_packets) "
                 "sampled 60 s apart", "needs": ["an RDMA-capable NIC (mlx5-class or similar)", "ethtool / rdma-core",
                                                 "a real netdev (the harness runs with --network none)"], "probe": pr},
        {"part": "L3 N:1 RDMA incast with switch queue watermarks, ECN threshold A/B on a lab leaf",
         "needs": [">= 4 hosts with RoCEv2 NICs on one lab leaf", "switch CLI/telemetry access", "perftest"],
         "probe": "not applicable to a single host"},
    ]
    notes = [
        f"Incast: N sender threads each send {nbytes >> 20} MiB over loopback TCP to one receiver; 1 warm-up (1/8 size) and "
        f"{reps} timed repetitions per N; FCT measured at the receiver from a common start.",
        "Loopback has no egress queue, no ECN marking and no PFC: the shared bottleneck is the receiver's CPU and socket "
        "stack. Treat the numbers as host-stack behaviour, not fabric behaviour.",
        f"Counter rates: {rate_src or 'not computed'}. Simulation: {sim_src or 'not run'}.",
    ]
    return {"metrics": metrics, "tables": {"incast": rows, "counter_rates": rates_tbl, "counter_deltas": [deltas],
                                           "simulated_incast": sim_rows, "probe": [pr], "raw_fct": raw},
            "notes": notes, "not_runnable_parts": not_runnable}


def check(result: dict, env: dict) -> list[str]:
    t, m = result["tables"], result["metrics"]
    fails = []
    rows = t["incast"]
    for r in rows:
        if r["bytes_missing"]:
            fails.append(f"N={r['senders']}: {r['bytes_missing']} bytes missing: TCP delivers every byte, so the receiver "
                         "loop or the byte accounting is wrong")
        if not 0 < r["jain_min"] <= 1.000001:
            fails.append(f"N={r['senders']}: Jain index {r['jain_min']} outside (0, 1]")
        if r["reps"] < 5:
            fails.append("fewer than 5 repetitions")
    if rows[-1]["completion_ms_median"] <= rows[0]["completion_ms_median"]:
        fails.append("the N-sender incast finished no later than a single flow carrying 1/N of the bytes: the receiver "
                     "cannot be the bottleneck, check the timing start point")
    if rows[-1]["flow_gbps_median"] > 1.1 * rows[0]["flow_gbps_median"]:
        fails.append("per-flow bandwidth rose with more senders sharing one receiver: check the per-flow FCT computation")
    for r in t["counter_rates"]:
        if any(v < 0 for k, v in r.items() if k != "run"):
            fails.append("negative counter rate: counters_to_rates must return NaN, never a negative rate")
    if m["ce_marked_pkts_delta"] not in (None, 0):
        fails.append("CE-marked packets on loopback: nothing on this path marks ECN, so the counter source is wrong")
    return fails


def tail_lines(rows: list[dict], d: dict) -> list[str]:
    """A data-driven note when some N shows a p99 FCT far above its median (the incast tail)."""
    worst = max(rows, key=lambda r: r["fct_ms_p99"] / max(r["fct_ms_median"], 1e-9))
    ratio = worst["fct_ms_p99"] / max(worst["fct_ms_median"], 1e-9)
    if ratio < 3:
        return [f"- The FCT tail stayed within {ratio:.1f}x of the median at every N: no retransmission-driven tail on this run."]
    causes = {k.split(".")[1]: v for k, v in d.items() if k.split(".")[1] in
              ("RetransSegs", "TCPTimeouts", "TCPLossProbes", "TCPBacklogDrop", "TCPRcvQDrop", "TCPSpuriousRTOs") and v}
    return [f"- At N={worst['senders']} the p99 FCT ({worst['fct_ms_p99']:.0f} ms) is {ratio:.0f}x the median: one flow in the "
            f"tail sets the incast's completion. Counters that moved during the runs: "
            f"{', '.join(f'{k} {v:+d}' for k, v in causes.items()) or 'none'}. Attribute a tail with counters like these, "
            "never by guessing; on a lossless RoCE fabric the equivalent evidence is pause duration and CNP rates."]


def report(result: dict, env: dict) -> str:
    t, m = result["tables"], result["metrics"]
    pr = t["probe"][0]
    lines = ["## Host congestion-control configuration (read now)", "",
             f"TCP congestion control **{pr['tcp_congestion_control']}** (available: {pr['tcp_available_congestion_control']}); "
             f"`tcp_ecn` = **{pr['tcp_ecn']}** (0 off, 1 request ECN, 2 accept ECN only when the peer requests it). "
             f"RDMA devices: {len(pr['rdma_devices'])}; interfaces: {pr['netdevs']}.", "",
             "## N:1 incast on loopback `[MEASURED, host stack only]`", "",
             "| Senders | Per-flow Gb/s (median) | Per-flow p5 | FCT median (ms) | FCT p95 | FCT p99 | Incast completion (ms) | "
             "Aggregate Gb/s | Jain (median / min) |", "|---|---|---|---|---|---|---|---|---|"]
    for r in t["incast"]:
        lines.append(f"| {r['senders']} | {r['flow_gbps_median']:.1f} | {r['flow_gbps_p5']:.1f} | {r['fct_ms_median']:.1f} | "
                     f"{r['fct_ms_p95']:.1f} | {r['fct_ms_p99']:.1f} | {r['completion_ms_median']:.1f} | "
                     f"{r['aggregate_gbps_median']:.1f} | {r['jain_median']:.3f} / {r['jain_min']:.3f} |")
    d = t["counter_deltas"][0]
    lines += ["", "Counter deltas over all runs: " + ", ".join(f"{k} {v:+d}" for k, v in sorted(d.items())) + ".", ""]
    if t["counter_rates"]:
        cols = [c for c in t["counter_rates"][0] if c != "run"]
        lines += ["Counter rates per run (events/s, via the lab's `counters_to_rates`):", "",
                  "| Run | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
        for r in t["counter_rates"]:
            lines.append(f"| {r['run']} | " + " | ".join(f"{r[c]:.0f}" for c in cols) + " |")
    if t["simulated_incast"]:
        lines += ["", "## The lab's 400 Gb/s incast model for comparison `[SIMULATED]`", "",
                  "| Config | Completion (us) | Peak queue (KB) | Pause time (us) | Dropped bytes | CNPs |", "|---|---|---|---|---|---|"]
        for r in t["simulated_incast"]:
            lines.append(f"| {r['config']} | {r['completion_us']:.0f} | {r['peak_queue_kb']:.0f} | {r['pause_time_us']:.0f} | "
                         f"{r['dropped_bytes']:.0f} | {r['cnps']:.0f} |")
    big = t["incast"][-1]
    lines += ["", "What to conclude:", "",
              f"- With {big['senders']} senders sharing one receiver, each flow got {big['flow_gbps_median']:.1f} Gb/s against "
              f"{t['incast'][0]['flow_gbps_median']:.1f} Gb/s alone, and the p99 FCT is the number a collective waits for. "
              "Report per-flow percentiles and fairness, never only the aggregate.",
              f"- ECN-capable packets {m['ect0_pkts_delta']}, CE marks {m['ce_marked_pkts_delta']}, retransmits "
              f"{m['retrans_segs_delta']}: with `tcp_ecn={pr['tcp_ecn']}` and no marking queue, nothing on this path can "
              "signal congestion early. On a RoCE fabric that signal is ECN at the switch and CNPs at the NIC; reading "
              "those counters as rates is exactly what the L2 extension asks for once an RDMA NIC is present.",
              *tail_lines(t["incast"], d),
              "- This is a laptop in a WSL2 container: loopback has no switch buffer, so queue build-up, PFC pauses and the "
              "ECN-threshold effect in the simulated table cannot be measured here. Those need the L3 lab fabric."]
    lines += ["", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}.")
    return "\n".join(lines)
