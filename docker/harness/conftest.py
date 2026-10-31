from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from common import Package  # noqa: E402


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--pkg", default="/work/pkg", help="package root inside the container")


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "exercise" in metafunc.fixturenames:
        pkg = Package(Path(metafunc.config.getoption("--pkg")))
        exercises = pkg.exercises()
        metafunc.parametrize("exercise", exercises, ids=[e.name for e in exercises])
