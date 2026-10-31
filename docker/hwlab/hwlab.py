"""hwlab: shared runtime for the L2 (single real GPU host) lab extensions.

Every chapter that has an L2 extension provides ``lab/l2/experiment.py`` with

    EXPERIMENT = {"id": "ch13-l2", "title": "...", "evidence": "MEASURED",
                  "cpu_fallback": "what the CPU run measures instead"}
    def run(ctx: Context) -> dict        # {"metrics": {...}, "tables": {...}, "notes": [...]}
    def check(result: dict, env: dict) -> list[str]   # physical invariants; [] = pass
    def report(result: dict, env: dict) -> str        # optional Markdown body

``ctx.device`` is "cuda" when a GPU is visible and "cpu" otherwise (or when forced), so the same
experiment always runs: on a GPU it measures the GPU; without one it runs the documented CPU fallback.
Benchmark discipline follows docs/LAB_STANDARDS.md section 5 (warm-up, >= 5 repetitions, median,
p95 and spread, environment manifest).
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

try:  # torch is present in the GPU image; experiments that need it import it from ctx
    import torch
except ImportError:  # pragma: no cover - the L1 image has no torch
    torch = None

NVSMI_FIELDS = [
    "name", "driver_version", "memory.total", "pci.bus_id", "pcie.link.gen.max", "pcie.link.gen.current",
    "pcie.link.width.max", "pcie.link.width.current", "clocks.max.sm", "clocks.max.memory",
    "power.limit", "power.max_limit", "temperature.gpu", "compute_cap",
]


def _run(cmd: list[str], timeout: int = 20) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def nvidia_smi_query(fields: list[str]) -> list[dict]:
    """Rows of ``nvidia-smi --query-gpu`` (one per GPU); [] when nvidia-smi is absent."""
    if not shutil.which("nvidia-smi"):
        return []
    out = _run(["nvidia-smi", f"--query-gpu={','.join(fields)}", "--format=csv,noheader,nounits"])
    rows = []
    for line in out.splitlines():
        vals = [v.strip() for v in line.split(",")]
        if len(vals) == len(fields):
            rows.append(dict(zip(fields, vals)))
    return rows


def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def mem_total_gib() -> float | None:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 1024 ** 2, 1)
    except OSError:
        pass
    return None


def environment(device: str) -> dict:
    """Environment manifest recorded with every run (what LAB_STANDARDS section 3 asks learners to fill)."""
    env = {
        "device": device,
        "python": platform.python_version(),
        "os": platform.platform(),
        "kernel": platform.release(),
        "wsl": "microsoft" in platform.release().lower(),
        "cpu_model": cpu_model(),
        "cpu_count": os.cpu_count(),
        "mem_total_gib": mem_total_gib(),
        "torch": getattr(torch, "__version__", None),
        "cuda_runtime": getattr(getattr(torch, "version", None), "cuda", None),
        "cudnn": (torch.backends.cudnn.version() if torch is not None and torch.backends.cudnn.is_available() else None),
        "gpus": nvidia_smi_query(NVSMI_FIELDS) if device == "cuda" else [],
    }
    if device == "cuda" and torch is not None:
        p = torch.cuda.get_device_properties(0)
        env["gpu0"] = {"name": p.name, "sm_count": p.multi_processor_count, "capability": f"{p.major}.{p.minor}",
                       "total_memory_gib": round(p.total_memory / 1024 ** 3, 2)}
    return env


def label_for(env: dict) -> str:
    """Results folder name: ``gpu-<model>`` or ``cpu-fallback``."""
    if env["device"] != "cuda":
        return "cpu-fallback"
    name = env.get("gpu0", {}).get("name") or (env["gpus"][0]["name"] if env["gpus"] else "unknown")
    return "gpu-" + re.sub(r"[^a-z0-9]+", "-", name.lower().replace("nvidia", "").replace("geforce", "")).strip("-")


def summarize(samples: list[float]) -> dict:
    s = sorted(samples)
    q = statistics.quantiles(s, n=4) if len(s) >= 4 else [s[0], statistics.median(s), s[-1]]
    p95 = s[min(len(s) - 1, round(0.95 * (len(s) - 1)))]
    return {"n": len(s), "median": statistics.median(s), "p95": p95, "min": s[0], "max": s[-1],
            "iqr": q[2] - q[0], "mean": statistics.fmean(s)}


@dataclass
class Context:
    device: str
    quick: bool
    log_lines: list[str] = field(default_factory=list)

    @property
    def torch(self):
        if torch is None:
            raise RuntimeError("this experiment needs PyTorch (run it in the ai-infra-gpu image)")
        return torch

    @property
    def is_gpu(self) -> bool:
        return self.device == "cuda"

    def sync(self) -> None:
        if self.is_gpu:
            torch.cuda.synchronize()

    def log(self, msg: str) -> None:
        self.log_lines.append(msg)
        print(msg, flush=True)

    def reps(self, full: int = 10) -> int:
        """Repetitions: >= 5 always (LAB_STANDARDS section 5)."""
        return 5 if self.quick else max(5, full)

    def bench(self, fn, *, warmup: int = 3, reps: int | None = None) -> dict:
        """Time ``fn()`` (seconds) with device synchronisation; returns summarize() stats."""
        reps = reps or self.reps()
        for _ in range(warmup):
            fn()
        self.sync()
        samples = []
        for _ in range(reps):
            if self.is_gpu:
                start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                start.record()
                fn()
                end.record()
                torch.cuda.synchronize()
                samples.append(start.elapsed_time(end) / 1000.0)
            else:
                t0 = time.perf_counter()
                fn()
                samples.append(time.perf_counter() - t0)
        return summarize(samples)


def not_runnable(reason: str, *, needs: list[str], fallback: str) -> dict:
    """Result for an extension whose hardware is absent: recorded honestly, never faked."""
    return {"status": "not-runnable", "reason": reason, "needs": needs, "fallback": fallback,
            "metrics": {}, "tables": {}, "notes": []}


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
