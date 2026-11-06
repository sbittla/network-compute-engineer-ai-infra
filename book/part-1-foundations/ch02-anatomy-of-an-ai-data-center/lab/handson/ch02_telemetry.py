"""GPU telemetry at ~100 ms with nvidia-smi, plus helpers to cut it into measured windows.

Used by the Chapter 2 hands-on lab. Standard library only (the sampler is nvidia-smi itself):

    tel = Telemetry(out_dir / "ch02_telemetry.csv")
    tel.start()          # nvidia-smi --query-gpu=... -lms 100 -f <csv>
    t0 = time.time(); ...work...; t1 = time.time()
    tel.stop()
    rows = tel.read()
    window(rows, t0, t1)                  # samples inside [t0, t1]
    energy_j(rows, t0, t1)                # integral of power over [t0, t1] (trapezoid)

Fields that the driver does not report on this platform (WSL2 reports several as [N/A]) are probed once
with probe_fields() and left out of the sampler; the probe result is saved as evidence.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import subprocess
import time
from pathlib import Path

# Everything the chapter asks about. Order matters only for the CSV header.
WANTED = [
    "timestamp",
    "power.draw.instant", "power.draw.average", "power.draw", "enforced.power.limit",
    "power.default_limit", "power.min_limit", "power.max_limit", "power.limit",
    "clocks.sm", "clocks.gr", "clocks.mem", "clocks.max.sm", "clocks.max.mem",
    "temperature.gpu", "temperature.memory", "fan.speed", "pstate",
    "utilization.gpu", "utilization.memory", "memory.used",
    "clocks_event_reasons.active",
    "clocks_event_reasons.sw_power_cap", "clocks_event_reasons.sw_thermal_slowdown",
    "clocks_event_reasons.hw_slowdown", "clocks_event_reasons.hw_thermal_slowdown",
    "clocks_event_reasons.hw_power_brake_slowdown", "clocks_event_reasons.sync_boost",
    "clocks_event_reasons_counters.sw_power_cap", "clocks_event_reasons_counters.sw_thermal_slowdown",
    "clocks_event_reasons_counters.hw_thermal_slowdown",
    "clocks_event_reasons_counters.hw_power_brake_slowdown",
]
# What the ~100 ms sampler records. Each extra field slows nvidia-smi down (on WSL2 the achieved period
# stretches from ~100 ms towards ~250 ms with many fields), so slow-moving or cumulative fields (limits,
# violation counters) are read with snapshot() at segment boundaries instead.
SAMPLE = [
    "timestamp", "power.draw.instant", "power.draw.average", "clocks.sm", "clocks.mem",
    "temperature.gpu", "utilization.gpu", "pstate", "clocks_event_reasons.active",
]
SNAPSHOT = [
    "timestamp", "enforced.power.limit", "clocks_event_reasons_counters.sw_power_cap",
    "clocks_event_reasons_counters.sw_thermal_slowdown", "clocks_event_reasons_counters.hw_thermal_slowdown",
    "clocks_event_reasons_counters.hw_power_brake_slowdown",
]
# nvidia-smi writes canonical names in the CSV header; map them back to the names we asked for.
ALIAS = {
    "clocks.current.sm": "clocks.sm", "clocks.current.graphics": "clocks.gr",
    "clocks.current.memory": "clocks.mem", "clocks.max.memory": "clocks.max.mem",
    "clocks.max.graphics": "clocks.max.gr", "gpu.power.draw.instant": "power.draw.instant",
}
# Bits of clocks_event_reasons.active (nvml.h nvmlClocksEventReason*).
REASON_BITS = {
    0x1: "gpu_idle", 0x2: "applications_clocks_setting", 0x4: "sw_power_cap", 0x8: "hw_slowdown",
    0x10: "sync_boost", 0x20: "sw_thermal_slowdown", 0x40: "hw_thermal_slowdown",
    0x80: "hw_power_brake_slowdown", 0x100: "display_clock_setting",
}
UNAVAILABLE = ("[N/A]", "N/A", "[Not Supported]", "Not Supported", "[Unknown Error]")


def probe_fields(fields: list[str] = WANTED) -> dict[str, str]:
    """Query each field once; return {field: value or 'UNAVAILABLE: <why>'}."""
    out: dict[str, str] = {}
    for f in fields:
        r = subprocess.run(["nvidia-smi", f"--query-gpu={f}", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=30)
        v = (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else ""
        bad = r.returncode != 0 or v in UNAVAILABLE or "deprecated" in v.lower() or "not a valid" in v.lower()
        out[f] = f"UNAVAILABLE: {v}" if bad else v
    return out


class Telemetry:
    def __init__(self, path: Path, period_ms: int = 100, fields: list[str] | None = None):
        self.path = Path(path)
        self.period_ms = period_ms
        if fields is None:
            avail = probe_fields()
            fields = [f for f in SAMPLE if not avail.get(f, "UNAVAILABLE").startswith("UNAVAILABLE")]
            self.availability = avail
        else:
            self.availability = {}
        self.fields = fields
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        # -f puts the output path (which carries the chapter prefix) on nvidia-smi's command line, so
        # teardown.sh can find a sampler that outlived its parent.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.proc = subprocess.Popen(
            ["nvidia-smi", f"--query-gpu={','.join(self.fields)}", "--format=csv,nounits",
             "-lms", str(self.period_ms), "-f", str(self.path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)  # let the first samples arrive

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            time.sleep(0.5)
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None

    def read(self) -> list[dict]:
        return read_csv(self.path)


def _num(v: str):
    v = v.strip()
    if v.startswith("0x"):
        return int(v, 16)
    try:
        return float(v)
    except ValueError:
        return v


def read_csv(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="") as fh:
        rd = csv.reader(fh)
        header = [h.split(" [")[0].strip() for h in next(rd)]
        header = [ALIAS.get(h, h) for h in header]
        for rec in rd:
            if len(rec) != len(header):
                continue  # a partial last line when the sampler was stopped
            row = {h: _num(v) for h, v in zip(header, rec)}
            try:
                row["t"] = dt.datetime.strptime(str(row["timestamp"]).strip(), "%Y/%m/%d %H:%M:%S.%f").timestamp()
            except ValueError:
                continue
            rows.append(row)
    return rows


def snapshot(fields: list[str] = SNAPSHOT) -> dict:
    """One reading of slow-moving and cumulative fields (limits, clock-event violation counters in us)."""
    r = subprocess.run(["nvidia-smi", f"--query-gpu={','.join(fields)}", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True, timeout=30)
    vals = [v.strip() for v in r.stdout.strip().split(",")]
    if r.returncode != 0 or len(vals) != len(fields):
        return {"error": (r.stdout + r.stderr).strip()}
    return {f: _num(v) for f, v in zip(fields, vals)}


def window(rows: list[dict], t0: float, t1: float) -> list[dict]:
    return [r for r in rows if t0 <= r["t"] <= t1]


def power_key(rows: list[dict]) -> str:
    for k in ("power.draw.instant", "power.draw"):
        if rows and isinstance(rows[0].get(k), float):
            return k
    raise KeyError("no numeric power field in telemetry")


def energy_j(rows: list[dict], t0: float, t1: float, key: str | None = None) -> float:
    """Integral of power over [t0, t1] by the trapezoid rule, with the samples just outside the window
    used to interpolate the edges."""
    key = key or power_key(rows)
    pts = [(r["t"], r[key]) for r in rows if isinstance(r.get(key), float)]
    if len(pts) < 2:
        return float("nan")

    def p_at(t: float) -> float:
        for (ta, pa), (tb, pb) in zip(pts, pts[1:]):
            if ta <= t <= tb:
                return pa + (pb - pa) * (t - ta) / (tb - ta) if tb > ta else pa
        return pts[0][1] if t < pts[0][0] else pts[-1][1]

    inner = [(t, p) for t, p in pts if t0 < t < t1]
    seq = [(t0, p_at(t0))] + inner + [(t1, p_at(t1))]
    return sum((tb - ta) * (pa + pb) / 2 for (ta, pa), (tb, pb) in zip(seq, seq[1:]))


def stats(vals: list[float]) -> dict:
    vals = sorted(v for v in vals if isinstance(v, (int, float)))
    if not vals:
        return {"n": 0}
    n = len(vals)
    q = lambda p: vals[min(n - 1, max(0, round(p * (n - 1))))]  # noqa: E731
    return {"n": n, "mean": sum(vals) / n, "p05": q(0.05), "median": q(0.5), "p95": q(0.95),
            "min": vals[0], "max": vals[-1]}


def reasons(mask) -> list[str]:
    if not isinstance(mask, int):
        return []
    return [name for bit, name in REASON_BITS.items() if mask & bit]


def save_json(obj, path: Path) -> None:
    Path(path).write_text(json.dumps(obj, indent=2, default=str) + "\n")
