"""L2 extension tests, run inside the package's GPU image (with or without a GPU).

    python -m pytest /opt/hwlab/test_l2.py --pkg /work/pkg

1. The experiment runs now, on whatever device is visible (GPU, or the CPU fallback), in quick mode,
   and every physical invariant in its check() holds.
2. The committed evidence bundles (lab/l2/results/*/) are complete, passed their invariants, and
   include a CPU-fallback run plus, unless the extension is not runnable on one GPU, a GPU run.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REQUIRED_FILES = ("environment.json", "results.json", "report.md")


@pytest.fixture(scope="session")
def pkg(pytestconfig) -> Path:
    return Path(pytestconfig.getoption("--pkg"))


@pytest.fixture(scope="session")
def l2(pkg: Path) -> Path:
    return pkg / ("starter-kit" if (pkg / "starter-kit").is_dir() else "lab") / "l2"


def test_experiment_runs_now(pkg: Path, tmp_path: Path) -> None:
    proc = subprocess.run([sys.executable, "/opt/hwlab/run.py", "--pkg", str(pkg), "--out", str(tmp_path), "--quick"],
                          capture_output=True, text=True, timeout=1800)
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-4000:]
    bundles = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(bundles) == 1
    for name in REQUIRED_FILES:
        assert (bundles[0] / name).is_file(), name


def committed_bundles(l2: Path) -> list[Path]:
    res = l2 / "results"
    return sorted(p for p in res.iterdir() if p.is_dir() and not p.name.endswith("-quick")) if res.is_dir() else []


def test_committed_evidence(l2: Path) -> None:
    bundles = committed_bundles(l2)
    assert bundles, "no committed evidence under lab/l2/results/ (run: python scripts/hw_labs.py run <id>)"
    names = [b.name for b in bundles]
    assert "cpu-fallback" in names, "a CPU-fallback run must be committed"
    for b in bundles:
        for name in REQUIRED_FILES:
            assert (b / name).is_file(), f"{b.name}/{name} missing"
        result = json.loads((b / "results.json").read_text(encoding="utf-8"))
        assert result["status"] in ("ran", "not-runnable"), f"{b.name}: status {result['status']}"
        assert result["invariants"]["passed"], f"{b.name}: {result['invariants']['failures']}"
        env = json.loads((b / "environment.json").read_text(encoding="utf-8"))
        assert env["device"] == ("cpu" if b.name == "cpu-fallback" else "cuda")
        assert env.get("quick") is False, f"{b.name}: committed evidence must be a full (non-quick) run"
    gpu = [b for b in bundles if b.name.startswith("gpu-")]
    cpu_result = json.loads((l2 / "results" / "cpu-fallback" / "results.json").read_text(encoding="utf-8"))
    if not gpu:
        assert cpu_result["status"] == "not-runnable" or cpu_result["experiment"].get("gpu_optional"), \
            "a GPU run must be committed for an extension that can run on one GPU"
