"""Ch 10 L2: probe for a NIC and optic; soak-test the one physical link this host has (the GPU's PCIe link).

The chapter's L2 extension snapshots a 100G+ NIC port twice, 600 s apart, under load: DOM
(``ethtool -m``), FEC mode and statistics, and driver error counters, then runs the analyzer on the
deltas. This host has no NIC port and no pluggable module, so that part is probed and recorded as not
runnable.

The *method* applies to any serial link, and the host does have one under test: the GPU's PCIe link.
PCIe has the same physical-layer vocabulary as an optical port. It has a capability and a negotiated
rate (``LnkCap`` vs ``LnkSta``, like a 400G optic linked at 200G), line coding (128b/130b vs
256b/257b + RS-FEC), and an error counter (the data-link layer replays a TLP whose LCRC fails, like a
corrected FEC codeword). The experiment applies the chapter's soak procedure to it:

* snapshot at T0: negotiated generation/width versus capability, and ``Replays Since Reset`` /
  ``Replay Number Rollovers`` from the PCI section of ``nvidia-smi -q``;
* a sustained bidirectional copy load (H2D and D2H on separate streams), sampling the link state
  during the load, while counting every byte moved;
* snapshot at T1; deltas with the lab's own ``counter_delta`` (which handles counter resets);
* achieved throughput per direction against the coded line rate;
* what error rate the soak can *certify*. With k = 0 events in N bits, the 95 % upper bound is 3 / N
  (the "rule of three"). The report shows the soak length needed to certify the PCIe 1e-12 BER target,
  which is why the chapter asks for a 600 s window rather than a quick look.

Every run also executes the L1 analyzer (``analyze`` on ``lab/data/snapshot_t0/t1.csv``) as the
reference classification.

CPU fallback: no PCIe link is visible to the container (WSL2 guest PCI functions expose no link
status), so the fallback runs the L1 analyzer on the lab snapshots, probes for NICs, and tabulates the
soak duration needed to certify a BER at 400 Gb/s and at the PCIe rate `[MODELED]`.
"""
from __future__ import annotations

import importlib.util
import math
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch10-l2",
    "title": "Lab 10 L2: NIC/optic probe and a physical-layer soak of the GPU's PCIe link",
    "evidence": "MEASURED",
    "cpu_fallback": ("the L1 link-health analyzer on the lab snapshots, a NIC/optic probe of this host, and the soak "
                     "length needed to certify a BER [MODELED]; no PCIe link is visible without the GPU"),
}

PKG = Path(__file__).resolve().parents[2]
PCIE_GBPS_PER_LANE = {1: 0.25, 2: 0.5, 3: 0.985, 4: 1.969, 5: 3.938, 6: 7.563}  # GB/s per lane after line coding
PCIE_RAW_GT = {1: 2.5, 2: 5.0, 3: 8.0, 4: 16.0, 5: 32.0, 6: 64.0}  # GT/s per lane
PCIE_BER_TARGET = 1e-12   # PCIe base specification receiver BER target, Gen1-Gen5 (Gen6 uses FEC + FLIT)
ETH_PRE_FEC_THRESHOLD = 2.4e-4


def sh(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip("\n")
    except FileNotFoundError:
        return 127, f"{cmd[0]}: command not found"
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)


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


def probe_nic() -> dict:
    nets = {}
    for d in sorted(Path("/sys/class/net").iterdir()) if Path("/sys/class/net").is_dir() else []:
        nets[d.name] = {"speed": read(d / "speed"), "mtu": read(d / "mtu"), "operstate": read(d / "operstate"),
                        "device": (d / "device").exists()}
    return {"netdevs": nets, "physical_ports": [n for n, v in nets.items() if v["device"]],
            "tools": {t: bool(shutil.which(t)) for t in ("ethtool", "mlxlink", "ip")},
            "pci_link_status_files": sorted(str(p) for p in Path("/sys/bus/pci/devices").glob("*/current_link_speed"))}


def link_state() -> dict:
    """Negotiated and maximum generation/width (cheap query, used for sampling during the load)."""
    snap = {}
    rc, q = sh(["nvidia-smi", "--query-gpu=pcie.link.gen.gpumax,pcie.link.gen.gpucurrent,pcie.link.width.max,"
                "pcie.link.width.current", "--format=csv,noheader,nounits"])
    vals = [v.strip() for v in q.split(",")] if rc == 0 else []
    if len(vals) == 4:
        snap.update({"gen_max": int(vals[0]), "gen_cur": int(vals[1]), "width_max": int(vals[2]), "width_cur": int(vals[3])})
    return snap


def pci_snapshot() -> dict:
    """T0/T1 snapshot: the PCI section of ``nvidia-smi -q`` (replay counters, Tx/Rx throughput) plus the link state."""
    rc, out = sh(["nvidia-smi", "-q"])
    snap = {"ts": time.monotonic(), "raw_ok": rc == 0}
    for key, pat in (("replays", r"Replays Since Reset\s*:\s*(\d+)"), ("replay_rollovers", r"Replay Number Rollovers\s*:\s*(\d+)"),
                     ("tx_kbs", r"Tx Throughput\s*:\s*(\d+)"), ("rx_kbs", r"Rx Throughput\s*:\s*(\d+)")):
        m = re.search(pat, out)
        snap[key] = int(m.group(1)) if m else None
    snap.update(link_state())
    return snap


def l1_reference() -> dict:
    mod, src = load_l1("linkhealth")
    if mod is None:
        return {"error": "linkhealth module not found"}
    try:
        data = PKG / "lab" / "data"
        res = mod.analyze(mod.load_snapshot(data / "snapshot_t0.csv"), mod.load_snapshot(data / "snapshot_t1.csv"),
                          mod.load_schedule(data / "cabling_schedule.csv"), mod.load_yaml(data / "thresholds.yaml"))
        counts = res["primary"].value_counts().to_dict()
        return {"module": src, "ports": len(res), "by_primary": {str(k): int(v) for k, v in counts.items()},
                "by_layer": {str(k): int(v) for k, v in res["layer"].value_counts().to_dict().items()},
                "mod": mod}
    except Exception as exc:  # noqa: BLE001 - starter TODOs
        return {"module": src, "error": f"{type(exc).__name__}: {exc}"}


def certify_table() -> list[dict]:
    """Bits and soak time needed to certify a BER at 95 % confidence with zero errors (rule of three)."""
    rows = []
    for name, gbps in (("400GbE port (one direction)", 400.0), ("PCIe Gen4 x8 (one direction)", 16.0 * 8 * 128 / 130),
                       ("PCIe Gen5 x16 (one direction)", 32.0 * 16 * 128 / 130)):
        for target in (1e-12, 1e-15):
            bits = 3 / target
            rows.append({"link": name, "ber_target": target, "bits_needed": bits, "seconds_at_line_rate": bits / (gbps * 1e9)})
    return rows


def ber_bound(events: int, bits: float) -> float:
    """95 % upper bound on the per-bit event rate: 3/N for zero events, else a normal approximation."""
    if bits <= 0:
        return float("inf")
    if events == 0:
        return 3.0 / bits
    return (events + 1.96 * math.sqrt(events) + 1.92) / bits


def run(ctx) -> dict:
    torch = ctx.torch
    nic = probe_nic()
    ref = l1_reference()
    mod = ref.pop("mod", None)
    tables = {"certify": certify_table(), "nic_probe": [nic]}
    metrics = {"physical_ports": len(nic["physical_ports"]), "l1_ports_classified": ref.get("ports"),
               "l1_primary_counts": ref.get("by_primary")}
    notes = []
    not_runnable = [{
        "part": "NIC port soak: ethtool -m (DOM per lane), --show-fec / -I --show-fec, ethtool -S, ip -s -s link, 600 s apart",
        "needs": ["a 100G+ NIC port with a pluggable optic or DAC", "ethtool >= 5.13 (mlxlink for NVIDIA NICs)",
                  "root for ethtool -m", "a peer or loopback to carry load"], "probe": nic}]
    if not ctx.is_gpu:
        notes.append("CPU fallback: no PCIe link status is visible in this container; the soak table is [MODELED].")
        return {"metrics": metrics, "tables": tables, "notes": notes, "not_runnable_parts": not_runnable, "l1": ref}

    soak_s = 6.0 if ctx.quick else 60.0
    mib = 64 if ctx.quick else 256
    n = mib << 20
    h_src = torch.empty(n, dtype=torch.uint8).pin_memory()
    h_dst = torch.empty(n, dtype=torch.uint8).pin_memory()
    d_dst = torch.empty(n, dtype=torch.uint8, device="cuda")
    d_src = torch.empty(n, dtype=torch.uint8, device="cuda")
    s_h2d, s_d2h = torch.cuda.Stream(), torch.cuda.Stream()
    # warm-up so the link is at its loaded rate before T0
    for _ in range(3):
        d_dst.copy_(h_src, non_blocking=True)
        h_dst.copy_(d_src, non_blocking=True)
    torch.cuda.synchronize()
    uni = ctx.bench(lambda: d_dst.copy_(h_src, non_blocking=True))
    t0 = pci_snapshot()
    states, stop, moved = [], threading.Event(), {"h2d": 0, "d2h": 0}

    def sampler():
        while not stop.is_set():
            s = link_state()
            states.append({k: s.get(k) for k in ("gen_cur", "width_cur")})
            stop.wait(0.5)

    th = threading.Thread(target=sampler, daemon=True)
    th.start()
    windows = []
    t_start = time.perf_counter()
    while time.perf_counter() - t_start < soak_s or len(windows) < 5:
        w0 = time.perf_counter()
        for _ in range(8):
            with torch.cuda.stream(s_h2d):
                d_dst.copy_(h_src, non_blocking=True)
            with torch.cuda.stream(s_d2h):
                h_dst.copy_(d_src, non_blocking=True)
        torch.cuda.synchronize()
        dt = time.perf_counter() - w0
        moved["h2d"] += 8 * n
        moved["d2h"] += 8 * n
        windows.append({"h2d_gbs": 8 * n / dt / 1e9, "d2h_gbs": 8 * n / dt / 1e9, "seconds": dt})
    elapsed = time.perf_counter() - t_start
    stop.set()
    th.join(timeout=5)
    t1 = pci_snapshot()

    cd = mod.counter_delta if mod is not None and hasattr(mod, "counter_delta") else (lambda a, b: b - a if b >= a else b)
    replays = cd(t0["replays"], t1["replays"]) if t0["replays"] is not None and t1["replays"] is not None else None
    rollovers = cd(t0["replay_rollovers"], t1["replay_rollovers"]) if t0["replay_rollovers"] is not None else None
    bits = 8.0 * (moved["h2d"] + moved["d2h"])
    ceiling = PCIE_GBPS_PER_LANE[t0["gen_max"]] * t0["width_max"]
    per_dir = sorted(w["h2d_gbs"] for w in windows)
    med = per_dir[len(per_dir) // 2]
    bound = ber_bound(replays or 0, bits)
    secs_needed = 3 / PCIE_BER_TARGET / (bits / elapsed)
    loaded_gens = sorted({s["gen_cur"] for s in states if s["gen_cur"] is not None})
    loaded_widths = sorted({s["width_cur"] for s in states if s["width_cur"] is not None})
    metrics.update({
        "soak_s": round(elapsed, 2), "bytes_moved": moved["h2d"] + moved["d2h"], "bits_moved": bits,
        "link_capability": f"Gen{t0['gen_max']} x{t0['width_max']}", "raw_gt_per_lane": PCIE_RAW_GT[t0["gen_max"]],
        "link_gens_seen_under_load": loaded_gens, "link_widths_seen_under_load": loaded_widths,
        "replays_t0": t0["replays"], "replays_t1": t1["replays"], "replays_delta": replays, "replay_rollovers_delta": rollovers,
        "per_direction_gbs_median": round(med, 2), "unidirectional_h2d_gbs": round(n / uni["median"] / 1e9, 2), "bidirectional_gbs_median": round(2 * med, 2),
        "coded_ceiling_gbs_per_direction": round(ceiling, 2), "utilisation_per_direction": round(med / ceiling, 3),
        "replay_rate_upper_bound_per_bit": bound, "certifies_pcie_ber_target": bound <= PCIE_BER_TARGET,
        "soak_seconds_needed_for_1e-12": round(secs_needed, 1), "link_state_samples": len(states),
    })
    if mod is not None and hasattr(mod, "fec_margin_decades"):
        try:
            metrics["bound_margin_decades_vs_1e-12"] = round(mod.fec_margin_decades(bound, PCIE_BER_TARGET), 2)
        except Exception:  # noqa: BLE001
            pass
    tables.update({"uni_n": uni["n"], "snapshots": [dict(t0, at="T0"), dict(t1, at="T1")], "link_states": states, "windows": windows})
    ctx.log(f"soak {elapsed:.1f} s: {2 * med:.2f} GB/s bidirectional, {bits:.3g} bits, replays {replays}; "
            f"95 % bound {bound:.2e}/bit; link seen {loaded_gens} x{loaded_widths}")
    notes += [
        f"Load: {mib} MiB pinned H2D and D2H copies on two streams, 8 of each per timing window, for {elapsed:.1f} s.",
        "Replays are counted by the GPU's data-link layer; one replay means at least one TLP failed its LCRC check, so a "
        "bound on replays per bit is a bound on detected errors, not a full BER measurement.",
        "Link state was sampled every 0.5 s during the load with nvidia-smi.",
    ]
    del h_src, h_dst, d_src, d_dst
    return {"metrics": metrics, "tables": tables, "notes": notes, "not_runnable_parts": not_runnable, "l1": ref}


def check(result: dict, env: dict) -> list[str]:
    m = result["metrics"]
    fails = []
    l1 = result.get("l1", {})
    if "error" not in l1 and l1.get("ports") and sum(l1["by_primary"].values()) != l1["ports"]:
        fails.append("L1 analyzer: every port must get exactly one primary classification")
    for r in result["tables"]["certify"]:
        if abs(r["bits_needed"] * r["ber_target"] - 3) > 1e-6:
            fails.append("rule-of-three table is wrong: bits needed must be 3 / target")
    if env["device"] != "cuda":
        return fails
    if m["replays_delta"] is None:
        fails.append("no replay counter in the PCI section of nvidia-smi -q: check the driver exposes 'Replays Since Reset'")
    elif m["replays_delta"] < 0:
        fails.append("negative replay delta: counter_delta must never return a negative")
    if m["per_direction_gbs_median"] > 1.05 * m["coded_ceiling_gbs_per_direction"]:
        fails.append(f"{m['per_direction_gbs_median']} GB/s per direction exceeds the 128b/130b-coded ceiling "
                     f"{m['coded_ceiling_gbs_per_direction']} GB/s: check the byte accounting")
    cap = m["link_capability"]
    gmax, wmax = int(cap.split()[0][3:]), int(cap.split()[1][1:])
    if any(g > gmax for g in m["link_gens_seen_under_load"]) or any(w > wmax for w in m["link_widths_seen_under_load"]):
        fails.append("the link reported a state above its capability: nvidia-smi fields are inconsistent")
    if m["link_state_samples"] < 5:
        fails.append("fewer than 5 link-state samples during the soak: lengthen it")
    if m["replays_delta"] == 0 and abs(m["replay_rate_upper_bound_per_bit"] - 3 / m["bits_moved"]) > 1e-30:
        fails.append("with zero events the 95 % bound must be exactly 3 / bits")
    return fails


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    l1 = result.get("l1", {})
    lines = []
    if env["device"] == "cuda":
        g = m["link_gens_seen_under_load"]
        w = m["link_widths_seen_under_load"]
        full = g == [int(m["link_capability"].split()[0][3:])] and w == [int(m["link_capability"].split()[1][1:])]
        lines += ["## PCIe link soak `[MEASURED]`", "",
                  "| Quantity | T0 | T1 | Delta |", "|---|---|---|---|",
                  f"| Replays since reset | {m['replays_t0']} | {m['replays_t1']} | {m['replays_delta']} |",
                  f"| Replay number rollovers | {t['snapshots'][0]['replay_rollovers']} | {t['snapshots'][1]['replay_rollovers']} | "
                  f"{m['replay_rollovers_delta']} |", "",
                  "| Quantity | Value |", "|---|---|",
                  f"| Capability | {m['link_capability']} ({m['raw_gt_per_lane']} GT/s per lane, 128b/130b) |",
                  f"| Negotiated under load | Gen{'/'.join(map(str, g))} x{'/'.join(map(str, w))} ({m['link_state_samples']} samples) |",
                  f"| Soak | {m['soak_s']} s, {m['bytes_moved'] / 1e9:.1f} GB moved ({m['bits_moved']:.3g} bits) |",
                  f"| Per direction (median window) | {m['per_direction_gbs_median']} GB/s of {m['coded_ceiling_gbs_per_direction']} "
                  f"GB/s coded ceiling ({m['utilisation_per_direction'] * 100:.0f} %) |",
                  f"| H2D alone (median of {t['uni_n']}) | {m['unidirectional_h2d_gbs']} GB/s |",
                  f"| 95 % upper bound on replay events per bit | {m['replay_rate_upper_bound_per_bit']:.2e} |",
                  f"| Certifies the PCIe 1e-12 target? | {'yes' if m['certifies_pcie_ber_target'] else 'no'} |",
                  f"| Soak needed to certify 1e-12 at this rate | {m['soak_seconds_needed_for_1e-12']} s |", "",
                  "What to conclude:", "",
                  f"- The link {'held its full capability' if full else 'ran BELOW its capability'} under load "
                  f"(Gen{'/'.join(map(str, g))} x{'/'.join(map(str, w))} of {m['link_capability']}) and moved "
                  f"{m['bits_moved']:.2g} bits with {m['replays_delta']} replays. "
                  + ("Zero errors is not a BER of zero: it only bounds the rate below " if m["replays_delta"] == 0
                     else "With replays present the 95 % bound is ")
                  + f"{m['replay_rate_upper_bound_per_bit']:.1e} per bit at 95 % confidence.",
                  f"- To certify 1e-12 this soak would need about {m['soak_seconds_needed_for_1e-12']:.0f} s at the achieved rate, "
                  "and 1e-15 a thousand times longer. The same arithmetic is why the chapter's optics check differences "
                  "counters 600 s apart under load and why pre-FEC BER (millions of corrected codewords) is the useful early "
                  "signal on a 400G port, not post-FEC errors.",
                  f"- With both directions busy each got {m['per_direction_gbs_median']} GB/s against "
                  f"{m['unidirectional_h2d_gbs']} GB/s for H2D alone: the full-duplex link is not the only shared resource "
                  "(DMA engines, host memory and the root complex are too). Measure the load you will actually run.",
                  "- Read capability *and* negotiated state, under load: a link that trains down (x8 to x4, Gen4 to Gen3) passes "
                  "every ping and halves throughput, exactly like a 400G optic linked at 200G.",
                  "- This is a laptop GPU's PCIe link, not a 400G optical port: there is no DOM, no FEC histogram and no lane "
                  "power to read. Those rows of the analyzer need the L2 NIC host."]
    lines += ["", "## Soak length needed to certify a BER (zero errors, 95 %) `[MODELED]`", "",
              "| Link | BER target | Bits needed | Seconds at line rate |", "|---|---|---|---|"]
    for r in t["certify"]:
        lines.append(f"| {r['link']} | {r['ber_target']:.0e} | {r['bits_needed']:.1e} | {r['seconds_at_line_rate']:.1f} |")
    lines += ["", "## L1 analyzer on the lab snapshots (reference)", ""]
    if "error" in l1:
        lines.append(f"_Not run: {l1['error']}._")
    else:
        lines.append(f"{l1['ports']} ports classified by `{l1['module']}`: " +
                     ", ".join(f"{k} {v}" for k, v in sorted(l1["by_primary"].items())) + ".")
    if env["device"] != "cuda":
        lines += ["", "_CPU fallback: no GPU, so no PCIe link was soaked; the link-state, replay and throughput invariants "
                  "were skipped._"]
    lines += ["", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}. Probe: physical ports "
                     f"{p['probe']['physical_ports'] or 'none'}, interfaces {list(p['probe']['netdevs'])}.")
    return "\n".join(lines)
