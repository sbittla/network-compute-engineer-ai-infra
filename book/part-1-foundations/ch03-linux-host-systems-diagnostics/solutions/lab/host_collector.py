#!/usr/bin/env python3
"""Read-only Linux host diagnostic collector (Chapter 3, Progressive Lab 1) — REFERENCE SOLUTION.

Collects a timestamped host inventory and health snapshot from standard tools
(lscpu, numactl, free, vmstat, iostat, mpstat, ip, ethtool, lspci, dmesg/journalctl,
nvidia-smi, numastat, taskset) plus a few sysfs/procfs files, and writes it as JSON
(machine-readable, schema ``hostdiag/1``) and Markdown (human-readable).

Safety contract:
  * Read-only. Every command is on an explicit allowlist and is run with an argv list
    (never a shell), a timeout, and ``LC_ALL=C`` so output is parseable.
  * Never escalates privileges (no sudo). When a tool needs root, the section is
    recorded as ``denied`` and the report says what evidence is missing.
  * Degrades gracefully: missing tools -> ``missing``; timeouts -> ``timeout``;
    non-Linux platforms -> every section ``skipped``. The collector itself never
    raises for a per-command failure.

Usage (on a Linux host; root optional but gives more evidence):
    python host_collector.py --out-dir ./out
    python host_collector.py --out-dir ./out --pid 48211 --note "W-TRAIN straggler"
"""
from __future__ import annotations

import argparse
import json
import re
import os
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

SCHEMA = "hostdiag/1"
SAFE_PATH = "/usr/sbin:/usr/bin:/sbin:/bin"   # fixed tool search path; never the caller's PATH
COLLECTOR_VERSION = "1.0"

#: Exact read-only command forms, per tool. Anything not listed is refused (default deny): an
#: unknown tool, an unknown option, an extra argument, or a missing one. Placeholders: <int> small
#: integer, <pid> process ID, <iface> interface name, <bdf> PCI address, <fields> comma-separated
#: nvidia-smi query fields. ``--opt=value`` tokens are split before matching, so a setter such as
#: ``--power-limit=300`` cannot hide inside a single token.
ALLOWED_FORMS: dict[str, tuple[tuple[str, ...], ...]] = {
    "uname": (("-a",), ("-r",)),
    "lscpu": ((),),
    "numactl": (("--hardware",), ("-H",)),
    "free": (("-m",),),
    "vmstat": (("<int>", "<int>"),),
    "iostat": (("-x", "<int>", "<int>"),),
    "mpstat": (("-P", "ALL", "<int>", "<int>"),),
    "ip": (("link", "show"), ("-br", "link", "show"), ("-s", "link", "show"),
           ("link", "show", "dev", "<iface>"), ("-s", "link", "show", "dev", "<iface>")),
    "ethtool": (("<iface>",), ("-i", "<iface>"), ("-S", "<iface>"), ("-l", "<iface>")),
    "lspci": (("-vv",), ("-tv",), ("-s", "<bdf>", "-vv")),
    "dmesg": (("-T",),),
    "journalctl": (("-k", "-b", "--no-pager"),),
    "nvidia-smi": (("--query-gpu", "<fields>", "--format", "csv"),
                   ("--query-gpu", "<fields>", "--format", "csv,noheader"),
                   ("-q",), ("topo", "-m")),
    "numastat": (("-p", "<pid>"), ("-m",)),
    "taskset": (("-cp", "<pid>"),),   # a CPU list before the PID would SET the affinity
}

PLACEHOLDERS = {
    "<int>": re.compile(r"\d{1,3}"),
    "<pid>": re.compile(r"[1-9]\d{0,7}"),
    "<iface>": re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,14}"),
    "<bdf>": re.compile(r"(?:[0-9a-fA-F]{4}:)?[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]"),
    "<fields>": re.compile(r"[a-z][a-z0-9_.]*(?:,[a-z][a-z0-9_.]*)*"),
}


def split_opts(args: tuple[str, ...]) -> tuple[str, ...]:
    """Split ``--opt=value`` tokens into ``--opt`` and ``value``; other tokens are unchanged."""
    out: list[str] = []
    for tok in args:
        if tok.startswith("--") and "=" in tok:
            opt, val = tok.split("=", 1)
            out += [opt, val]
        else:
            out.append(tok)
    return tuple(out)


@dataclass(frozen=True)
class CommandSpec:
    """One read-only command to run. ``name`` is the report section name."""
    name: str
    argv: tuple[str, ...]
    timeout_s: float = 15.0
    fallback: tuple[str, ...] | None = None   # argv to try if the primary is denied/missing


@dataclass
class CommandResult:
    """Outcome of one command. ``status`` is ok|missing|denied|timeout|error|skipped."""
    argv: list[str]
    status: str
    returncode: int | None
    stdout: str = ""
    stderr: str = ""
    elapsed_s: float = 0.0
    attempts: list[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {"argv": self.argv, "status": self.status, "returncode": self.returncode,
             "stdout": self.stdout, "stderr": self.stderr, "elapsed_s": round(self.elapsed_s, 3)}
        if len(self.attempts) > 1:
            d["attempts"] = self.attempts
        return d


Runner = Callable[[tuple[str, ...], float], CommandResult]

DENIED_MARKERS = ("operation not permitted", "permission denied", "insufficient permissions",
                  "must be root", "access denied")


def classify_outcome(returncode: int | None, stderr: str, exc: BaseException | None) -> str:
    """Map a subprocess outcome to a report status.

    Args:
        returncode: process exit code, or None if the process never ran.
        stderr: captured standard error (may be empty).
        exc: exception raised while launching/waiting, or None.

    Returns:
        "missing" (executable not found), "denied" (permission problem, from the
        exception or from stderr text), "timeout", "error" (any other failure), or "ok".
    """
    if isinstance(exc, FileNotFoundError):
        return "missing"
    if isinstance(exc, PermissionError):
        return "denied"
    if isinstance(exc, subprocess.TimeoutExpired):
        return "timeout"
    if exc is not None:
        return "error"
    low = (stderr or "").lower()
    if returncode != 0 and any(m in low for m in DENIED_MARKERS):
        return "denied"
    if returncode != 0:
        return "error"
    return "ok"


def run_command(argv: tuple[str, ...], timeout_s: float) -> CommandResult:
    """Run one allowlisted command safely (no shell, timeout, C locale) and classify it."""
    if not argv_is_read_only(argv):
        return CommandResult(list(argv), "error", None, stderr="refused: not an allowed read-only form")
    # Resolve the tool only from a fixed system PATH, never from the caller's PATH (which under sudo
    # or a hostile environment could point at a look-alike binary).
    exe = shutil.which(argv[0], path=SAFE_PATH)
    if exe is None:
        return CommandResult(list(argv), "missing", None, stderr=f"{argv[0]} not found in {SAFE_PATH}")
    env = {"PATH": SAFE_PATH, "LC_ALL": "C", "LANG": "C"}
    t0 = time.perf_counter()
    try:
        p = subprocess.run([exe, *argv[1:]], capture_output=True, text=True, timeout=timeout_s, env=env,
                           stdin=subprocess.DEVNULL, check=False, encoding="utf-8", errors="replace")
        status = classify_outcome(p.returncode, p.stderr, None)
        return CommandResult(list(argv), status, p.returncode, p.stdout, p.stderr, time.perf_counter() - t0)
    except (OSError, subprocess.SubprocessError) as exc:
        return CommandResult(list(argv), classify_outcome(None, "", exc), None, "", str(exc),
                             time.perf_counter() - t0)


def build_command_plan(interfaces: list[str], pid: int | None = None) -> list[CommandSpec]:
    """Return the ordered list of read-only commands to run.

    Args:
        interfaces: network interface names to query with ``ethtool <iface>``
            (e.g. discovered from /sys/class/net, excluding ``lo``).
        pid: optional process ID whose NUMA placement and CPU affinity to record.

    Returns:
        CommandSpecs for uname, lscpu, numactl --hardware, free -m, vmstat 1 5,
        iostat -x 1 2, mpstat -P ALL 1 1, ip link show, ethtool per interface,
        lspci -vv, nvidia-smi PCIe query, the kernel log (dmesg -T with a journalctl
        -k fallback), and — if pid is given — numastat -p and taskset -cp.
    """
    plan = [
        CommandSpec("uname", ("uname", "-a")),
        CommandSpec("lscpu", ("lscpu",)),
        CommandSpec("numactl_hardware", ("numactl", "--hardware")),
        CommandSpec("free", ("free", "-m")),
        CommandSpec("vmstat", ("vmstat", "1", "5"), timeout_s=15),
        CommandSpec("iostat", ("iostat", "-x", "1", "2"), timeout_s=15),
        CommandSpec("mpstat", ("mpstat", "-P", "ALL", "1", "1"), timeout_s=15),
        CommandSpec("ip_link", ("ip", "link", "show")),
    ]
    plan += [CommandSpec(f"ethtool:{i}", ("ethtool", i)) for i in interfaces if i != "lo"]
    plan += [
        CommandSpec("lspci", ("lspci", "-vv"), timeout_s=30),
        CommandSpec("nvidia_smi", ("nvidia-smi",
                                   "--query-gpu=index,pci.bus_id,pcie.link.gen.current,pcie.link.gen.max,"
                                   "pcie.link.width.current,pcie.link.width.max,utilization.gpu",
                                   "--format=csv"), timeout_s=30),
        CommandSpec("kernel_log", ("dmesg", "-T"), fallback=("journalctl", "-k", "-b", "--no-pager")),
    ]
    if pid is not None:
        plan += [CommandSpec("numastat_pid", ("numastat", "-p", str(int(pid)))),
                 CommandSpec("taskset_pid", ("taskset", "-cp", str(int(pid))))]
    return plan


def argv_is_read_only(argv: tuple[str, ...]) -> bool:
    """True only if ``argv`` exactly matches one of ALLOWED_FORMS for its tool (default deny).

    Split ``--opt=value`` tokens first (:func:`split_opts`). A form matches when it has the same
    number of arguments and every position is either the identical literal or a placeholder whose
    regex (PLACEHOLDERS) fully matches the token. Unknown tools never match.
    """
    if not argv:
        return False
    forms = ALLOWED_FORMS.get(argv[0])
    if forms is None:
        return False
    args = split_opts(tuple(argv[1:]))
    for form in forms:
        if len(form) != len(args):
            continue
        if all(PLACEHOLDERS[want].fullmatch(tok) if want in PLACEHOLDERS else tok == want
               for want, tok in zip(form, args)):
            return True
    return False


def is_read_only(spec: CommandSpec) -> bool:
    """True if the primary argv and the fallback (if any) are both allowed read-only forms."""
    return all(argv_is_read_only(a) for a in (spec.argv, spec.fallback) if a is not None)


# --------------------------------------------------------------------------- file readers
def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def read_pcie_sysfs(root: Path = Path("/sys/bus/pci/devices")) -> CommandResult:
    """PCIe link state from sysfs — readable without root, unlike lspci's capability dump."""
    keep = ("0x0302", "0x0300", "0x0200", "0x0207", "0x0108")   # 3D, VGA, Ethernet, IB, NVMe
    lines = []
    try:
        devs = sorted(root.iterdir())
    except OSError as exc:
        return CommandResult(["read", str(root)], "denied" if isinstance(exc, PermissionError) else "missing",
                             None, stderr=str(exc))
    for d in devs:
        cls = _read(d / "class") or ""
        if not cls.startswith(keep):
            continue
        fields = [d.name, f"class={cls}"]
        for key in ("vendor", "device", "numa_node", "current_link_speed", "current_link_width",
                    "max_link_speed", "max_link_width"):
            fields.append(f"{key}={_read(d / key) or 'unknown'}")
        # AER counters since boot (world-readable; kernel 4.17+). The last line is TOTAL_ERR_*.
        for key, fname in (("aer_cor_total", "aer_dev_correctable"), ("aer_nonfatal_total", "aer_dev_nonfatal"),
                           ("aer_fatal_total", "aer_dev_fatal")):
            text = _read(d / fname)
            total = text.split()[-1] if text else ""
            fields.append(f"{key}={total if total.isdigit() else 'unknown'}")
        lines.append(";".join(fields))
    return CommandResult(["read", f"{root}/*/{{class,numa_node,*_link_*,aer_dev_*}}"], "ok", 0,
                         "\n".join(lines) + "\n")


def read_interrupts(path: Path = Path("/proc/interrupts")) -> CommandResult:
    text = _read(path)
    if text is None:
        return CommandResult(["read", str(path)], "missing", None, stderr=f"cannot read {path}")
    return CommandResult(["read", str(path)], "ok", 0, text + "\n")


def read_cpufreq(root: Path = Path("/sys/devices/system/cpu")) -> CommandResult:
    """Summarise scaling driver/governor/current frequency across all CPUs."""
    drivers: dict[str, int] = {}
    govs: dict[str, int] = {}
    freqs: list[int] = []
    for cpu in sorted(root.glob("cpu[0-9]*")):
        cf = cpu / "cpufreq"
        drv, gov, cur = _read(cf / "scaling_driver"), _read(cf / "scaling_governor"), _read(cf / "scaling_cur_freq")
        if drv:
            drivers[drv] = drivers.get(drv, 0) + 1
        if gov:
            govs[gov] = govs.get(gov, 0) + 1
        if cur and cur.isdigit():
            freqs.append(int(cur))
    if not drivers and not govs:
        return CommandResult(["read", f"{root}/cpu*/cpufreq"], "missing", None,
                             stderr="no cpufreq interface (VM, container, or cpufreq disabled)")
    out = [f"scaling_driver: {k} ({v} cpus)" for k, v in sorted(drivers.items())]
    out += [f"scaling_governor: {k} ({v} cpus)" for k, v in sorted(govs.items())]
    if freqs:
        freqs.sort()
        out.append(f"scaling_cur_freq_khz: min={freqs[0]} median={freqs[len(freqs) // 2]} max={freqs[-1]}")
    return CommandResult(["read", f"{root}/cpu*/cpufreq/{{scaling_driver,scaling_governor,scaling_cur_freq}}"],
                         "ok", 0, "\n".join(out) + "\n")


def discover_interfaces(root: Path = Path("/sys/class/net")) -> list[str]:
    try:
        return sorted(p.name for p in root.iterdir() if p.name != "lo")
    except OSError:
        return []


# --------------------------------------------------------------------------- collection
def collect(plan: list[CommandSpec], runner: Runner = run_command, platform: str | None = None,
            host: str | None = None, now: datetime | None = None, is_root: bool | None = None,
            file_sections: dict[str, Callable[[], CommandResult]] | None = None,
            context: dict | None = None) -> dict:
    """Run the plan and assemble a ``hostdiag/1`` report dict.

    Args:
        plan: commands from :func:`build_command_plan`.
        runner: function executing one argv with a timeout (injectable for tests).
        platform: ``sys.platform`` value; anything not starting with "linux" makes every
            section ``skipped`` without calling the runner.
        host: hostname to record (default: ``socket.gethostname()``).
        now: collection timestamp (default: current UTC time).
        is_root: whether the collector runs as root (default: ``os.geteuid() == 0`` when available).
        file_sections: extra sections produced by reading files (sysfs/procfs); on Linux each
            callable is invoked and its result stored under its key.
        context: free-form context to record (pid, operator note).

    Returns:
        dict with keys schema, collector_version, host, collected_at (ISO-8601 UTC, "Z"),
        platform, user_is_root, context, sections (name -> CommandResult.to_dict()).
        If a spec has a fallback and the primary is denied or missing, the fallback is tried;
        the stored section reflects the last attempt and lists all attempts.
    """
    platform = platform or sys.platform
    now = now or datetime.now(timezone.utc)
    if is_root is None:
        is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    report = {
        "schema": SCHEMA, "collector_version": COLLECTOR_VERSION,
        "host": host or socket.gethostname(),
        "collected_at": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform": "linux" if platform.startswith("linux") else platform,
        "user_is_root": bool(is_root), "context": context or {}, "sections": {},
    }
    linux = platform.startswith("linux")
    for spec in plan:
        if not linux:
            res = CommandResult(list(spec.argv), "skipped", None, stderr=f"not supported on {platform}")
        elif not is_read_only(spec):
            res = CommandResult(list(spec.argv), "error", None, stderr="refused: not read-only")
        else:
            res = runner(spec.argv, spec.timeout_s)
            attempts = [list(spec.argv)]
            if spec.fallback and res.status in ("denied", "missing"):
                first = res
                res = runner(spec.fallback, spec.timeout_s)
                attempts.append(list(spec.fallback))
                res.stderr = (first.stderr.rstrip("\n") + "\n" + res.stderr).strip("\n") + "\n"
            res.attempts = attempts
        report["sections"][spec.name] = res.to_dict()
    for name, fn in (file_sections or {}).items():
        if not linux:
            res = CommandResult(["read", name], "skipped", None, stderr=f"not supported on {platform}")
        else:
            try:
                res = fn()
            except OSError as exc:   # defensive: readers should not raise, but never crash
                res = CommandResult(["read", name], "error", None, stderr=str(exc))
        report["sections"][name] = res.to_dict()
    return report


def render_markdown(report: dict, max_lines: int = 40) -> str:
    """Render a report as Markdown: a header, a status summary table, then one section per command.

    The summary table has one row per section with its status, so a reader sees evidence gaps
    (missing/denied/timeout/skipped) before reading any output. Output blocks are truncated to
    ``max_lines`` lines with an explicit "... (N more lines)" marker.
    """
    secs = report["sections"]
    lines = [f"# Host diagnostic snapshot — {report['host']}", "",
             f"- Collected at: {report['collected_at']}",
             f"- Platform: {report['platform']}; running as root: {'yes' if report['user_is_root'] else 'no'}",
             f"- Schema: {report['schema']}; collector {report.get('collector_version', '?')}"]
    ctx = report.get("context") or {}
    if ctx:
        lines.append("- Context: " + ", ".join(f"{k}={v}" for k, v in ctx.items() if v not in (None, "")))
    gaps = [n for n, s in secs.items() if s["status"] != "ok"]
    lines += ["", f"Evidence gaps: {len(gaps)} of {len(secs)} sections not ok"
              + (f" ({', '.join(gaps)})" if gaps else ""), "",
              "| Section | Command | Status | Elapsed (s) |", "|---|---|---|---|"]
    for name, s in secs.items():
        lines.append(f"| {name} | `{' '.join(s['argv'])}` | {s['status']} | {s['elapsed_s']:.2f} |")
    for name, s in secs.items():
        lines += ["", f"## {name}", "", f"Status: **{s['status']}** (rc={s['returncode']})"]
        body = s["stdout"].splitlines()
        if s["status"] != "ok" and s["stderr"]:
            lines.append("")
            lines.append("stderr: " + s["stderr"].strip().replace("\n", " | "))
        if body:
            shown = body[:max_lines]
            lines += ["", "```text", *shown]
            if len(body) > max_lines:
                lines.append(f"... ({len(body) - max_lines} more lines)")
            lines.append("```")
    return "\n".join(lines) + "\n"


def write_report(report: dict, out_dir: Path) -> tuple[Path, Path]:
    """Write ``hostdiag-<host>-<YYYYmmddTHHMMSSZ>.{json,md}`` into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = report["collected_at"].replace("-", "").replace(":", "")
    base = out_dir / f"hostdiag-{report['host']}-{stamp}"
    j, m = base.with_suffix(".json"), base.with_suffix(".md")
    j.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    m.write_text(render_markdown(report), encoding="utf-8")
    return j, m


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=Path, default=Path("out"), help="directory for the JSON and Markdown report")
    ap.add_argument("--pid", type=int, help="optional PID whose NUMA placement/affinity to record")
    ap.add_argument("--note", default="", help="free-text context, e.g. job and symptom")
    args = ap.parse_args(argv)
    linux = sys.platform.startswith("linux")
    plan = build_command_plan(discover_interfaces() if linux else [], args.pid)
    files = {"pcie_sysfs": read_pcie_sysfs, "interrupts": read_interrupts, "cpufreq": read_cpufreq}
    report = collect(plan, file_sections=files, context={"pid": args.pid, "note": args.note})
    j, m = write_report(report, args.out_dir)
    bad = [n for n, s in report["sections"].items() if s["status"] != "ok"]
    print(f"wrote {j}\nwrote {m}\n{len(report['sections']) - len(bad)}/{len(report['sections'])} sections ok"
          + (f"; gaps: {', '.join(bad)}" if bad else ""))
    if not linux:
        print(f"note: platform {sys.platform} is not Linux; all sections were skipped by design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
