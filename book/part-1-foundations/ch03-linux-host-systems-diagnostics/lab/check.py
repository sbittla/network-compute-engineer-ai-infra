#!/usr/bin/env python3
"""Automated checker for the Chapter 3 lab (host collector + fleet analyzer).

    python check.py                    # check your starter/ implementation (default)
    python check.py --impl solution    # check the reference implementation (instructors)

Prints one line per check (PASS / FAIL / TODO) and exits 0 only if every check passes.
Pure Python, no root, no hardware, no network; the collector is exercised with a fake runner,
so no real command is executed. Expected analyzer findings are stored only as salted hashes,
so this file does not reveal the planted faults.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SNAPS = DATA / "snapshots"
BASELINE = DATA / "orion_hx8_baseline.yaml"

# sha256("ch03-salt|host|CHECK_ID|severity")[:16] for every critical/warning finding the
# reference analyzer produces on the six ORION snapshots.
EXPECTED = {
    "1b6f96ba8ad47c22", "8b00720ab53ae1e4", "267505f0a459f7c7", "194deb4914e3bcbe",
    "98f144d82f2ad2f0", "f74f91abc8b92fb8", "29881e256d57444e", "e610b9e35c51227e",
    "0f21ec64648645dc", "b0c8d621b3bec3a9", "0047da9354dfde06", "fc280f9e750c6668",
    "b1b29b8ae3b4eac3", "20e6278e1a694a92",
}


def h(key: str) -> str:
    return hashlib.sha256(("ch03-salt|" + key).encode()).hexdigest()[:16]


def load_module(impl: str, name: str) -> ModuleType:
    base = HERE / "starter" if impl == "starter" else HERE.parent / "solutions" / "lab"
    path = base / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found (solutions are not shipped in the student edition)")
    spec = importlib.util.spec_from_file_location(f"ch03_{impl}_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod          # dataclasses need the module registered
    spec.loader.exec_module(mod)
    return mod


class Check:
    def __init__(self) -> None:
        self.results: list[tuple[str, str, str]] = []

    def run(self, name: str, fn) -> None:
        try:
            msg = fn()
            self.results.append(("PASS", name, msg or ""))
        except NotImplementedError as exc:
            self.results.append(("TODO", name, str(exc) or "not implemented"))
        except AssertionError as exc:
            self.results.append(("FAIL", name, str(exc) or "assertion failed"))
        except Exception as exc:  # report learner bugs without a traceback dump
            tb = traceback.extract_tb(exc.__traceback__)[-1]
            self.results.append(("FAIL", name, f"{type(exc).__name__}: {exc} (at {Path(tb.filename).name}:{tb.lineno})"))


# --------------------------------------------------------------------------- fakes
def make_fake_runner(col: ModuleType):
    calls: list[tuple[str, ...]] = []

    def runner(argv, timeout_s):
        calls.append(tuple(argv))
        tool = argv[0]
        if tool == "iostat":
            return col.CommandResult(list(argv), "missing", None, "", "[Errno 2] No such file or directory: 'iostat'")
        if tool == "dmesg":
            return col.CommandResult(list(argv), "denied", 1, "", "dmesg: read kernel buffer failed: Operation not permitted\n")
        out = "\n".join(f"{tool} line {i}" for i in range(60)) + "\n"
        return col.CommandResult(list(argv), "ok", 0, out, "")
    return runner, calls


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        col = load_module(args.impl, "host_collector")
        ana = load_module(args.impl, "host_analyzer")
    except Exception as exc:
        print(f"FAIL import: {type(exc).__name__}: {exc}")
        return 2

    snaps = {p.stem: ana.load_snapshot(p) for p in sorted(SNAPS.glob("*.json"))}
    base = ana.load_baseline(BASELINE)

    def out(host: str, sec: str) -> str:
        return snaps[host]["sections"][sec]["stdout"]

    C = Check()

    # ------------------------------------------------------------------ collector
    def c_classify():
        f = col.classify_outcome
        import subprocess
        assert f(None, "", FileNotFoundError("x")) == "missing", "FileNotFoundError should be 'missing'"
        assert f(None, "", PermissionError("x")) == "denied", "PermissionError should be 'denied'"
        assert f(None, "", subprocess.TimeoutExpired(["x"], 1)) == "timeout", "TimeoutExpired should be 'timeout'"
        assert f(None, "", OSError("x")) == "error", "other exceptions should be 'error'"
        assert f(1, "dmesg: read kernel buffer failed: Operation not permitted", None) == "denied", \
            "non-zero rc with 'Operation not permitted' should be 'denied'"
        assert f(2, "something broke", None) == "error", "non-zero rc without permission text should be 'error'"
        assert f(0, "", None) == "ok"
        return "missing/denied/timeout/error/ok classified"
    C.run("collector.classify_outcome", c_classify)

    def c_plan():
        plan = col.build_command_plan(["lo", "rail0", "fe0"], pid=48211)
        names = [s.name for s in plan]
        need = {"uname", "lscpu", "numactl_hardware", "free", "vmstat", "iostat", "mpstat", "ip_link", "lspci",
                "nvidia_smi", "kernel_log", "ethtool:rail0", "ethtool:fe0", "numastat_pid", "taskset_pid"}
        assert need <= set(names), f"missing sections: {sorted(need - set(names))}"
        assert "ethtool:lo" not in names, "do not run ethtool on lo"
        for s in plan:
            assert isinstance(s.argv, tuple) and all(isinstance(a, str) for a in s.argv), f"{s.name}: argv must be a tuple of str"
            assert col.is_read_only(s), f"{s.name}: {s.argv} is not read-only"
        kl = next(s for s in plan if s.name == "kernel_log")
        assert kl.fallback and kl.fallback[0] == "journalctl", "kernel_log needs a journalctl fallback"
        assert "numastat_pid" not in [s.name for s in col.build_command_plan([], None)], "pid sections only when pid given"
        bad = [("ethtool", "-s", "rail0", "speed", "200000"), ("ethtool", "--set-priv-flags", "rail0", "x", "on"),
               ("ethtool", "-sfoo"), ("sudo", "lspci", "-vv"), ("ip", "link", "set", "rail0", "mtu", "1500"),
               ("dmesg", "-c"), ("rm", "-rf", "/tmp/x"), ("nvidia-smi", "--power-limit=300"),
               ("nvidia-smi", "-pl", "300"), ("nvidia-smi", "-mig", "1"), ("nvidia-smi", "-lmc", "1593"),
               ("nvidia-smi", "-r"), ("taskset", "-cp", "0-3", "1234"), ("lspci", "-vv", "-s", "5d:00.0;reboot"),
               ("numactl", "--membind=0", "python3")]
        for argv in bad:
            assert not col.argv_is_read_only(argv), f"guard accepted a mutating/unknown command: {argv}"
        assert not col.is_read_only(col.CommandSpec("d", ("dmesg", "-T"), fallback=("dmesg", "-c"))),             "a mutating fallback must make the whole spec unsafe"
        # Held-out cases (encoded so they are not a checklist to code against): more setters and
        # allowed forms with extra tokens. A default-deny guard refuses all of them without changes.
        import base64, json
        held = json.loads(base64.b64decode("W1sibnZpZGlhLXNtaSIsICItcG0iLCAiMSJdLCBbImV0aHRvb2wiLCAiLUsiLCAicmFpbDAiLCAidHNvIiwgIm9mZiJdLCBbImRtZXNnIiwgIi0tY2xlYXIiXSwgWyJpcCIsICJyb3V0ZSIsICJkZWwiLCAiZGVmYXVsdCJdLCBbImlwIiwgIi1zIiwgImxpbmsiLCAic2hvdyIsICJleHRyYSJdLCBbImV0aHRvb2wiLCAiLWkiLCAicmFpbDAiLCAicmFpbDEiXSwgWyJudW1hc3RhdCIsICItcCIsICIxIiwgIjIiXSwgWyJudmlkaWEtc21pIiwgIi1xIiwgIi1kIiwgIngiLCAiLS1yZXNldCJdLCBbImpvdXJuYWxjdGwiLCAiLS12YWN1dW0tc2l6ZT0xTSJdLCBbImxzcGNpIiwgIi12diIsICItdyJdLCBbIm52aWRpYS1zbWkiLCAiLS1xdWVyeS1ncHU9aW5kZXgiLCAiLS1mb3JtYXQ9Y3N2IiwgIi1mIiwgIi9ldGMvcGFzc3dkIl0sIFsidW5hbWUiLCAiLWEiLCAiLW4iLCAieCJdXQ=="))
        leaked = [tuple(a) for a in held if col.argv_is_read_only(tuple(a))]
        assert not leaked, f"guard accepted {len(leaked)} held-out unsafe/over-long form(s), e.g. {leaked[0][0]} ..."
        good = [("ip", "-s", "link", "show"), ("ethtool", "-i", "rail0"), ("lspci", "-s", "5d:00.0", "-vv"),
                ("nvidia-smi", "--query-gpu=index,pci.bus_id", "--format=csv"), ("numastat", "-p", "1")]
        for argv in good:
            assert col.argv_is_read_only(argv), f"guard refused a read-only command: {argv}"
        return (f"{len(plan)} commands, all read-only; {len(bad)} listed + {len(held)} held-out unsafe forms refused; "
                f"{len(good)} read-only forms allowed")
    C.run("collector.build_command_plan + is_read_only", c_plan)

    def c_collect_linux():
        runner, calls = make_fake_runner(col)
        plan = [col.CommandSpec("lscpu", ("lscpu",)), col.CommandSpec("iostat", ("iostat", "-x", "1", "2")),
                col.CommandSpec("kernel_log", ("dmesg", "-T"), fallback=("journalctl", "-k", "-b", "--no-pager")),
                col.CommandSpec("evil", ("ip", "link", "set", "rail0", "down"))]

        def broken_reader():
            raise OSError("simulated sysfs read failure")
        rep = col.collect(plan, runner=runner, platform="linux", host="lab-host",
                          now=datetime(2026, 10, 14, 9, 15, 2, tzinfo=timezone.utc), is_root=False,
                          file_sections={"cpufreq": broken_reader}, context={"pid": 7, "note": "t"})
        assert rep["schema"] == "hostdiag/1", "schema must be 'hostdiag/1'"
        assert rep["collected_at"] == "2026-10-14T09:15:02Z", f"collected_at should be ISO UTC with Z, got {rep['collected_at']}"
        assert rep["host"] == "lab-host" and rep["user_is_root"] is False
        s = rep["sections"]
        assert s["iostat"]["status"] == "missing", "missing tool must be recorded as 'missing'"
        assert s["kernel_log"]["argv"][0] == "journalctl" and s["kernel_log"]["status"] == "ok", \
            "dmesg denied -> journalctl fallback should be tried and stored"
        assert len(s["kernel_log"].get("attempts", [])) == 2, "record both attempts for kernel_log"
        assert "Operation not permitted" in s["kernel_log"]["stderr"], "keep the primary's stderr as evidence"
        assert s["evil"]["status"] == "error", "a mutating spec must be refused"
        assert ("ip", "link", "set", "rail0", "down") not in calls, "refused command must never reach the runner"
        assert s["cpufreq"]["status"] == "error", "a failing file reader must become an 'error' section, not a crash"
        return f"{len(s)} sections; fallback, refusal and missing-tool paths correct"
    C.run("collector.collect (linux, degraded)", c_collect_linux)

    def c_collect_other():
        runner, calls = make_fake_runner(col)
        plan = [col.CommandSpec("lscpu", ("lscpu",)), col.CommandSpec("free", ("free", "-m")),
                col.CommandSpec("kernel_log", ("dmesg", "-T"), fallback=("journalctl", "-k", "-b", "--no-pager"))]
        rep = col.collect(plan, runner=runner, platform="win32", host="laptop",
                          is_root=False, file_sections={"interrupts": lambda: None})
        assert not calls, "runner must not be called on a non-Linux platform"
        st = {v["status"] for v in rep["sections"].values()}
        assert st == {"skipped"}, f"all sections should be 'skipped' on win32, got {st}"
        return f"{len(rep['sections'])} sections skipped, 0 commands run"
    C.run("collector.collect (non-Linux)", c_collect_other)

    def c_render():
        md = col.render_markdown(snaps["orion-n28"], max_lines=40)
        assert "orion-n28" in md and "2026-10-14T09:24:49Z" in md, "header must show host and timestamp"
        assert re.search(r"Evidence gaps:\s*3\b", md), "expected 'Evidence gaps: 3 ...' summary line"
        assert "| kernel_log |" in md and "denied" in md, "summary table must list each section and status"
        assert "more lines)" in md, "long outputs must be truncated with a '... (N more lines)' marker"
        assert "## lscpu" in md and "```text" in md
        return f"{len(md.splitlines())} lines of Markdown"
    C.run("collector.render_markdown", c_render)

    # ------------------------------------------------------------------ parsers
    def p_lscpu():
        c = ana.parse_lscpu(out("orion-n01", "lscpu"))
        assert (c["cpus"], c["sockets"], c["cores_per_socket"], c["threads_per_core"], c["numa_nodes"]) == (224, 2, 56, 2, 2), c
        assert len(c["numa_cpus"][1]) == 112 and 56 in c["numa_cpus"][1] and 223 in c["numa_cpus"][1], "NUMA CPU lists"
        assert "8480" in c["model_name"]
        return "2 sockets x 56 cores x 2 threads, 2 NUMA nodes"
    C.run("parse_lscpu", p_lscpu)

    def p_numactl():
        n = ana.parse_numactl_hardware(out("orion-n01", "numactl_hardware"))
        assert n["nodes"][0]["size_mb"] == 1031868 and n["nodes"][1]["size_mb"] == 1032151, n["nodes"].keys()
        assert len(n["nodes"][0]["cpus"]) == 112 and n["distances"] == [[10, 21], [21, 10]], "cpus/distances"
        return "node sizes, CPU lists, distance matrix"
    C.run("parse_numactl_hardware", p_numactl)

    def p_lspci():
        d = ana.parse_lspci_links(out("orion-n07", "lspci"))
        assert len(d) == 27, f"expected 27 devices, got {len(d)}"
        g = [x for x in d if x["kind"] == "gpu"]
        assert len(g) == 8, f"expected 8 GPUs, got {len(g)}"
        x = next(x for x in d if x["bdf"] == "0000:2a:00.0")
        assert (x["cap_speed_gts"], x["cap_width"], x["sta_speed_gts"], x["sta_width"], x["numa_node"]) == (32.0, 16, 32.0, 16, 0), x
        nr = ana.parse_lspci_links(out("orion-n28", "lspci"))
        assert all(y["access_denied"] and y["sta_width"] is None for y in nr), "non-root lspci: capabilities hidden"
        return "27 endpoints; link cap/status parsed; non-root access-denied detected"
    C.run("parse_lspci_links", p_lspci)

    def p_vmstat():
        v = ana.parse_vmstat(out("orion-n12", "vmstat"))
        assert v["samples"] == 4, f"exclude the since-boot first row: expected 4 live samples, got {v['samples']}"
        assert v["b"] >= 14, f"live 'b' average looks wrong ({v['b']:.1f}); did you include the since-boot row?"
        return f"b={v['b']:.2f}, wa={v['wa']:.2f} over {v['samples']} samples"
    C.run("parse_vmstat", p_vmstat)

    def p_iostat():
        io = ana.parse_iostat(out("orion-n12", "iostat"))
        assert abs(io["avg_cpu"]["%iowait"] - 6.9) < 1e-6, "use the LAST report (first is since boot)"
        assert abs(io["devices"]["nvme3n1"]["r_await"] - 48.6) < 1e-6 and io["devices"]["nvme3n1"]["%util"] > 99, "device columns"
        assert len(io["devices"]) == 10
        return "last report; 10 devices"
    C.run("parse_iostat", p_iostat)

    def p_mpstat():
        m = ana.parse_mpstat(out("orion-n12", "mpstat"))
        assert abs(m["all"]["%idle"] - 88.45) < 1e-6, "'all' row"
        assert len(m["cpus"]) == 224 and abs(m["cpus"][0]["%soft"] - 76.5) < 1e-6, "per-CPU rows"
        return "224 CPUs + all"
    C.run("parse_mpstat", p_mpstat)

    def p_irq():
        irqs = ana.parse_interrupts(out("orion-n01", "interrupts"))
        assert len(irqs) == 16, f"expected 16 IRQ rows, got {len(irqs)}"
        assert all(len(i["counts"]) == 224 for i in irqs), "one count per CPU"
        assert irqs[0]["bdf"] == "0000:19:00.0" and irqs[0]["name"].startswith("mlx5_comp0"), irqs[0]["name"]
        return "16 IRQs x 224 CPUs"
    C.run("parse_interrupts", p_irq)

    def p_net():
        links = ana.parse_ip_link(out("orion-n01", "ip_link"))
        assert len(links) == 11 and links["lo"]["mtu"] == 65536 and links["rail3"]["mtu"] == 9000, links.keys()
        assert links["fe1"]["state"] == "UP"
        e = ana.parse_ethtool(out("orion-n01", "ethtool:rail0"))
        assert e == {"speed_mbps": 400000, "duplex": "Full", "link_detected": True}, e
        e2 = ana.parse_ethtool("Settings for x:\n\tSpeed: Unknown!\n\tDuplex: Unknown! (255)\n\tLink detected: no\n")
        assert e2["speed_mbps"] is None and e2["link_detected"] is False, e2
        return "ip link + ethtool (incl. link-down form)"
    C.run("parse_ip_link + parse_ethtool", p_net)

    def p_numa_proc():
        n = ana.parse_numastat_process(out("orion-n01", "numastat_pid"))
        assert abs(n[0] - 205877.4) < 0.01 and abs(n[1] - 2210.6) < 0.01, n
        return "per-node MB from Total row"
    C.run("parse_numastat_process", p_numa_proc)

    def p_klog():
        ev = ana.scan_kernel_log(out("orion-n01", "kernel_log"))
        aer = [e for e in ev if e["kind"] == "aer_corrected"]
        assert len(aer) == 2 and aer[0]["device"] == "0000:9b:00.0", f"count one AER event per 'error received' line ({len(aer)})"
        extra = ("[x] EDAC MC0: 3 CE memory read error on CPU_SrcID#0_MC#0_Chan#1_DIMM#0 (channel:1)\n"
                 "[x] NVRM: Xid (PCI:0000:18:00): 79, pid=1234, GPU has fallen off the bus.\n"
                 "[x] pcieport 0000:15:01.0: AER: Uncorrected (Non-Fatal) error received: 0000:18:00.0\n")
        e2 = ana.scan_kernel_log(extra)
        kinds = sorted(e["kind"] for e in e2)
        assert kinds == ["aer_uncorrected", "edac_ce", "xid"], kinds
        assert next(e for e in e2 if e["kind"] == "edac_ce")["count"] == 3
        assert next(e for e in e2 if e["kind"] == "xid")["xid"] == 79
        return "AER/EDAC/Xid extraction"
    C.run("scan_kernel_log", p_klog)

    # ------------------------------------------------------------------ analysis
    def a_healthy():
        f = ana.analyze_host(snaps["orion-n01"], base)
        bad = [x for x in f if x.severity != "info"]
        assert not bad, f"reference node should have no warning/critical findings, got {[(x.check_id, x.subject) for x in bad]}"
        return f"0 warning/critical ({len(f)} info)"
    C.run("analyze_host on the reference node", a_healthy)

    fleet_cache: dict = {}

    def fleet():
        if "f" not in fleet_cache:
            fleet_cache["f"] = ana.analyze_fleet(snaps, base)
        return fleet_cache["f"]

    def a_recall():
        got = {h(x.key()) for x in fleet() if x.severity != "info"}
        found = len(EXPECTED & got)
        assert found == len(EXPECTED), f"found {found}/{len(EXPECTED)} expected host/check/severity findings"
        return f"{found}/{len(EXPECTED)} planted problems detected at the right severity"
    C.run("analyze_fleet recall (planted faults)", a_recall)

    def a_precision():
        extra = sorted({x.key() for x in fleet() if x.severity != "info" and h(x.key()) not in EXPECTED})
        assert not extra, f"{len(extra)} unexpected warning/critical findings: {extra[:4]}"
        return "no false positives at warning/critical"
    C.run("analyze_fleet precision (no false alarms)", a_precision)

    def a_graceful():
        f = ana.analyze_host(snaps["orion-n28"], base)
        gaps = [x for x in f if x.check_id == "EVIDENCE_GAP"]
        assert len(gaps) >= 3, f"expected >= 3 EVIDENCE_GAP findings, got {len(gaps)}"
        assert not [x for x in f if x.severity != "info"], "non-root idle snapshot should raise no warning/critical"
        assert any("sysfs" in x.evidence for x in f), "fall back to sysfs PCIe data when lspci is access-denied"
        skipped = {"host": "laptop", "context": {}, "sections": {
            k: {"argv": [k], "status": "skipped", "returncode": None, "stdout": "", "stderr": "not supported on win32",
                "elapsed_s": 0.0} for k in ("lscpu", "lspci", "kernel_log", "ip_link", "iostat")}}
        f2 = ana.analyze_host(skipped, base)
        assert {x.check_id for x in f2} == {"EVIDENCE_GAP"}, "an all-skipped snapshot yields only EVIDENCE_GAP findings"
        return f"{len(gaps)} evidence gaps reported; sysfs fallback used; all-skipped snapshot handled"
    C.run("analyze_host graceful degradation", a_graceful)

    def a_sysfs_aer():
        import copy
        snap = copy.deepcopy(snaps["orion-n07"])
        snap["sections"]["kernel_log"].update(status="denied", stdout="", stderr="Operation not permitted")
        f = ana.analyze_host(snap, base)
        hit = [x for x in f if x.check_id == "PCIE_AER_CORRECTED" and x.severity == "warning"]
        assert hit and "sysfs" in hit[0].evidence,             "with the kernel log denied, use the sysfs aer_cor_total counters for PCIE_AER_CORRECTED"
        p = ana.parse_pcie_sysfs(out("orion-n01", "pcie_sysfs"))
        assert next(d for d in p if d["bdf"] == "0000:9b:00.0")["aer_cor_total"] == 2, "parse aer_cor_total"
        return "sysfs AER counters parsed and used as a kernel-log fallback"
    C.run("AER from sysfs when the kernel log is denied", a_sysfs_aer)

    def a_report():
        F = ana.Finding
        fs = [F("hostA", "MTU_MISMATCH", "critical", "rail3", "rail3 mtu 1500"),
              F("hostA", "IO_SATURATION", "warning", "nvme3n1", "r_await 48 ms"),
              F("hostB", "EVIDENCE_GAP", "info", "iostat", "missing")]
        md = ana.write_report(fs, ["hostA", "hostB", "hostC"])
        for host in ("hostA", "hostB", "hostC"):
            assert host in md, f"{host} missing from report"
        assert md.find("Critical") < md.find("Warning") < md.find("Info"), "group findings critical -> warning -> info"
        return f"{len(md.splitlines())} lines"
    C.run("write_report", a_report)

    width = max(len(n) for _, n, _ in C.results)
    for status, name, msg in C.results:
        print(f"{status:<4} {name:<{width}}  {msg}")
    passed = sum(1 for s, _, _ in C.results if s == "PASS")
    todo = sum(1 for s, _, _ in C.results if s == "TODO")
    print(f"\n{passed}/{len(C.results)} checks passed ({todo} TODO) [impl={args.impl}]")
    return 0 if passed == len(C.results) else 1


if __name__ == "__main__":
    sys.exit(main())
