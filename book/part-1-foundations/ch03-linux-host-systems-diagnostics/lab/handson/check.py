#!/usr/bin/env python3
"""Check a Chapter 3 hands-on results bundle for completeness and physical sense.

    python check.py results/<run-id>

Prints one PASS/FAIL line per check and exits 0 only if every check passes. Standard library only;
it reads the bundle and never touches the host. It tests mechanisms, not this machine's numbers: another
host gives other values and still passes if the mechanisms show.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

REQUIRED = [
    "environment.json", "summary.json", "report.md",
    "step1-collector/collector-root.log", "step1-collector/collector-nonroot.log", "step1-collector/triage-vs-orion-hx8.md",
    "step2-percpu/vmstat.txt", "step2-percpu/mpstat.txt", "step2-percpu/affinity.txt",
    "step3-pinning/bench.json", "step3-pinning/lscpu-e.txt",
    "step4-pagecache/pagecache.json", "step4-pagecache/free-before.txt",
    "step5-pinned/ulimit.txt", "step5-pinned/mlock.jsonl", "step5-pinned/pinned_copy.json",
    "step6-signals/dmesg.txt", "step6-signals/vmstat-overload.txt", "step6-signals/psi-before.txt", "step6-signals/psi-during.txt",
]


class Checker:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def run(self, name: str, fn) -> None:
        try:
            self.rows.append(("PASS", name, fn() or ""))
        except AssertionError as exc:
            self.rows.append(("FAIL", name, str(exc) or "assertion failed"))
        except Exception as exc:  # a malformed bundle must give a useful line, not a traceback
            tb = traceback.extract_tb(exc.__traceback__)[-1]
            self.rows.append(("FAIL", name, f"{type(exc).__name__}: {exc} (check.py:{tb.lineno})"))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    d = Path(sys.argv[1])
    C = Checker()
    sm: dict = {}

    def files():
        missing = [f for f in REQUIRED if not (d / f).is_file() or (d / f).stat().st_size == 0]
        assert not missing, f"missing or empty: {', '.join(missing)}"
        for mode in ("root", "nonroot"):
            assert list((d / "step1-collector" / mode).glob("hostdiag-*.json")), f"no collector snapshot for {mode}"
        return f"{len(REQUIRED)} files and both snapshots present"
    C.run("bundle complete", files)

    def load():
        nonlocal sm
        sm = json.loads((d / "summary.json").read_text(encoding="utf-8"))
        env = json.loads((d / "environment.json").read_text(encoding="utf-8"))
        for k in ("captured_at", "kernel", "cpu", "cpus", "mem_gib"):
            assert env.get(k) not in (None, ""), f"environment.json lacks {k}"
        for k in ("step1", "step2", "step3", "step4", "step5", "step6"):
            assert k in sm, f"summary.json lacks {k} (rerun summarize.py)"
        rep = (d / "report.md").read_text(encoding="utf-8")
        assert rep.count("[MEASURED]") >= 10, "report.md labels fewer than 10 numbers [MEASURED]"
        return f"{env['cpus']} CPUs, kernel {env['kernel']}"
    C.run("summary, environment and report", load)

    def s1():
        x = sm["step1"]
        r, n = x["root"], x["nonroot"]
        assert r and n, "collector did not produce both a root and a non-root snapshot"
        assert r["user_is_root"] and not n["user_is_root"], "the snapshots do not record root / non-root correctly"
        assert r["sections"] >= 10, f"only {r['sections']} sections in the root snapshot"
        assert r["ok"] >= n["ok"], f"non-root collected more sections ({n['ok']}) than root ({r['ok']}): implausible"
        t = x["triage_vs_orion"]
        assert t and t["critical"] >= 1 and "INVENTORY_MISMATCH" in x["triage_check_ids"], \
            "the analyzer should flag a non-HX8 host as INVENTORY_MISMATCH against the ORION baseline"
        return f"root {r['ok']}/{r['sections']} ok, non-root {n['ok']}/{n['sections']} ok; triage {t['critical']} critical"
    C.run("Step 1 collector root vs non-root, triage", s1)

    def s2():
        x = sm["step2"]
        assert x["vmstat_live_rows"] >= 3, "vmstat needs at least 3 live rows after the since-boot row"
        assert x["hot_cpu_busy_pct"] >= 80, f"the pinned spinner's CPU is only {x['hot_cpu_busy_pct']} % busy (expect ≈ 100)"
        assert x["all_cpu_busy_pct"] <= x["hot_cpu_busy_pct"] - 30, \
            f"all-CPU average {x['all_cpu_busy_pct']} % is not far below the hot CPU's {x['hot_cpu_busy_pct']} %"
        aff = str(x["spinner_affinity"])
        assert aff == str(x["hot_cpu"]), f"taskset -cp shows affinity {aff}, expected the single CPU {x['hot_cpu']}"
        return f"CPU {x['hot_cpu']} {x['hot_cpu_busy_pct']} % vs all {x['all_cpu_busy_pct']} %"
    C.run("Step 2 one hot core hidden in the average", s2)

    def s3():
        x = sm["step3"]
        same = x["same_cpu"]["per_worker_vs_alone"]
        sep = x["separate_cores"]["per_worker_vs_alone"]
        assert all(0.3 <= v <= 0.7 for v in same), f"two workers on one CPU should each get ≈ 0.5 of alone, got {same}"
        assert 0.8 <= x["same_cpu"]["total_vs_alone"] <= 1.2, "two workers on one CPU should together do ≈ the work of one"
        assert all(v >= 0.7 for v in sep), f"workers on separate cores should each run near full speed, got {sep}"
        if "alone_again" in x:
            drift = x["alone_again"]["per_worker_vs_alone"][0]
            assert 0.7 <= drift <= 1.4, f"'alone' drifted to {drift} during the run: too noisy, rerun on a quieter host"
        return f"same CPU {same}, separate cores {sep}"
    C.run("Step 3 time-sharing one CPU halves each worker", s3)

    def s4():
        x = sm["step4"]
        assert x["resident_after_fadvise"] <= 0.1, f"{x['resident_after_fadvise']:.0%} still cached after DONTNEED"
        assert x["resident_after_cold_read"] >= 0.9, "a buffered read should leave the file in the page cache"
        assert x["warm_gb_per_s"] > x["cold_gb_per_s"], "a warm (cached) read should be faster than a cold one"
        return f"cold {x['cold_gb_per_s']} GB/s, warm {x['warm_gb_per_s']} GB/s, O_DIRECT {x['odirect_gb_per_s']} GB/s"
    C.run("Step 4 page cache: eviction, residency, cold vs warm", s4)

    def s5():
        x = sm["step5"]
        msg = []
        for m in x["mlock"]:
            lim = m["rlimit_memlock_soft_kib"]
            if m["uid"] == 0:
                assert m["mlock_ok"], "root (CAP_IPC_LOCK) should be able to mlock 128 MiB"
            elif lim is not None:
                expect = m["request_mib"] * 1024 <= lim
                assert m["mlock_ok"] == expect, \
                    f"non-root mlock of {m['request_mib']} MiB with a {lim} KiB limit: ok={m['mlock_ok']}, expected {expect}"
            msg.append(f"uid {m['uid']} {m['request_mib']} MiB {'ok' if m['mlock_ok'] else 'refused'}")
        g = x["gpu"]
        if "skipped" in g:
            msg.append("GPU step skipped")
        else:
            assert g["h2d_pinned_gb_per_s"] >= g["h2d_pageable_gb_per_s"], "pinned H2D should not be slower than pageable"
            assert g["h2d_pinned_host_blocked_ms"] < 0.2 * g["h2d_pageable_host_blocked_ms"], \
                "a non_blocking copy from pinned memory should return to the CPU far sooner than one from pageable memory"
            assert 0.5 < g["h2d_pinned_gb_per_s"] < 128, f"implausible pinned H2D rate {g['h2d_pinned_gb_per_s']} GB/s"
            msg.append(f"H2D pinned {g['h2d_pinned_gb_per_s']} vs pageable {g['h2d_pageable_gb_per_s']} GB/s")
        return "; ".join(msg)
    C.run("Step 5 RLIMIT_MEMLOCK and pinned copies", s5)

    def s6():
        x = sm["step6"]
        ncpu = sm["environment"]["cpus"]
        assert x["dmesg_lines"] > 0, "dmesg captured nothing (dmesg_restrict? run as root)"
        assert x["psi_cpu_some_avg10_during"] > x["psi_cpu_some_avg10_before"] + 5, \
            f"CPU pressure did not rise under {x['hogs']} busy loops ({x['psi_cpu_some_avg10_before']} → {x['psi_cpu_some_avg10_during']})"
        assert x["vmstat_r_live_max_during"] >= ncpu, f"vmstat r peaked at {x['vmstat_r_live_max_during']} < {ncpu} CPUs under overload"
        return f"PSI cpu {x['psi_cpu_some_avg10_before']} → {x['psi_cpu_some_avg10_during']}, r max {x['vmstat_r_live_max_during']}"
    C.run("Step 6 saturation shows in PSI and vmstat r", s6)

    w = max(len(n) for _, n, _ in C.rows)
    for status, name, msg in C.rows:
        print(f"{status:<4} {name:<{w}}  {msg}")
    passed = sum(1 for s, _, _ in C.rows if s == "PASS")
    print(f"\n{passed}/{len(C.rows)} checks passed [{d}]")
    return 0 if passed == len(C.rows) else 1


if __name__ == "__main__":
    sys.exit(main())
