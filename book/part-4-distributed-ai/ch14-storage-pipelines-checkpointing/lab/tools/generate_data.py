#!/usr/bin/env python3
"""Generate the Chapter 14 lab datasets (deterministic, seeded).

Outputs (under ``lab/data/`` by default):

* ``io_trace.csv``               -- per-operation data-loader trace from one HX8 client node
* ``fio_nvme_acceptance.json``   -- fio-format (JSON subset) acceptance run on 8 local NVMe drives
* ``checkpoints/``               -- a small checkpoint store with manifests, shards, commit markers

All values are SIMULATED for teaching; they are not measurements of any product. Regenerating
with the same seed produces byte-identical files.

Usage:
    python tools/generate_data.py [--out DIR] [--seed 14]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

SEED = 14
MiB = 1024 * 1024
KiB = 1024

# --------------------------------------------------------------------------------------------
# Part B: data-loader I/O trace
# --------------------------------------------------------------------------------------------
N_WORKERS = 8
N_TARGETS = 8          # storage targets (OST/NSD-like) the PFS stripes files over
SLOW_TARGET = 5        # planted: one storage target with degraded latency
SMALL_END_S = 6.0      # phase 1: small-file (metadata-bound) epoch
GAP_END_S = 7.0        # phase 2: idle gap (epoch boundary / shuffle)
SHARD_END_S = 19.0     # phase 3: sharded sequential reads (bandwidth-bound)
INTERF_START_S, INTERF_END_S = 13.0, 17.0   # planted: checkpoint write burst on shared PFS


def _lat_open(rng: np.random.Generator) -> float:
    """Metadata open latency in microseconds (lognormal, median 5 ms: busy metadata service)."""
    return float(rng.lognormal(np.log(5000.0), 0.5))


def _lat_read(rng: np.random.Generator, nbytes: int, target: int, t_s: float) -> float:
    """Read latency in microseconds: fixed cost + transfer at a per-stream rate, plus plants."""
    per_stream_Bps = 1.4e9
    base = 400.0 + nbytes / per_stream_Bps * 1e6
    lat = base * float(rng.lognormal(0.0, 0.15))
    if target == SLOW_TARGET:
        lat *= 4.0                                   # planted slow target
    if INTERF_START_S <= t_s < INTERF_END_S and nbytes >= MiB:
        lat *= 2.5 * float(rng.lognormal(0.0, 0.35))   # planted write-burst interference
    return lat


def generate_trace(rng: np.random.Generator) -> list[tuple]:
    rows: list[tuple] = []
    for w in range(N_WORKERS):
        # ---- phase 1: one file per sample: open -> read -> close
        t = float(rng.uniform(0, 0.005))
        while t < SMALL_END_S:
            target = int(rng.integers(0, N_TARGETS))
            lat = _lat_open(rng)
            rows.append((t, w, "open", target, 0, lat))
            t += lat / 1e6
            nbytes = int(rng.integers(64, 257)) * KiB
            lat = _lat_read(rng, nbytes, target, t)
            rows.append((t, w, "read", target, nbytes, lat))
            t += lat / 1e6
            lat = float(rng.lognormal(np.log(200.0), 0.3))
            rows.append((t, w, "close", target, 0, lat))
            t += lat / 1e6
        # ---- phase 2: idle gap until GAP_END_S
        t = GAP_END_S + float(rng.uniform(0, 0.005))
        # ---- phase 3: 256 MiB shards read as 16 x 16 MiB sequential reads
        while t < SHARD_END_S:
            target0 = int(rng.integers(0, N_TARGETS))
            lat = _lat_open(rng)
            rows.append((t, w, "open", target0, 0, lat))
            t += lat / 1e6
            for i in range(16):
                target = (target0 + i) % N_TARGETS          # 16 MiB stripe unit, round-robin
                lat = _lat_read(rng, 16 * MiB, target, t)
                rows.append((t, w, "read", target, 16 * MiB, lat))
                t += lat / 1e6
                if t >= SHARD_END_S:
                    break
            lat = float(rng.lognormal(np.log(200.0), 0.3))
            rows.append((t, w, "close", target0, 0, lat))
            t += lat / 1e6
    rows = [r for r in rows if r[0] < SHARD_END_S]
    rows.sort(key=lambda r: (r[0], r[1]))
    return rows


def write_trace(path: Path, rows: list[tuple]) -> None:
    with path.open("w", newline="\n", encoding="utf-8") as f:
        f.write("t_s,worker,op,target,bytes,lat_us\n")
        for t, w, op, target, nbytes, lat in rows:
            f.write(f"{t:.6f},{w},{op},{target},{nbytes},{lat:.1f}\n")


# --------------------------------------------------------------------------------------------
# Part B: fio acceptance results (fio JSON output, subset of fields)
# --------------------------------------------------------------------------------------------
def _pct(p50: float, p99: float, p999: float, p9999: float) -> dict:
    return {"50.000000": int(p50), "99.000000": int(p99), "99.900000": int(p999),
            "99.990000": int(p9999)}


def generate_fio(rng: np.random.Generator) -> dict:
    jobs = []
    for d in range(8):
        dev = f"/dev/nvme{d}n1"
        # 4 KiB random read, iodepth 32, single job
        mean_ns = 78_000 * float(rng.normal(1.0, 0.02))
        p999 = 260_000 * float(rng.normal(1.0, 0.05))
        p9999 = 410_000 * float(rng.normal(1.0, 0.05))
        if d == 5:                                     # planted: tail-latency outlier
            mean_ns *= 1.12
            p999, p9999 = 9_100_000.0, 31_000_000.0
        iops = 32 / (mean_ns / 1e9)
        jobs.append({
            "jobname": f"randread-4k-qd32-nvme{d}",
            "job options": {"name": f"randread-4k-qd32-nvme{d}", "filename": dev, "rw": "randread",
                            "bs": "4k", "iodepth": "32", "direct": "1", "runtime": "60"},
            "read": {"io_bytes": int(iops * 4096 * 60), "bw_bytes": int(iops * 4096),
                     "iops": round(iops, 3), "runtime": 60000,
                     "clat_ns": {"mean": round(mean_ns, 3),
                                 "percentile": _pct(mean_ns * 0.93, mean_ns * 2.1, p999, p9999)}},
            "write": {"io_bytes": 0, "bw_bytes": 0, "iops": 0.0, "runtime": 0,
                      "clat_ns": {"mean": 0.0, "percentile": {}}},
        })
        # 1 MiB sequential write, iodepth 8
        bw = 3.45e9 * float(rng.normal(1.0, 0.015))
        if d == 2:                                     # planted: bandwidth-degraded drive
            bw = 1.62e9
        iops_w = bw / MiB
        mean_w = 8 / iops_w * 1e9
        jobs.append({
            "jobname": f"seqwrite-1m-qd8-nvme{d}",
            "job options": {"name": f"seqwrite-1m-qd8-nvme{d}", "filename": dev, "rw": "write",
                            "bs": "1M", "iodepth": "8", "direct": "1", "runtime": "60"},
            "read": {"io_bytes": 0, "bw_bytes": 0, "iops": 0.0, "runtime": 0,
                     "clat_ns": {"mean": 0.0, "percentile": {}}},
            "write": {"io_bytes": int(bw * 60), "bw_bytes": int(bw), "iops": round(iops_w, 3),
                      "runtime": 60000,
                      "clat_ns": {"mean": round(mean_w, 3),
                                  "percentile": _pct(mean_w * 0.98, mean_w * 1.6, mean_w * 2.4,
                                                     mean_w * 3.5)}},
        })
    return {"fio version": "fio-3.x (synthetic)", "timestamp": 0,
            "global options": {"ioengine": "libaio", "direct": "1", "time_based": "1"},
            "jobs": jobs}


# --------------------------------------------------------------------------------------------
# Part C: checkpoint store
# --------------------------------------------------------------------------------------------
WORLD = 8
SHARD_BYTES = 8 * KiB
STEPS = [900, 1200, 1500, 1800, 2100, 2400, 2700]
# Planted defects (documented only in solutions/lab/README.md):
#   1200: shard_05 truncated (size mismatch)    1500: shard_03 silent corruption (checksum)
#   2100: shard_06 missing but COMMIT written   2400: manifest rewritten after commit
#   2700: no COMMIT (async persist in flight at crash); `latest` points here


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def generate_checkpoints(root: Path, rng: np.random.Generator) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for step in STEPS:
        d = root / f"step_{step:06d}"
        d.mkdir(exist_ok=True)
        shards = []
        payloads = {}
        for r in range(WORLD):
            data = rng.integers(0, 256, SHARD_BYTES, dtype=np.uint8).tobytes()
            name = f"shard_{r:02d}.bin"
            payloads[name] = data
            shards.append({"rank": r, "file": name, "bytes": len(data), "sha256": _sha256(data)})
        manifest = {"format": "halcyon-ckpt-v1", "step": step, "world_size": WORLD,
                    "parallelism": {"tp": 8, "pp": 4, "dp": 8, "note": "scaled-down shards"},
                    "shards": shards}
        mbytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        commit = _sha256(mbytes)

        if step == 1200:
            payloads["shard_05.bin"] = payloads["shard_05.bin"][: SHARD_BYTES // 2]
        if step == 1500:
            b = bytearray(payloads["shard_03.bin"])
            b[4096] ^= 0x01                                        # single bit flip
            payloads["shard_03.bin"] = bytes(b)
        if step == 2100:
            del payloads["shard_06.bin"]
        if step == 2400:
            manifest["step"] = 2401                                # edited after commit
            mbytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()

        for name, data in payloads.items():
            (d / name).write_bytes(data)
        (d / "manifest.json").write_bytes(mbytes)
        if step != 2700:
            (d / "COMMIT").write_bytes(commit.encode())
    (root / "latest").write_bytes(b"step_002700")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    write_trace(args.out / "io_trace.csv", generate_trace(np.random.default_rng(args.seed)))
    fio = generate_fio(np.random.default_rng(args.seed + 1))
    (args.out / "fio_nvme_acceptance.json").write_text(json.dumps(fio, indent=2) + "\n",
                                                        encoding="utf-8", newline="\n")
    generate_checkpoints(args.out / "checkpoints", np.random.default_rng(args.seed + 2))
    (args.out / ".gitattributes").write_text("* -text\n", encoding="utf-8", newline="\n")
    print(f"wrote datasets to {args.out}")


if __name__ == "__main__":
    main()
