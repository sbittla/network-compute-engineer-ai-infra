#!/usr/bin/env python3
"""Chapter 16 hands-on lab: judge the collected evidence against the acceptance policy.

    python3 evaluate.py results/<run-id> [--policy acceptance_policy_laptop.json]

Reads <run>/raw/host.json, <run>/raw/gpu_stress.json and <run>/raw/telemetry.csv; writes
<run>/acceptance_record.json (the evidence, shaped like lab/data/acceptance_results.json),
<run>/summary.json (one row per check: PASS / WARN / FAIL / N/A, with its reason code) and
<run>/report.md. Standard library only.

N/A is not PASS. A check that could not run produced no evidence, so the node cannot be validated
on it. The verdict on the checks that ran is reported separately from the acceptance decision.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REASONS = {0x1: "GPU_IDLE", 0x2: "APPLICATIONS_CLOCKS_SETTING", 0x4: "SW_POWER_CAP", 0x8: "HW_SLOWDOWN",
           0x10: "SYNC_BOOST", 0x20: "SW_THERMAL_SLOWDOWN", 0x40: "HW_THERMAL_SLOWDOWN",
           0x80: "HW_POWER_BRAKE_SLOWDOWN", 0x100: "DISPLAY_CLOCK_SETTING"}
# The chapter's HX8 policy (lab/data/acceptance_policy.yaml, acc-2026.10), for the comparison table.
HX8 = {"gpu_count": 8, "gpu_product": "H100-SXM-80GB", "gpu_mem_mib": 81000, "pcie": (5, 16), "compute_nics": 8,
       "frontend_nics": 2, "mtu": 9000, "nvme": 8, "drive_gbs": 5.0, "total_gbs": 40.0}


def num(v: str):
    try:
        return float(v.strip().split()[0])
    except (ValueError, IndexError):
        return None


def reasons(mask: int) -> list[str]:
    return [n for b, n in REASONS.items() if mask & b]


def load_telemetry(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        rd = csv.reader(f)
        header = None
        for r in rd:
            if not r:
                continue
            if r[0].startswith("timestamp"):
                header = [h.strip().split(" [")[0] for h in r]
                continue
            if header is None or len(r) != len(header):
                continue
            d = dict(zip(header, (x.strip() for x in r)))
            mask = d.get("clocks_event_reasons.active", "0x0")
            rows.append({"temp_c": num(d["temperature.gpu"]), "power_w": num(d["power.draw"]),
                         "sm_mhz": num(d["clocks.current.sm"] if "clocks.current.sm" in d else d.get("clocks.sm", "")),
                         "sm_max_mhz": num(d.get("clocks.max.sm", "")), "util": num(d["utilization.gpu"]),
                         "pcie_gen": num(d["pcie.link.gen.current"]), "pcie_width": num(d["pcie.link.width.current"]),
                         "reasons": reasons(int(mask, 16)) if mask.startswith("0x") else []})
    return rows


def counters(path: Path) -> dict:
    lines = [l for l in path.read_text().splitlines() if l.strip()]
    if len(lines) < 2:
        return {}
    keys = [k.strip().split(" [")[0].split(".")[-1] for k in lines[0].split(",")]
    vals = [num(v) for v in lines[1].split(",")]
    return dict(zip(keys, vals))


def stats(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return {"median": statistics.median(xs), "p95": xs[min(len(xs) - 1, int(0.95 * len(xs)))], "min": xs[0], "max": xs[-1]}


def evaluate(run: Path, policy: dict) -> dict:
    host = json.loads((run / "raw" / "host.json").read_text())
    gs = json.loads((run / "raw" / "gpu_stress.json").read_text())
    tele = load_telemetry(run / "raw" / "telemetry.csv")
    c0, c1 = counters(run / "raw" / "clock_event_counters_before.csv"), counters(run / "raw" / "clock_event_counters_after.csv")
    exp, thr = policy["expected"], policy["thresholds"]
    checks: list[dict] = []

    def add(stage, code, status, evidence, criterion, lab_local=False):
        checks.append({"stage": stage, "code": code, "status": status, "evidence": evidence,
                       "criterion": criterion, "lab_local": lab_local})

    gpus = host["gpu"]["gpus"]
    g = gpus[0] if gpus else {}
    loaded = [r for r in tele if (r["util"] or 0) >= 90]
    # 1. inventory and discovery
    add("discovery", "GPU_COUNT", "PASS" if len(gpus) == exp["gpu_count"] else "FAIL",
        f"{len(gpus)} GPU(s) from nvidia-smi", f"== {exp['gpu_count']}")
    add("discovery", "GPU_PRODUCT", "PASS" if g.get("product") == exp["gpu_product"] else "FAIL",
        f"{g.get('product')}", f"== {exp['gpu_product']}")
    add("discovery", "HBM_CAPACITY", "PASS" if (g.get("memory_total_mib") or 0) >= exp["gpu_mem_total_mib_min"] else "FAIL",
        f"{g.get('memory_total_mib')} MiB (GDDR6 on this SKU, not HBM)", f">= {exp['gpu_mem_total_mib_min']} MiB")
    # 2. PCIe under load
    if loaded:
        gen = statistics.median([r["pcie_gen"] for r in loaded])
        width = statistics.median([r["pcie_width"] for r in loaded])
        mx = g.get("pcie_max", {})
        ok = gen >= mx.get("gen", 99) and width >= mx.get("width", 99)
        add("pcie", "PCIE_DEGRADED", "PASS" if ok else "FAIL",
            f"under load Gen{gen:g} x{width:g} (median of {len(loaded)} samples); idle Gen{g['pcie_idle']['gen']} x{g['pcie_idle']['width']}",
            f"Gen{mx.get('gen')} x{mx.get('width')} (the GPU's maximum) under load")
    else:
        add("pcie", "PCIE_DEGRADED", "FAIL", "no telemetry samples at >= 90 % utilisation", "link judged under load")
    # 3. GPU health
    add("gpu-health", "NVLINK_DOWN", "N/A", host["gpu"]["nvlink_status_text"] or "no NVLink",
        "18/18 links per GPU (HX8); this GPU has no NVLink, so there is nothing to test")
    add("gpu-health", "ECC_DBE / ECC_SBE_ELEVATED", "N/A", f"ecc.mode.current = {g.get('ecc_mode')}",
        "0 volatile DBE, SBE <= 10: needs a GPU with memory ECC enabled")
    rr = host["gpu"]["row_remap"]
    add("gpu-health", "HBM_ROW_REMAP_PENDING / HBM_ROW_REMAP_FAILURE", "N/A",
        f"driver reports correctable={rr.get('correctable')} uncorrectable={rr.get('uncorrectable')} pending={rr.get('pending')} "
        f"failure={rr.get('failure')}, but with ECC off nothing detects the errors that would trigger a remap",
        "no pending remap or failure, on a GPU whose ECC feeds the remapper")
    kl = host["kernel_log"]
    add("gpu-health", "DCGM_DIAG_FAIL", "N/A", f"dcgmi on PATH: {kl['dcgmi_on_path']}; DCGM does not support GeForce GPUs or WSL",
        f"dcgmi diag -r {thr['dcgm_diag_min_level']} Pass")
    num_ = gs["numerics"]
    errs = {f"{k}_{p}": v[f"{p}_err"] for k, v in num_.items() for p in ("fp32", "fp16")}
    ok = all(v <= thr[f"gemm_{k.split('_')[1]}_rel_err_max"] for k, v in errs.items())
    st = gs["stress"]
    ok = ok and st["golden_mismatches"] == 0 and st["golden_checks"] > 0
    add("gpu-health", "GPU_NUMERICS", "PASS" if ok else "FAIL",
        f"GEMM vs CPU reference: FP32 cold {errs['cold_fp32']:.1e} hot {errs['hot_fp32']:.1e}; FP16 cold {errs['cold_fp16']:.1e} "
        f"hot {errs['hot_fp16']:.1e}; golden output {st['golden_mismatches']}/{st['golden_checks']} mismatched during stress",
        f"FP32 <= {thr['gemm_fp32_rel_err_max']:g}, FP16 <= {thr['gemm_fp16_rel_err_max']:g} (scaled by |A||B|); golden bit-identical",
        lab_local=True)
    mp = gs["memory_pattern"]
    add("gpu-health", "GPU_MEM_PATTERN", "PASS" if mp["mismatched_words"] == 0 else "FAIL",
        f"{mp['bytes'] / 2**30:.2f} GiB x {mp['patterns']} patterns: {mp['mismatched_words']} mismatched words",
        "0 mismatches", lab_local=True)
    # 4. burn-in: thermals, reasons, sustained performance
    seen = sorted({x for r in loaded for x in r["reasons"]})
    bad = sorted(set(seen) & set(thr["throttle_reasons_fail"]))
    dc = {k: (c1.get(k) or 0) - (c0.get(k) or 0) for k in c1}
    bad_ctr = [k for k in ("sw_thermal_slowdown", "hw_thermal_slowdown", "hw_power_brake_slowdown") if dc.get(k, 0) > 0]
    tmax = max((r["temp_c"] for r in tele if r["temp_c"] is not None), default=None)
    long_enough = st["seconds"] >= thr["min_stress_seconds"]
    ok = tmax is not None and tmax < thr["max_gpu_temp_c"] and not bad and not bad_ctr and long_enough
    # A reason in neither policy list (e.g. HW_SLOWDOWN, which covers thermal and power-brake) is not ignored silently.
    unclassified = sorted(set(seen) - set(thr["throttle_reasons_fail"]) - set(thr["throttle_reasons_ignore"]))
    add("burn-in", "THERMAL_THROTTLE", ("WARN" if unclassified else "PASS") if ok else "FAIL",
        f"max {tmax} C over {st['seconds']:.0f} s; reasons seen under load {seen or 'none'}"
        + (f" (not in either policy list: {unclassified})" if unclassified else "") + "; counter deltas (us) "
        + ", ".join(f"{k} {v:,.0f}" for k, v in dc.items()),
        f"max < {thr['max_gpu_temp_c']} C; none of {thr['throttle_reasons_fail']}; soak >= {thr['min_stress_seconds']} s")
    w = [x["tflops"] for x in st["windows"]]
    third = max(1, len(w) // 3)
    first, last = statistics.median(w[:third]), statistics.median(w[-third:])
    decay = 1 - last / first
    add("burn-in", "STRESS_PERF_DECAY", "WARN" if decay > thr["stress_decay_warn_frac"] else "PASS",
        f"GEMM {first:.1f} TFLOP/s in the first third, {last:.1f} in the last ({decay * 100:+.1f} % decay)",
        f"decay <= {thr['stress_decay_warn_frac'] * 100:.0f} % (else WARN)", lab_local=True)
    # 5. host memory
    m = host["memory"]
    add("host", "HOST_MEM_CAPACITY", "PASS" if m["mem_total_bytes"] / 2**30 >= exp["host_mem_gib_min"] else "FAIL",
        f"MemTotal {m['mem_total_bytes'] / 2**30:.2f} GiB (the WSL2 VM's share, not the laptop's DIMMs)",
        f">= {exp['host_mem_gib_min']} GiB", lab_local=True)
    pt = m["pattern_test"]
    add("host", "HOST_MEM_PATTERN", "PASS" if pt["bad_chunks"] == 0 and m["hw_corrupted_bytes"] == 0 else "FAIL",
        f"{pt['bytes'] / 2**20:.0f} MiB x {pt['patterns']} patterns: {pt['bad_chunks']} bad 1 MiB chunks; HardwareCorrupted {m['hw_corrupted_bytes']} B",
        "0 bad chunks (a user-space pattern test, not memtest86)", lab_local=True)
    add("host", "HOST_ECC", "N/A", f"EDAC present: {m['edac_present']} (a VM sees no memory controller)",
        "0 corrected/uncorrected DIMM errors from EDAC or the BMC SEL", lab_local=True)
    # 6. NICs
    nd = [n for n in host["nics"]["netdevs"] if n["has_device"]]
    fe = exp["frontend_nic"]
    add("nic", "NIC_COUNT", "PASS" if len(nd) == fe["count"] else "FAIL",
        f"{len(nd)} device-backed netdev(s): {', '.join('%s (%s)' % (n['name'], n['driver']) for n in nd)}; "
        f"virtual (no device) skipped: {len(host['nics']['netdevs']) - len(nd)}", f"{fe['count']} frontend, {exp['compute_nic_count']} compute")
    for n in nd:
        up = n["operstate"] == "up" and n["carrier"] == "1"
        add("nic", "NIC_LINK_DOWN", "PASS" if up else "FAIL", f"{n['name']} operstate {n['operstate']}, carrier {n['carrier']}", "up")
        add("nic", "NIC_SPEED", "PASS" if (n["speed_mbps"] or 0) >= fe["speed_mbps_min"] else "FAIL",
            f"{n['name']} {n['speed_mbps']} Mb/s (a value the virtual NIC reports, not a negotiated PHY rate)",
            f">= {fe['speed_mbps_min']} Mb/s")
        add("nic", "NIC_MTU", "PASS" if n["mtu"] == fe["mtu"] else "FAIL", f"{n['name']} MTU {n['mtu']}", f"== {fe['mtu']}")
    rd = host["nics"]["rdma_devices"]
    soft = ", ".join(r["name"] for r in rd) or "none"
    add("nic", "RDMA_PAIR_BW_LOW", "N/A", f"RDMA devices: {soft} (software rxe from other labs, if any: not a compute NIC)",
        "ib_write_bw per rail against a reference node, median of 5 >= 360 Gb/s")
    add("nic", "LINK_BER_HIGH", "N/A", "no physical link: no FEC histogram or pre-FEC BER exists", "pre-FEC BER < 1e-6, 0 flaps")
    add("nic", "GDR_PATH_FAIL", "N/A", "no RDMA NIC, no PCIe tree visible in WSL2 (no ACS, no peer memory)",
        "GPU-buffer >= 90 % of host-buffer bandwidth per rail")
    # 7. storage
    sto = host["storage"]
    disks = sto["data_disks"]
    add("storage", "NVME_COUNT", "PASS" if len(disks) >= exp["data_disk_count_min"] else "FAIL",
        f"{len(disks)} data disk(s): {', '.join('%s (%s)' % (d['device'], d['model']) for d in disks)}; NVMe devices visible: {len(sto['nvme_devices'])}",
        f">= {exp['data_disk_count_min']} data disk (8 NVMe on HX8)")
    add("storage", "NVME_MEDIA_ERRORS", "N/A", f"SMART tool: {sto['smart_tool']}; a Hyper-V virtual disk exposes no SMART log",
        "critical_warning 0, media_errors 0")
    total, slow = 0.0, []
    per = []
    for d in disks:
        bws = [r["bw_GBps"] for r in d["runs"] if not r["warmup"] and r["rc"] == 0]
        medbw = statistics.median(bws) if bws else 0.0
        per.append((d["device"], medbw, bws))
        total += medbw
        if medbw < thr["disk_seq_read_min_gbs"]:
            slow.append(d["device"])
    add("storage", "NVME_DRIVE_SLOW", "FAIL" if slow or not per else "PASS",
        "; ".join(f"/dev/{dv} median {b:.2f} GB/s (runs {', '.join(f'{x:.2f}' for x in bws)})" for dv, b, bws in per),
        f"each >= {thr['disk_seq_read_min_gbs']} GB/s, fio read-only 1 MiB QD32 O_DIRECT, median of timed runs")
    add("storage", "STORAGE_THROUGHPUT_LOW", "PASS" if total >= thr["storage_seq_read_min_gbs"] else "FAIL",
        f"sum of per-disk medians {total:.2f} GB/s", f">= {thr['storage_seq_read_min_gbs']} GB/s")
    # 8. collective, kernel log, firmware
    add("collective", "NCCL_BUSBW_LOW / NCCL_ALGO_UNRECORDED", "N/A", "1 GPU: there is no intra-node collective to run",
        "all_reduce_perf -g 8 busbw >= 400 (NVLS) / 330 (Ring) GB/s")
    if kl["xid_lines"]:
        add("kernel-log", "XID_PRESENT", "FAIL", f"{len(kl['xid_lines'])} Xid line(s) in dmesg", "no Xid during acceptance")
    elif not kl["nvidia_kernel_module_loaded"]:
        add("kernel-log", "XID_PRESENT", "N/A",
            f"dmesg scanned ({kl['dmesg_lines']} lines, 0 Xid), but the nvidia kernel module is not loaded in this kernel "
            f"(GPU reached through /dev/dxg: {kl['dxg_device']}): Xid events are logged by the Windows driver and cannot appear here",
            "no Xid during acceptance, from a log the GPU driver writes to")
    else:
        add("kernel-log", "XID_PRESENT", "PASS", f"dmesg scanned ({kl['dmesg_lines']} lines): 0 Xid", "no Xid during acceptance")
    add("firmware", "FW_OFF_MATRIX / FW_DEPRECATED", "N/A",
        f"driver {g.get('driver')}, VBIOS {g.get('vbios')} recorded; no BMC/Redfish, no platform bundle to compare against",
        "BIOS, BMC, NIC, GPU firmware == the production bundle")

    counts = {s: sum(c["status"] == s for c in checks) for s in ("PASS", "WARN", "FAIL", "N/A")}
    verdict = "FAIL" if counts["FAIL"] else "WARN" if counts["WARN"] else "PASS"
    if verdict == "FAIL":
        decision = "REJECTED: repair and ticket"
    elif counts["N/A"]:
        decision = f"NOT VALIDATED: {counts['N/A']} required checks produced no evidence (N/A)"
    else:
        decision = "VALIDATED" if verdict == "PASS" else "VALIDATED only with a recorded waiver"

    # The same evidence against the chapter's unadapted HX8 policy.
    hx8 = []
    if len(gpus) != HX8["gpu_count"]:
        hx8.append(("GPU_COUNT", f"{len(gpus)} != {HX8['gpu_count']}"))
    if g.get("product") != HX8["gpu_product"]:
        hx8.append(("GPU_PRODUCT", f"{g.get('product')}"))
    if (g.get("memory_total_mib") or 0) < HX8["gpu_mem_mib"]:
        hx8.append(("HBM_CAPACITY", f"{g.get('memory_total_mib')} MiB < {HX8['gpu_mem_mib']}"))
    if loaded and (gen, width) != HX8["pcie"]:
        hx8.append(("PCIE_DEGRADED", f"Gen{gen:g} x{width:g} != Gen5 x16"))
    hx8.append(("NVLINK_DOWN", "0/18 links"))
    hx8.append(("NIC_COUNT", f"0 compute / {len(nd)} frontend != 8 / 2"))
    if any(n["mtu"] != HX8["mtu"] for n in nd):
        hx8.append(("NIC_MTU", f"MTU {nd[0]['mtu']} != {HX8['mtu']}"))
    if len(sto["nvme_devices"]) != HX8["nvme"]:
        hx8.append(("NVME_COUNT", f"{len(sto['nvme_devices'])} NVMe != {HX8['nvme']}"))
    if any(b < HX8["drive_gbs"] for _, b, _ in per):
        hx8.append(("NVME_DRIVE_SLOW", f"{', '.join(f'{b:.2f}' for _, b, _ in per)} GB/s < {HX8['drive_gbs']}"))
    if total < HX8["total_gbs"]:
        hx8.append(("STORAGE_THROUGHPUT_LOW", f"{total:.2f} GB/s < {HX8['total_gbs']}"))

    telemetry = {"samples": len(tele), "samples_loaded": len(loaded),
                 "temp_c": stats([r["temp_c"] for r in loaded]), "power_w": stats([r["power_w"] for r in loaded]),
                 "sm_mhz": stats([r["sm_mhz"] for r in loaded]), "sm_max_mhz": loaded[0]["sm_max_mhz"] if loaded else None,
                 "reasons_share": {x: sum(x in r["reasons"] for r in loaded) / len(loaded) for x in seen} if loaded else {},
                 "counter_deltas_us": dc, "tflops": stats(w)}
    record = {"node": host["hostname"], "collected_at": host["collected_at"], "acceptance_policy": policy["policy_version"],
              "firmware": {"kernel": host["kernel"], "gpu_driver": g.get("driver"), "gpu_vbios": g.get("vbios")},
              "gpus": [{"index": g.get("index"), "uuid": g.get("uuid"), "bdf": g.get("bdf"), "product": g.get("product"),
                        "hbm_total_mib": g.get("memory_total_mib"),
                        "pcie": {"gen": gen if loaded else None, "width": width if loaded else None, "gen_idle": g.get("pcie_idle", {}).get("gen")},
                        "nvlink_links_up": None, "ecc": None, "row_remap": rr,
                        "burn_in": {"duration_h": st["seconds"] / 3600, "max_temp_c": tmax, "throttle_reasons": seen}}] if gpus else [],
              "dcgm_diag": None,
              "nics": [{"name": n["name"], "role": "frontend", "link_state": n["operstate"], "speed_mbps": n["speed_mbps"], "mtu": n["mtu"]} for n in nd],
              "gdr": None,
              "storage": {"nvme": [], "data_disks": [{"device": dv, "seq_read_gbs": b} for dv, b, _ in per], "fio_seq_read_gbs": total},
              "nccl_single_node": None, "xid_events": kl["xid_lines"],
              "_note": "None means not collected on this platform (N/A), never zero."}
    return {"lab": "ch16-handson", "policy_version": policy["policy_version"], "checks": checks, "counts": counts,
            "verdict_on_checks_that_ran": verdict, "decision": decision, "hx8_policy_codes": hx8,
            "telemetry": telemetry, "numerics": num_, "memory_pattern": mp, "host_memory_pattern": pt,
            "disks": [{"device": dv, "median_GBps": b, "runs_GBps": bws} for dv, b, bws in per],
            "gpu": {k: g.get(k) for k in ("product", "memory_total_mib", "driver", "vbios", "bdf", "pcie_max", "pcie_idle")},
            "stress_seconds": st["seconds"], "record": record}


def report(run: Path, s: dict, env: dict, policy: dict) -> str:
    t = s["telemetry"]
    L = [f"# Chapter 16 hands-on: acceptance report for `{s['node']}` (`{run.name}`)", "",
         f"Policy `{s['policy_version']}` (derived from the chapter's `acc-2026.10`; adaptations listed below). "
         f"Collected {s['collected_at']}; {env.get('cpu')}, {env.get('mem_gib')} GiB, kernel {env.get('kernel')}. "
         "Every value in the evidence column is `[MEASURED]` on this machine by the stage named; thresholds are the "
         "chapter's `[ILLUSTRATIVE]` values unless marked lab-local.", "",
         f"**Verdict on the checks that ran: {s['verdict_on_checks_that_ran']}** "
         f"({s['counts']['PASS']} PASS, {s['counts']['WARN']} WARN, {s['counts']['FAIL']} FAIL).  ",
         f"**Acceptance decision: {s['decision']}.**", "",
         "N/A is not PASS: an N/A check produced no evidence, so it cannot support a claim that the node is healthy. "
         "A fleet controller treats N/A on a required check like a missing test result and keeps the node out of "
         "`validated` (Figure 16.1).", "",
         "| Stage | Check (reason code) | Status | Evidence `[MEASURED]` | Criterion |", "|---|---|---|---|---|"]
    for c in s["checks"]:
        code = c["code"] + (" *(lab-local)*" if c["lab_local"] else "")
        L.append(f"| {c['stage']} | `{code}` | **{c['status']}** | {c['evidence']} | {c['criterion']} |")
    L += ["", "## Burn-in telemetry `[MEASURED]`", "",
          f"{s['stress_seconds']:.0f} s of FP16 GEMM stress, nvidia-smi sampled every 500 ms ({t['samples']} samples, "
          f"{t['samples_loaded']} at >= 90 % utilisation).", "",
          "| Signal under load | median | p95 | min-max |", "|---|---|---|---|"]
    for k, lab in (("tflops", "GEMM TFLOP/s per 1 s window"), ("temp_c", "temperature C"), ("power_w", "power W"), ("sm_mhz", "SM clock MHz")):
        v = t[k]
        if v:
            L.append(f"| {lab} | {v['median']:.1f} | {v['p95']:.1f} | {v['min']:.1f}-{v['max']:.1f} |")
    L += ["", f"Clock-event reasons under load (share of samples): {t['reasons_share'] or 'none'}; maximum SM clock "
          f"{t['sm_max_mhz']} MHz. Driver counters accrued during the soak (µs): {t['counter_deltas_us']}.", "",
          "## The same evidence against the chapter's HX8 policy (`acc-2026.10`, unadapted)", "",
          "| Code | Why |", "|---|---|"]
    L += [f"| `{c}` | {why} |" for c, why in s["hx8_policy_codes"]]
    L += ["", "A laptop is not an HX8 node, so the unadapted policy rejects it on hardware it does not have. That is why "
          "`expected` is per SKU and versioned, while the thresholds (87 C, throttle-reason classes, numerics) transfer.", "",
          "## Policy adaptations", ""] + [f"- {x}" for x in policy["adaptations"]] + [""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    ap.add_argument("--policy", type=Path, default=HERE / "acceptance_policy_laptop.json")
    a = ap.parse_args()
    policy = json.loads(a.policy.read_text())
    s = evaluate(a.run, policy)
    env = json.loads((a.run / "environment.json").read_text())
    record = s.pop("record")
    (a.run / "acceptance_record.json").write_text(json.dumps(record, indent=1))
    s["node"], s["collected_at"] = record["node"], record["collected_at"]
    s["policy"] = policy
    (a.run / "summary.json").write_text(json.dumps(s, indent=1))
    (a.run / "report.md").write_text(report(a.run, s, env, policy))
    print(f"verdict on checks that ran: {s['verdict_on_checks_that_ran']}; decision: {s['decision']}")
    for c in s["checks"]:
        print(f"  {c['status']:4s}  {c['code']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
