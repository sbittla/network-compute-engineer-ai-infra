"""Capstone A L2: host topology, GPU/NIC locality and measured GPU power on one host.

What it teaches (starter-kit README section 8, L2; manuscript Ch 2 power and cooling, Ch 4 node
anatomy): the design pack's rack-power and locality assumptions must be replaced by measured values.
On this host the experiment
  1. probes the topology the design relies on (``nvidia-smi topo -m``, NUMA nodes, GPU PCIe link,
     RDMA NICs, BMC), recording what exists and what does not;
  2. measures GPU board power at idle and under a sustained GEMM load, sampled every 200 ms through
     nvidia-smi, together with SM clock, temperature and the clock-event reasons. It reports the median
     (sustained) and the maximum, and the ratio between them;
  3. reruns the L1 rack-power and 2N feed check (``cluster_model.rack_power``) with the HX8 node's
     ``watts_sustained`` rescaled by the sustained/maximum ratio measured here. This is a sensitivity
     analysis labelled ``[MODELED]``. It does not claim to measure an HX8 node;
  4. shows the cost of a power cap. Under the enforced board limit the SM clock settles well below
     ``clocks.max.sm``, which is the straggler mechanism behind the exemplar's warning about capping
     rack-05's GPUs.

Not runnable here: GPU<->NIC PCIe affinity (no RDMA NICs), lstopo/hwloc, chassis power from the BMC
(ipmitool dcmi / Redfish), an 8-GPU all_reduce_perf load, and the 30-minute chassis log. Each is probed.

CPU fallback: the topology probe and a sustained CPU GEMM load with throughput stability. CPU package
power is not readable in the container (no RAPL powercap), so that part is recorded as not runnable,
and the L1 rack-power check runs with the design's own values only.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import statistics
import subprocess
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "capstone-a-l2",
    "title": "Capstone A L2: host topology, GPU/NIC locality and measured GPU power",
    "evidence": "MEASURED",
    "cpu_fallback": ("topology probe plus a sustained CPU GEMM load; CPU package power is not readable in the container "
                     "(no RAPL powercap), so power is recorded as not runnable and the L1 rack-power check uses the design values"),
}

PKG = Path(__file__).resolve().parents[2]
REASONS = {0x1: "idle", 0x4: "sw_power_cap", 0x8: "hw_slowdown", 0x20: "sw_thermal", 0x40: "hw_thermal", 0x80: "hw_power_brake"}
TELEMETRY = ["power.draw", "clocks.sm", "temperature.gpu", "utilization.gpu", "clocks_event_reasons.active",
             "pcie.link.gen.current", "pcie.link.width.current"]


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


def sh(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 127, str(e)


def stats(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return {"n": len(xs), "median": statistics.median(xs), "p95": xs[min(len(xs) - 1, round(0.95 * (len(xs) - 1)))],
            "min": xs[0], "max": xs[-1]}


class Telemetry:
    """nvidia-smi -lms sampling in a background thread."""

    def __init__(self, interval_ms: int = 200):
        self.interval_ms, self.rows, self.p = interval_ms, [], None

    def __enter__(self):
        if shutil.which("nvidia-smi"):
            self.p = subprocess.Popen(["nvidia-smi", f"--query-gpu={','.join(TELEMETRY)}", "--format=csv,noheader,nounits",
                                       "-lms", str(self.interval_ms)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            self.t = threading.Thread(target=self._read, daemon=True)
            self.t.start()
        return self

    def _read(self):
        for line in self.p.stdout:
            vals = [v.strip() for v in line.split(",")]
            if len(vals) == len(TELEMETRY):
                row = {k: (int(v, 16) if v.startswith("0x") else num(v)) for k, v in zip(TELEMETRY, vals)}
                row["t"] = time.monotonic()
                self.rows.append(row)

    def __exit__(self, *a):
        if self.p:
            self.p.terminate()
            try:
                self.p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.p.kill()
            self.t.join(timeout=2)
        return False


def topology(ctx) -> dict:
    rc, topo = sh(["nvidia-smi", "topo", "-m"]) if shutil.which("nvidia-smi") else (127, "")
    topo = re.sub(r"\x1b\[[0-9;]*m", "", topo)                     # strip terminal underline codes
    enforced = sh(["nvidia-smi", "--query-gpu=enforced.power.limit", "--format=csv,noheader,nounits"])[1] if shutil.which("nvidia-smi") else ""
    nodes = sorted(p.name for p in Path("/sys/devices/system/node").glob("node[0-9]*")) if Path("/sys/devices/system/node").is_dir() else []
    ib = Path("/sys/class/infiniband")
    matrix = topo.split("Legend")[0] if topo else ""
    header = matrix.splitlines()[0].split() if matrix else []
    gpu_cols = [h for h in header if re.fullmatch(r"GPU\d+", h)]
    nic_cols = [h for h in header if re.fullmatch(r"NIC\d+|mlx5_\d+", h)]
    return {"nvidia_smi_topo_m": topo[:2000], "topo_gpus": len(gpu_cols), "topo_nics": len(nic_cols),
            "numa_nodes": nodes, "cpu_count": os.cpu_count(),
            "rdma_devices": sorted(os.listdir(ib)) if ib.is_dir() else [],
            "net_interfaces": sorted(os.listdir("/sys/class/net")) if Path("/sys/class/net").is_dir() else [],
            "lstopo": bool(shutil.which("lstopo")), "ibv_devinfo": bool(shutil.which("ibv_devinfo")),
            "ipmitool": bool(shutil.which("ipmitool")), "dev_ipmi": any(Path("/dev").glob("ipmi*")),
            "rapl": Path("/sys/class/powercap/intel-rapl").exists(),
            "torch_gpus": ctx.torch.cuda.device_count() if ctx.is_gpu else 0,
            "enforced_power_limit_w": num(enforced.splitlines()[0]) if enforced else None}


def power_run(ctx, seconds: float) -> dict:
    """Idle baseline, then a sustained FP16 GEMM load, with board power/clock/temperature sampled."""
    torch = ctx.torch
    n = 4096
    a = torch.randn(n, n, device="cuda", dtype=torch.float16)
    b = torch.randn(n, n, device="cuda", dtype=torch.float16)
    c = torch.empty_like(a)
    with Telemetry(200) as tel:
        time.sleep(2.0)                                   # idle baseline
        t_load = time.monotonic()
        iters = 0
        while time.monotonic() - t_load < seconds:
            for _ in range(20):
                torch.matmul(a, b, out=c)
            torch.cuda.synchronize()
            iters += 20
        t_end = time.monotonic()
        tflops = 2 * n ** 3 * iters / (t_end - t_load) / 1e12
        time.sleep(1.5)                                   # cool-down tail
    rows = tel.rows
    idle = [r for r in rows if r["t"] < t_load - 0.2]
    load = [r for r in rows if t_load + 1.0 <= r["t"] <= t_end]      # skip the clock ramp
    steady = load[len(load) // 4:]                                    # sustained = last 75 % of the load
    reasons = {}
    for r in load:
        for bit, name in REASONS.items():
            if int(r.get("clocks_event_reasons.active") or 0) & bit:
                reasons[name] = reasons.get(name, 0) + 1
    return {"seconds": t_end - t_load, "tflops": tflops, "n_samples": len(rows),
            "idle": {f: stats([r[f] for r in idle]) for f in ("power.draw", "clocks.sm", "temperature.gpu", "pcie.link.gen.current")},
            "load": {f: stats([r[f] for r in load]) for f in ("power.draw", "clocks.sm", "temperature.gpu", "utilization.gpu",
                                                              "pcie.link.gen.current", "pcie.link.width.current")},
            "sustained_power_w": statistics.median(r["power.draw"] for r in steady) if steady else None,
            "max_power_w": max((r["power.draw"] for r in load), default=None),
            "reason_share": {k: v / len(load) for k, v in reasons.items()} if load else {},
            "series": [{"t_s": round(r["t"] - t_load, 2), "w": r["power.draw"], "mhz": r["clocks.sm"], "c": r["temperature.gpu"]} for r in rows]}


def cpu_load(ctx, seconds: float) -> dict:
    torch = ctx.torch
    a = torch.randn(1024, 1024)
    tf, t0 = [], time.monotonic()
    while time.monotonic() - t0 < seconds:
        w0 = time.perf_counter()
        for _ in range(10):
            a @ a
        tf.append(10 * 2 * 1024 ** 3 / (time.perf_counter() - w0) / 1e12)
    return {"seconds": time.monotonic() - t0, "tflops": stats(tf), "windows": len(tf),
            "cv": statistics.pstdev(tf) / statistics.fmean(tf) if len(tf) > 1 else 0.0}


def l1_rack_power(ratio: float | None) -> dict:
    """L1 rack power and 2N check, design values vs node watts_sustained rescaled by the measured ratio [MODELED]."""
    cm, src = load_l1("cluster_model")
    if cm is None:
        return {"available": False, "why": "no L1 cluster_model found"}
    try:
        inputs = cm.load_inputs(PKG / "starter-kit" / "data")
        opt = "A_rail_1to1"
        cables = cm.cable_plan(inputs, opt)
        base = cm.rack_power(inputs, opt, cables)
        node = inputs["design"]["catalog"]["node_hx8"]
        out = {"available": True, "source": src, "option": opt, "design_ratio": node["watts_sustained"] / node["watts_max"],
               "node_watts_max": node["watts_max"], "node_watts_sustained": node["watts_sustained"],
               "design": base[base["kind"] == "gpu"][["rack", "max_kw", "sustained_kw", "feed_usable_kw", "ok_2n_max", "ok_2n_sustained"]].to_dict("records")}
        if ratio is not None:
            import copy
            alt = copy.deepcopy(inputs)
            alt["design"]["catalog"]["node_hx8"]["watts_sustained"] = round(node["watts_max"] * ratio)
            rp = cm.rack_power(alt, opt, cables)
            out["rescaled_node_watts_sustained"] = round(node["watts_max"] * ratio)
            out["rescaled"] = rp[rp["kind"] == "gpu"][["rack", "max_kw", "sustained_kw", "feed_usable_kw", "ok_2n_max", "ok_2n_sustained"]].to_dict("records")
        return out
    except NotImplementedError as e:
        return {"available": False, "why": f"starter cluster_model not implemented yet ({e})"}


def run(ctx) -> dict:
    torch = ctx.torch
    if not ctx.is_gpu:
        torch.set_num_threads(min(8, os.cpu_count() or 1))
    topo = topology(ctx)
    secs = 8.0 if ctx.quick else 60.0
    res = {"topology": topo, "notes": [], "not_runnable_parts": []}
    if ctx.is_gpu:
        pw = power_run(ctx, secs)
        ratio = pw["sustained_power_w"] / pw["max_power_w"] if pw["max_power_w"] else None
        res["power"] = pw
        res["metrics"] = {"idle_power_w": pw["idle"]["power.draw"]["median"] if pw["idle"]["power.draw"] else None,
                          "sustained_power_w": pw["sustained_power_w"], "max_power_w": pw["max_power_w"],
                          "sustained_to_max": round(ratio, 3) if ratio else None,
                          "load_sm_clock_mhz": pw["load"]["clocks.sm"]["median"] if pw["load"]["clocks.sm"] else None,
                          "load_tflops": round(pw["tflops"], 2)}
        ctx.log(f"power idle {res['metrics']['idle_power_w']} W, sustained {pw['sustained_power_w']} W, max {pw['max_power_w']} W "
                f"(ratio {ratio:.3f}); SM clock under load {res['metrics']['load_sm_clock_mhz']} MHz")
    else:
        cl = cpu_load(ctx, secs)
        ratio = None
        res["cpu_load"] = cl
        res["metrics"] = {"cpu_tflops_median": round(cl["tflops"]["median"], 4), "cpu_load_cv": round(cl["cv"], 4)}
        res["not_runnable_parts"].append({"part": "CPU package power", "probe": f"/sys/class/powercap/intel-rapl present={topo['rapl']}",
                                          "needs": ["RAPL powercap exposed to the container, or a BMC/PDU reading"],
                                          "fallback": "sustained CPU load throughput only; L1 rack power with design values"})
    res["l1_rack_power"] = l1_rack_power(ratio)
    res["not_runnable_parts"] += [
        {"part": "GPU<->NIC PCIe affinity (expect PIX between GPU i and NIC i)",
         "probe": f"nvidia-smi topo -m lists {topo['topo_gpus']} GPU(s) and {topo['topo_nics']} NIC(s); /sys/class/infiniband="
                  f"{topo['rdma_devices'] or 'none'}", "needs": ["HX8-class node with 8 RDMA NICs"],
         "fallback": "topology matrix recorded as found"},
        {"part": "lstopo / hwloc PCIe tree", "probe": f"lstopo on PATH={topo['lstopo']}", "needs": ["hwloc installed on the host"],
         "fallback": "NUMA nodes from /sys/devices/system/node"},
        {"part": "chassis power from the BMC (ipmitool dcmi power reading / Redfish)",
         "probe": f"ipmitool={topo['ipmitool']}, /dev/ipmi*={topo['dev_ipmi']}", "needs": ["BMC with DCMI or Redfish, read-only account"],
         "fallback": "GPU board power from nvidia-smi (GPU only, not the chassis)" if ctx.is_gpu else "none"},
        {"part": "8-GPU all_reduce_perf load and 30-minute chassis power log",
         "probe": f"GPUs={topo['torch_gpus']}", "needs": ["8 GPUs + nccl-tests"], "fallback": "single-GPU GEMM load"}]
    res["notes"] += ["Telemetry: nvidia-smi --query-gpu ... -lms 200; the first second of load is excluded (clock ramp); "
                     "'sustained' = median of the last 75 % of the load, 'max' = highest 200 ms sample.",
                     f"Load duration {secs:.0f} s (quick mode 8 s). The README asks for >= 30 minutes of chassis power on an HX8 node."]
    return res


def check(result: dict, env: dict) -> list[str]:
    fails = []
    topo = result["topology"]
    if env["device"] == "cuda":
        if topo["topo_gpus"] and topo["topo_gpus"] != topo["torch_gpus"]:
            fails.append(f"nvidia-smi topo shows {topo['topo_gpus']} GPUs but CUDA sees {topo['torch_gpus']}: check CUDA_VISIBLE_DEVICES")
        pw = result["power"]
        g = (env.get("gpus") or [{}])[0]
        if not pw["load"]["power.draw"] or pw["load"]["power.draw"]["n"] < 5:
            fails.append("fewer than 5 power samples under load: check nvidia-smi -lms inside the container")
            return fails
        idle, sus, mx = pw["idle"]["power.draw"], pw["sustained_power_w"], pw["max_power_w"]
        if idle and sus <= idle["median"]:
            fails.append(f"sustained power {sus:.1f} W is not above idle {idle['median']:.1f} W: the load did not reach the GPU")
        if not (0 < sus <= mx):
            fails.append("sustained power must be positive and no higher than the maximum sample")
        pmax = num(g.get("power.max_limit"))
        if pmax and mx > 1.10 * pmax:
            fails.append(f"a power sample of {mx:.0f} W exceeds power.max_limit {pmax:.0f} W by > 10 %: telemetry parse error")
        clk = num(g.get("clocks.max.sm"))
        if clk and pw["load"]["clocks.sm"]["max"] > 1.02 * clk:
            fails.append("SM clock above clocks.max.sm: telemetry parse error")
        sm = env.get("gpu0", {}).get("sm_count")
        if sm and clk and pw["tflops"] * 1e12 > 1.05 * sm * 512 * clk * 1e6:
            fails.append("load throughput exceeds the FP16 tensor peak: check the FLOP count")
    else:
        if result["cpu_load"]["windows"] < 5:
            fails.append("fewer than 5 CPU load windows")
    rp = result["l1_rack_power"]
    if rp.get("available"):
        for rows in [rp["design"]] + ([rp["rescaled"]] if "rescaled" in rp else []):
            if any(r["sustained_kw"] > r["max_kw"] + 1e-9 for r in rows):
                fails.append("L1 rack power: sustained kW above max kW for a rack: the rescaled watts_sustained exceeds watts_max")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    topo = result["topology"]
    L = ["## Topology probe", "", "```text", topo["nvidia_smi_topo_m"].split("Legend")[0].strip() or "(nvidia-smi absent)", "```", "",
         f"NUMA nodes: {', '.join(topo['numa_nodes']) or 'not exposed'}; CPUs: {topo['cpu_count']}; RDMA devices: "
         f"{topo['rdma_devices'] or 'none'}; network interfaces in the container: {', '.join(topo['net_interfaces'])}. "
         "The HX8 design assumes GPU i and NIC i share a PCIe switch (PIX). There is no NIC column to check here."]
    if gpu:
        pw, m = result["power"], result["metrics"]
        g = (env.get("gpus") or [{}])[0]
        L += ["", f"## GPU board power: idle, then {pw['seconds']:.0f} s sustained FP16 GEMM", "",
              "| Phase | power median (W) | power max (W) | SM clock median (MHz) | temperature max (C) | PCIe gen |", "|---|---|---|---|---|---|"]
        for ph in ("idle", "load"):
            x = pw[ph]
            L.append(f"| {ph} | {x['power.draw']['median']:.1f} | {x['power.draw']['max']:.1f} | {x['clocks.sm']['median']:.0f} | "
                     f"{x['temperature.gpu']['max']:.0f} | {x['pcie.link.gen.current']['median']:.0f} |")
        share = ", ".join(f"{k} {v * 100:.0f} %" for k, v in sorted(pw["reason_share"].items())) or "none"
        L += ["", f"Sustained **{m['sustained_power_w']:.1f} W**, maximum sample **{m['max_power_w']:.1f} W**, ratio **{m['sustained_to_max']:.3f}** "
              f"`[MEASURED]`. Limits reported by nvidia-smi: power.max_limit {g.get('power.max_limit')} W, power.limit {g.get('power.limit')}, "
              f"enforced.power.limit {topo.get('enforced_power_limit_w')} W. "
              f"Clock-event reasons during load: {share}. Throughput {m['load_tflops']:.1f} TFLOP/s.",
              f"Under the board's power limit the SM clock settled at {m['load_sm_clock_mhz']:.0f} MHz, versus clocks.max.sm "
              f"{g.get('clocks.max.sm')} MHz. That is what a power cap does: a capped GPU runs slower, and in a synchronous job it "
              "becomes the straggler. This is why the exemplar keeps capped rack-05 nodes out of W-TRAIN."]
    else:
        cl = result["cpu_load"]
        L += ["", f"## Sustained CPU load ({cl['seconds']:.0f} s)", "",
              f"Median {cl['tflops']['median'] * 1e3:.0f} GFLOP/s, min {cl['tflops']['min'] * 1e3:.0f}, max {cl['tflops']['max'] * 1e3:.0f}; "
              f"window CV {cl['cv'] * 100:.1f} %. Power was not measurable (no RAPL in the container)."]
    rp = result["l1_rack_power"]
    if rp.get("available"):
        L += ["", f"## L1 rack power and 2N check (`{rp['source']}`, option {rp['option']}) `[MODELED]`", "",
              f"Design node: watts_max {rp['node_watts_max']} W, watts_sustained {rp['node_watts_sustained']} W (ratio {rp['design_ratio']:.3f})."]
        if "rescaled" in rp:
            L.append(f"Sensitivity: watts_sustained rescaled to watts_max x measured ratio = **{rp['rescaled_node_watts_sustained']} W**.")
        L += ["", "| Rack | max kW | feed usable kW | 2N at max | sustained kW (design) | 2N sustained (design) |"
              + (" sustained kW (rescaled) | 2N sustained (rescaled) |" if "rescaled" in rp else ""),
              "|---|---|---|---|---|---|" + ("---|---|" if "rescaled" in rp else "")]
        resc = {r["rack"]: r for r in rp.get("rescaled", [])}
        for r in rp["design"]:
            line = (f"| {r['rack']} | {r['max_kw']:.2f} | {r['feed_usable_kw']:.2f} | {r['ok_2n_max']} | {r['sustained_kw']:.2f} | "
                    f"{r['ok_2n_sustained']} |")
            if resc:
                x = resc[r["rack"]]
                line += f" {x['sustained_kw']:.2f} | {x['ok_2n_sustained']} |"
            L.append(line)
        if "rescaled" in rp:
            L += ["", "_The ratio comes from one laptop GPU under a synthetic GEMM load, not from an HX8 chassis running W-TRAIN. "
                  "It shows how the 2N verdict depends on the sustained/max assumption. Replace it with the chassis measurement._"]
    elif rp:
        L += ["", f"L1 rack power skipped: {rp.get('why')}"]
    L += ["", "## Not runnable here", ""]
    for p in result["not_runnable_parts"]:
        L.append(f"- **{p['part']}**. Probe: {p['probe']}. Needs: {', '.join(p['needs'])}. Fallback: {p.get('fallback', '-')}.")
    L += ["", "## What to conclude", "",
          "- Size feeds on the maximum. Sustained power follows the workload and the power limit, so the sustained/max ratio is "
          "a measurement, not a constant."]
    if gpu:
        m = result["metrics"]
        L.append(f"- Under a compute-saturating load this GPU sits on its enforced limit (sustained/max = {m['sustained_to_max']:.2f}, "
                 "SW power cap active). A power-limited node's sustained draw is its limit. The design's 0.83 assumes a workload "
                 "that does *not* saturate the GPUs, so measure W-TRAIN itself on the chassis before relaxing the 2N sizing.")
        L.append("- 'Idle' here is the GPU with no load from this experiment. Other tenants or the display can keep the clocks up, "
                 "so check the idle row before using it as a baseline.")
        L.append("- This is a **laptop Ada GPU (about 80 W enforced), not an H100 SXM (about 700 W)**: only the method transfers, the watts do not.")
    else:
        L.append("- _CPU fallback: no GPU was used. GPU power, clock and topology invariants were skipped._")
    return "\n".join(L)
