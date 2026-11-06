#!/usr/bin/env python3
"""Chapter 14 hands-on lab: turn the raw fio and checkpoint outputs into summary.json and report.md.

    python3 summarize.py results/<run-id> [--mtbf-h 48 3]

Standard library only. Reads <run>/raw/fio_jobs.json, <run>/raw/fio/*.json, <run>/raw/ckpt_bench.json
and <run>/environment.json; never modifies them.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

QDS = (1, 4, 16, 32)
PATTERNS = ("randread-4k", "seqread-1m")


def fio_read(path: Path) -> dict | None:
    try:
        job = json.loads(path.read_text())["jobs"][0]
    except (OSError, ValueError, KeyError, IndexError):
        return None
    side = job["read"] if job["read"]["io_bytes"] else job["write"]
    lat = side.get("lat_ns", {})
    pct = side.get("clat_ns", {}).get("percentile", {})
    return {"iops": side["iops"], "bw_GBps": side["bw_bytes"] / 1e9, "lat_mean_us": lat.get("mean", 0) / 1e3,
            "slat_mean_us": side.get("slat_ns", {}).get("mean", 0) / 1e3,
            "clat_mean_us": side.get("clat_ns", {}).get("mean", 0) / 1e3,
            "clat_p99_us": pct.get("99.000000", 0) / 1e3, "clat_p999_us": pct.get("99.900000", 0) / 1e3,
            "runtime_ms": job.get("job_runtime") or side.get("runtime"), "io_GB": side["io_bytes"] / 1e9}


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def young(delta: float, m: float) -> float:
    return math.sqrt(2 * delta * m)


def daly(delta: float, m: float) -> float:
    if delta >= 2 * m:
        return m
    r = delta / (2 * m)
    return math.sqrt(2 * delta * m) * (1 + math.sqrt(r) / 3 + r / 9) - delta


def waste(delta: float, tau: float, m: float) -> float:
    """Fraction of time lost: checkpoint overhead + expected recomputation (Section 14.11)."""
    return delta / tau + (tau / 2) / m


def summarize_fio(run: Path) -> dict:
    idx = json.loads((run / "raw" / "fio_jobs.json").read_text())
    jobs = idx["jobs"]
    for j in jobs:
        j["m"] = fio_read(run / "raw" / "fio" / f"{j['name']}.json") if j["rc"] == 0 else None
    out: dict = {"meta": idx["meta"], "jobs_total": len(jobs), "jobs_failed": [j["name"] for j in jobs if j["rc"] != 0]}

    def cells(step: str) -> dict:
        res = {}
        for pat in PATTERNS:
            for qd in QDS:
                ms = [j["m"] for j in jobs if j.get("step") == step and j.get("pattern") == pat and j["qd"] == qd and j["m"]]
                if not ms:
                    continue
                iops = [m["iops"] for m in ms]
                res[f"{pat}-qd{qd}"] = {
                    "pattern": pat, "qd": qd, "n": len(ms),
                    "iops_median": med(iops), "iops_min": min(iops), "iops_max": max(iops),
                    "bw_GBps_median": med([m["bw_GBps"] for m in ms]),
                    "lat_mean_us_median": med([m["lat_mean_us"] for m in ms]),
                    "slat_mean_us_median": med([m["slat_mean_us"] for m in ms]),
                    "clat_p99_us_median": med([m["clat_p99_us"] for m in ms]),
                    "clat_p999_us_median": med([m["clat_p999_us"] for m in ms]),
                    # Little's law: requests actually in flight = IOPS x mean total latency
                    "littles_law_qd": med([m["iops"] * m["lat_mean_us"] / 1e6 for m in ms]),
                }
        return res

    out["ext4_direct"] = cells("ext4_direct")
    out["ext4_buffered_cold"] = cells("ext4_buffered_cold")
    out["ext4_buffered_warm"] = cells("ext4_buffered_warm")
    out["p9_direct"] = cells("p9_direct")
    out["p9_buffered"] = cells("p9_buffered")
    lay = {j["name"]: j["m"] for j in jobs if j.get("step") == "layout" and j["m"]}
    out["seq_write_1m_GBps"] = {k: v["bw_GBps"] for k, v in lay.items()}
    warm = [j for j in jobs if j.get("step") == "ext4_buffered_warm"]
    out["page_cache_bytes_during_warm"] = min((j["page_cache_before_bytes"] for j in warm), default=None)

    def r(sec, key, f="iops_median"):
        return out[sec].get(key, {}).get(f)

    d, c, w = "ext4_direct", "ext4_buffered_cold", "ext4_buffered_warm"
    ratios = {
        "direct_randread_iops_qd32_over_qd1": r(d, "randread-4k-qd32") / r(d, "randread-4k-qd1"),
        "buffered_cold_randread_iops_qd32_over_qd1": r(c, "randread-4k-qd32") / r(c, "randread-4k-qd1"),
        "warm_cache_over_direct_randread_qd1": r(w, "randread-4k-qd1") / r(d, "randread-4k-qd1"),
        "warm_cache_over_direct_randread_qd32": r(w, "randread-4k-qd32") / r(d, "randread-4k-qd32"),
        "warm_cache_over_direct_seqread_qd32_bw": r(w, "seqread-1m-qd32", "bw_GBps_median") / r(d, "seqread-1m-qd32", "bw_GBps_median"),
        "buffered_cold_over_direct_seqread_qd1_bw": r(c, "seqread-1m-qd1", "bw_GBps_median") / r(d, "seqread-1m-qd1", "bw_GBps_median"),
    }
    if out["p9_direct"]:
        ratios["ext4_over_9p_seqread_qd32_bw"] = r(d, "seqread-1m-qd32", "bw_GBps_median") / r("p9_direct", "seqread-1m-qd32", "bw_GBps_median")
        ratios["ext4_over_9p_randread_qd32_iops"] = r(d, "randread-4k-qd32") / r("p9_direct", "randread-4k-qd32")
        ratios["p9_randread_iops_qd32_over_qd1"] = r("p9_direct", "randread-4k-qd32") / r("p9_direct", "randread-4k-qd1")
    out["ratios"] = ratios
    return out


def summarize_ckpt(run: Path, mtbf_h: list[float]) -> dict:
    raw = json.loads((run / "raw" / "ckpt_bench.json").read_text())
    if raw.get("status") != "ran":
        return {"status": raw.get("status"), "reason": raw.get("reason")}
    sb = raw["state_bytes"]
    base = med(raw["step_ms_baseline"])
    methods = {}
    for name, runs in raw["saves"].items():
        timed = [x for x in runs if not x["warmup"]]
        blk, comp = [x["blocking_s"] for x in timed], [x["completion_s"] for x in timed]
        during = [t for x in timed for t in x["during_ms"]]
        before = [t for x in timed for t in x["before_ms"]]
        m = {"n": len(timed), "blocking_s_median": med(blk), "blocking_s_min": min(blk), "blocking_s_max": max(blk),
             "completion_s_median": med(comp), "completion_s_min": min(comp), "completion_s_max": max(comp),
             "bytes_on_disk": timed[-1]["bytes_on_disk"], "files": timed[-1]["files"],
             "write_GBps_end_to_end": sb / med(comp) / 1e9,
             "step_ms_before_median": med(before), "step_ms_during_median": med(during),
             "steps_during_total": len(during)}
        m["persist_s_median"] = m["completion_s_median"] - m["blocking_s_median"]
        if during and m["step_ms_before_median"]:
            m["interference_frac"] = max(0.0, m["step_ms_during_median"] / m["step_ms_before_median"] - 1)
        else:
            m["interference_frac"] = 0.0
        # Section 14.12 Step 4: effective cost = blocking + interference x background persist
        m["delta_s"] = (m["completion_s_median"] if name == "sync"
                        else m["blocking_s_median"] + m["interference_frac"] * m["persist_s_median"])
        if name == "thread":
            m["snapshot_GBps_median"] = med([x.get("snapshot_gbs") for x in timed])
        methods[name] = m
    loads = raw["loads"]
    load = {c: {"s_median": med([x["load_s"] for x in loads if x["cache"] == c]),
                "GBps_median": med([x["gbs"] for x in loads if x["cache"] == c]),
                "evict": next((x["evict"] for x in loads if x["cache"] == c), None)} for c in ("cold", "warm")}
    yd = []
    for h in mtbf_h:
        msec = h * 3600
        for name, m in methods.items():
            t_y, t_d = young(m["delta_s"], msec), daly(m["delta_s"], msec)
            yd.append({"mtbf_h": h, "method": name, "delta_s": m["delta_s"], "tau_young_s": t_y, "tau_daly_s": t_d,
                       "waste_frac_at_young": waste(m["delta_s"], t_y, msec),
                       "tau_ge_completion": t_y >= m["completion_s_median"]})
    return {"status": "ran", "state_bytes": sb, "params": raw["params"], "model": raw["model"],
            "step_ms_baseline_median": base, "methods": methods, "load": load, "consistency": raw["consistency"],
            "swap_growth_bytes": raw["swap_used_bytes_end"] - raw["swap_used_bytes_start"],
            "gpu_mem_peak_bytes": raw["gpu_mem_peak_bytes"], "mem_available_bytes_start": raw["mem_available_bytes"],
            "young_daly": yd, "mtbf_h_assumed": mtbf_h}


def fmt(x, nd=2):
    if x is None:
        return "n/a"
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:.{nd}f}"


def report(run: Path, s: dict, env: dict) -> str:
    f, c = s["fio"], s["checkpoint"]
    L = [f"# Chapter 14 hands-on: storage and checkpoints on `{run.name}`", "",
         f"Captured {env.get('captured_at')} on {env.get('cpu')} ({env.get('cpus')} CPUs, {env.get('mem_gib')} GiB), "
         f"GPU {env.get('gpu')}, kernel {env.get('kernel')}. Every number below is `[MEASURED]` by the step named, "
         "except rows labelled `[MODELED]` (computed from measured values) or `[ASSUMED]`.", "",
         f"Test file: `{f['meta']['ext4_file']}` ({f['meta']['size_gib']} GiB) on `{f['meta']['ext4_fs']}`; "
         f"{f['meta']['reps']} interleaved repetitions of {f['meta']['ramp_s']} s ramp + {f['meta']['runtime_s']} s; "
         f"{f['meta']['fio_version']}, `--ioengine=libaio`. {f['jobs_total']} fio jobs, {len(f['jobs_failed'])} failed.", "",
         "## Step 1: O_DIRECT reads on the ext4 virtual disk `[MEASURED]`", "",
         "| Pattern | QD | IOPS median (min-max) | GB/s | mean latency µs | p99 µs | p99.9 µs | IOPS x latency (Little) |",
         "|---|---|---|---|---|---|---|---|"]
    for k, v in f["ext4_direct"].items():
        L.append(f"| {v['pattern']} | {v['qd']} | {fmt(v['iops_median'])} ({fmt(v['iops_min'])}-{fmt(v['iops_max'])}) | "
                 f"{fmt(v['bw_GBps_median'], 3)} | {fmt(v['lat_mean_us_median'], 1)} | {fmt(v['clat_p99_us_median'], 1)} | "
                 f"{fmt(v['clat_p999_us_median'], 1)} | {fmt(v['littles_law_qd'], 1)} |")
    rt = f["ratios"]
    L += ["", f"Random 4 KiB IOPS grow {rt['direct_randread_iops_qd32_over_qd1']:.1f}x from QD 1 to QD 32 `[MEASURED]`, "
          "and IOPS x mean latency recovers the queue depth fio was asked for (Section 14.2). "
          f"Sequential 1 MiB write while laying out the file: {', '.join(f'{k} {v:.2f} GB/s' for k, v in f['seq_write_1m_GBps'].items())} `[MEASURED]`.", ""]
    if f["p9_direct"]:
        L += ["## Step 2: the same reads over 9P (`/mnt/<drive>`) `[MEASURED]`", "",
              f"`{f['meta']['p9_dir']}` on `{f['meta']['p9_fs']}`.", "",
              "| Path | Pattern | QD | IOPS | GB/s | mean latency µs |", "|---|---|---|---|---|---|"]
        for sec, lab in (("p9_direct", "9P, O_DIRECT"), ("p9_buffered", "9P, buffered"), ("ext4_direct", "ext4, O_DIRECT")):
            for k, v in f[sec].items():
                if v["qd"] in (1, 32):
                    L.append(f"| {lab} | {v['pattern']} | {v['qd']} | {fmt(v['iops_median'])} | {fmt(v['bw_GBps_median'], 3)} | {fmt(v['lat_mean_us_median'], 1)} |")
        L += ["", f"ext4 reads sequentially {rt['ext4_over_9p_seqread_qd32_bw']:.0f}x faster than 9P at QD 32, and 9P random IOPS "
              f"barely move with queue depth (QD 32 / QD 1 = {rt['p9_randread_iops_qd32_over_qd1']:.2f}) `[MEASURED]`: "
              "every 9P request is a message to a file server in Windows, so the path, not the drive, sets the rate.", ""]
    L += ["## Step 3: the page cache inflates \"storage\" numbers `[MEASURED]`", "",
          "| Pattern | QD | O_DIRECT IOPS | buffered, cold cache | buffered, warm cache | warm GB/s |", "|---|---|---|---|---|---|"]
    for k, v in f["ext4_direct"].items():
        cold, warm = f["ext4_buffered_cold"].get(k, {}), f["ext4_buffered_warm"].get(k, {})
        L.append(f"| {v['pattern']} | {v['qd']} | {fmt(v['iops_median'])} | {fmt(cold.get('iops_median'))} | "
                 f"{fmt(warm.get('iops_median'))} | {fmt(warm.get('bw_GBps_median'), 2)} |")
    seq_w = rt['warm_cache_over_direct_seqread_qd32_bw']
    L += ["", f"With the file in the page cache, 4 KiB random reads at QD 1 run {rt['warm_cache_over_direct_randread_qd1']:.0f}x "
          "faster than the disk delivers `[MEASURED]`: that is the kernel copying pages from RAM, not storage. "
          f"Sequential 1 MiB reads at QD 32 from the warm cache run at {seq_w:.1f}x the O_DIRECT rate `[MEASURED]`: "
          "a buffered read is a single-threaded memory copy, while O_DIRECT large reads on a virtual disk can be "
          "served from the hypervisor host's own cache, so for large sequential I/O the two converge. "
          "Cold buffered random reads gain only "
          f"{rt['buffered_cold_randread_iops_qd32_over_qd1']:.2f}x from QD 1 to QD 32 (O_DIRECT: "
          f"{rt['direct_randread_iops_qd32_over_qd1']:.1f}x): buffered libaio submits synchronously, so the requested "
          "queue depth never reaches the device. Cold buffered sequential reads at QD 1 get "
          f"{rt['buffered_cold_over_direct_seqread_qd1_bw']:.2f}x the O_DIRECT rate because kernel readahead adds the "
          "parallelism the application did not.", ""]
    if c.get("status") != "ran":
        L += ["## Step 4: checkpoints", "", f"Not run: {c.get('reason')}", ""]
        return "\n".join(L)
    ms = c["methods"]
    L += ["## Step 4: checkpoint save and load `[MEASURED]`", "",
          f"State: {c['state_bytes'] / 1e9:.3f} GB ({c['params'] / 1e6:.1f} M params, {c['model']}); "
          f"baseline training step {c['step_ms_baseline_median']:.1f} ms; peak GPU memory {c['gpu_mem_peak_bytes'] / 2**30:.2f} GiB; "
          f"swap growth during the run {c['swap_growth_bytes'] / 2**20:.0f} MiB.", "",
          "| Method | blocking s (min-max) | completion s (min-max) | on disk GB | end-to-end GB/s | step ms before / during | interference | δ (effective cost) s |",
          "|---|---|---|---|---|---|---|---|"]
    names = {"sync": "dcp.save (sync)", "dcp_async": "dcp.async_save", "thread": "pinned snapshot + thread"}
    for k, m in ms.items():
        L.append(f"| {names[k]} | {m['blocking_s_median']:.3f} ({m['blocking_s_min']:.3f}-{m['blocking_s_max']:.3f}) | "
                 f"{m['completion_s_median']:.3f} ({m['completion_s_min']:.3f}-{m['completion_s_max']:.3f}) | "
                 f"{m['bytes_on_disk'] / 1e9:.3f} | {m['write_GBps_end_to_end']:.2f} | {fmt(m['step_ms_before_median'], 1)} / "
                 f"{fmt(m['step_ms_during_median'], 1)} | {m['interference_frac'] * 100:.0f} % | {m['delta_s']:.3f} |")
    ld = c["load"]
    cs = c["consistency"]
    L += ["", f"Pinned D2H snapshot: {ms['thread']['snapshot_GBps_median']:.1f} GB/s `[MEASURED]`. "
          f"dcp.load: cold cache ({ld['cold']['evict']}) {ld['cold']['s_median']:.3f} s = {ld['cold']['GBps_median']:.2f} GB/s; "
          f"warm cache {ld['warm']['s_median']:.3f} s = {ld['warm']['GBps_median']:.2f} GB/s `[MEASURED]`.", "",
          f"Consistency: an async_save taken while {cs['steps_during_persist']} training steps ran differs from the state at "
          f"the call in {cs['differ_from_state_at_call']} of {cs['tensors']} tensors (live state changed meanwhile: "
          f"{cs['live_state_changed_meanwhile']}) `[MEASURED]`.", "",
          "## Step 5: the checkpoint interval (Young/Daly) `[MODELED]` from measured δ and `[ASSUMED]` MTBF", "",
          "MTBF values are assumptions, not measurements: 48 h is the chapter's ORION-256 planning value and 3 h its "
          "ORION-XL value (Section 14.11). This laptop has no failure history to measure.", "",
          "| MTBF `[ASSUMED]` | Method | δ s | τ* Young s | τ* Daly s | time lost at τ* | τ* ≥ completion |", "|---|---|---|---|---|---|---|"]
    for y in c["young_daly"]:
        L.append(f"| {y['mtbf_h']:g} h | {names[y['method']]} | {y['delta_s']:.3f} | {y['tau_young_s']:,.0f} | "
                 f"{y['tau_daly_s']:,.0f} | {y['waste_frac_at_young'] * 100:.3f} % | {y['tau_ge_completion']} |")
    L += ["", f"Absolute values describe a {c['state_bytes'] / 1e9:.1f} GB state on one laptop disk; ORION's δ is set by 980 GB going to a shared PFS "
          "(Section 14.12). The relations carry over: τ* grows with √δ, async shrinks δ to the blocking snapshot plus "
          "interference, and the time lost at the optimum is √(2δ/M).", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    ap.add_argument("--mtbf-h", type=float, nargs="+", default=[48.0, 3.0])
    a = ap.parse_args()
    env = json.loads((a.run / "environment.json").read_text())
    s = {"lab": "ch14-handson", "run_id": a.run.name, "fio": summarize_fio(a.run),
         "checkpoint": summarize_ckpt(a.run, a.mtbf_h)}
    (a.run / "summary.json").write_text(json.dumps(s, indent=1))
    (a.run / "report.md").write_text(report(a.run, s, env))
    print(f"wrote {a.run / 'summary.json'} and {a.run / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
