"""Capstone B L2: a real counter collector on one host, parsed and rated by the L1 pipeline, plus Prometheus exposition.

What it teaches (starter-kit README section 8, L2; manuscript Ch 18 observability): a parser built
on a simulated bundle meets real counters with *different native names*. Rates are only right if
the deltas handle wraps and resets. A collector has a measurable cost that bounds its poll interval.
On this host the experiment
  1. probes for the RDMA NIC counters the L2 extension targets (``/sys/class/infiniband``, ethtool,
     rdma, mlnx_qos) and records what exists;
  2. drives a known, rate-limited TCP stream over the loopback interface (the only interface in the
     container), and polls the real kernel counters every second in the bundle's
     ``### collected_at=... host=... dev=... netdev=...`` format;
  3. parses the capture with the L1 ``parse_nic_ethtool``. With the stock map it finds **no**
     canonical counters, because the native names differ. With a host adapter map
     (``tx_bytes -> tx_bytes``) it does, and ``compute_rates`` then gives per-interval rates. These are
     checked against the bytes the application actually sent, and the remainder is the per-packet
     TCP/IP header overhead;
  4. replays the same real counter series as a 32-bit counter, offset so that it wraps mid-run, and
     shows that ``counter_delta`` recovers every interval exactly;
  5. exposes GPU telemetry (power, SM clock, temperature, utilization, clock-event reasons) and the
     interface counters as Prometheus text exposition, re-parses the exposition, and validates names,
     types, counter monotonicity and physical ranges. It also measures the collector's cost per scrape.

Not runnable here: RDMA hw_counters (``np_cnp_sent`` and the rest), ``ethtool -S`` on an mlx5 netdev,
PFC/ECN configuration (``mlnx_qos``), and the L3 incast and switch-telemetry drill. Each is probed.

CPU fallback: the same loopback collector, L1 parsing, wrap test and exposition, without GPU metrics.
The GPU-only invariants are skipped.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import socket
import statistics
import subprocess
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "capstone-b-l2",
    "title": "Capstone B L2: real counter collection, L1 rate pipeline and Prometheus exposition",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same loopback-interface collector, L1 parse/rate/wrap checks and Prometheus exposition of "
                     "interface and process counters, without GPU metrics; RDMA NIC counters are recorded as not runnable"),
}

PKG = Path(__file__).resolve().parents[2]
NET = Path("/sys/class/net")
GPU_FIELDS = ["power.draw", "clocks.sm", "temperature.gpu", "utilization.gpu", "clocks_event_reasons.active", "power.max_limit"]
REASONS = {0x1: "idle", 0x4: "sw_power_cap", 0x8: "hw_slowdown", 0x20: "sw_thermal", 0x40: "hw_thermal", 0x80: "hw_power_brake"}
NAME_RE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")


def load_l1(name: str):
    for p in (PKG / "instructor" / "reference" / f"{name}.py", PKG / "starter-kit" / "starter" / f"{name}.py"):
        if p.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, p.relative_to(PKG).as_posix()
    return None, None


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pct(xs, p):
    s = sorted(xs)
    return s[min(len(s) - 1, round(p / 100 * (len(s) - 1)))] if s else float("nan")


def probes() -> dict:
    ib = Path("/sys/class/infiniband")
    devs = sorted(os.listdir(ib)) if ib.is_dir() else []
    return {"rdma_devices": devs, "hw_counters": sorted(os.listdir(ib / devs[0] / "ports" / "1" / "hw_counters")) if devs else [],
            "net_interfaces": sorted(os.listdir(NET)) if NET.is_dir() else [], "ethtool": bool(shutil.which("ethtool")),
            "rdma_tool": bool(shutil.which("rdma")), "mlnx_qos": bool(shutil.which("mlnx_qos")),
            "gnmic": bool(shutil.which("gnmic")), "nvidia_smi": bool(shutil.which("nvidia-smi"))}


# ---------------------------------------------------------------------------------- traffic and collection
class LoopbackStream:
    """A rate-limited TCP stream over 127.0.0.1; ``sent`` counts application bytes handed to the kernel."""

    def __init__(self, rate_bytes_s: float, chunk: int = 256 * 1024):
        self.rate, self.chunk, self.sent, self.stop = rate_bytes_s, chunk, 0, threading.Event()
        self.srv = socket.socket()
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(1)
        self.port = self.srv.getsockname()[1]

    def _sink(self):
        conn, _ = self.srv.accept()
        with conn:
            while conn.recv(1 << 20):
                pass

    def _source(self):
        s = socket.create_connection(("127.0.0.1", self.port))
        buf = b"\0" * self.chunk
        t0 = time.monotonic()
        with s:
            while not self.stop.is_set():
                if self.sent > self.rate * (time.monotonic() - t0):
                    time.sleep(0.001)
                    continue
                s.sendall(buf)
                self.sent += len(buf)

    def __enter__(self):
        self.ts = threading.Thread(target=self._sink, daemon=True)
        self.tc = threading.Thread(target=self._source, daemon=True)
        self.ts.start()
        self.tc.start()
        return self

    def __exit__(self, *a):
        self.stop.set()
        self.tc.join(timeout=5)
        self.ts.join(timeout=5)
        self.srv.close()
        return False


def read_if(dev: str) -> dict:
    d = NET / dev / "statistics"
    return {k: int((d / k).read_text()) for k in ("rx_bytes", "tx_bytes", "rx_packets", "tx_packets", "rx_dropped", "tx_dropped")}


def gpu_sample() -> dict | None:
    if not shutil.which("nvidia-smi"):
        return None
    out = subprocess.run(["nvidia-smi", f"--query-gpu={','.join(GPU_FIELDS)}", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, timeout=10).stdout.strip().splitlines()
    if not out:
        return None
    vals = [v.strip() for v in out[0].split(",")]
    return {k: (int(v, 16) if v.startswith("0x") else num(v)) for k, v in zip(GPU_FIELDS, vals)}


def gpu_reason_counters() -> dict:
    """Cumulative clock-event-reason counters (microseconds) from nvidia-smi -q -d PERFORMANCE."""
    out = subprocess.run(["nvidia-smi", "-q", "-d", "PERFORMANCE"], capture_output=True, text=True, timeout=10).stdout
    return {k.strip().lower().replace(" ", "_"): int(v) for k, v in re.findall(r"^\s+([A-Za-z ]+?)\s*:\s*(\d+) us", out, re.M)}


def exposition(dev: str, ifc: dict, gpu: dict | None, reasons: dict, cpu_s: float, scrape_s: float) -> str:
    """Prometheus text exposition format 0.0.4 (one scrape)."""
    L = []

    def metric(name, typ, help_, samples):
        L.append(f"# HELP {name} {help_}")
        L.append(f"# TYPE {name} {typ}")
        for labels, v in samples:
            lab = ",".join(f'{k}="{val}"' for k, val in labels.items())
            L.append(f"{name}{{{lab}}} {v}" if lab else f"{name} {v}")

    metric("node_network_transmit_bytes_total", "counter", "Bytes transmitted (kernel interface counter).", [({"device": dev}, ifc["tx_bytes"])])
    metric("node_network_receive_bytes_total", "counter", "Bytes received (kernel interface counter).", [({"device": dev}, ifc["rx_bytes"])])
    metric("node_network_transmit_packets_total", "counter", "Packets transmitted.", [({"device": dev}, ifc["tx_packets"])])
    metric("node_network_receive_drop_total", "counter", "Received packets dropped.", [({"device": dev}, ifc["rx_dropped"])])
    metric("process_cpu_seconds_total", "counter", "Collector process CPU time.", [({}, round(cpu_s, 4))])
    if gpu:
        g = {"gpu": "0"}
        metric("gpu_power_watts", "gauge", "Board power draw (nvidia-smi power.draw).", [(g, gpu["power.draw"])])
        metric("gpu_sm_clock_hertz", "gauge", "SM clock.", [(g, int((gpu["clocks.sm"] or 0) * 1e6))])
        metric("gpu_temperature_celsius", "gauge", "GPU core temperature.", [(g, gpu["temperature.gpu"])])
        metric("gpu_utilization_ratio", "gauge", "Fraction of time a kernel was running.", [(g, (gpu["utilization.gpu"] or 0) / 100)])
        mask = int(gpu["clocks_event_reasons.active"] or 0)
        metric("gpu_clock_event_reason_active", "gauge", "1 if the clock-event reason is active now.",
               [({**g, "reason": n}, int(bool(mask & b))) for b, n in REASONS.items()])
        if reasons:
            metric("gpu_clock_event_reason_seconds_total", "counter", "Cumulative time clocks were held by a reason.",
                   [({**g, "reason": k}, v / 1e6) for k, v in sorted(reasons.items())])
    metric("collector_scrape_duration_seconds", "gauge", "Time the collector spent producing this scrape.", [({}, round(scrape_s, 6))])
    return "\n".join(L) + "\n"


def parse_exposition(text: str) -> tuple[dict, list[str]]:
    """Minimal parser: returns {(name, labels): value} and a list of format problems."""
    types, out, problems = {}, {}, []
    for line in text.splitlines():
        if line.startswith("# TYPE"):
            _, _, name, typ = line.split(None, 3)
            types[name] = typ
            continue
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([^{\s]+)(\{[^}]*\})?\s+(\S+)$", line)
        if not m:
            problems.append(f"unparseable line: {line!r}")
            continue
        name, labels, val = m.group(1), m.group(2) or "", m.group(3)
        if not NAME_RE.match(name):
            problems.append(f"bad metric name {name}")
        if name not in types:
            problems.append(f"{name} has no # TYPE line before its samples")
        if types.get(name) == "counter" and not name.endswith("_total"):
            problems.append(f"counter {name} should end in _total")
        try:
            out[(name, labels)] = float(val)
        except ValueError:
            problems.append(f"non-numeric value for {name}: {val}")
    return {"samples": out, "types": types}, problems


def collect(ctx, seconds: int, rate: float) -> dict:
    """Poll the loopback counters (and GPU telemetry) aligned to whole seconds while a known stream runs."""
    dev = "lo"
    host = socket.gethostname()
    blocks, polls, expos, cost_if, cost_gpu = [], [], [], [], []
    stop = threading.Event()
    load = None
    if ctx.is_gpu:                         # a duty-cycled GPU load so the telemetry has something to show
        torch = ctx.torch
        a = torch.randn(2048, 2048, device="cuda", dtype=torch.float16)

        def gpu_load():
            torch.cuda.set_device(0)
            while not stop.is_set():
                for _ in range(50):
                    a @ a
                torch.cuda.synchronize()
                time.sleep(0.02)
        load = threading.Thread(target=gpu_load, daemon=True)
        load.start()
    with LoopbackStream(rate) as stream:
        time.sleep(1.0 - (time.time() % 1.0) + 0.05)
        for i in range(seconds + 1):
            t0 = time.perf_counter()
            ifc = read_if(dev)
            sent = stream.sent
            t1 = time.perf_counter()
            gpu = gpu_sample() if ctx.is_gpu else None
            reasons = gpu_reason_counters() if ctx.is_gpu else {}
            t2 = time.perf_counter()
            cost_if.append(t1 - t0)
            if ctx.is_gpu:
                cost_gpu.append(t2 - t1)
            now = int(time.time())
            polls.append({"collected_at": now, "app_sent": sent, **ifc, "gpu": gpu, "reasons": reasons})
            blocks.append(f"### collected_at={now} host={host} dev={dev} netdev={dev} rail=-\n" +
                          "\n".join(f"     {k}: {v}" for k, v in ifc.items()))
            expos.append(exposition(dev, ifc, gpu, reasons, time.process_time(), t2 - t0))
            if i < seconds:
                time.sleep(max(0.0, 1.0 - (time.time() % 1.0) + 0.05))
    stop.set()
    if load:
        load.join(timeout=5)
    return {"device": dev, "text": "\n".join(blocks) + "\n", "polls": polls, "expositions": expos,
            "cost_if_s": cost_if, "cost_gpu_s": cost_gpu}


# ---------------------------------------------------------------------------------- analysis with the L1 pipeline
def l1_analysis(cap: dict) -> dict:
    tel, src = load_l1("telemetry")
    if tel is None:
        return {"available": False, "why": "no L1 telemetry model found"}
    import pandas as pd
    try:
        stock = tel.parse_nic_ethtool(cap["text"])
        saved = dict(tel.NIC_ETHTOOL_MAP)
        adapter = {"tx_bytes": "tx_bytes", "rx_bytes": "rx_bytes", "rx_dropped": "rx_discards", "tx_dropped": "tx_discards"}
        tel.NIC_ETHTOOL_MAP.clear()
        tel.NIC_ETHTOOL_MAP.update(adapter)
        try:
            adapted = tel.parse_nic_ethtool(cap["text"])
        finally:
            tel.NIC_ETHTOOL_MAP.clear()
            tel.NIC_ETHTOOL_MAP.update(saved)
        profiles = {"platforms": {"nic_ethtool": {"counter_width_bits": {"default": 64}}}}
        rates = tel.compute_rates(adapted, profiles)
    except NotImplementedError as e:
        return {"available": False, "why": f"starter telemetry.py not implemented yet ({e})"}
    tx = rates[rates["counter"] == "tx_bytes"].reset_index(drop=True)
    polls = cap["polls"]
    rows = []
    for i in range(1, len(polls)):
        p0, p1 = polls[i - 1], polls[i]
        r = tx.iloc[i - 1] if i - 1 < len(tx) else None
        d_app = p1["app_sent"] - p0["app_sent"]
        d_ctr = p1["tx_bytes"] - p0["tx_bytes"]
        d_pkt = p1["tx_packets"] - p0["tx_packets"]
        rows.append({"interval": i, "dt_s": float(r["dt_s"]) if r is not None else None, "valid": bool(r["valid"]) if r is not None else False,
                     "l1_rate_Bps": float(r["rate"]) if r is not None and r["valid"] else None, "counter_delta": d_ctr,
                     "l1_delta": float(r["delta"]) if r is not None and r["valid"] else None, "app_delta": d_app, "packets": d_pkt,
                     "overhead_per_packet": (d_ctr - d_app) / d_pkt if d_pkt else None})
    # 32-bit wrap replay of the real series
    tx_vals = [p["tx_bytes"] for p in polls]
    span = tx_vals[-1] - tx_vals[0]
    offset = 2 ** 32 - tx_vals[0] - span // 2
    masked = [(v + offset) % 2 ** 32 for v in tx_vals]
    wraps = sum(1 for a, b in zip(masked, masked[1:]) if b < a)
    recovered = [tel.counter_delta(a, b, 32, max_delta=4e9) for a, b in zip(masked, masked[1:])]
    truth = [b - a for a, b in zip(tx_vals, tx_vals[1:])]
    return {"available": True, "source": src, "stock_rows": len(stock), "stock_counters": sorted(stock["counter"].unique()) if len(stock) else [],
            "native_names_present": sorted({ln.split(":")[0].strip() for ln in cap["text"].splitlines() if ln.startswith("     ")}),
            "adapter_map": adapter, "adapted_rows": len(adapted), "adapted_counters": sorted(adapted["counter"].unique()),
            "rates_invalid": int((~rates["valid"]).sum()), "intervals": rows,
            "wrap_test": {"offset": offset, "wraps": wraps, "recovered_exact": recovered == truth, "n": len(truth),
                          "deltas_32bit": recovered[:5], "deltas_true": truth[:5]}}


def run(ctx) -> dict:
    seconds = 6 if ctx.quick else 30
    rate = 200e6
    pr = probes()
    cap = collect(ctx, seconds, rate)
    ana = l1_analysis(cap)
    parsed = [parse_exposition(e) for e in cap["expositions"]]
    problems = sorted({p for _, ps in parsed for p in ps})
    series = {}
    for (doc, _), poll in zip(parsed, cap["polls"]):
        for key, v in doc["samples"].items():
            series.setdefault(key, []).append(v)
    types = parsed[-1][0]["types"]
    non_mono = [f"{k[0]}{k[1]}" for k, vs in series.items() if types.get(k[0]) == "counter" and any(b < a for a, b in zip(vs, vs[1:]))]
    reason_rates = {}
    for k, vs in series.items():
        if k[0] == "gpu_clock_event_reason_seconds_total" and len(vs) > 1:
            reason_rates[k[1]] = (vs[-1] - vs[0]) / seconds
    ivs = [r for r in ana.get("intervals", []) if r["valid"]] if ana.get("available") else []
    oh = [r["overhead_per_packet"] for r in ivs if r["overhead_per_packet"] is not None]
    rates = [r["l1_rate_Bps"] for r in ivs if r["l1_rate_Bps"]]
    metrics = {"polls": len(cap["polls"]), "loopback_rate_MBps_median": round(statistics.median(rates) / 1e6, 1) if rates else None,
               "header_overhead_B_per_pkt_median": round(statistics.median(oh), 1) if oh else None,
               "scrape_cost_ms_if_median": round(statistics.median(cap["cost_if_s"]) * 1e3, 3),
               "exposition_problems": len(problems)}
    if cap["cost_gpu_s"]:
        metrics["scrape_cost_ms_gpu_median"] = round(statistics.median(cap["cost_gpu_s"]) * 1e3, 1)
        metrics["scrape_cost_ms_gpu_p95"] = round(pct(cap["cost_gpu_s"], 95) * 1e3, 1)
    gpu_rows = [p["gpu"] for p in cap["polls"] if p["gpu"]]
    nr = [{"part": "RDMA NIC hw_counters (np_cnp_sent, rp_cnp_handled, out_of_sequence, ...) and ethtool -S on an mlx5 netdev",
           "probe": f"/sys/class/infiniband={pr['rdma_devices'] or 'none'}; interfaces={pr['net_interfaces']}; ethtool={pr['ethtool']}",
           "needs": ["host with an mlx5-class RDMA NIC", "root for ethtool/sysfs reads"],
           "fallback": "kernel loopback counters collected in the same native format"},
          {"part": "PFC/ECN configuration (mlnx_qos) and rdma statistic", "probe": f"mlnx_qos={pr['mlnx_qos']}, rdma={pr['rdma_tool']}",
           "needs": ["vendor NIC tools"], "fallback": "none"},
          {"part": "L3: switch streaming telemetry (gNMI) and incast with ECN disabled", "probe": f"gnmic={pr['gnmic']}, single host",
           "needs": ["2+ RDMA hosts", "lab switch with PFC/ECN"], "fallback": "none"}]
    return {"metrics": metrics, "probes": pr, "l1": ana, "capture_text": cap["text"], "polls": cap["polls"],
            "exposition_last": cap["expositions"][-1], "exposition_problems": problems, "non_monotonic_counters": non_mono,
            "reason_rates_s_per_s": reason_rates, "scrape_cost": {"if_ms": [x * 1e3 for x in cap["cost_if_s"]],
                                                                "gpu_ms": [x * 1e3 for x in cap["cost_gpu_s"]]},
            "gpu_samples": gpu_rows, "stream_rate_target_Bps": rate, "seconds": seconds, "not_runnable_parts": nr,
            "notes": ["Polls aligned to whole seconds (collected_at is integer epoch seconds, as in the bundle).",
                      f"Traffic: one TCP stream over 127.0.0.1, rate-limited to {rate / 1e6:.0f} MB/s of application bytes.",
                      "The 32-bit wrap test replays the real tx_bytes series modulo 2^32 with an offset; the wrap is synthetic, "
                      "the deltas are real."]}


def check(result: dict, env: dict) -> list[str]:
    fails = []
    a = result["l1"]
    if not a.get("available"):
        return fails
    if a["stock_rows"] != 0:
        fails.append("the stock NIC map matched loopback counters: the native-name gap the lab teaches is not being shown")
    if a["adapted_rows"] == 0:
        fails.append("the adapter map produced no rows: the collector's native format does not match parse_nic_ethtool")
    if a["rates_invalid"]:
        fails.append(f"{a['rates_invalid']} intervals invalid in compute_rates: polls landed in the same second (bad_dt) "
                     "or a counter reset; check the poll alignment")
    ivs = [r for r in a["intervals"] if r["valid"]]
    for r in ivs:
        if r["l1_delta"] is not None and int(r["l1_delta"]) != r["counter_delta"]:
            fails.append(f"interval {r['interval']}: L1 delta {r['l1_delta']} != raw counter delta {r['counter_delta']}")
    # Over the whole run the interface must have carried at least the application bytes (minus what can sit in
    # socket buffers at the last poll; per interval the two samples are skewed by up to a chunk in flight).
    ctr = sum(r["counter_delta"] for r in a["intervals"])
    app = sum(r["app_delta"] for r in a["intervals"])
    if ctr < app - 8 * 2 ** 20:
        fails.append(f"the interface counted {ctr} B but the application sent {app} B: the counter is not this stream's path")
    oh = [r["overhead_per_packet"] for r in ivs if r["overhead_per_packet"] is not None and r["app_delta"] > 0]
    if oh and not (20 <= statistics.median(oh) <= 200):
        fails.append(f"median per-packet overhead {statistics.median(oh):.0f} B is outside a TCP/IPv4 header's 20-200 B: "
                     "the rate is not the stream we generated")
    target = result["stream_rate_target_Bps"]
    app_rates = [r["app_delta"] / r["dt_s"] for r in ivs if r["dt_s"]]
    if app_rates and statistics.median(app_rates) > 1.10 * target:
        fails.append("application rate above the configured rate limit: the rate limiter is broken")
    w = a["wrap_test"]
    if w["wraps"] < 1:
        fails.append("the 32-bit replay did not wrap: the offset is wrong")
    if not w["recovered_exact"]:
        fails.append("counter_delta did not recover the true deltas across a 32-bit wrap")
    if result["exposition_problems"]:
        fails.append(f"Prometheus exposition problems: {result['exposition_problems'][:3]}")
    if result["non_monotonic_counters"]:
        fails.append(f"counters decreased between scrapes: {result['non_monotonic_counters'][:3]}")
    if env["device"] == "cuda":
        g = result["gpu_samples"]
        if len(g) < 3:
            fails.append("fewer than 3 GPU telemetry samples")
        for s in g:
            if not (0 <= (s["utilization.gpu"] or 0) <= 100) or not (0 < (s["temperature.gpu"] or 0) < 110):
                fails.append(f"GPU telemetry out of physical range: {s}")
                break
            pmax = s.get("power.max_limit")
            if pmax and s["power.draw"] > 1.10 * pmax:
                fails.append(f"power {s['power.draw']} W above power.max_limit {pmax} W")
                break
        for k, v in result["reason_rates_s_per_s"].items():
            if v > 1.05:
                fails.append(f"clock-event reason counter {k} advanced {v:.2f} s per s: a cumulative time counter cannot exceed 1 s/s")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    a, m = result["l1"], result["metrics"]
    L = ["## What exists on this host", "",
         f"RDMA devices: {result['probes']['rdma_devices'] or 'none'}; interfaces: {result['probes']['net_interfaces']}; "
         f"ethtool: {result['probes']['ethtool']}; rdma: {result['probes']['rdma_tool']}; mlnx_qos: {result['probes']['mlnx_qos']}.",
         "", "Collector output (first block, bundle format):", "", "```text", result["capture_text"].split("\n###")[0].strip(), "```"]
    if a.get("available"):
        L += ["", f"## L1 pipeline on real counters (`{a['source']}`)", "",
              f"- `parse_nic_ethtool` with the stock map: **{a['stock_rows']} rows**. None of the native names here "
              f"({', '.join(a['native_names_present'])}) are mlx5 names.",
              f"- With a host adapter map {a['adapter_map']}: {a['adapted_rows']} rows, canonical counters {a['adapted_counters']}.",
              f"- `compute_rates`: {a['rates_invalid']} invalid intervals.", "",
              "| Interval | dt (s) | L1 rate (MB/s) | counter delta (B) | app bytes | packets | overhead (B/pkt) |", "|---|---|---|---|---|---|---|"]
        for r in a["intervals"]:
            L.append(f"| {r['interval']} | {r['dt_s']:.0f} | {(r['l1_rate_Bps'] or 0) / 1e6:.1f} | {r['counter_delta']} | {r['app_delta']} | "
                     f"{r['packets']} | {r['overhead_per_packet'] if r['overhead_per_packet'] is None else round(r['overhead_per_packet'], 1)} |")
        w = a["wrap_test"]
        L += ["", f"32-bit replay: {w['wraps']} wrap(s) across {w['n']} intervals; `counter_delta(prev, cur, 32)` recovered every true delta "
              f"exactly: **{w['recovered_exact']}**."]
    else:
        L += ["", f"L1 pipeline skipped: {a.get('why')}"]
    sc = result["scrape_cost"]
    L += ["", "## Prometheus exposition (last scrape)", "", "```text", result["exposition_last"].strip(), "```", "",
          f"Re-parsed {m['polls']} scrapes: {m['exposition_problems']} format problems, counters monotonic: {not result['non_monotonic_counters']}.",
          "", "| Collector step | median (ms) | p95 (ms) |", "|---|---|---|",
          f"| sysfs interface counters | {statistics.median(sc['if_ms']):.3f} | {pct(sc['if_ms'], 95):.3f} |"]
    if sc["gpu_ms"]:
        L.append(f"| nvidia-smi query + PERFORMANCE counters | {statistics.median(sc['gpu_ms']):.1f} | {pct(sc['gpu_ms'], 95):.1f} |")
    L += ["", "## Not runnable here", ""]
    for p in result["not_runnable_parts"]:
        L.append(f"- **{p['part']}**. Probe: {p['probe']}. Needs: {', '.join(p['needs'])}. Fallback: {p['fallback']}.")
    L += ["", "## What to conclude", "",
          "- A parser validated only on the simulated bundle returns *nothing* on a new driver. That is silent, and worse than "
          "an error. Record the native names each driver/firmware exposes, and map them explicitly.",
          f"- Interface byte counters include headers: here ~{m['header_overhead_B_per_pkt_median']} B per packet on top of the application "
          "bytes. Compare like with like before calling a rate 'wrong'.",
          "- Wrap handling is only correct if the counter width is known per native name (device_profiles.yaml). A 64-bit "
          "assumption on a 32-bit counter turns every wrap into a fake reset or a negative rate."]
    if gpu:
        L.append(f"- Each nvidia-smi scrape costs ~{m.get('scrape_cost_ms_gpu_median')} ms of wall time (p95 {m.get('scrape_cost_ms_gpu_p95')} ms). "
                 "For sub-second telemetry use a resident agent (DCGM exporter, NVML), not a process per poll. "
                 "This is a laptop Ada GPU, not an H100 node.")
    else:
        L.append("- _CPU fallback: no GPU was used. GPU metrics and their physical-range invariants were skipped._")
    return "\n".join(L)
