#!/usr/bin/env python3
"""Step 4: the page cache's effect on reads. Writes a test file, evicts only that file from the page
cache with posix_fadvise(DONTNEED) (unlike drop_caches, the rest of the cache is untouched), then times a
cold read, a warm read and an O_DIRECT read, recording page-cache residency (mincore) and /proc/meminfo
"Cached" after each step.

    python3 pagecache.py /var/tmp/ch03-pagecache.bin 1024 > pagecache.json
"""
from __future__ import annotations

import ctypes
import json
import mmap
import os
import sys
import time

BLOCK = 8 << 20
PAGE = os.sysconf("SC_PAGE_SIZE")
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
libc.mmap.restype = ctypes.c_void_p
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]


def meminfo_kib(key: str) -> int:
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith(key + ":"):
                return int(line.split()[1])
    return -1


def resident_fraction(path: str) -> float:
    """Fraction of the file's pages that are in the page cache, from mincore(2) on a read-only mapping.
    Mapping the file does not read it, so measuring does not change the answer."""
    size = os.path.getsize(path)
    npages = (size + PAGE - 1) // PAGE
    fd = os.open(path, os.O_RDONLY)
    try:
        addr = libc.mmap(None, size, mmap.PROT_READ, mmap.MAP_SHARED, fd, 0)
        if addr in (None, ctypes.c_void_p(-1).value):
            raise OSError(ctypes.get_errno(), "mmap failed")
        try:
            vec = (ctypes.c_ubyte * npages)()
            if libc.mincore(addr, size, vec) != 0:
                raise OSError(ctypes.get_errno(), "mincore failed")
            return sum(v & 1 for v in vec) / npages
        finally:
            libc.munmap(addr, size)
    finally:
        os.close(fd)


def timed_read(path: str, direct: bool = False) -> dict:
    fd = os.open(path, os.O_RDONLY | (os.O_DIRECT if direct else 0))
    buf = mmap.mmap(-1, BLOCK)          # anonymous, page-aligned: what O_DIRECT requires
    total = 0
    t0 = time.perf_counter()
    try:
        while (n := os.readv(fd, [buf])) > 0:
            total += n
    finally:
        os.close(fd)
        buf.close()
    dt = time.perf_counter() - t0
    return {"bytes": total, "seconds": round(dt, 4), "gb_per_s": round(total / dt / 1e9, 3)}


def main() -> int:
    path, mib = sys.argv[1], int(sys.argv[2])
    out: dict = {"file": path, "size_mib": mib, "block_bytes": BLOCK, "steps": []}

    def step(name: str, **extra) -> None:
        out["steps"].append({"step": name, "resident_fraction": round(resident_fraction(path), 4),
                             "meminfo_cached_kib": meminfo_kib("Cached"), **extra})

    chunk = os.urandom(1 << 20)
    t0 = time.perf_counter()
    with open(path, "wb") as f:
        for _ in range(mib):
            f.write(chunk)
        f.flush()
        os.fsync(f.fileno())
    step("after_write_fsync", write_seconds=round(time.perf_counter() - t0, 3))
    fd = os.open(path, os.O_RDONLY)
    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    os.close(fd)
    step("after_fadvise_dontneed")
    cold = timed_read(path)
    step("after_cold_read", read=cold)
    warm = timed_read(path)
    step("after_warm_read", read=warm)
    direct = timed_read(path, direct=True)
    step("after_odirect_read", read=direct)
    out.update(cold_gb_per_s=cold["gb_per_s"], warm_gb_per_s=warm["gb_per_s"], odirect_gb_per_s=direct["gb_per_s"],
               warm_over_cold=round(warm["gb_per_s"] / cold["gb_per_s"], 2))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
