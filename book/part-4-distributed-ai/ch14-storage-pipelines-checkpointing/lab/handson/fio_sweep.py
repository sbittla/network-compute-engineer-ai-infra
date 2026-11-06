#!/usr/bin/env python3
"""Chapter 14 hands-on lab, steps 1-3: fio read sweeps on the WSL ext4 disk, the 9P path and the page cache.

    sudo python3 fio_sweep.py --out results/<run-id> [--ext4-dir DIR] [--p9-dir DIR] [--size-gib 2] [--reps 5]

Writes one unedited fio JSON file per job to <out>/raw/fio/ and an index of the jobs to
<out>/raw/fio_jobs.json. Standard library only. Needs root (drop_caches) and fio on PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

QDS = (1, 4, 16, 32)
PATTERNS = {"randread-4k": ("randread", "4k"), "seqread-1m": ("read", "1M")}


def meminfo() -> dict[str, int]:
    out = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k, v = line.split(":", 1)
        out[k] = int(v.split()[0]) * 1024
    return out


def drop_caches() -> None:
    """Write dirty pages back, then drop the clean page cache (root). Affects the whole host's cache."""
    os.sync()
    Path("/proc/sys/vm/drop_caches").write_text("1\n")


def fs_type(path: Path) -> str:
    r = subprocess.run(["findmnt", "-no", "FSTYPE,SOURCE", "--target", str(path)], capture_output=True, text=True)
    return r.stdout.strip()


class Sweep:
    def __init__(self, out: Path, ramp: int, runtime: int):
        self.raw = out / "raw" / "fio"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.ramp, self.runtime = ramp, runtime
        self.jobs: list[dict] = []

    def run(self, name: str, filename: Path, rw: str, bs: str, qd: int, *, direct: bool, tag: dict,
            invalidate: bool = True, time_based: bool = True, size: str | None = None) -> dict:
        out = self.raw / f"{name}.json"
        cmd = ["fio", f"--name={name}", f"--filename={filename}", f"--rw={rw}", f"--bs={bs}",
               f"--iodepth={qd}", "--ioengine=libaio", f"--direct={int(direct)}",
               f"--invalidate={int(invalidate)}", "--readonly", "--numjobs=1", "--group_reporting",
               "--output-format=json", f"--output={out}"]
        if time_based:
            cmd += [f"--ramp_time={self.ramp}", f"--runtime={self.runtime}", "--time_based"]
        if size:
            cmd += [f"--size={size}"]
        cached_before = meminfo()["Cached"]
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=self.ramp + self.runtime + 300)
        rec = {"name": name, "file": str(filename), "rw": rw, "bs": bs, "qd": qd, "direct": direct,
               "invalidate": invalidate, "time_based": time_based, "cmd": " ".join(cmd),
               "rc": r.returncode, "stderr": r.stderr.strip()[-2000:], "wall_s": round(time.time() - t0, 2),
               "page_cache_before_bytes": cached_before, "page_cache_after_bytes": meminfo()["Cached"], **tag}
        self.jobs.append(rec)
        status = "ok" if r.returncode == 0 else f"rc={r.returncode} {r.stderr.strip()[:200]}"
        print(f"  {name:42s} {status}", flush=True)
        return rec


def layout(path: Path, size_gib: float, sweep: Sweep, name: str) -> dict:
    """Write the test file once with fio (sequential 1 MiB, O_DIRECT where allowed, fsync at the end)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = sweep.raw / f"{name}.json"
    size = f"{int(size_gib * 1024)}M"
    for direct in (1, 0):
        cmd = ["fio", f"--name={name}", f"--filename={path}", "--rw=write", "--bs=1M", "--iodepth=8",
               "--ioengine=libaio", f"--direct={direct}", f"--size={size}", "--end_fsync=1",
               "--output-format=json", f"--output={out}"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if r.returncode == 0:
            break
    rec = {"name": name, "file": str(path), "rw": "write", "bs": "1M", "qd": 8, "direct": bool(direct),
           "cmd": " ".join(cmd), "rc": r.returncode, "stderr": r.stderr.strip()[-2000:], "step": "layout"}
    sweep.jobs.append(rec)
    if r.returncode != 0:
        raise SystemExit(f"could not write test file {path}: {r.stderr.strip()[:300]}")
    print(f"  laid out {path} ({size}, direct={direct})", flush=True)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--ext4-dir", type=Path, default=Path(os.environ.get("CH14_EXT4_DIR", "/var/tmp/ch14-handson")))
    ap.add_argument("--p9-dir", type=Path, default=Path(os.environ.get("CH14_9P_DIR", "/mnt/c/Users/Public/ch14-handson")))
    ap.add_argument("--size-gib", type=float, default=1.0, help="ext4 test file size (must fit in free RAM for step 3)")
    ap.add_argument("--p9-size-gib", type=float, default=0.25)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--ramp", type=int, default=2)
    ap.add_argument("--runtime", type=int, default=6)
    a = ap.parse_args()
    if os.geteuid() != 0:
        sys.exit("needs root: drop_caches is written between runs")
    if not shutil.which("fio"):
        sys.exit("fio not found: run setup.sh")
    avail = meminfo()["MemAvailable"]
    if avail < (a.size_gib + 1.5) * 2**30:
        a.size_gib = max(0.5, round(avail / 2**30 - 1.5, 1))
        print(f"note: only {avail / 2**30:.1f} GiB available; test file shrunk to {a.size_gib} GiB", flush=True)

    sw = Sweep(a.out, a.ramp, a.runtime)
    f = a.ext4_dir / "fio-test.dat"
    meta = {"ext4_file": str(f), "ext4_fs": fs_type(a.ext4_dir.parent if not a.ext4_dir.exists() else a.ext4_dir),
            "size_gib": a.size_gib, "reps": a.reps, "ramp_s": a.ramp, "runtime_s": a.runtime,
            "mem_total_bytes": meminfo()["MemTotal"], "mem_available_bytes_at_start": avail,
            "fio_version": subprocess.run(["fio", "--version"], capture_output=True, text=True).stdout.strip()}

    print("Step 1: ext4 virtual disk, O_DIRECT (page cache bypassed)", flush=True)
    layout(f, a.size_gib, sw, "layout-ext4")
    meta["ext4_fs"] = fs_type(f)
    for rep in range(1, a.reps + 1):          # interleave repetitions so drift hits every cell equally
        for pat, (rw, bs) in PATTERNS.items():
            for qd in QDS:
                sw.run(f"ext4-direct-{pat}-qd{qd}-r{rep}", f, rw, bs, qd, direct=True,
                       tag={"step": "ext4_direct", "pattern": pat, "rep": rep})

    print("Step 3a: ext4, buffered, cold cache (drop_caches before every job)", flush=True)
    for pat, (rw, bs) in PATTERNS.items():
        for qd in QDS:
            drop_caches()
            seq = pat.startswith("seq")      # one pass for sequential, so no lap re-reads cached data
            sw.run(f"ext4-buffered-cold-{pat}-qd{qd}", f, rw, bs, qd, direct=False, invalidate=True,
                   time_based=not seq, size=None, tag={"step": "ext4_buffered_cold", "pattern": pat, "rep": 1})
    print("Step 3b: ext4, buffered, warm cache (file read once, cache kept)", flush=True)
    drop_caches()
    sw.run("ext4-buffered-warmup-read", f, "read", "1M", 16, direct=False, invalidate=False, time_based=False,
           tag={"step": "warmup", "pattern": "seqread-1m", "rep": 1})
    for pat, (rw, bs) in PATTERNS.items():
        for qd in QDS:
            sw.run(f"ext4-buffered-warm-{pat}-qd{qd}", f, rw, bs, qd, direct=False, invalidate=False,
                   tag={"step": "ext4_buffered_warm", "pattern": pat, "rep": 1})
    f.unlink(missing_ok=True)
    drop_caches()

    print("Step 2: the 9P path (/mnt/<drive>, a Windows directory served to the VM over 9P)", flush=True)
    p9_ok = a.p9_dir.parent.is_dir() and fs_type(a.p9_dir.parent).startswith("9p")
    meta["p9_dir"], meta["p9_fs"] = str(a.p9_dir), fs_type(a.p9_dir.parent) if a.p9_dir.parent.is_dir() else "absent"
    if not p9_ok:
        print(f"  skipped: {a.p9_dir.parent} is not a 9P mount (not WSL, or the drive is absent)", flush=True)
        meta["p9_skipped"] = True
    else:
        g = a.p9_dir / "fio-test.dat"
        try:
            layout(g, a.p9_size_gib, sw, "layout-9p")
            meta["p9_layout_direct"] = sw.jobs[-1]["direct"]
            for pat, (rw, bs) in PATTERNS.items():
                for qd in (1, 32):
                    for direct in (True, False):
                        mode = "direct" if direct else "buffered"
                        sw.run(f"9p-{mode}-{pat}-qd{qd}", g, rw, bs, qd, direct=direct,
                               tag={"step": f"p9_{mode}", "pattern": pat, "rep": 1})
        finally:
            g.unlink(missing_ok=True)
        meta["p9_skipped"] = False

    (a.out / "raw" / "fio_jobs.json").write_text(json.dumps({"meta": meta, "jobs": sw.jobs}, indent=1))
    bad = [j["name"] for j in sw.jobs if j["rc"] != 0]
    print(f"fio sweep done: {len(sw.jobs)} jobs, {len(bad)} failed {bad[:6]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
