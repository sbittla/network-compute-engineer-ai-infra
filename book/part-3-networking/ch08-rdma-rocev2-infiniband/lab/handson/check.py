#!/usr/bin/env python3
"""Check a Chapter 8 hands-on evidence bundle: complete, internally consistent and physically sensible.

    python check.py results/<run-id>

Prints one PASS / FAIL / SKIP line per check and exits 0 only if no check fails. Standard library only;
it re-derives the numbers from the raw outputs (via ch08_analyze's parsers) rather than trusting
summary.json, then confirms summary.json agrees.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ch08_analyze import analyze, gid_ipv4  # noqa: E402

FILES = ["environment.json", "summary.json", "report.md", "counters-final.txt",
         "step1-device/ibv_devinfo-v.txt", "step1-device/rdma-link.txt", "step2-gids/gid-table.txt",
         "step2-gids/rc_pingpong.client.txt", "step3-bandwidth/ibv_devinfo-netdev1500.txt",
         "step3-bandwidth/ibv_devinfo-netdev9000.txt", "step3-bandwidth/pkts_netdev1500.counters.txt",
         "step3-bandwidth/pkts_netdev9000.counters.txt", "step3-bandwidth/rdma-res-qp.txt",
         "step4-latency/write_lat.client.txt", "step4-latency/read_lat.client.txt", "step4-latency/send_lat.client.txt",
         "step5-mtu/netdev1500_ask4096.client.txt", "step6-failures/wrong_device.client.txt",
         "step6-failures/no_server.client.txt", "step6-failures/gid7_client_only.client.txt",
         "step6-failures/gid7_both.client.txt", "step6-failures/gid0_linklocal.client.txt",
         "step7-ack-timeout/u14.samples.csv", "step7-ack-timeout/u16.samples.csv",
         "step7-ack-timeout/cm_retry3.events.txt", "step7-ack-timeout/cm_retry3.client.txt"]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run = Path(sys.argv[1])
    results: list[tuple[str, str, str]] = []

    def check(name: str, fn) -> None:
        try:
            msg = fn()
            results.append(("SKIP" if msg.startswith("SKIP:") else "PASS", name, msg.removeprefix("SKIP: ")))
        except AssertionError as e:
            results.append(("FAIL", name, str(e)))
        except Exception as e:  # noqa: BLE001
            results.append(("FAIL", name, f"{type(e).__name__}: {e}"))

    missing = [f for f in FILES if not (run / f).is_file()]
    bw_files = {m: sorted((run / "step3-bandwidth").glob(f"write_bw_netdev{m}_rep*.client.txt")) for m in (1500, 9000)}
    mtu_files = sorted((run / "step5-mtu").glob("path_mtu*_rep*.client.txt"))
    if any(len(v) < 2 for v in bw_files.values()):
        missing.append("step3-bandwidth/write_bw_netdev*_rep*.client.txt (need >= 2 repetitions per MTU)")
    if len(mtu_files) < 5:
        missing.append("step5-mtu/path_mtu*_rep*.client.txt (need all five path MTUs)")
    check("bundle_complete", lambda: (_ for _ in ()).throw(AssertionError(f"missing {', '.join(missing)} in {run}"))
          if missing else f"all {len(FILES)} files present, plus {sum(map(len, bw_files.values()))} bandwidth sweeps")
    if missing:
        return report(results)

    S = analyze(run)
    s1, s2, s3, s4, s5, s6, s7 = (S[f"step{i}"] for i in range(1, 8))
    env = json.loads((run / "environment.json").read_text(encoding="utf-8"))

    def c_env():
        assert env.get("captured_at") and env.get("kernel"), "environment.json lacks captured_at or kernel"
        return f"kernel {env['kernel']}, {env.get('cpus')} CPUs"
    check("environment", c_env)

    def c_device():
        assert s1["state"] == "ACTIVE", f"rdma link state {s1['state']!r}, expected ACTIVE"
        assert s1["link_layer"] == "Ethernet", f"link_layer {s1['link_layer']!r}: a RoCE device reports Ethernet"
        assert s1["transport"] and s1["transport"].startswith("InfiniBand"), \
            f"transport {s1['transport']!r}: verbs devices report InfiniBand (0) even on RoCE"
        return f"{s1['device']} on {s1['netdev']}: ACTIVE, transport {s1['transport']}, link_layer Ethernet"
    check("device_up", c_device)

    def c_active_mtu():
        a, b = s1["active_mtu_netdev1500"], s1["active_mtu_netdev9000"]
        assert a == 1024, f"active_mtu at netdev MTU 1500 is {a}; 2048 + RoCE headers does not fit in 1500, expected 1024"
        assert b == 4096, f"active_mtu at netdev MTU 9000 is {b}, expected 4096"
        return "active_mtu 1024 at netdev 1500, 4096 at netdev 9000 (Section 8.6)"
    check("active_mtu_follows_netdev", c_active_mtu)

    def c_gid():
        i, g, t = s2["ipv4_gid_index"], s2["ipv4_gid"], s2["ipv4_gid_type"]
        assert i is not None, "no IPv4-mapped GID in gid-table.txt"
        assert gid_ipv4(g) == "10.208.0.1", f"IPv4-mapped GID {g} decodes to {gid_ipv4(g)}, expected 10.208.0.1"
        assert t == "RoCE v2", f"GID {i} has type {t!r}, expected RoCE v2"
        assert any(x.startswith("fe80") for x in (d["gid"] for d in s2["gids"])), "no link-local fe80 GID"
        return f"index {i} = {g} (10.208.0.1), RoCE v2; types present: {', '.join(s2['types'])}"
    check("gid_table", c_gid)

    def c_pingpong():
        assert s2["rc_pingpong_rc"] == 0, f"ibv_rc_pingpong client rc {s2['rc_pingpong_rc']}"
        u = s2["rc_pingpong_usec_per_iter"]
        assert u and 0.5 < u < 10_000, f"implausible {u} usec/iter"
        return f"{u} usec/iter over 1000 RC ping-pongs"
    check("rc_pingpong", c_pingpong)

    def c_bw():
        out = []
        for m, mtu in ((1500, 1024), (9000, 4096)):
            c = s3[f"netdev{m}"]
            assert c["path_mtu"] == mtu, f"netdev {m}: perftest path MTU {c['path_mtu']}, expected {mtu}"
            assert c["sizes"] >= 20, f"netdev {m}: only {c['sizes']} sizes in the -a sweep"
            p = c["plateau_gbps"]
            assert 0.05 < p < 400, f"netdev {m}: plateau {p} Gb/s is not plausible for software RDMA"
            curve = {int(k): v for k, v in c["curve_gbps"].items()}
            assert curve[2] < p / 20, f"netdev {m}: 2-byte BW {curve[2]} Gb/s is not far below the plateau {p}"
            assert c["n_half_bytes"] >= 256, f"netdev {m}: n_half {c['n_half_bytes']} B is implausibly small"
            out.append(f"MTU {mtu}: plateau {p} Gb/s, n_half {c['n_half_bytes']} B")
        a, b = s3["netdev1500"]["plateau_gbps"], s3["netdev9000"]["plateau_gbps"]
        assert b > 1.2 * a, f"path MTU 4096 plateau {b} not clearly above MTU 1024 plateau {a}: per-packet cost should dominate rxe"
        return "; ".join(out)
    check("bandwidth_sweep", c_bw)

    def c_pkts():
        a, b = s3["netdev1500"].get("sent_pkts_per_64KiB_write"), s3["netdev9000"].get("sent_pkts_per_64KiB_write")
        assert a and b, "packet counters missing"
        assert 64 <= a <= 64 * 2 + 1, f"{a} packets per 64 KiB WRITE at MTU 1024; expected 64 data packets plus ACKs"
        assert 16 <= b <= 16 * 2 + 1, f"{b} packets per 64 KiB WRITE at MTU 4096; expected 16 data packets plus ACKs"
        return f"{a} packets per 64 KiB WRITE at path MTU 1024, {b} at 4096 (data + ACKs; loopback counts both)"
    check("packets_per_message", c_pkts)

    def c_qp():
        qps = s3["qp_snapshot"]
        rc = [q for q in qps if q.get("type") == "RC"]
        assert len(rc) >= 2, f"expected two RC QPs (client and server) in rdma resource, got {qps}"
        pair = [q for q in rc if any(p.get("lqpn") == q.get("rqpn") and p.get("rqpn") == q.get("lqpn") for p in rc)]
        assert len(pair) >= 2, f"no two RC QPs name each other as remote QPN: {rc}"
        states = sorted(q.get("state") for q in pair)
        assert "RTS" in states, f"QP states {states}: the WRITE requester must be in RTS"
        assert all(s in ("RTR", "RTS") for s in states), f"QP states {states}: expected RTR or RTS while connected"
        return f"connected RC pair lqpn {pair[0]['lqpn']}<->{pair[1]['lqpn']}, states {states}"
    check("qp_state", c_qp)

    def c_lat():
        w, r, s = (s4[t]["typical_2B_us"] for t in ("write_lat", "read_lat", "send_lat"))
        assert all(x and 0.5 < x < 5000 for x in (w, r, s)), f"implausible 2 B latencies WRITE {w}, READ {r}, SEND {s} µs"
        for t in ("write_lat", "read_lat", "send_lat"):
            assert s4[t]["typical_8MiB_us"] > 10 * s4[t]["typical_2B_us"], f"{t}: 8 MiB not slower than 2 B?"
        return f"2 B typical: WRITE {w} µs, READ {r} µs, SEND {s} µs; 8 MiB READ {s4['read_lat']['typical_8MiB_us']} µs"
    check("latency_sweep", c_lat)

    def c_mtu():
        rows = {p["requested"]: p for p in s5["path_mtu"]}
        assert set(rows) == {256, 512, 1024, 2048, 4096}, f"path MTUs present: {sorted(rows)}"
        for k, p in rows.items():
            assert p["reported"] == [k], f"asked for path MTU {k}, perftest reported {p['reported']}"
        assert rows[4096]["gbps_median"] > 2 * rows[256]["gbps_median"], \
            f"4096 B ({rows[4096]['gbps_median']} Gb/s) is not > 2x 256 B ({rows[256]['gbps_median']} Gb/s)"
        clamp = s5["netdev1500_ask4096"]["reported_mtu"]
        assert clamp == 1024, f"-m 4096 at netdev MTU 1500 gave path MTU {clamp}; expected the 1024 clamp"
        return "; ".join(f"{k}: {p['gbps_median']} Gb/s" for k, p in sorted(rows.items())) + "; -m 4096 at netdev 1500 -> 1024"
    check("path_mtu", c_mtu)

    def c_fail():
        out = []
        for case in ("wrong_device", "no_server", "gid7_client_only", "gid7_both"):
            d = s6[case]
            assert d["rc"] not in (0, None), f"{case}: client rc {d['rc']}, expected a failure"
            assert d["signature_found"], f"{case}: error text /{d['signature']}/ not found"
            out.append(f"{case} rc {d['rc']}")
        return "; ".join(out)
    check("failure_signatures", c_fail)

    def c_memlock():
        m = s6["memlock"]
        need = {"memlock_nobody_4096", "memlock_nobody_65536", "memlock_root_4096"}
        assert need <= set(m), f"missing memlock cases {sorted(need - set(m))}"
        assert m["memlock_nobody_4096"]["mr_failed"], "8 MiB registration under a 4 MiB limit (uid 65534) did not fail"
        assert not m["memlock_nobody_4096"]["completed"], "client completed although the server's MR failed"
        assert m["memlock_nobody_65536"]["completed"], "8 MiB registration under a 64 MiB limit did not complete"
        assert m["memlock_root_4096"]["completed"] and m["memlock_root_4096"]["uid"] == 0, \
            "root (CAP_IPC_LOCK) under a 4 MiB limit should register 8 MiB"
        lims = sorted((v["limit_kib"], v["mr_failed"]) for k, v in m.items() if k.startswith("memlock_nobody"))
        fails = [l for l, f in lims if f]
        oks = [l for l, f in lims if not f]
        assert max(fails) < min(oks), f"failures are not below successes: {lims}"
        return f"uid 65534: MR fails at {fails} KiB, succeeds at {oks} KiB; root succeeds at 4096 KiB"
    check("memlock", c_memlock)

    def c_timeout():
        out = []
        for u in (14, 16):
            d = s7[f"u{u}"]
            iv, model = d.get("mean_interval_s"), d["t_ack_model_s"]
            assert iv, f"timeout={u}: no retransmission timeouts measured after the responder died"
            assert 0.7 * model < iv < 1.5 * model, \
                f"timeout={u}: mean retry interval {iv} s vs model 4.096 us x 2^{u} = {model} s"
            out.append(f"timeout={u}: {iv} s (model {model} s, {d['retries']} retries)")
        a, b = s7["u14"]["mean_interval_s"], s7["u16"]["mean_interval_s"]
        assert 2.5 < b / a < 6, f"interval ratio {b / a:.2f} for timeout 16 vs 14; expected about 4"
        return "; ".join(out)
    check("ack_timeout_interval", c_timeout)

    def c_retry_exc():
        c = s7.get("cm_retry3")
        assert c, "cm_retry3 events missing"
        assert c["client_rc"] != 0, "client exited 0 after its peer died"
        assert c["wc_status"] == 12, f"completion status {c['wc_status']}, expected 12 (IBV_WC_RETRY_EXC_ERR)"
        assert c["retry_exceeded_delta"] >= 1, "retry_exceeded_err did not increase"
        assert 0.05 < c["time_to_fail_s"] < 60, f"time to failure {c['time_to_fail_s']} s"
        return f"status 12 after {c['time_to_fail_s']} s = 4 x {c['implied_t_ack_s']} s"
    check("retry_exceeded", c_retry_exc)

    def c_summary():
        on_disk = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        for k in ("step1", "step2", "step3", "step5", "step6", "step7"):
            assert json.dumps(on_disk.get(k), sort_keys=True) == json.dumps(S[k], sort_keys=True), \
                f"summary.json {k} differs from what the raw outputs give; re-run ch08_analyze.py"
        rep = (run / "report.md").read_text(encoding="utf-8")
        assert rep.count("[MEASURED]") >= 10, "report.md has fewer than 10 [MEASURED] labels"
        assert not any(isinstance(v, float) and math.isnan(v) for v in S["step3"]["netdev9000"].values()), "NaN in summary"
        return "summary.json matches the raw outputs; report.md labelled"
    check("summary_consistent", c_summary)

    return report(results)


def report(results: list[tuple[str, str, str]]) -> int:
    for status, name, msg in results:
        print(f"{status} {name}: {msg}")
    failed = sum(1 for s, _, _ in results if s == "FAIL")
    passed = sum(1 for s, _, _ in results if s == "PASS")
    print(f"\n{passed}/{len(results)} checks passed" + (f", {failed} failed" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
