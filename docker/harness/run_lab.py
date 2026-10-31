"""Learner entry point: run this package's lab checker (default: your starter/ code).

    docker run --rm -it --network none -v "$PWD/lab/starter:/work/pkg/lab/starter" ai-infra-lab:ch09-learner
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

root = Path("/work/pkg")
lab = root / ("starter-kit" if (root / "starter-kit").is_dir() else "lab")
sys.exit(subprocess.call([sys.executable, "check.py", *sys.argv[1:]], cwd=lab))
