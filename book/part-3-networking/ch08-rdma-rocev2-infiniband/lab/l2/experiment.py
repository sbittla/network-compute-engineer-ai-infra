"""Ch 8 L2: run the readiness validator on this host's real RDMA inventory, and measure memory-registration cost.

The chapter's hardware extension is L3: perftest (``ib_write_bw`` / ``ib_write_lat``) per rail between
two hosts with RDMA NICs. This host has no RDMA device, so that part is probed and recorded as not
runnable. Two things do apply on one host, and the experiment does both:

1. **Readiness on real data (L1 analysis on locally probed input).** It captures this host's inventory
   with the same ``### cmd:`` sections as ``lab/data/inventory/`` (``ibv_devinfo``, ``rdma link``,
   ``ip -o link``, ``lsmod`` ...), using the real command output or, where the tool is not installed,
   the equivalent sysfs/procfs view rendered in that tool's format and labelled as such. It then runs
   the lab's own ``check_node`` against ``baseline.yaml``. The validator must say NOT_READY and name
   the missing devices and peer-memory module: a readiness tool that passes a host without RDMA
   devices is broken.
2. **Memory registration (Section 8.3: memory regions, pinning).** ``ibv_reg_mr`` pins the pages of a
   buffer so the NIC can DMA into it. The same kernel pinning path is exercised here with
   ``cudaHostRegister`` (page-locking an existing pageable buffer for GPU DMA) and with ``mlock``. It
   measures registration and deregistration time against buffer size, then the break-even number of
   reuses after which registering beats copying from pageable memory. That is the reason RDMA
   libraries cache registrations instead of registering per message.

CPU fallback: the readiness run is identical; registration is measured with ``mlock``/``munlock`` only
(the GPU pinning and pinned-vs-pageable copy are skipped, and the report says so).
"""
from __future__ import annotations

import ctypes
import ctypes.util
import importlib.util
import os
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch08-l2",
    "title": "Lab 8 L2: readiness validator on this host's real inventory, and memory-registration cost",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same readiness run on the real host inventory, and mlock/munlock registration cost versus "
                     "size (no cudaHostRegister or pinned-vs-pageable copy without a GPU)"),
}

PKG = Path(__file__).resolve().parents[2]
HOST_LABEL = "l2host-01"  # check_node derives the node index from a trailing number


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


# --------------------------------------------------------------------------------------------- inventory
def sysfs_ip_link() -> str:
    """``ip -o link show`` rendered from /sys/class/net (iproute2 is not installed in the image)."""
    out = []
    for i, d in enumerate(sorted(Path("/sys/class/net").iterdir()), 1):
        flags = int(read(d / "flags") or "0", 16)
        state = (read(d / "operstate") or "unknown").upper()
        fl = ",".join(n for bit, n in ((0x8, "LOOPBACK"), (0x1, "UP"), (0x40, "LOWER_UP")) if flags & bit)
        out.append(f"{i}: {d.name}: <{fl}> mtu {read(d / 'mtu')} qdisc noqueue state {state} mode DEFAULT "
                   f"group default qlen 1000\\    link/{'loopback' if flags & 0x8 else 'ether'} {read(d / 'address')}")
    return "\n".join(out)


def proc_lsmod() -> str:
    lines = ["Module                  Size  Used by"]
    for ln in (read("/proc/modules") or "").splitlines():
        p = ln.split()
        if len(p) >= 3:
            lines.append(f"{p[0]:<24}{p[1]:>6}  {p[2]}")
    return "\n".join(lines)


def capture_inventory() -> tuple[str, list[dict]]:
    """A capture file in the lab's format; every section records how it was obtained."""
    sections, prov = [], []

    def add(cmd: str, how: str, text: str) -> None:
        sections.append(f"### cmd: {cmd}\n{text}")
        prov.append({"section": cmd, "source": how, "lines": len(text.splitlines())})

    for cmd in (["ibv_devinfo"], ["rdma", "link", "show"], ["show_gids"]):
        rc, out = sh(cmd)
        add(" ".join(cmd), "command" if rc != 127 else "command not installed", out)
    for nd in ("ens1np0",):
        for cmd in (["ethtool", "-i", nd], ["ethtool", nd]):
            rc, out = sh(cmd)
            add(" ".join(cmd), "command" if rc != 127 else "command not installed", out)
    rc, out = sh(["ip", "-o", "link", "show"])
    add("ip -o link show", "command", out) if rc == 0 else add("ip -o link show", "rendered from /sys/class/net", sysfs_ip_link())
    rc, out = sh(["ip", "-o", "-4", "addr", "show"])
    add("ip -o -4 addr show", "command" if rc == 0 else "command not installed", out)
    add("lsmod | grep -E 'peermem|mlx5|ib_core|ib_uverbs'", "rendered from /proc/modules (filtered)",
        "\n".join(ln for ln in proc_lsmod().splitlines() if any(k in ln for k in ("peermem", "mlx5", "ib_core", "ib_uverbs"))))
    env_txt = read("/etc/halcyon/rdma.env")
    add("cat /etc/halcyon/rdma.env", "file" if env_txt is not None else "file absent", env_txt or "")
    head = [f"### host: {HOST_LABEL}", f"### collected: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"]
    return "\n".join(head + sections) + "\n", prov


def readiness_on_host() -> dict:
    import yaml  # noqa: PLC0415
    text, prov = capture_inventory()
    mod, src = load_l1("readiness")
    baseline = yaml.safe_load((PKG / "lab" / "data" / "baseline.yaml").read_text(encoding="utf-8"))
    out = {"inventory": text, "provenance": prov, "module": src, "findings": [], "verdict": None, "error": None}
    if mod is None:
        out["error"] = "readiness module not found"
        return out
    try:
        inv = mod.split_sections(text)
        findings = mod.check_node(inv, baseline)
        out["findings"] = [{"device": f.device, "check": f.check_id, "message": f.message} for f in findings]
        out["verdict"] = "NOT_READY" if findings else "READY"
        out["rails_expected"] = len(baseline["rails"])
    except Exception as exc:  # noqa: BLE001 - starter TODOs
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


# --------------------------------------------------------------------------------------------- registration
def libc():
    return ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6", use_errno=True)


def time_mlock(buf_ptr: int, nbytes: int, reps: int) -> tuple[list[float], list[float], int]:
    lc = libc()
    lc.mlock.argtypes = lc.munlock.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    reg, dereg, err = [], [], 0
    for i in range(reps + 2):
        t0 = time.perf_counter()
        rc = lc.mlock(ctypes.c_void_p(buf_ptr), ctypes.c_size_t(nbytes))
        t1 = time.perf_counter()
        if rc != 0:
            err = ctypes.get_errno()
            break
        lc.munlock(ctypes.c_void_p(buf_ptr), ctypes.c_size_t(nbytes))
        t2 = time.perf_counter()
        if i >= 2:  # 2 warm-ups
            reg.append(t1 - t0)
            dereg.append(t2 - t1)
    return reg, dereg, err


def time_cuda_register(torch, t, reps: int) -> tuple[list[float], list[float]]:
    cudart = torch.cuda.cudart()
    reg, dereg = [], []
    ptr, n = t.data_ptr(), t.numel() * t.element_size()
    for i in range(reps + 2):
        t0 = time.perf_counter()
        rc = cudart.cudaHostRegister(ptr, n, 0)
        t1 = time.perf_counter()
        if int(rc) != 0:
            raise RuntimeError(f"cudaHostRegister returned {rc}")
        cudart.cudaHostUnregister(ptr)
        t2 = time.perf_counter()
        if i >= 2:
            reg.append(t1 - t0)
            dereg.append(t2 - t1)
    return reg, dereg


def run(ctx) -> dict:
    torch = ctx.torch
    import hwlab  # noqa: PLC0415 - /opt/hwlab is on sys.path inside the image

    rdy = readiness_on_host()
    probe = {
        "sys_class_infiniband": sorted(p.name for p in Path("/sys/class/infiniband").iterdir())
        if Path("/sys/class/infiniband").is_dir() else [],
        "dev_infiniband": Path("/dev/infiniband").exists(),
        "rdma_rxe_module": "rdma_rxe" in (read("/proc/modules") or ""),
        "tools": {t: bool(shutil.which(t)) for t in ("ibv_devinfo", "ib_write_bw", "ib_write_lat", "rdma", "ethtool")},
        "rlimit_memlock": resource.getrlimit(resource.RLIMIT_MEMLOCK),
        "euid": os.geteuid(),
    }
    sizes_mib = [4, 64] if ctx.quick else [4, 64, 256, 1024]
    reps = ctx.reps(10)
    rows, copy_rows = [], []
    for mib in sizes_mib:
        n = mib << 20
        buf = torch.empty(n, dtype=torch.uint8)
        buf.fill_(1)  # fault the pages in first: registration cost is then pinning, not page allocation
        reg, dereg, err = time_mlock(buf.data_ptr(), n, reps)
        if reg:
            r, d = hwlab.summarize(reg), hwlab.summarize(dereg)
            rows.append({"method": "mlock", "size_mib": mib, "register_median_s": r["median"], "register_p95_s": r["p95"],
                         "deregister_median_s": d["median"], "n": r["n"], "us_per_mib": r["median"] / mib * 1e6})
        else:
            rows.append({"method": "mlock", "size_mib": mib, "error": os.strerror(err), "n": 0})
        if ctx.is_gpu:
            reg, dereg = time_cuda_register(torch, buf, reps)
            r, d = hwlab.summarize(reg), hwlab.summarize(dereg)
            rows.append({"method": "cudaHostRegister", "size_mib": mib, "register_median_s": r["median"],
                         "register_p95_s": r["p95"], "deregister_median_s": d["median"], "n": r["n"],
                         "us_per_mib": r["median"] / mib * 1e6})
            dev = torch.empty(n, dtype=torch.uint8, device="cuda")
            pinned = torch.empty(n, dtype=torch.uint8).pin_memory()
            pg = ctx.bench(lambda: dev.copy_(buf), reps=reps)
            pn = ctx.bench(lambda: dev.copy_(pinned, non_blocking=True), reps=reps)
            gain = pg["median"] - pn["median"]
            reg_cost = rows[-1]["register_median_s"] + rows[-1]["deregister_median_s"]
            copy_rows.append({"size_mib": mib, "pageable_h2d_s": pg["median"], "pinned_h2d_s": pn["median"],
                              "pageable_gbs": n / pg["median"] / 1e9, "pinned_gbs": n / pn["median"] / 1e9,
                              "register_plus_deregister_s": reg_cost,
                              "break_even_reuses": (reg_cost / gain) if gain > 0 else None})
            del dev, pinned
        ctx.log(f"{mib:>5} MiB  " + "  ".join(f"{r['method']} reg {r['register_median_s'] * 1e3:.2f} ms"
                                              for r in rows if r["size_mib"] == mib and "register_median_s" in r))
        del buf

    metrics = {"readiness_verdict": rdy["verdict"], "readiness_findings": len(rdy["findings"]),
               "readiness_checks_failed": sorted({f["check"] for f in rdy["findings"]}),
               "rdma_devices": len(probe["sys_class_infiniband"]), "rlimit_memlock": ("unlimited" if probe["rlimit_memlock"][0] == resource.RLIM_INFINITY
                                  else f"{probe['rlimit_memlock'][0] >> 10} KiB")}
    for meth in ("mlock", "cudaHostRegister"):
        big = [r for r in rows if r["method"] == meth and "us_per_mib" in r]
        if big:
            metrics[f"{meth}_us_per_mib_at_{big[-1]['size_mib']}MiB"] = round(big[-1]["us_per_mib"], 2)
    if copy_rows:
        metrics["break_even_reuses_at_largest"] = (round(copy_rows[-1]["break_even_reuses"], 2)
                                                   if copy_rows[-1]["break_even_reuses"] else None)
    not_runnable = [
        {"part": "perftest per rail (ib_write_bw -a --report_gbits, ib_write_lat -a) between two hosts",
         "needs": ["2+ hosts with RDMA NICs (RoCEv2 or InfiniBand) on a lab fabric", "rdma-core and perftest",
                   "root or CAP_NET_ADMIN for dcb/ethtool"], "probe": probe},
        {"part": "Soft-RoCE stand-in (rdma link add rxe0 type rxe netdev <if>)",
         "needs": ["a kernel with the rdma_rxe module", "CAP_NET_ADMIN", "a real netdev (the harness runs with --network none)"],
         "probe": {"rdma_rxe_module": probe["rdma_rxe_module"], "euid": probe["euid"]}},
    ]
    notes = [
        "Inventory sections are the real command output where the tool exists; ip -o link and lsmod are rendered from "
        "/sys/class/net and /proc/modules in those tools' formats (see tables.inventory_provenance).",
        f"The host is labelled {HOST_LABEL} because check_node derives the node index from a trailing number.",
        "Registration timing: perf_counter around each call, 2 warm-ups, then >= 5 repetitions per size; the buffer's "
        "pages are touched first so the cost measured is pinning, not page allocation.",
    ]
    if rdy["error"]:
        notes.append(f"Readiness validator not run: {rdy['error']} (implement lab/starter/readiness.py).")
    tables = {"registration": rows, "pinned_vs_pageable": copy_rows, "readiness_findings": rdy["findings"],
              "inventory_provenance": rdy["provenance"], "inventory": rdy["inventory"]}
    return {"metrics": metrics, "tables": tables, "notes": notes, "not_runnable_parts": not_runnable}


def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    fails = []
    if m["readiness_verdict"] is not None:
        if m["rdma_devices"] == 0 and m["readiness_verdict"] == "READY":
            fails.append("readiness says READY on a host with no RDMA device: check_node is not checking device presence")
        if m["rdma_devices"] == 0 and "PORT_STATE" not in m["readiness_checks_failed"]:
            fails.append("missing RDMA devices must surface as PORT_STATE findings")
    for meth in ("mlock",) + (("cudaHostRegister",) if env["device"] == "cuda" else ()):
        rows = [r for r in t["registration"] if r["method"] == meth]
        if any("error" in r for r in rows):
            fails.append(f"{meth} failed ({rows[0].get('error')}): check RLIMIT_MEMLOCK ({m['rlimit_memlock']}) or CAP_IPC_LOCK")
            continue
        if any(r["n"] < 5 for r in rows):
            fails.append(f"{meth}: fewer than 5 repetitions")
        if rows[-1]["register_median_s"] <= rows[0]["register_median_s"]:
            fails.append(f"{meth}: registering {rows[-1]['size_mib']} MiB was not slower than {rows[0]['size_mib']} MiB; "
                         "pinning cost must grow with the number of pages")
        if len(rows) >= 2 and rows[-1]["us_per_mib"] > 5 * rows[-2]["us_per_mib"]:
            fails.append(f"{meth}: per-MiB cost jumped > 5x between the two largest sizes (memory pressure? check "
                         "free memory in the container)")
    if env["device"] == "cuda":
        for r in t["pinned_vs_pageable"]:
            if r["pinned_h2d_s"] > 1.05 * r["pageable_h2d_s"]:
                fails.append(f"pinned H2D slower than pageable at {r['size_mib']} MiB")
    return fails


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    lines = ["## Readiness validator on this host's real inventory", ""]
    if m["readiness_verdict"]:
        lines += [f"Verdict: **{m['readiness_verdict']}**, {m['readiness_findings']} findings "
                  f"({', '.join(m['readiness_checks_failed'])}). RDMA devices found: {m['rdma_devices']}.", "",
                  "| Device | Check | Evidence |", "|---|---|---|"]
        for f in t["readiness_findings"]:
            lines.append(f"| {f['device']} | {f['check']} | {f['message']} |")
    else:
        lines.append("_Validator not run (see notes)._")
    lines += ["", "| Inventory section | Source |", "|---|---|"]
    for p in t["inventory_provenance"]:
        sec = p["section"].replace("|", "\\|")
        lines.append(f"| `{sec}` | {p['source']} |")
    lines += ["", "## Memory registration cost (pinning pages for DMA)", "",
              "| Method | Size (MiB) | Register median (ms) | p95 (ms) | Deregister median (ms) | us per MiB | n |",
              "|---|---|---|---|---|---|---|"]
    for r in t["registration"]:
        if "error" in r:
            lines.append(f"| {r['method']} | {r['size_mib']} | failed: {r['error']} | | | | 0 |")
        else:
            lines.append(f"| {r['method']} | {r['size_mib']} | {r['register_median_s'] * 1e3:.3f} | {r['register_p95_s'] * 1e3:.3f} | "
                         f"{r['deregister_median_s'] * 1e3:.3f} | {r['us_per_mib']:.1f} | {r['n']} |")
    if t["pinned_vs_pageable"]:
        lines += ["", "| Size (MiB) | Pageable H2D (GB/s) | Pinned H2D (GB/s) | Register + deregister (ms) | Break-even reuses |",
                  "|---|---|---|---|---|"]
        for r in t["pinned_vs_pageable"]:
            be = f"{r['break_even_reuses']:.1f}" if r["break_even_reuses"] else "never (pinned not faster)"
            lines.append(f"| {r['size_mib']} | {r['pageable_gbs']:.2f} | {r['pinned_gbs']:.2f} | "
                         f"{r['register_plus_deregister_s'] * 1e3:.2f} | {be} |")
    lines += ["", "What to conclude:", "",
              "- A readiness tool is only trustworthy if it fails loudly on a host that cannot do RDMA at all; this one "
              "reports every expected rail as missing and the peer-memory module as absent.",
              "- Registration cost grows with the number of pages pinned, so registering per message is expensive. "
              "Register once, reuse the memory region, and let NCCL/UCX registration caches do this for you. Unbounded "
              "pinning is also why RLIMIT_MEMLOCK (`ulimit -l`) must be raised on RDMA hosts "
              f"(here: {m['rlimit_memlock']}).",
              "- This is a laptop host in a WSL2 container with no NIC; the RDMA rows of the chapter (perftest bandwidth "
              "plateau, p99.9 latency) need the L3 two-host setup."]
    if env["device"] != "cuda":
        lines += ["", "_CPU fallback: cudaHostRegister and the pinned-versus-pageable copy were not measured; mlock exercises "
                  "the same kernel page-pinning path._"]
    lines += ["", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}.")
    return "\n".join(lines)
