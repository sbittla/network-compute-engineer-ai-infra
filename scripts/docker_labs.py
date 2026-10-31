#!/usr/bin/env python3
"""Build, test and regenerate outputs for every lab package in its own Docker container.

Each package (24 chapters + 8 capstones) gets its own image, ``ai-infra-lab:<id>``, built from
docker/lab.Dockerfile with only that package inside. Tests run with no network access.

    python scripts/docker_labs.py list
    python scripts/docker_labs.py build   [ids...]   # build images (instructor + learner targets)
    python scripts/docker_labs.py test    [ids...]   # run each package's test suite in its container
    python scripts/docker_labs.py outputs [ids...]   # regenerate committed outputs (bind-mounts the package)
    python scripts/docker_labs.py ci                  # full build of every image, then the full test run

ids are like ch09, capstone-d; omit for all. Results: build/test-results/<id>/junit.xml + summary.md.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = "docker/lab.Dockerfile"
RESULTS = ROOT / "build" / "test-results"
RUN_LIMITS = ["--network", "none", "--memory", "2g", "--cpus", "2"]


def packages() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for d in sorted(ROOT.glob("book/part-*/ch[0-9][0-9]-*")):
        found[d.name[:4]] = d
    for d in sorted(ROOT.glob("capstones/capstone-*")):
        found[d.name[:len("capstone-a")]] = d
    return found


def select(ids: list[str]) -> dict[str, Path]:
    pk = packages()
    if not ids:
        return pk
    unknown = [i for i in ids if i not in pk]
    if unknown:
        sys.exit(f"unknown package id(s): {unknown}; see `list`")
    return {i: pk[i] for i in ids}


def sh(cmd: list[str], timeout: int = 1800) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build_one(pid: str, path: Path) -> tuple[str, int, str, float]:
    t0 = time.perf_counter()
    log = ""
    for target, tag in (("instructor", f"ai-infra-lab:{pid}"), ("learner", f"ai-infra-lab:{pid}-learner")):
        rc, out = sh(["docker", "build", "-q", "-f", DOCKERFILE, "--target", target,
                      "--build-arg", f"PKG={rel(path)}", "-t", tag, "."])
        log += out
        if rc != 0:
            return pid, rc, log, time.perf_counter() - t0
    return pid, 0, log, time.perf_counter() - t0


def test_one(pid: str, path: Path) -> tuple[str, int, str, float]:
    t0 = time.perf_counter()
    out_dir = RESULTS / pid
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    rc, out = sh(["docker", "run", "--rm", *RUN_LIMITS, "-v", f"{out_dir}:/results",
                  f"ai-infra-lab:{pid}"])
    (out_dir / "pytest.log").write_text(out, encoding="utf-8")
    return pid, rc, out, time.perf_counter() - t0


def outputs_one(pid: str, path: Path) -> tuple[str, int, str, float]:
    t0 = time.perf_counter()
    rc, out = sh(["docker", "run", "--rm", *RUN_LIMITS, "-v", f"{path}:/work/pkg",
                  f"ai-infra-lab:{pid}", "python", "/opt/harness/generate_outputs.py", "/work/pkg"])
    return pid, rc, out, time.perf_counter() - t0


def junit_counts(pid: str) -> tuple[int, int, int, int]:
    f = RESULTS / pid / "junit.xml"
    if not f.is_file():
        return 0, 0, 0, 0
    root = ET.parse(f).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    a = suite.attrib
    return int(a["tests"]), int(a["failures"]) + int(a["errors"]), int(a["skipped"]), 0


def run_all(fn, pk: dict[str, Path], jobs: int, verb: str) -> list[tuple[str, int, str, float]]:
    results = []
    with cf.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(fn, pid, path): pid for pid, path in pk.items()}
        for fut in cf.as_completed(futures):
            pid, rc, out, secs = fut.result()
            results.append((pid, rc, out, secs))
            print(f"{'OK  ' if rc == 0 else 'FAIL'} {verb:7} {pid:11} {secs:6.1f}s", flush=True)
            if rc != 0:
                print("\n".join("     | " + line for line in out.strip().splitlines()[-25:]), flush=True)
    return sorted(results)


def summarize(results: list[tuple[str, int, str, float]]) -> int:
    lines = ["# Lab container test results", "",
             "| Package | Result | Tests | Failed | Skipped | Time (s) |", "|---|---|---|---|---|---|"]
    failed = 0
    for pid, rc, _out, secs in results:
        tests, bad, skipped, _ = junit_counts(pid)
        failed += rc != 0
        lines.append(f"| {pid} | {'PASS' if rc == 0 else 'FAIL'} | {tests} | {bad} | {skipped} | {secs:.1f} |")
    total = sum(junit_counts(p)[0] for p, *_ in results)
    lines += ["", f"**{len(results) - failed}/{len(results)} packages passed, {total} tests.**"]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-1:]))
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["list", "build", "test", "outputs", "ci"])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("-j", "--jobs", type=int, default=3, help="parallel containers (default 3)")
    args = ap.parse_args()
    pk = select(args.ids)

    if args.command == "list":
        for pid, path in pk.items():
            print(f"{pid:11} {rel(path)}")
        return 0
    if args.command in ("build", "ci"):
        built = run_all(build_one, pk, max(args.jobs, 4), "build")
        if any(rc for _, rc, *_ in built):
            print("build failed; tests not run")
            return 1
        print(f"built {len(built)} packages ({2 * len(built)} images)")
        if args.command == "build":
            return 0
    if args.command == "outputs":
        res = run_all(outputs_one, pk, args.jobs, "outputs")
        return 1 if any(rc for _, rc, *_ in res) else 0
    return summarize(run_all(test_one, pk, args.jobs, "test"))


if __name__ == "__main__":
    sys.exit(main())
