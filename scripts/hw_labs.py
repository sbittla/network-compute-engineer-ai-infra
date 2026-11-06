#!/usr/bin/env python3
"""Run the L2 (single real GPU host) lab extensions in the GPU image, with automatic CPU fallback.

Packages with an L2 extension provide lab/l2/experiment.py (capstones: starter-kit/l2/).

    python scripts/hw_labs.py list
    python scripts/hw_labs.py build [ids...] [--cpu-image]   # ai-infra-gpu:<id> images (CUDA, or CPU-only for CI)
    python scripts/hw_labs.py run   [ids...] [--device gpu|cpu|auto] [--quick]
                                                             # writes lab/l2/results/<gpu-model|cpu-fallback>/
    python scripts/hw_labs.py test  [ids...] [--device ...]  # quick run now + committed-evidence checks
    python scripts/hw_labs.py evidence [ids...]              # GPU run then CPU-fallback run (full mode), serially
    python scripts/hw_labs.py summary                        # regenerate docs/HARDWARE_RUNS.md from the bundles

GPU runs are always serial: concurrent benchmarks on one GPU would corrupt each other's numbers.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = "docker/gpu.Dockerfile"


def packages() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for d in sorted(ROOT.glob("book/part-*/ch[0-9][0-9]-*")):
        if (d / "lab" / "l2" / "experiment.py").is_file():
            found[d.name[:4]] = d
    for d in sorted(ROOT.glob("capstones/capstone-*")):
        if (d / "starter-kit" / "l2" / "experiment.py").is_file():
            found[d.name[:len("capstone-a")]] = d
    return found


def select(ids: list[str]) -> dict[str, Path]:
    pk = packages()
    if not ids:
        return pk
    bad = [i for i in ids if i not in pk]
    if bad:
        sys.exit(f"no L2 extension for {bad}; see `list`")
    return {i: pk[i] for i in ids}


def l2_dir(path: Path) -> Path:
    return path / ("starter-kit" if (path / "starter-kit").is_dir() else "lab") / "l2"


def sh(cmd: list[str], timeout: int = 7200) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def gpu_flags(device: str) -> list[str]:
    """--gpus all for gpu; for auto only when the host has an NVIDIA driver (else run the CPU fallback)."""
    if device == "gpu" or (device == "auto" and shutil.which("nvidia-smi")):
        return ["--gpus", "all"]
    return []


CPU_IMAGE_ARGS = ["--build-arg", "BASE=python:3.11.11-slim-bookworm", "--build-arg", "TORCH_CPU=1"]


def build(pid: str, path: Path, cpu_image: bool = False) -> int:
    rc, out = sh(["docker", "build", "-q", "-f", DOCKERFILE, "--build-arg", f"PKG={path.relative_to(ROOT).as_posix()}",
                  *(CPU_IMAGE_ARGS if cpu_image else []), "-t", f"ai-infra-gpu:{pid}", "."])
    print(f"{'OK  ' if rc == 0 else 'FAIL'} build {pid}", flush=True)
    if rc:
        print(out[-3000:])
    return rc


def run(pid: str, path: Path, device: str, quick: bool) -> int:
    out_dir = l2_dir(path) / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dir.chmod(0o777)
    dev = {"gpu": "cuda", "cpu": "cpu", "auto": "auto"}[device]
    cmd = ["docker", "run", "--rm", "--network", "none", "--shm-size", "2g", "--ulimit", "memlock=-1:-1", *gpu_flags(device),
           "-v", f"{out_dir}:/results", f"ai-infra-gpu:{pid}",
           "python", "/opt/hwlab/run.py", "--pkg", "/work/pkg", "--out", "/results", "--device", dev]
    if quick:
        cmd.append("--quick")
    t0 = time.perf_counter()
    rc, out = sh(cmd)
    print(f"{'OK  ' if rc == 0 else 'FAIL'} run   {pid:11} device={device:4} {time.perf_counter() - t0:7.1f}s", flush=True)
    print("\n".join("     | " + line for line in out.strip().splitlines()[-12:]), flush=True)
    return rc


def test(pid: str, path: Path, device: str) -> int:
    cmd = ["docker", "run", "--rm", "--network", "none", "--shm-size", "2g", "--ulimit", "memlock=-1:-1", *gpu_flags(device), f"ai-infra-gpu:{pid}",
           "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--rootdir", "/opt/hwlab",
           "/opt/hwlab/test_l2.py", "--pkg", "/work/pkg"]
    rc, out = sh(cmd)
    print(f"{'OK  ' if rc == 0 else 'FAIL'} test  {pid:11} {out.strip().splitlines()[-1] if out.strip() else ''}", flush=True)
    if rc:
        print("\n".join("     | " + line for line in out.strip().splitlines()[-30:]))
    return rc


def _bundle(l2: Path, name: str) -> tuple[dict, dict] | None:
    folder = l2 / "results" / name
    if not (folder / "results.json").is_file():
        return None
    return (json.loads((folder / "results.json").read_text(encoding="utf-8")),
            json.loads((folder / "environment.json").read_text(encoding="utf-8")))


def _cell(text: str, limit: int = 150) -> str:
    text = " ".join(str(text).split()).replace("|", "/")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def summary(pk: dict[str, Path]) -> int:
    """Write docs/HARDWARE_RUNS.md: L2 evidence per package, plus every L3 extension and what it needs."""
    rows, gpu_env = [], None
    for pid, path in packages().items():
        l2 = l2_dir(path)
        gpu_dirs = sorted(p.name for p in (l2 / "results").glob("gpu-*") if not p.name.endswith("-quick")) \
            if (l2 / "results").is_dir() else []
        gpu = _bundle(l2, gpu_dirs[0]) if gpu_dirs else None
        cpu = _bundle(l2, "cpu-fallback")
        gpu_env = gpu_env or (gpu[1] if gpu else None)
        meta = (gpu or cpu or ({},))[0].get("experiment", {})
        parts = [p.get("part", "") for p in (gpu or cpu or ({},))[0].get("not_runnable_parts", [])]

        def state(b):
            if not b:
                return "missing"
            r = b[0]
            return f"{r['status']}, invariants {'pass' if r['invariants']['passed'] else 'FAIL'}"
        rel = (l2 / "results").relative_to(ROOT).as_posix()
        rows.append(f"| {pid} | {_cell(meta.get('title', ''), 90)} | {state(gpu)} | {state(cpu)} | "
                    f"{_cell('; '.join(parts) or '—')} | [{rel}](../{rel}/) |")

    l3 = []
    for d in sorted(ROOT.glob("book/part-*/ch[0-9][0-9]-*/lab/manifest.yaml")) + sorted(ROOT.glob("capstones/*/starter-kit/manifest.yaml")):
        import yaml  # host-side only; the manifests are YAML
        m = yaml.safe_load(d.read_text(encoding="utf-8")) or {}
        rel = d.relative_to(ROOT).parts
        pid = rel[2][:4] if rel[0] == "book" else rel[1][:10]
        for e in m.get("extensions") or []:
            if str(e.get("tier")) == "L3":
                l3.append(f"| {pid} | {_cell(e.get('requires', ''), 220)} |")

    g = (gpu_env or {}).get("gpu0", {})
    gpus = (gpu_env or {}).get("gpus") or [{}]
    lines = [
        "# Hardware runs (L2 and L3 extensions)", "",
        "Generated by `python scripts/hw_labs.py summary` from the committed evidence bundles. Do not edit by hand.", "",
        "## Reference L2 host", "",
        f"- GPU: **{g.get('name', 'n/a')}**, {g.get('total_memory_gib', '?')} GiB, {g.get('sm_count', '?')} SMs, "
        f"compute capability {g.get('capability', '?')}; PCIe Gen{gpus[0].get('pcie.link.gen.max', '?')} "
        f"x{gpus[0].get('pcie.link.width.max', '?')}; driver {gpus[0].get('driver_version', '?')}",
        f"- Host: {(gpu_env or {}).get('cpu_model', '?')}; {(gpu_env or {}).get('os', '?')}",
        f"- Runtime: PyTorch {(gpu_env or {}).get('torch', '?')}, CUDA {(gpu_env or {}).get('cuda_runtime', '?')}, in Docker "
        "with the NVIDIA container runtime (`docker/gpu.Dockerfile`)",
        "- This is a power-capped **laptop** GPU, not an H100-class data-center GPU. Its numbers validate the methods "
        "and the L1 models' structure. They are not ORION figures: re-run on your own hardware.", "",
        "## L2 evidence per package", "",
        "Every package ran twice in full mode, serially, on an otherwise idle GPU: once on the GPU and once as the "
        "automatic CPU fallback (`--device cpu`). CI re-runs every CPU fallback on each push.", "",
        "| Package | Experiment | GPU run | CPU fallback | Not runnable on one GPU host | Evidence |",
        "|---|---|---|---|---|---|", *rows, "",
        "## L3 extensions (multi-node RDMA): not run", "",
        "L3 needs two or more GPU nodes joined by an RDMA fabric (RoCEv2 or InfiniBand) with switch access. "
        "A single host cannot provide that, so none of these has been executed. Each is still runnable at L1 "
        "on the lab's synthetic data, which CI tests on every push.", "",
        "| Package | Requires |", "|---|---|", *l3, "",
    ]
    out = ROOT / "docs" / "HARDWARE_RUNS.md"
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(ROOT)}: {len(rows)} L2 packages, {len(l3)} L3 extensions")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["list", "build", "run", "test", "evidence", "summary"])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--device", choices=["gpu", "cpu", "auto"], default="auto")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--cpu-image", action="store_true",
                    help="build: small CPU-only torch image (CI without a GPU) instead of the CUDA base")
    a = ap.parse_args()
    pk = select(a.ids)
    if a.command == "list":
        for pid, path in pk.items():
            print(f"{pid:11} {l2_dir(path).relative_to(ROOT).as_posix()}")
        return 0
    if a.command == "build":
        return 1 if sum([bool(build(p, d, a.cpu_image)) for p, d in pk.items()]) else 0
    if a.command == "run":
        return 1 if sum([bool(run(p, d, a.device, a.quick)) for p, d in pk.items()]) else 0
    if a.command == "test":
        return 1 if sum([bool(test(p, d, a.device)) for p, d in pk.items()]) else 0
    if a.command == "summary":
        return summary(pk)
    failed = 0
    for pid, path in pk.items():
        res = l2_dir(path) / "results"
        for stale in res.glob("*-quick") if res.is_dir() else []:
            shutil.rmtree(stale)
        failed += bool(run(pid, path, "gpu", False)) + bool(run(pid, path, "cpu", False))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
