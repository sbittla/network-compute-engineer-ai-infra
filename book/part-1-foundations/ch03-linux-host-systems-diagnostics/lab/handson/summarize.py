#!/usr/bin/env python3
"""Turn the raw outputs of one Chapter 3 hands-on run into summary.json and report.md.

    python summarize.py results/<run-id>

Only parses what run.sh captured; it never edits the raw files.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def vmstat_rows(text: str) -> tuple[list[str], list[list[int]]]:
    lines = [ln.split() for ln in text.splitlines() if ln.strip()]
    header = next(ln for ln in lines if ln and ln[0] == "r")
    rows = [list(map(int, ln)) for ln in lines if ln and ln[0].isdigit() and len(ln) == len(header)]
    return header, rows


def mpstat_average(text: str) -> dict[str, dict[str, float]]:
    out, cols = {}, []
    for ln in text.splitlines():
        if not ln.startswith("Average:"):
            continue
        f = ln.split()
        if f[1] == "CPU":
            cols = f[2:]
            continue
        if cols:
            out[f[1]] = dict(zip(cols, map(float, f[2:])))
    return out


def psi_some_avg10(text: str, res: str) -> float:
    m = re.search(rf"^{res}: some avg10=([\d.]+)", text, re.M)
    return float(m.group(1)) if m else float("nan")


def step1(d: Path) -> dict:
    s = d / "step1-collector"
    out = {"collector": read(s / "collector_path.txt").strip()}
    for mode in ("root", "nonroot"):
        js = sorted((s / mode).glob("hostdiag-*.json"))
        if not js:
            out[mode] = None
            continue
        rep = json.loads(js[0].read_text())
        secs = rep["sections"]
        lspci = secs.get("lspci", {}).get("stdout", "")
        out[mode] = {
            "user_is_root": rep["user_is_root"], "sections": len(secs),
            "ok": sum(1 for v in secs.values() if v["status"] == "ok"),
            "gaps": {k: v["status"] for k, v in secs.items() if v["status"] != "ok"},
            "lspci_access_denied_lines": lspci.count("<access denied>"),
            "lspci_functions": len(re.findall(r"^[0-9a-f]{2,4}:[0-9a-f]{2}:[0-9a-f]{2}\.\d|^[0-9a-f]{2}:[0-9a-f]{2}\.\d", lspci, re.M)),
            "nvidia_smi_status": secs.get("nvidia_smi", {}).get("status"),
            "nvidia_smi_stderr": secs.get("nvidia_smi", {}).get("stderr", "")[:160],
        }
    tri = read(s / "triage-vs-orion-hx8.md")
    m = re.search(r"\| (\S+) \| (\d+) \| (\d+) \| (\d+) \| ([^|]+) \|", tri)
    out["triage_vs_orion"] = ({"critical": int(m.group(2)), "warning": int(m.group(3)), "info": int(m.group(4)),
                               "verdict": m.group(5).strip()} if m else None)
    out["triage_check_ids"] = sorted(set(re.findall(r"`([A-Z_]+)`", tri)))
    return out


def step2(d: Path, ncpu: int) -> dict:
    s = d / "step2-percpu"
    hot = read(s / "hot_cpu.txt").strip()
    avg = mpstat_average(read(s / "mpstat.txt"))
    header, rows = vmstat_rows(read(s / "vmstat.txt"))
    idc = header.index("id")
    aff = re.search(r"current affinity list: (\S+)", read(s / "affinity.txt"))
    return {
        "hot_cpu": int(hot), "spinner_affinity": aff.group(1) if aff else None,
        "hot_cpu_busy_pct": round(100 - avg[hot]["%idle"], 1),
        "all_cpu_busy_pct": round(100 - avg["all"]["%idle"], 1),
        "one_core_share_of_host_pct": round(100 / ncpu, 2),
        "busiest_other_cpu_busy_pct": round(max(100 - v["%idle"] for k, v in avg.items() if k not in ("all", hot)), 1),
        "vmstat_since_boot_idle_pct": rows[0][idc], "vmstat_live_idle_pct_mean": round(sum(r[idc] for r in rows[1:]) / max(1, len(rows) - 1), 1),
        "vmstat_live_rows": len(rows) - 1,
    }


def step3(d: Path) -> dict:
    b = json.loads(read(d / "step3-pinning" / "bench.json"))
    return {"cpu_x": b["cpu_x"], "smt_sibling": b["smt_sibling"], "other_core_cpu": b["other_core_cpu"],
            **{name: {"per_worker_vs_alone": c["per_worker_vs_alone"], "total_vs_alone": c["total_vs_alone"]}
               for name, c in b["configs"].items()}}


def step4(d: Path) -> dict:
    p = json.loads(read(d / "step4-pagecache" / "pagecache.json"))
    st = {x["step"]: x for x in p["steps"]}
    return {"size_mib": p["size_mib"], "cold_gb_per_s": p["cold_gb_per_s"], "warm_gb_per_s": p["warm_gb_per_s"],
            "odirect_gb_per_s": p["odirect_gb_per_s"], "warm_over_cold": p["warm_over_cold"],
            "resident_after_write": st["after_write_fsync"]["resident_fraction"],
            "resident_after_fadvise": st["after_fadvise_dontneed"]["resident_fraction"],
            "resident_after_cold_read": st["after_cold_read"]["resident_fraction"],
            "cached_drop_on_fadvise_mib": round((st["after_write_fsync"]["meminfo_cached_kib"] - st["after_fadvise_dontneed"]["meminfo_cached_kib"]) / 1024)}


def step5(d: Path) -> dict:
    s = d / "step5-pinned"
    ml = [json.loads(ln) for ln in read(s / "mlock.jsonl").splitlines() if ln.strip()]
    out = {"ulimit": read(s / "ulimit.txt").strip().splitlines(),
           "mlock": [{k: x[k] for k in ("uid", "request_mib", "rlimit_memlock_soft_kib", "mlock_ok", "error", "vmlck_kib_while_locked")} for x in ml]}
    pc = json.loads(read(s / "pinned_copy.json") or "{}")
    if "skipped" in pc or not pc:
        out["gpu"] = {"skipped": pc.get("skipped", "missing")}
    else:
        out["gpu"] = {
            "gpu": pc["gpu"], "mib": pc["mib"], "pin_memory_call_ms": pc["pin_memory_call_ms"],
            "vmlck_kib_after_pin": pc["proc_status_kib_after_pin"].get("VmLck"), "vmpin_kib_after_pin": pc["proc_status_kib_after_pin"].get("VmPin"),
            **{f"{k}_gb_per_s": pc[k]["gb_per_s"] for k in ("h2d_pageable", "h2d_pinned", "d2h_pageable", "d2h_pinned")},
            **{f"{k}_host_blocked_ms": pc[k]["host_blocked_median_ms"] for k in ("h2d_pageable", "h2d_pinned")},
            "h2d_copy_ms_pinned": pc["h2d_pinned"]["median_ms"], "h2d_pinned_over_pageable": pc["h2d_pinned_over_pageable"]}
    return out


def step6(d: Path, ncpu: int) -> dict:
    s = d / "step6-signals"
    dm = read(s / "dmesg.txt")
    cats = {"aer": r"AER|PCIe Bus Error", "edac": r"EDAC", "xid": r"NVRM: Xid", "mce": r"[Mm]achine [Cc]heck|mce:",
            "oom": r"[Oo]ut of memory|oom-kill", "io_error": r"I/O error|blk_update_request", "dxg_ioctl_failed": r"dxg.*Ioctl failed"}
    counts = {k: len(re.findall(v, dm)) for k, v in cats.items()}
    vmc = dict(ln.split() for ln in read(s / "vmstat-counters.txt").splitlines() if ln.strip())
    header, rows = vmstat_rows(read(s / "vmstat-overload.txt"))
    rcol = header.index("r")
    pb, pd = read(s / "psi-before.txt"), read(s / "psi-during.txt")
    return {
        "dmesg_lines": len(dm.splitlines()), "dmesg_err_lines": len(read(s / "dmesg-err.txt").splitlines()),
        "dmesg_warn_lines": len(read(s / "dmesg-warn.txt").splitlines()), "dmesg_categories": counts,
        "oom_kill_counter": int(vmc.get("oom_kill", -1)), "hogs": 2 * ncpu,
        "psi_cpu_some_avg10_before": psi_some_avg10(pb, "cpu"), "psi_cpu_some_avg10_during": psi_some_avg10(pd, "cpu"),
        "vmstat_r_live_max_during": max(r[rcol] for r in rows[1:]) if len(rows) > 1 else None,
        "loadavg_1m_before": float(read(s / "loadavg-before.txt").split()[0]),
        "loadavg_1m_during": float(read(s / "loadavg-during.txt").split()[0]),
    }


def is_wsl(env: dict) -> bool:
    return bool(env.get("wsl")) or "wsl2" in json.dumps(env.get("tools", {}))


def report(sm: dict) -> str:
    e, s1, s2, s3, s4, s5, s6 = (sm[k] for k in ("environment", "step1", "step2", "step3", "step4", "step5", "step6"))
    M = "`[MEASURED]`"
    L = [f"# Chapter 3 hands-on: host diagnostics on `{e.get('cpu')}` ({e.get('cpus')} CPUs)", "",
         f"Run captured {e.get('captured_at')} on kernel `{e.get('kernel')}` ({'WSL2' if is_wsl(e) else 'native Linux'}), "
         f"GPU: {e.get('gpu') or 'none'}. Every number below is {M} on this machine by the step named; raw outputs are in "
         "the step directories next to this file.", "",
         "## Step 1: the chapter's read-only collector, root and non-root", ""]
    for mode in ("root", "nonroot"):
        x = s1[mode]
        if x:
            gaps = ", ".join(f"{k} ({v})" for k, v in x["gaps"].items()) or "none"
            L.append(f"- {mode}: {x['ok']}/{x['sections']} sections ok {M}; gaps: {gaps}; `lspci -vv` lines reading "
                     f"`<access denied>`: {x['lspci_access_denied_lines']} {M}.")
    t = s1["triage_vs_orion"]
    if t:
        L.append(f"- Triage of the root snapshot against the ORION HX8 baseline: {t['critical']} critical, {t['warning']} warning, "
                 f"{t['info']} info, verdict **{t['verdict']}** {M} (this machine is not an HX8, so inventory rules fire).")
    L += ["", "## Step 2: averages hide the saturated core", "",
          f"- One busy thread on CPU {s2['hot_cpu']}: that CPU {s2['hot_cpu_busy_pct']} % busy, all-CPU average "
          f"{s2['all_cpu_busy_pct']} % busy {M} (`mpstat -P ALL 1 5`, Average block). One core is "
          f"{s2['one_core_share_of_host_pct']} % of this host.",
          f"- `vmstat 1 6`: since-boot row {s2['vmstat_since_boot_idle_pct']} % idle versus live rows {s2['vmstat_live_idle_pct_mean']} % idle {M}.",
          "", "## Step 3: CPU placement and throughput (per-worker throughput relative to one worker alone)", "",
          "| Placement | Per worker | Total |", "|---|---|---|"]
    for name in ("alone", "same_cpu", "smt_siblings", "separate_cores", "unpinned", "alone_again"):
        if name in s3:
            L.append(f"| {name} | {', '.join(f'{v:.2f}' for v in s3[name]['per_worker_vs_alone'])} {M} | {s3[name]['total_vs_alone']:.2f} {M} |")
    L += ["", "## Step 4: the page cache", "",
          f"- 1 GiB file: cold read {s4['cold_gb_per_s']} GB/s, warm read {s4['warm_gb_per_s']} GB/s "
          f"({s4['warm_over_cold']}× faster), O_DIRECT read {s4['odirect_gb_per_s']} GB/s {M}.",
          f"- Page-cache residency (mincore): {s4['resident_after_fadvise']:.0%} after `POSIX_FADV_DONTNEED`, "
          f"{s4['resident_after_cold_read']:.0%} after one cold read {M}; `Cached` fell by {s4['cached_drop_on_fadvise_mib']} MiB on eviction {M}.",
          "", "## Step 5: locked and pinned memory", ""]
    for x in s5["mlock"]:
        L.append(f"- uid {x['uid']}: mlock {x['request_mib']} MiB with RLIMIT_MEMLOCK {x['rlimit_memlock_soft_kib']} KiB: "
                 f"{'ok' if x['mlock_ok'] else 'refused (' + x['error'] + ')'} {M}.")
    g = s5["gpu"]
    if "skipped" in g:
        L.append(f"- GPU copy step skipped: {g['skipped']}.")
    else:
        L += [f"- {g['mib']} MiB H2D: pageable {g['h2d_pageable_gb_per_s']} GB/s, pinned {g['h2d_pinned_gb_per_s']} GB/s "
              f"({g['h2d_pinned_over_pageable']}×) {M}; D2H pageable {g['d2h_pageable_gb_per_s']}, pinned {g['d2h_pinned_gb_per_s']} GB/s {M}.",
              f"- CPU held by a `non_blocking=True` copy: pageable {g['h2d_pageable_host_blocked_ms']} ms, pinned "
              f"{g['h2d_pinned_host_blocked_ms']} ms {M}. Pinning the buffer cost {g['pin_memory_call_ms']} ms "
              f"(the pinned copy itself takes {g['h2d_copy_ms_pinned']} ms) {M}.",
              f"- VmLck/VmPin after `pin_memory()`: {g['vmlck_kib_after_pin']}/{g['vmpin_kib_after_pin']} KiB {M}."]
    c = s6["dmesg_categories"]
    L += ["", "## Step 6: kernel log and /proc signals", "",
          f"- `dmesg`: {s6['dmesg_lines']} lines, {s6['dmesg_err_lines']} at err or worse; AER {c['aer']}, EDAC {c['edac']}, "
          f"Xid {c['xid']}, MCE {c['mce']}, OOM {c['oom']}, I/O errors {c['io_error']}, `dxg` ioctl failures {c['dxg_ioctl_failed']} {M}; "
          f"`oom_kill` counter {s6['oom_kill_counter']} {M}.",
          f"- {s6['hogs']} niced busy loops on {sm['environment'].get('cpus')} CPUs: PSI `cpu some avg10` "
          f"{s6['psi_cpu_some_avg10_before']} → {s6['psi_cpu_some_avg10_during']} %, `vmstat r` up to {s6['vmstat_r_live_max_during']}, "
          f"1-minute load {s6['loadavg_1m_before']} → {s6['loadavg_1m_during']} {M}.", ""]
    return "\n".join(L) + "\n"


def main() -> int:
    d = Path(sys.argv[1])
    env = json.loads(read(d / "environment.json"))
    ncpu = int(env.get("cpus") or 1)
    sm = {"lab": "ch03-host-diagnostics", "run": d.name, "environment": env,
          "step1": step1(d), "step2": step2(d, ncpu), "step3": step3(d), "step4": step4(d),
          "step5": step5(d), "step6": step6(d, ncpu)}
    (d / "summary.json").write_text(json.dumps(sm, indent=1) + "\n", encoding="utf-8")
    (d / "report.md").write_text(report(sm), encoding="utf-8")
    print(f"wrote {d / 'summary.json'} and {d / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
