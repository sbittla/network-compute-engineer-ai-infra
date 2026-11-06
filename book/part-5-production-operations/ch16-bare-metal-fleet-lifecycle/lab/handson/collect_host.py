#!/usr/bin/env python3
"""Chapter 16 hands-on lab: collect the non-GPU-stress evidence for an acceptance record.

    sudo python3 collect_host.py --out results/<run-id> [--fio-reps 3]

Inventory and GPU discovery (nvidia-smi, idle), kernel-log scan, host memory capacity and a pattern
test, NICs and RDMA devices, data disks, and a read-only fio sequential read per data disk (one
warm-up plus --fio-reps timed runs). Every command's output is saved unedited under <out>/raw/;
the parsed values go to <out>/raw/host.json. Standard library only. Read-only on every device.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

RAW: Path


def sh(name: str, cmd: list[str] | str, timeout: int = 60) -> tuple[int, str]:
    """Run a command, save stdout+stderr to raw/<name>.txt, return (rc, output)."""
    try:
        r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout)
        out, rc = r.stdout + (("\n[stderr]\n" + r.stderr) if r.stderr.strip() else ""), r.returncode
    except FileNotFoundError as e:
        out, rc = f"[not found] {e}", 127
    except subprocess.TimeoutExpired:
        out, rc = f"[timeout after {timeout} s]", 124
    (RAW / f"{name}.txt").write_text(f"$ {cmd if isinstance(cmd, str) else ' '.join(cmd)}\n[rc={rc}]\n{out}")
    return rc, out


def read(p: str) -> str | None:
    try:
        return Path(p).read_text().strip()
    except OSError:
        return None


def gpu_inventory() -> dict:
    q = ("index,uuid,pci.bus_id,name,memory.total,vbios_version,driver_version,pcie.link.gen.current,"
         "pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,ecc.mode.current,temperature.gpu,power.limit")
    rc, out = sh("nvidia-smi-inventory-idle", ["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"])
    gpus = []
    for line in out.splitlines():
        if line.startswith("$") or line.startswith("[") or not line.strip():
            continue
        f = [x.strip() for x in line.split(",")]
        if len(f) != 14:
            continue
        num = lambda v: int(v) if v.isdigit() else None  # noqa: E731
        gpus.append({"index": int(f[0]), "uuid": f[1], "bdf": f[2], "product": f[3], "memory_total_mib": num(f[4]),
                     "vbios": f[5], "driver": f[6], "pcie_idle": {"gen": num(f[7]), "width": num(f[9])},
                     "pcie_max": {"gen": num(f[8]), "width": num(f[10])}, "ecc_mode": f[11],
                     "temp_idle_c": num(f[12]), "power_limit": f[13]})
    sh("nvidia-smi-L", ["nvidia-smi", "-L"])
    _, ecc = sh("nvidia-smi-q-ecc-rowremap", ["nvidia-smi", "-q", "-d", "ECC,ROW_REMAPPER"])
    rr = {}
    # Parse only the "Remapped Rows" section: "Pending" also appears under "ECC Mode" (the pending ECC mode).
    remap = ecc.split("Remapped Rows", 1)[1] if "Remapped Rows" in ecc else ""
    for key, field in (("Correctable Error", "correctable"), ("Uncorrectable Error", "uncorrectable"),
                       ("Pending", "pending"), ("Remapping Failure Occurred", "failure")):
        for line in remap.splitlines():
            if line.strip().startswith(key) and ":" in line:
                rr[field] = line.split(":", 1)[1].strip()
                break
    ecc_vals = [line.split(":", 1)[1].strip() for line in ecc.splitlines() if "DRAM Uncorrectable" in line]
    _, nvl = sh("nvidia-smi-nvlink-status", ["nvidia-smi", "nvlink", "--status"])
    sh("nvidia-smi-q-full", ["nvidia-smi", "-q"])
    sh("nvidia-smi-topo", ["nvidia-smi", "topo", "-m"])
    return {"gpus": gpus, "row_remap": rr, "ecc_dram_uncorrectable_fields": ecc_vals,
            "nvlink_supported": "does not have or support" not in nvl and "Link" in nvl,
            "nvlink_status_text": nvl.strip().splitlines()[-1] if nvl.strip() else ""}


def kernel_log() -> dict:
    rc, out = sh("dmesg", ["dmesg", "-T"], timeout=30)
    xid = [line for line in out.splitlines() if "xid" in line.lower() and "nvrm" in line.lower()]
    _, mods = sh("lsmod", ["lsmod"])
    nvidia_mod = any(line.split()[0] == "nvidia" for line in mods.splitlines()[3:] if line.split())
    return {"dmesg_rc": rc, "dmesg_lines": len(out.splitlines()), "xid_lines": xid,
            "nvidia_kernel_module_loaded": nvidia_mod, "dxg_device": os.path.exists("/dev/dxg"),
            "dcgmi_on_path": shutil.which("dcgmi") is not None, "nv_hostengine_on_path": shutil.which("nv-hostengine") is not None}


def host_memory(test_bytes_max: int) -> dict:
    mi = {k: int(v.split()[0]) * 1024 for k, v in (l.split(":", 1) for l in Path("/proc/meminfo").read_text().splitlines())}
    sh("meminfo", ["cat", "/proc/meminfo"])
    sh("lscpu", ["lscpu"])
    n = min(test_bytes_max, int(mi["MemAvailable"] * 0.2)) // 2**20 * 2**20
    chunk = 2**20
    buf = bytearray(n)
    mv = memoryview(buf)
    bad, t_w = 0, 0.0
    pats = [b"\x00", b"\xff", b"\x55", b"\xaa"]
    for p in pats:
        block = p * chunk
        t0 = time.perf_counter()
        for i in range(0, n, chunk):
            mv[i:i + chunk] = block
        t_w += time.perf_counter() - t0
        bad += sum(mv[i:i + chunk] != block for i in range(0, n, chunk))
    # address-in-address per 1 MiB chunk: each chunk holds its own offset, catches aliasing between chunks
    for i in range(0, n, chunk):
        mv[i:i + chunk] = i.to_bytes(8, "little") * (chunk // 8)
    bad += sum(mv[i:i + chunk] != i.to_bytes(8, "little") * (chunk // 8) for i in range(0, n, chunk))
    del mv, buf
    return {"mem_total_bytes": mi["MemTotal"], "mem_available_bytes": mi["MemAvailable"],
            "swap_total_bytes": mi["SwapTotal"], "swap_used_bytes": mi["SwapTotal"] - mi["SwapFree"],
            "hw_corrupted_bytes": mi.get("HardwareCorrupted", 0), "edac_present": os.path.isdir("/sys/devices/system/edac/mc"),
            "pattern_test": {"bytes": n, "patterns": len(pats) + 1, "bad_chunks": bad, "fill_GBps": len(pats) * n / t_w / 1e9}}


def nics() -> dict:
    out = []
    for d in sorted(Path("/sys/class/net").iterdir()):
        name = d.name
        if name == "lo":
            continue
        drv = os.path.basename(os.path.realpath(d / "device" / "driver")) if (d / "device" / "driver").exists() else None
        speed = read(str(d / "speed"))
        out.append({"name": name, "has_device": (d / "device").exists(), "driver": drv,
                    "operstate": read(str(d / "operstate")), "carrier": read(str(d / "carrier")),
                    "speed_mbps": int(speed) if speed and speed.lstrip("-").isdigit() else None,
                    "mtu": int(read(str(d / "mtu")) or 0)})
        if (d / "device").exists():
            sh(f"ethtool-{name}", ["ethtool", name])
            sh(f"ethtool-i-{name}", ["ethtool", "-i", name])
    ib = sorted(p.name for p in Path("/sys/class/infiniband").iterdir()) if Path("/sys/class/infiniband").is_dir() else []
    rdma = []
    for dev in ib:
        node_type = read(f"/sys/class/infiniband/{dev}/node_type")
        drv = os.path.basename(os.path.realpath(f"/sys/class/infiniband/{dev}/device/driver")) \
            if Path(f"/sys/class/infiniband/{dev}/device/driver").exists() else None
        rdma.append({"name": dev, "node_type": node_type, "driver": drv,
                     "software": dev.startswith(("rxe", "siw")) or "rxe" in dev or drv is None})
    sh("ip-link", ["ip", "-d", "link", "show"])
    sh("rdma-link", ["rdma", "link", "show"])
    return {"netdevs": out, "rdma_devices": rdma}


def data_disks() -> list[str]:
    """Block devices (TYPE disk) that hold a mounted, non-swap file system of this OS."""
    rc, out = sh("lsblk", ["lsblk", "-J", "-b", "-o", "NAME,KNAME,PKNAME,TYPE,SIZE,ROTA,MODEL,FSTYPE,MOUNTPOINTS"])
    js = json.loads(out.split("\n[stderr]")[0]) if rc == 0 else {"blockdevices": []}
    disks = []
    for dev in js["blockdevices"]:
        if dev["type"] != "disk":
            continue
        parts = [dev] + dev.get("children", [])
        mounted = any(m for p in parts for m in (p.get("mountpoints") or []) if m and m != "[SWAP]")
        if mounted and dev.get("fstype") != "swap":
            disks.append(dev["name"])
    return disks


def fio_disk(dev: str, reps: int) -> dict:
    runs = []
    for i in range(reps + 1):        # run 0 is the warm-up
        out = RAW / f"fio-{dev}-r{i}.json"
        cmd = ["fio", f"--name=ch16-{dev}", f"--filename=/dev/{dev}", "--readonly", "--rw=read", "--bs=1M",
               "--iodepth=32", "--ioengine=libaio", "--direct=1", "--ramp_time=2", "--runtime=8", "--time_based",
               "--output-format=json", f"--output={out}"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        rec = {"rep": i, "warmup": i == 0, "rc": r.returncode, "cmd": " ".join(cmd), "stderr": r.stderr.strip()[-500:]}
        if r.returncode == 0:
            j = json.loads(out.read_text())["jobs"][0]["read"]
            rec.update(bw_GBps=j["bw_bytes"] / 1e9, iops=j["iops"], clat_p999_us=j["clat_ns"]["percentile"].get("99.900000", 0) / 1e3)
        runs.append(rec)
        print(f"  fio /dev/{dev} rep {i}: {rec.get('bw_GBps', 'rc=' + str(r.returncode))}", flush=True)
    return {"device": dev, "model": read(f"/sys/block/{dev}/device/model"), "rotational": read(f"/sys/block/{dev}/queue/rotational"),
            "is_nvme": dev.startswith("nvme"), "runs": runs}


def main() -> int:
    global RAW
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fio-reps", type=int, default=3)
    ap.add_argument("--mem-test-mib", type=int, default=512)
    a = ap.parse_args()
    RAW = a.out / "raw"
    RAW.mkdir(parents=True, exist_ok=True)
    if os.geteuid() != 0:
        raise SystemExit("needs root (dmesg, raw block devices)")
    host: dict = {"collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "hostname": os.uname().nodename,
                  "kernel": os.uname().release}
    print("inventory + GPU discovery (idle)", flush=True)
    host["gpu"] = gpu_inventory()
    print("kernel log", flush=True)
    host["kernel_log"] = kernel_log()
    print("host memory", flush=True)
    host["memory"] = host_memory(a.mem_test_mib * 2**20)
    print("NICs", flush=True)
    host["nics"] = nics()
    print("storage", flush=True)
    sh("nvme-list", ["nvme", "list"])
    disks = data_disks()
    host["storage"] = {"nvme_devices": sorted(p.name for p in Path("/sys/class/nvme").iterdir()) if Path("/sys/class/nvme").is_dir() else [],
                       "data_disks": [fio_disk(d, a.fio_reps) for d in disks],
                       "smart_tool": shutil.which("nvme") or shutil.which("smartctl")}
    (RAW / "host.json").write_text(json.dumps(host, indent=1))
    print("host collection done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
