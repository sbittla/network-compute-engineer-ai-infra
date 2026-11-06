#!/usr/bin/env python3
"""Step 5a: can this process lock (pin) N MiB of memory? mlock(2) is what makes pages unmovable; the
limit is RLIMIT_MEMLOCK (`ulimit -l`) unless the process has CAP_IPC_LOCK (root does).

    python3 mlock_probe.py <mib>      # prints one JSON line
"""
import ctypes
import json
import mmap
import os
import resource
import sys

libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.mlock.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
libc.munlock.argtypes = [ctypes.c_void_p, ctypes.c_size_t]


def vm_lck_kib() -> int:
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmLck:"):
                return int(line.split()[1])
    return -1


mib = int(sys.argv[1])
size = mib << 20
buf = mmap.mmap(-1, size)
addr = ctypes.addressof(ctypes.c_char.from_buffer(buf))
soft, hard = resource.getrlimit(resource.RLIMIT_MEMLOCK)
before = vm_lck_kib()
rc = libc.mlock(addr, size)
err = ctypes.get_errno() if rc != 0 else 0
during = vm_lck_kib()
if rc == 0:
    libc.munlock(addr, size)
print(json.dumps({
    "uid": os.getuid(), "request_mib": mib,
    "rlimit_memlock_soft_kib": None if soft == resource.RLIM_INFINITY else soft // 1024,
    "rlimit_memlock_hard_kib": None if hard == resource.RLIM_INFINITY else hard // 1024,
    "mlock_ok": rc == 0, "errno": err, "error": os.strerror(err) if err else "",
    "vmlck_kib_before": before, "vmlck_kib_while_locked": during,
}))
