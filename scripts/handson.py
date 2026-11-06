#!/usr/bin/env python3
"""Drive the single-machine hands-on labs (docs/HANDS_ON_LABS.md).

    python scripts/handson.py list
    python scripts/handson.py setup ch09
    python scripts/handson.py run ch09 [run-id]     # unattended run; writes lab/handson/results/<run-id>/
    python scripts/handson.py check ch09 [run-id]   # default: the committed reference run
    python scripts/handson.py teardown ch09

On Windows the lab runs inside WSL (distribution from $HANDSON_WSL_DISTRO, default Ubuntu-24.04).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_RUN = "wsl2-rtx4060-laptop"
DISTRO = os.environ.get("HANDSON_WSL_DISTRO", "Ubuntu-24.04")


def labs() -> dict[str, Path]:
    out = {}
    for d in sorted(ROOT.glob("book/*/ch*/lab/handson")):
        out[d.parent.parent.name[:4]] = d
    return out


def wsl_path(p: Path) -> str:
    s = str(p.resolve())
    return f"/mnt/{s[0].lower()}{s[2:].replace(chr(92), '/')}" if os.name == "nt" else s


def sh(lab: Path, script: str, *args: str) -> int:
    cmd = f"cd {wsl_path(lab)!r} && bash {script} {' '.join(args)}"
    full = ["wsl.exe", "-d", DISTRO, "--", "bash", "-lc", cmd] if os.name == "nt" else ["bash", "-lc", cmd]
    return subprocess.call(full)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["list", "setup", "run", "check", "teardown"])
    ap.add_argument("chapter", nargs="?")
    ap.add_argument("run_id", nargs="?")
    a = ap.parse_args()
    found = labs()
    if a.action == "list":
        for ch, d in found.items():
            ref = (d / "results" / REFERENCE_RUN).is_dir()
            print(f"{ch}  {d.relative_to(ROOT).as_posix()}  reference run: {'yes' if ref else 'no'}")
        return 0
    if a.chapter not in found:
        print(f"no hands-on lab for {a.chapter!r}; have: {', '.join(found)}")
        return 2
    lab = found[a.chapter]
    if a.action == "check":
        run = lab / "results" / (a.run_id or REFERENCE_RUN)
        return subprocess.call([sys.executable, str(lab / "check.py"), str(run)])
    script = {"setup": "setup.sh", "run": "run.sh", "teardown": "teardown.sh"}[a.action]
    return sh(lab, script, *([a.run_id] if a.run_id else []))


if __name__ == "__main__":
    sys.exit(main())
