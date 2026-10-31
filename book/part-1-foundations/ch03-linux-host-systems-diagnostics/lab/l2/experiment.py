"""Ch 3 L2: run the lab's read-only collector and fleet analyzer on this real host, idle and under load.

What it teaches (Sections 3.2, 3.6, 3.10): a diagnostic tool is only trustworthy if (a) it cannot change
the host, (b) it says what evidence it could not collect, and (c) its parsers agree with an independent
reading of the same machine. The experiment reuses the reference solution unchanged:

1. **Safety first.** Every command in ``build_command_plan()`` must pass the read-only guard, and a list of
   real mutating forms (``nvidia-smi -pl``, ``ethtool -s``, ``ip link set``, ``taskset -cp <list> <pid>``,
   ``setpci``, ``--power-limit=`` hidden in one token, ...) must be refused by ``argv_is_read_only()`` and
   by ``run_command()`` *without being executed*.
2. **Two real snapshots** (``collect()`` with the sysfs/procfs readers): one idle, one while this
   experiment drives the GPU with a BF16 GEMM loop (CPU fallback: a CPU GEMM loop), with the loaded
   process's PID recorded so ``taskset -cp`` / ``numastat -p`` run against it.
3. **PCIe link state idle vs loaded**, sampled 5x each through the collector's own guarded
   ``run_command()`` (the allowed ``nvidia-smi --query-gpu`` form), with the query latency recorded.
   Many GPUs drop the link speed at idle; Section 3.6's PCIE_SPEED_LOW_IDLE rule exists for that.
4. **Triage** with ``analyze_fleet()`` against two baselines: one written for *this* host from independent
   probes (``/proc/cpuinfo``, ``/sys/devices/system/node``, ``/proc/meminfo``, ``torch.cuda.device_count()``)
   that must produce no INVENTORY_MISMATCH, and the ORION HX8 baseline, which must flag this host as the
   wrong machine (the triage works on real data; it is not a rubber stamp).

The root snapshot, ``lspci -vv`` capabilities, ``ethtool``/NIC checks and the L3 multi-node fleet run are
probed and recorded as not runnable here (the container runs as uid 1000; pciutils/ethtool/sysstat are not
installed in the image; WSL2 exposes no PCI functions for the GPU; there are no RDMA NICs).

CPU fallback: the same guard tests, the same two snapshots (CPU load instead of GPU load), the same
triage; ``nvidia-smi`` is absent, so its section is reported as ``missing`` and must surface as an
EVIDENCE_GAP finding (graceful degradation is the invariant). GPU-only invariants are skipped.
"""
from __future__ import annotations

import importlib.util
import os
import platform
import statistics
import sys
import threading
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch03-l2",
    "title": "Lab 3 L2: read-only host discovery and triage on a real GPU host, idle and under load",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same read-only guard tests, idle and CPU-loaded snapshots and fleet triage; nvidia-smi is absent "
                     "and must be reported as an evidence gap rather than crash the collector or the analyzer"),
}

PKG = Path(__file__).resolve().parents[2]
# Mutating or unknown forms an on-call engineer might be tempted to add. Every one must be refused.
UNSAFE = [
    ("nvidia-smi", "-pl", "100"), ("nvidia-smi", "--power-limit=100"), ("nvidia-smi", "-r"), ("nvidia-smi", "-lgc", "1500,1500"),
    ("nvidia-smi", "-pm", "1"), ("nvidia-smi", "--query-gpu", "index", "--format", "csv", "-pl", "100"),
    ("ethtool", "-s", "eth0", "speed", "1000"), ("ethtool", "-K", "eth0", "gro", "off"),
    ("ip", "link", "set", "eth0", "mtu", "1500"), ("ip", "link", "set", "dev", "eth0", "down"),
    ("taskset", "-cp", "0-3", "1"), ("setpci", "-s", "01:00.0", "CAP_EXP+10.w=0"), ("sysctl", "-w", "vm.swappiness=1"),
    ("numactl", "--membind=0", "true"), ("dmesg", "-C"), ("sh", "-c", "lscpu"), ("lscpu", ";", "reboot"),
    ("journalctl", "--vacuum-size=1M"), ("nvidia-smi", "--query-gpu", "index;reboot", "--format", "csv"),
]
SMI_FIELDS = "pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,utilization.gpu,clocks.sm"


def load(name: str):
    # Reference solution when present (instructor tree); the learner's starter/ in the student release.
    path = PKG / "solutions" / "lab" / f"{name}.py"
    if not path.is_file():
        path = PKG / "lab" / "starter" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"ch03_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ independent probes -> baseline for this host
def probe_host(ctx) -> dict:
    """Read the machine directly (not through the collector) so the analyzer can be cross-checked."""
    phys, cores, siblings = set(), None, None
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if k == "physical id":
                phys.add(v)
            elif k == "cpu cores" and cores is None:
                cores = int(v)
            elif k == "siblings" and siblings is None:
                siblings = int(v)
    except OSError:
        pass
    nodes = sorted(Path("/sys/devices/system/node").glob("node[0-9]*"))
    mem_kib = None
    try:
        mem_kib = int(next(l for l in Path("/proc/meminfo").read_text().splitlines() if l.startswith("MemTotal:")).split()[1])
    except (OSError, StopIteration):
        pass
    # Display-class PCI functions, read straight from sysfs (vendor recorded: 0x10de NVIDIA, 0x1414 Microsoft GPU-PV).
    pci_gpus = []
    for d in sorted(Path("/sys/bus/pci/devices").glob("*")):
        try:
            cls = (d / "class").read_text().strip()
            if cls.startswith(("0x0300", "0x0302")):
                pci_gpus.append({"bdf": d.name, "class": cls, "vendor": (d / "vendor").read_text().strip()})
        except OSError:
            continue
    # Same evidence order as the analyzer: GPUs the driver sees when a GPU is in use, else display-class functions.
    gpus = ctx.torch.cuda.device_count() if ctx.is_gpu else len(pci_gpus)
    return {"pci_display_functions": pci_gpus,"sockets": max(1, len(phys)), "cores_per_socket": cores or os.cpu_count(),
            "threads_per_core": (siblings // cores) if siblings and cores else 1, "numa_nodes": max(1, len(nodes)),
            "mem_total_mib": mem_kib // 1024 if mem_kib else None, "gpu_count": gpus, "cpu_count": os.cpu_count(),
            "source": "/proc/cpuinfo (physical id, cpu cores, siblings), /sys/devices/system/node, /proc/meminfo, "
                      "torch.cuda.device_count() (GPU run) or display-class functions in /sys/bus/pci/devices (CPU run)"}


def host_baseline(orion: dict, probe: dict) -> dict:
    b = {"platform": f"this host ({platform.node()}), written from independent probes",
         "inventory": {"sockets": probe["sockets"], "cores_per_socket": probe["cores_per_socket"],
                       "threads_per_core": probe["threads_per_core"], "numa_nodes": probe["numa_nodes"],
                       "mem_total_mib_min": int(0.95 * (probe["mem_total_mib"] or 0)),
                       "numa_node_mem_mb_min": int(0.9 * (probe["mem_total_mib"] or 0) / probe["numa_nodes"]),
                       "gpu_count": probe["gpu_count"]},
         "pcie": orion["pcie"], "interfaces": {},       # no rail/frontend NIC groups on a single laptop host
         "cpufreq": orion["cpufreq"], "thresholds": orion["thresholds"]}
    return b


# ------------------------------------------------------------------ load generator
class Load:
    def __init__(self, ctx):
        self.ctx, self.stop_ev, self.iters = ctx, threading.Event(), 0
        torch = ctx.torch
        if ctx.is_gpu:
            self.a = torch.randn(2048, 2048, device="cuda", dtype=torch.bfloat16)
        else:
            self.a = torch.randn(384, 384)
        self.t = threading.Thread(target=self._loop, daemon=True)

    def _loop(self):
        if self.ctx.is_gpu:
            import warnings
            self.ctx.torch.cuda.set_device(0)    # a new thread has no current CUDA context
            warnings.filterwarnings("ignore", message="Attempting to run cuBLAS")
        while not self.stop_ev.is_set():
            for _ in range(20):
                self.a @ self.a
            self.ctx.sync()
            self.iters += 20

    def __enter__(self):
        self.t.start()
        time.sleep(1.0)            # let clocks and the PCIe link leave their idle state
        return self

    def __exit__(self, *a):
        self.stop_ev.set()
        self.t.join(timeout=10)
        return False


def sample_link(col, n: int) -> list[dict]:
    """n samples of the GPU's PCIe link through the collector's guarded runner."""
    argv = ("nvidia-smi", f"--query-gpu={SMI_FIELDS}", "--format=csv,noheader")
    out = []
    for _ in range(n):
        r = col.run_command(argv, 15.0)
        row = {"status": r.status, "elapsed_s": r.elapsed_s}
        if r.status == "ok" and r.stdout.strip():
            v = [x.strip().split()[0] for x in r.stdout.strip().splitlines()[0].split(",")]
            try:
                row.update({"gen_cur": int(v[0]), "gen_max": int(v[1]), "width_cur": int(v[2]), "width_max": int(v[3]),
                            "util_pct": int(v[4]), "sm_mhz": int(v[5])})
            except (ValueError, IndexError):
                row["parse_error"] = r.stdout.strip()[:120]
        out.append(row)
        time.sleep(0.2)
    return out


def snapshot(col, host: str, note: str, pid: int | None) -> tuple[dict, float]:
    linux = sys.platform.startswith("linux")
    plan = col.build_command_plan(col.discover_interfaces() if linux else [], pid)
    files = {"pcie_sysfs": col.read_pcie_sysfs, "interrupts": col.read_interrupts, "cpufreq": col.read_cpufreq}
    t0 = time.perf_counter()
    rep = col.collect(plan, file_sections=files, host=host, context={"pid": pid, "note": note})
    return rep, time.perf_counter() - t0


def run(ctx) -> dict:
    import yaml
    col, an = load("host_collector"), load("host_analyzer")
    n = 5 if ctx.quick else 10
    # 1. the guard
    plan = col.build_command_plan(col.discover_interfaces(), os.getpid())
    plan_ok = {s.name: col.is_read_only(s) for s in plan}
    refused = {" ".join(a): not col.argv_is_read_only(a) for a in UNSAFE}
    t0 = time.perf_counter()
    executed = [col.run_command(a, 5.0) for a in UNSAFE]
    refuse_s = time.perf_counter() - t0
    run_refused = all(r.status == "error" and "refused" in r.stderr and r.returncode is None for r in executed)
    # 2-3. idle snapshot + link samples, then loaded
    link_idle = sample_link(col, n) if ctx.is_gpu else []
    idle, idle_s = snapshot(col, "l2host-idle", "idle baseline (non-root)", None)
    with Load(ctx) as ld:
        link_load = sample_link(col, n) if ctx.is_gpu else []
        loaded, loaded_s = snapshot(col, "l2host-loaded", "under GEMM load (non-root)", os.getpid())
    ctx.log(f"snapshots: idle {idle_s:.1f} s, loaded {loaded_s:.1f} s; load iterations {ld.iters}")
    # 4. triage
    orion = an.load_baseline(PKG / "lab" / "data" / "orion_hx8_baseline.yaml")
    probe = probe_host(ctx)
    mine = host_baseline(orion, probe)
    snaps = {"l2host-idle": idle, "l2host-loaded": loaded}
    f_mine = an.analyze_fleet(snaps, mine)
    f_orion = an.analyze_fleet(snaps, orion)
    as_dicts = lambda fs: [{"host": f.host, "check_id": f.check_id, "severity": f.severity, "subject": f.subject,  # noqa: E731
                            "evidence": f.evidence} for f in fs]
    parsed = {}
    for name, s in snaps.items():
        t = an._sec(s, "lscpu")
        parsed[name] = {"lscpu": {k: v for k, v in an.parse_lscpu(t).items() if k != "numa_cpus"} if t else None,
                        "free": an.parse_free(an._sec(s, "free")) if an._sec(s, "free") else None,
                        "nvidia_smi": an.parse_nvidia_smi_csv(an._sec(s, "nvidia_smi") or ""),
                        "sections": {k: v["status"] for k, v in s["sections"].items()},
                        "elapsed_s": {k: v["elapsed_s"] for k, v in s["sections"].items()}}
    lat = [r["elapsed_s"] for r in link_idle + link_load if r["status"] == "ok"]
    gaps = sorted({(k, v["status"], (v.get("stderr") or "").strip().splitlines()[0][:100] if (v.get("stderr") or "").strip() else "")
                   for k, v in loaded["sections"].items() if v["status"] != "ok"})
    not_runnable = []
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        not_runnable.append({"part": "root snapshot (sudo python host_collector.py ...)", "probe": f"euid = {os.geteuid()}",
                             "needs": ["root in the container (the harness runs as uid 1000 and never escalates)"],
                             "fallback": "non-root snapshots; sections that need root are recorded as denied"})
    for tool, part, need, fb in (
            ("lspci", "lspci -vv LnkCap/LnkSta", "pciutils in the image; root for capabilities",
             "sysfs link files (pcie_sysfs section) and nvidia-smi pcie.link.* fields"),
            ("ethtool", "ethtool -i/-S per interface", "ethtool and real NICs", "none: no rail/frontend NICs on this host"),
            ("iostat", "iostat -x / mpstat -P ALL", "sysstat in the image", "vmstat 1 5 (run queue, blocked tasks, iowait)"),
            ("lstopo-no-graphics", "lstopo-no-graphics --of console", "hwloc in the image",
             "lscpu NUMA lines and nvidia-smi topo -m")):
        sec = {"lspci": "lspci", "iostat": "iostat", "ethtool": None, "lstopo-no-graphics": None}[tool]
        st = loaded["sections"].get(sec, {}).get("status") if sec else ("missing" if not col.shutil.which(tool, path=col.SAFE_PATH) else "ok")
        if st in ("missing", None):
            not_runnable.append({"part": part, "probe": f"{tool}: {st or 'not in plan (no interfaces)'}", "needs": [need],
                                 "fallback": fb})
    if not Path("/sys/class/infiniband").exists():
        not_runnable.append({"part": "L3: collector on every node during all_reduce_perf; cross-host MTU/link checks",
                             "probe": "/sys/class/infiniband absent", "needs": ["2+ RDMA-connected GPU nodes, nccl-tests"],
                             "fallback": "the idle and loaded snapshots of this host analysed as a two-member 'fleet'"})
    pcie_gpu = [d for d in an.parse_pcie_sysfs(an._sec(loaded, "pcie_sysfs") or "") if d["kind"] == "gpu"]
    if ctx.is_gpu and not pcie_gpu:
        not_runnable.append({"part": "GPU PCIe link from sysfs (/sys/bus/pci/devices/*/current_link_speed)",
                             "probe": "pcie_sysfs lists no display-class function (WSL2 exposes the GPU through /dev/dxg, not PCI)",
                             "needs": ["native Linux kernel with the GPU as a PCI function"],
                             "fallback": "nvidia-smi pcie.link.* fields (the collector's nvidia_smi section)"})
    notes_extra = []
    ms = [g for g in probe["pci_display_functions"] if g["vendor"] == "0x1414"]
    if ms:
        notes_extra.append(f"WSL2: sysfs lists {len(ms)} Microsoft (vendor 0x1414) GPU-PV display functions "
                           f"({', '.join(g['bdf'] for g in ms)}), the paravirtual adapters through which the hypervisor shares the host's "
                           "GPUs (likely the NVIDIA GPU and the CPU's integrated GPU), with no link-speed files. Without nvidia-smi the analyzer's sysfs fallback counts these as GPUs; on a native Linux host "
                           "the same rule sees the real NVIDIA functions (vendor 0x10de) with their link state.")
    m = {"plan_commands": len(plan), "plan_all_read_only": all(plan_ok.values()), "unsafe_forms_refused": sum(refused.values()),
         "unsafe_forms_total": len(UNSAFE), "idle_snapshot_s": round(idle_s, 2), "loaded_snapshot_s": round(loaded_s, 2),
         "sections_ok_loaded": sum(1 for v in loaded["sections"].values() if v["status"] == "ok"),
         "sections_total": len(loaded["sections"]),
         "findings_own_baseline": len(f_mine), "findings_orion_baseline": len(f_orion)}
    if lat:
        m["nvidia_smi_query_median_ms"] = round(statistics.median(lat) * 1e3, 1)
    for tag, rows in (("idle", link_idle), ("loaded", link_load)):
        ok = [r for r in rows if "gen_cur" in r]
        if ok:
            m[f"pcie_gen_{tag}_median"] = statistics.median(r["gen_cur"] for r in ok)
            m[f"gpu_util_{tag}_median_pct"] = statistics.median(r["util_pct"] for r in ok)
    return {"metrics": m, "guard": {"plan": plan_ok, "unsafe_refused": refused, "run_command_refused_without_executing": run_refused,
                                    "refusal_wall_s": refuse_s},
            "link_samples": {"idle": link_idle, "loaded": link_load}, "probe": probe, "baseline_written": mine,
            "parsed": parsed, "evidence_gaps": [list(g) for g in gaps],
            "findings": {"own_baseline": as_dicts(f_mine), "orion_baseline": as_dicts(f_orion)},
            "triage_report_own": an.write_report(f_mine, sorted(snaps)), "not_runnable_parts": not_runnable,
            "snapshots": {"idle": idle, "loaded": loaded}, "baseline_yaml": yaml.safe_dump(mine, sort_keys=False),
            "tables": {}, "notes": [
                "Both snapshots are non-root and read-only; the analyzer treats them as two hosts (l2host-idle, l2host-loaded).",
                "The machine is shared: 'idle' means this experiment was not loading the GPU, not that nothing else was.",
                "Snapshot wall time is dominated by vmstat 1 5 (5 s of sampling by design).", *notes_extra]}


def check(result: dict, env: dict) -> list[str]:
    fails = []
    gpu = env["device"] == "cuda"
    g, m = result["guard"], result["metrics"]
    bad = [k for k, v in g["plan"].items() if not v]
    if bad:
        fails.append(f"plan commands not read-only: {bad} (fix build_command_plan or ALLOWED_FORMS)")
    leaked = [k for k, v in g["unsafe_refused"].items() if not v]
    if leaked:
        fails.append(f"the guard ACCEPTED mutating forms: {leaked}; tighten ALLOWED_FORMS before running anywhere")
    if not g["run_command_refused_without_executing"]:
        fails.append("run_command() executed (or mis-reported) a refused form: it must refuse before resolving the tool")
    allowed = {"ok", "missing", "denied", "timeout", "error", "skipped"}
    for name, snap in result["snapshots"].items():
        if snap.get("schema") != "hostdiag/1":
            fails.append(f"{name}: schema {snap.get('schema')} is not hostdiag/1")
        st = {k: v["status"] for k, v in snap["sections"].items()}
        if set(st.values()) - allowed:
            fails.append(f"{name}: unknown section status {set(st.values()) - allowed}")
        for core in ("uname", "lscpu", "free"):
            if st.get(core) != "ok":
                fails.append(f"{name}: core section {core} is {st.get(core)}: these tools exist on every Linux host; check SAFE_PATH")
    p = result["probe"]
    for name, parsed in result["parsed"].items():
        ls = parsed["lscpu"]
        if ls and ls["cpus"] != p["cpu_count"]:
            fails.append(f"{name}: lscpu CPU(s) {ls['cpus']} != os.cpu_count() {p['cpu_count']}: parse_lscpu or the probe is wrong")
    inv = [f for f in result["findings"]["own_baseline"] if f["check_id"] == "INVENTORY_MISMATCH"]
    if inv:
        fails.append(f"collector+analyzer disagree with the independent probe: {[f['evidence'] for f in inv]}")
    if not any(f["check_id"] == "INVENTORY_MISMATCH" and f["severity"] == "critical" for f in result["findings"]["orion_baseline"]):
        fails.append("against the ORION HX8 baseline this host should be flagged INVENTORY_MISMATCH (critical): the triage "
                     "is not comparing inventory")
    if not gpu:
        st = result["snapshots"]["loaded"]["sections"].get("nvidia_smi", {}).get("status")
        if st == "ok":
            fails.append("nvidia-smi section ok without a GPU in use: the CPU fallback is not running without a GPU")
        if not any(f["check_id"] == "EVIDENCE_GAP" and f["subject"] == "nvidia_smi" for f in result["findings"]["own_baseline"]):
            fails.append("the missing nvidia-smi section was not reported as an EVIDENCE_GAP: graceful degradation broken")
        return fails
    for name in ("idle", "loaded"):
        if result["snapshots"][name]["sections"].get("nvidia_smi", {}).get("status") != "ok":
            fails.append(f"{name}: nvidia_smi section not ok on a GPU host: check the container runtime (--gpus all)")
    for tag, rows in result["link_samples"].items():
        for r in rows:
            if "gen_cur" not in r:
                fails.append(f"{tag}: nvidia-smi sample not parsed ({r.get('status')}, {r.get('parse_error', '')})")
                break
            if r["gen_cur"] > r["gen_max"] or r["width_cur"] > r["width_max"]:
                fails.append(f"{tag}: current PCIe link Gen{r['gen_cur']} x{r['width_cur']} exceeds max Gen{r['gen_max']} x{r['width_max']}")
    if m.get("pcie_gen_loaded_median", 0) < m.get("pcie_gen_idle_median", 0):
        fails.append("the PCIe link was slower under load than idle: check for a degraded link (lspci LnkSta) or a thermal event")
    if m.get("gpu_util_loaded_median_pct", 0) < 50:
        fails.append("GPU utilisation under the GEMM load was < 50 %: the load thread did not run or the GPU is contended")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    m, p = result["metrics"], result["probe"]
    L = ["## 1. The read-only guard", "",
         f"- {m['plan_commands']} commands in the plan, all read-only: **{m['plan_all_read_only']}**.",
         f"- {m['unsafe_forms_refused']}/{m['unsafe_forms_total']} mutating or unknown forms refused by `argv_is_read_only()`; "
         f"`run_command()` refused them without executing anything: **{result['guard']['run_command_refused_without_executing']}** "
         f"({result['guard']['refusal_wall_s'] * 1e3:.2f} ms for all of them).", "",
         "| Refused form | Refused |", "|---|---|"]
    for k, v in result["guard"]["unsafe_refused"].items():
        L.append(f"| `{k}` | {v} |")
    L += ["", "## 2. Inventory: collector + parsers vs an independent probe", "",
          "| Field | Collector (`lscpu`/`free`, parsed by the lab's analyzer) | Independent probe |", "|---|---|---|"]
    ls = result["parsed"]["l2host-idle"]["lscpu"] or {}
    fr = result["parsed"]["l2host-idle"]["free"] or {}
    for k, pk in (("cpus", "cpu_count"), ("sockets", "sockets"), ("cores_per_socket", "cores_per_socket"),
                  ("threads_per_core", "threads_per_core"), ("numa_nodes", "numa_nodes")):
        L.append(f"| {k} | {ls.get(k)} | {p.get(pk)} |")
    L.append(f"| memory (MiB) | {fr.get('mem_total_mib')} | {p.get('mem_total_mib')} (/proc/meminfo) |")
    L.append(f"| model | {ls.get('model_name')} | {env.get('cpu_model')} |")
    nv = result["parsed"]["l2host-loaded"]["nvidia_smi"]
    if nv:
        L.append(f"| GPUs (nvidia_smi section) | {len(nv)} at {', '.join(g['bdf'] for g in nv)} | {p['gpu_count']} (torch) |")
    L += ["", f"Probe source: {p['source']}."]
    if gpu:
        L += ["", "## 3. GPU PCIe link, idle vs loaded (collector's guarded `nvidia-smi --query-gpu`)", "",
              "| State | Samples | Link (median) | Max | GPU util (median) | SM clock (median, MHz) | Query latency median / max (ms) |",
              "|---|---|---|---|---|---|---|"]
        for tag, rows in result["link_samples"].items():
            ok = [r for r in rows if "gen_cur" in r]
            if not ok:
                continue
            med = lambda k: statistics.median(r[k] for r in ok)  # noqa: E731
            L.append(f"| {tag} | {len(ok)} | Gen{med('gen_cur'):g} x{med('width_cur'):g} | Gen{ok[0]['gen_max']} x{ok[0]['width_max']} | "
                     f"{med('util_pct'):g} % | {med('sm_mhz'):g} | {statistics.median(r['elapsed_s'] for r in ok) * 1e3:.0f} / "
                     f"{max(r['elapsed_s'] for r in ok) * 1e3:.0f} |")
        L += ["", "If the idle link reads below its maximum and the loaded one at it, that is power management (ASPM / "
              "dynamic link speed), which the analyzer reports as PCIE_SPEED_LOW_IDLE (info), not as a fault. A link that "
              "stays low under load is the real PCIE_SPEED_DEGRADED warning. On a shared GPU 'idle' is relative: another "
              "job may hold the link up."]
    L += ["", "## 4. Evidence gaps (loaded snapshot, non-root)", "", "| Section | Status | Why |", "|---|---|---|"]
    for name, st, why in result["evidence_gaps"]:
        L.append(f"| {name} | {st} | {why} |")
    L += ["", f"{m['sections_ok_loaded']}/{m['sections_total']} sections ok. Each gap is a finding (EVIDENCE_GAP, info), not "
          "a crash: that is the collector's contract.", "",
          "## 5. Triage with a baseline written for this host", "", result["triage_report_own"].replace("# ORION host diagnostic report", "").strip(),
          "", "## 6. The same snapshots against the ORION HX8 baseline", ""]
    crit = [f for f in result["findings"]["orion_baseline"] if f["severity"] == "critical"]
    for f in crit[:10]:
        L.append(f"- **{f['host']}** `{f['check_id']}` [{f['subject']}] — {f['evidence']}")
    L += ["", "A laptop is not an HX8 node: the inventory rules fire at once. Writing the baseline for the platform you "
          "actually run is step one of Section 9's L2 instructions (`my_baseline.yaml`; the one used here is in "
          "`results.json` under `baseline_yaml`).", "", "## What to conclude", "",
          "- The collector ran on a real host without root, changed nothing, and told you exactly which evidence it could "
          "not collect and why; the guard refused every mutating form before any process was started.",
          "- Parsers that pass on simulated ORION snapshots also agree with an independent probe of a real machine; "
          "that cross-check is what makes the triage verdicts credible.",
          "- The ORION-class findings (rails, MTU 9000, eight GPUs on Gen5 x16) need the real platform: see the table below."]
    if not gpu:
        L += ["", "_CPU fallback: no GPU was used. nvidia-smi was absent (reported as an evidence gap, as designed); the PCIe "
              "link comparison and the GPU-only invariants were skipped._"]
    if result.get("not_runnable_parts"):
        L += ["", "## Not runnable on this host (probed, not faked)", "", "| Part | Probe | Needs | Used instead |", "|---|---|---|---|"]
        for x in result["not_runnable_parts"]:
            L.append(f"| {x['part']} | {x['probe']} | {', '.join(x['needs'])} | {x['fallback']} |")
    return "\n".join(L)
