#!/usr/bin/env python3
"""Summarize a Chapter 8 hands-on run: parse the raw perftest, ibv_devinfo, sysfs and counter outputs.

    python3 ch08_analyze.py results/<run-id>      # writes summary.json and report.md into the run

Standard library only. check.py imports the parsers below and re-derives the numbers from the raw files.
"""
from __future__ import annotations

import csv
import ipaddress
import json
import re
import statistics
import sys
from pathlib import Path

T_ACK_UNIT_S = 4.096e-6  # IBA local ACK timeout: 4.096 us x 2^timeout (Section 8.6)

# ------------------------------------------------------------------------------------------- parsers


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def perftest_mtu(text: str) -> int | None:
    m = re.search(r"Mtu\s*:\s*(\d+)\[B\]", text)
    return int(m.group(1)) if m else None


def bw_units(text: str) -> str | None:
    m = re.search(r"BW peak\[([A-Za-z/]+)\]", text)
    return m.group(1) if m else None


def parse_bw(text: str) -> list[dict]:
    """Rows of a perftest bandwidth table: bytes, iterations, BW peak, BW average, MsgRate[Mpps]."""
    rows = []
    for line in text.splitlines():
        f = line.split()
        if len(f) == 5 and f[0].isdigit() and f[1].isdigit():
            try:
                rows.append({"bytes": int(f[0]), "iters": int(f[1]), "peak": float(f[2]),
                             "avg": float(f[3]), "mpps": float(f[4])})
            except ValueError:
                pass
    return rows


def parse_lat(text: str) -> list[dict]:
    """Rows of a perftest latency table (usec): bytes, iters, min, max, typical, avg, stdev, p99, p99.9."""
    rows = []
    for line in text.splitlines():
        f = line.split()
        if len(f) == 9 and f[0].isdigit() and f[1].isdigit():
            try:
                v = [float(x) for x in f[2:]]
            except ValueError:
                continue
            rows.append({"bytes": int(f[0]), "iters": int(f[1]), "t_min": v[0], "t_max": v[1],
                         "t_typical": v[2], "t_avg": v[3], "t_stdev": v[4], "p99": v[5], "p999": v[6]})
    return rows


def parse_devinfo(text: str) -> dict:
    out = {}
    for key in ("transport", "fw_ver", "node_guid", "vendor_id", "state", "max_mtu", "active_mtu", "link_layer",
                "max_qp", "max_mr", "max_mr_size", "phys_port_cnt"):
        m = re.search(rf"^\s*{key}:\s*(.+?)\s*$", text, re.M)
        if m:
            out[key] = m.group(1)
    for key in ("max_mtu", "active_mtu"):
        if key in out:
            out[key + "_bytes"] = int(out[key].split()[0])
    return out


def parse_gid_table(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines()[1:]:
        f = line.split()
        if len(f) >= 3 and f[0].isdigit():
            rows.append({"index": int(f[0]), "gid": f[1], "type": f[2].replace("_", " "),
                         "ndev": f[3] if len(f) > 3 else ""})
    return rows


def gid_ipv4(gid: str) -> str | None:
    """IPv4 address inside an IPv4-mapped GID (::ffff:a.b.c.d), else None."""
    try:
        a = ipaddress.IPv6Address(gid)
    except ValueError:
        return None
    return str(a.ipv4_mapped) if a.ipv4_mapped else None


def parse_rdma_stats(text: str) -> dict[str, int]:
    return {k: int(v) for k, v in re.findall(r"\b([a-z_]+) (\d+)\b", text)}


def parse_qp_line(line: str) -> dict[str, str]:
    """`rdma resource show qp` line: key value pairs after 'link <dev>/<port>'."""
    f = line.split()
    return dict(zip(f[2::2], f[3::2]))


def kv(text: str) -> dict[str, str]:
    return dict(re.findall(r"(\w+)=(\S+)", text))


def rc_of(p: Path) -> list[int]:
    return [int(x) for x in read(p).split()] if p.is_file() else []


# ------------------------------------------------------------------------------------------- analysis

SIGNATURES = {
    "wrong_device": r"IB device mlx5_0 not found",
    "no_server": r"Couldn't connect to 10\.208\.0\.1:\d+",
    "gid7_client_only": r"Incompatibility issue with GID types",
    "gid7_both": r"Failed to modify QP \S+ to RTR",
}


def bw_curve(files: list[Path]) -> dict:
    """Median-of-repetitions BW average per size (Gb/s), plateau, n_half and small-message rate."""
    per_size: dict[int, list[float]] = {}
    rate2: list[float] = []
    for f in files:
        t = read(f)
        assert bw_units(t) == "Gb/sec", f"{f.name}: expected --report_gbits output"
        for r in parse_bw(t):
            per_size.setdefault(r["bytes"], []).append(r["avg"])
            if r["bytes"] == 2:
                rate2.append(r["mpps"])
    curve = {s: statistics.median(v) for s, v in sorted(per_size.items())}
    if not curve:
        return {"sizes": 0}
    plateau_size = max(curve, key=curve.get)
    plateau = curve[plateau_size]
    n_half = min(s for s, v in curve.items() if v >= plateau / 2)
    spread = per_size[plateau_size]
    return {"sizes": len(curve), "reps": len(files), "curve_gbps": {str(k): round(v, 3) for k, v in curve.items()},
            "plateau_gbps": round(plateau, 3), "plateau_size": plateau_size,
            "plateau_min_max_gbps": [min(spread), max(spread)], "n_half_bytes": n_half,
            "bw_8MiB_gbps": round(curve.get(8388608, float("nan")), 3),
            "msg_rate_2B_mpps": round(statistics.median(rate2), 4) if rate2 else None}


def implied_interval(samples: Path, kill_t: float) -> dict:
    """Mean time between retransmission timeouts after the responder was killed."""
    rows = list(csv.DictReader(open(samples))) if samples.is_file() else []
    pts = [(float(r["t_s"]), int(r["completer_retry_err"])) for r in rows if r["completer_retry_err"]]
    if len(pts) < 3:
        return {"retries": 0}
    c0 = pts[0][1]
    changes = [(t, c) for (t, c), (_, prev) in zip(pts[1:], pts[:-1]) if c != prev]
    if len(changes) < 3:
        return {"retries": pts[-1][1] - c0}
    (t_first, c_first), (t_last, c_last) = changes[0], changes[-1]
    return {"retries": pts[-1][1] - c0, "first_retry_after_kill_s": round(t_first - kill_t, 3),
            "mean_interval_s": round((t_last - t_first) / (c_last - c_first), 4),
            "retry_exceeded_delta": int(rows[-1]["retry_exceeded_err"]) - int(rows[0]["retry_exceeded_err"])}


def analyze(run: Path) -> dict:
    s1, s2, s3, s4, s5, s6, s7 = (run / d for d in ("step1-device", "step2-gids", "step3-bandwidth",
                                                     "step4-latency", "step5-mtu", "step6-failures",
                                                     "step7-ack-timeout"))
    S: dict = {}
    dev = parse_devinfo(read(s1 / "ibv_devinfo-v.txt"))
    link = read(s1 / "rdma-link.txt")
    m = re.search(r"link (\S+)/1 state (\S+) physical_state (\S+) netdev (\S+)", link)
    S["step1"] = {"device": m.group(1) if m else None, "state": m.group(2) if m else None,
                  "netdev": m.group(4) if m else None, "transport": dev.get("transport"),
                  "link_layer": dev.get("link_layer"), "port_state": dev.get("state"),
                  "max_mtu": dev.get("max_mtu_bytes"), "fw_ver": dev.get("fw_ver"), "vendor_id": dev.get("vendor_id"),
                  "devices_before": [l for l in read(s1 / "ibv_devices-before.txt").splitlines()[1:] if l.strip()]}
    for mtu in (1500, 9000):
        S["step1"][f"active_mtu_netdev{mtu}"] = parse_devinfo(read(s3 / f"ibv_devinfo-netdev{mtu}.txt")).get("active_mtu_bytes")

    gids = parse_gid_table(read(s2 / "gid-table.txt"))
    v4 = [g for g in gids if gid_ipv4(g["gid"])]
    pp = read(s2 / "rc_pingpong.client.txt")
    pm = re.search(r"(\d+) iters in [\d.]+ seconds = ([\d.]+) usec/iter", pp)
    S["step2"] = {"gids": gids, "ipv4_gid_index": v4[0]["index"] if v4 else None,
                  "ipv4_gid": v4[0]["gid"] if v4 else None, "ipv4_gid_addr": gid_ipv4(v4[0]["gid"]) if v4 else None,
                  "ipv4_gid_type": v4[0]["type"] if v4 else None,
                  "types": sorted({g["type"] for g in gids}),
                  "rc_pingpong_rc": (rc_of(s2 / "rc_pingpong.rc") or [None])[0],
                  "rc_pingpong_usec_per_iter": float(pm.group(2)) if pm else None,
                  "rc_pingpong_gids": re.findall(r"GID (\S+)", pp)}

    S["step3"] = {}
    for mtu in (1500, 9000):
        files = sorted(s3.glob(f"write_bw_netdev{mtu}_rep*.client.txt"))
        c = bw_curve(files)
        c["path_mtu"] = perftest_mtu(read(files[0])) if files else None
        cnt = kv(read(s3 / f"pkts_netdev{mtu}.counters.txt"))
        if cnt:
            c["sent_pkts_per_64KiB_write"] = round((int(cnt["sent_pkts_after"]) - int(cnt["sent_pkts_before"]))
                                                   / int(cnt["messages"]), 2)
        S["step3"][f"netdev{mtu}"] = c
    qp = read(s3 / "rdma-res-qp.txt")
    S["step3"]["qp_snapshot"] = [parse_qp_line(l) for l in qp.splitlines() if l.startswith("link ")]

    S["step4"] = {}
    for t in ("write_lat", "read_lat", "send_lat"):
        rows = parse_lat(read(s4 / f"{t}.client.txt"))
        by = {r["bytes"]: r for r in rows}
        S["step4"][t] = {"sizes": len(rows), "typical_2B_us": by.get(2, {}).get("t_typical"),
                         "p99_2B_us": by.get(2, {}).get("p99"), "typical_64KiB_us": by.get(65536, {}).get("t_typical"),
                         "typical_8MiB_us": by.get(8388608, {}).get("t_typical")}
    w, r = S["step4"]["write_lat"]["typical_2B_us"], S["step4"]["read_lat"]["typical_2B_us"]
    S["step4"]["read_over_write_2B"] = round(r / w, 2) if w and r else None

    S["step5"] = {"path_mtu": []}
    for pmtu in (256, 512, 1024, 2048, 4096):
        files = sorted(s5.glob(f"path_mtu{pmtu}_rep*.client.txt"))
        bws = [parse_bw(read(f))[-1]["avg"] for f in files if parse_bw(read(f))]
        rep_mtu = {perftest_mtu(read(f)) for f in files}
        if bws:
            g = statistics.median(bws)
            S["step5"]["path_mtu"].append({"requested": pmtu, "reported": sorted(x for x in rep_mtu if x),
                                           "gbps_median": round(g, 3), "gbps_all": bws,
                                           "payload_pkts_per_s_M": round(g * 1e9 / 8 / pmtu / 1e6, 3)})
    clamp = read(s5 / "netdev1500_ask4096.client.txt")
    S["step5"]["netdev1500_ask4096"] = {"reported_mtu": perftest_mtu(clamp),
                                        "gbps": parse_bw(clamp)[-1]["avg"] if parse_bw(clamp) else None}

    S["step6"] = {}
    for case, pat in SIGNATURES.items():
        t = read(s6 / f"{case}.client.txt") + read(s6 / f"{case}.server.txt")
        S["step6"][case] = {"rc": (rc_of(s6 / f"{case}.rc") or [None])[0], "signature": pat,
                            "signature_found": bool(re.search(pat, t))}
    ll = read(s6 / "gid0_linklocal.client.txt")
    S["step6"]["gid0_linklocal"] = {"rc": (rc_of(s6 / "gid0_linklocal.rc") or [None])[0],
                                    "completed": bool(parse_bw(ll)), "gid_seen": re.findall(r"GID: (\S+)", ll)[:1]}
    mem = {}
    for f in sorted(s6.glob("memlock_*.server.txt")):
        case = f.name.removesuffix(".server.txt")
        srv, cli = read(f), read(s6 / f"{case}.client.txt")
        rcs = rc_of(s6 / f"{case}.rc")
        lim = re.search(r"ulimit -l = (\d+) KiB, uid (\d+)", srv)
        mem[case] = {"limit_kib": int(lim.group(1)) if lim else None, "uid": int(lim.group(2)) if lim else None,
                     "mr_failed": bool(re.search(r"Couldn't allocate MR|Failed to create MR", srv)),
                     "completed": bool(parse_bw(cli)), "server_rc": rcs[0] if rcs else None,
                     "client_rc": rcs[1] if len(rcs) > 1 else None,
                     "client_error": next((l.strip() for l in cli.splitlines()
                                           if re.search(r"Couldn't|Failed|Unable", l)), None)}
    S["step6"]["memlock"] = mem
    S["step6"]["dmesg_enomem_lines"] = len(re.findall(r"err = -12", read(s6 / "dmesg-rxe.txt")))

    S["step7"] = {}
    for u in (14, 16):
        ev = kv(read(s7 / f"u{u}.events.txt"))
        d = implied_interval(s7 / f"u{u}.samples.csv", float(ev.get("kill_t_s", "nan")))
        d["timeout"] = u
        d["t_ack_model_s"] = round(T_ACK_UNIT_S * 2 ** u, 4)
        d["client_alive_after_sampling"] = ev.get("client_alive_after_sampling")
        S["step7"][f"u{u}"] = d
    ev = kv(read(s7 / "cm_retry3.events.txt"))
    cli = read(s7 / "cm_retry3.client.txt")
    st = re.search(r"status\s*:?\s*(\d+)", cli, re.I) or re.search(r"Failed status (\d+)", cli)
    if ev:
        dt = float(ev["client_exit_t_s"]) - float(ev["kill_t_s"])
        S["step7"]["cm_retry3"] = {"time_to_fail_s": round(dt, 3), "client_rc": int(ev["client_rc"]),
                                   "wc_status": int(st.group(1)) if st else None,
                                   "retry_exceeded_delta": int(ev["retry_exceeded_after"]) - int(ev["retry_exceeded_before"]),
                                   "implied_t_ack_s": round(dt / 4, 4),
                                   "implied_timeout_exponent": round(__import__("math").log2(dt / 4 / T_ACK_UNIT_S), 2)}
    S["counters_final"] = parse_rdma_stats(read(run / "counters-final.txt"))
    return S


# ------------------------------------------------------------------------------------------- report


def report(S: dict, env: dict) -> str:
    M = "`[MEASURED]`"
    s1, s2, s3, s4, s5, s6, s7 = (S[f"step{i}"] for i in range(1, 8))
    b15, b90 = s3["netdev1500"], s3["netdev9000"]
    L = [f"# Chapter 8 hands-on: Soft-RoCE verbs on {env.get('cpu', 'this host')}", "",
         f"Kernel {env.get('kernel')}, {env.get('cpus')} CPUs; captured {env.get('captured_at')}. One rxe device "
         f"(`{s1['device']}`) on veth `{s1['netdev']}`; every test is server and client on this host. These are "
         "software-RDMA numbers on one CPU, not NIC or fabric numbers.", "",
         "| Step | Result | Label |", "|---|---|---|",
         f"| 1 Device | `{s1['device']}` {s1['state']}, transport `{s1['transport']}`, link_layer {s1['link_layer']}, "
         f"active_mtu {s1['active_mtu_netdev1500']} at netdev MTU 1500 and {s1['active_mtu_netdev9000']} at 9000 | {M} |",
         f"| 2 GID table | {len(s2['gids'])} entries, types {', '.join(s2['types'])}; IPv4-mapped RoCE v2 GID at index "
         f"**{s2['ipv4_gid_index']}** = `{s2['ipv4_gid']}` ({s2['ipv4_gid_addr']}); ibv_rc_pingpong "
         f"{s2['rc_pingpong_usec_per_iter']} µs/iter | {M} |",
         f"| 3 ib_write_bw, path MTU {b15['path_mtu']} | plateau {b15['plateau_gbps']} Gb/s at {b15['plateau_size']} B "
         f"(3 reps: {b15['plateau_min_max_gbps'][0]}–{b15['plateau_min_max_gbps'][1]}), n½ = {b15['n_half_bytes']} B, "
         f"2 B rate {b15['msg_rate_2B_mpps']} M msg/s, {b15.get('sent_pkts_per_64KiB_write')} packets per 64 KiB WRITE | {M} |",
         f"| 3 ib_write_bw, path MTU {b90['path_mtu']} | plateau {b90['plateau_gbps']} Gb/s at {b90['plateau_size']} B "
         f"(3 reps: {b90['plateau_min_max_gbps'][0]}–{b90['plateau_min_max_gbps'][1]}), n½ = {b90['n_half_bytes']} B, "
         f"2 B rate {b90['msg_rate_2B_mpps']} M msg/s, {b90.get('sent_pkts_per_64KiB_write')} packets per 64 KiB WRITE | {M} |",
         f"| 4 Latency, 2 B typical | WRITE {s4['write_lat']['typical_2B_us']} µs, READ {s4['read_lat']['typical_2B_us']} µs, "
         f"SEND {s4['send_lat']['typical_2B_us']} µs; READ/WRITE = {s4['read_over_write_2B']} | {M} |"]
    pm = "; ".join(f"{p['requested']} B → {p['gbps_median']} Gb/s ({p['payload_pkts_per_s_M']} M pkt/s)"
                   for p in s5["path_mtu"])
    L.append(f"| 5 Path MTU, 1 MiB WRITEs | {pm} | {M} (packet rate derived) |")
    L.append(f"| 5 Clamp | asked for 4096 at netdev MTU 1500, perftest used {s5['netdev1500_ask4096']['reported_mtu']} | {M} |")
    for case, label in (("wrong_device", "-d mlx5_0"), ("no_server", "no server"),
                        ("gid7_client_only", "client -x 7"), ("gid7_both", "both -x 7")):
        d = s6[case]
        L.append(f"| 6 {label} | rc {d['rc']}, signature `{d['signature']}` found: {d['signature_found']} | {M} |")
    L.append(f"| 6 -x 0 (link-local GID) | completed: {s6['gid0_linklocal']['completed']} (loopback only) | {M} |")
    mm = "; ".join(f"{k.removeprefix('memlock_')}: MR {'FAILED' if v['mr_failed'] else 'ok'}"
                   for k, v in s6["memlock"].items())
    L.append(f"| 6 Locked memory, 8 MiB buffer | {mm} | {M} |")
    for u in (14, 16):
        d = s7[f"u{u}"]
        L.append(f"| 7 Peer killed, timeout={u}, retry_cnt 7 | {d.get('retries')} retransmission timeouts, mean interval "
                 f"{d.get('mean_interval_s')} s (model {d['t_ack_model_s']} s); client still waiting: "
                 f"{d.get('client_alive_after_sampling')} | {M} |")
    c = s7.get("cm_retry3", {})
    L.append(f"| 7 Peer killed, rdma_cm, retry_cnt 3 | failed after {c.get('time_to_fail_s')} s with completion status "
             f"{c.get('wc_status')}; retry_exceeded_err +{c.get('retry_exceeded_delta')}; implied T_ack ≈ "
             f"{c.get('implied_t_ack_s')} s (timeout ≈ {c.get('implied_timeout_exponent')}) | {M} |")
    L += ["", "What carries over to ORION: the verbs objects, GID selection, the path-MTU arithmetic, the failure "
          "signatures and the ACK-timeout formula. What does not: every bandwidth and latency number above, which "
          "measure one CPU running the transport in software (no NIC, no PCIe, no switch, no PFC).", ""]
    return "\n".join(L)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run = Path(sys.argv[1])
    S = analyze(run)
    env = json.loads(read(run / "environment.json") or "{}")
    (run / "summary.json").write_text(json.dumps(S, indent=2) + "\n")
    (run / "report.md").write_text(report(S, env), encoding="utf-8")
    print(f"wrote {run / 'summary.json'} and {run / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
