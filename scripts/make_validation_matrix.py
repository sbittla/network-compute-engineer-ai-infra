#!/usr/bin/env python3
"""Write docs/LAB_VALIDATION_MATRIX.md: what each lab was validated on, when, with which software, and the result.

Everything is read from committed evidence, nothing is typed by hand:

- L1 (laptop) labs: docs/TEST_RESULTS.md (written by scripts/make_expected_outputs.py from the package test suite);
- L2 (one GPU host) extensions: lab/l2/results/<bundle>/{environment,results}.json (capstones: starter-kit/l2/);
- single-machine hands-on labs: lab/handson/results/<run>/environment.json, re-checked with scripts/handson.py check;
- L3 (multi-node RDMA) extensions: no committed evidence exists; they are listed as not run.

    python scripts/make_validation_matrix.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "LAB_VALIDATION_MATRIX.md"
WAVE_B = {"07", "17", "18", "19", "20", "23"}  # docs/HANDS_ON_LABS.md: need Docker, not yet built


def packages() -> list[tuple[str, Path]]:
    out = [(p.name[2:4] and f"ch{p.name[2:4]}", p) for p in sorted(ROOT.glob("book/part-*/ch[0-9][0-9]-*"))]
    out += [("-".join(p.name.split("-")[:2]), p) for p in sorted((ROOT / "capstones").glob("capstone-*"))]
    return out


def l1_results() -> dict[str, tuple[str, str]]:
    text = (ROOT / "docs" / "TEST_RESULTS.md").read_text(encoding="utf-8")
    stamp = re.search(r"Generated (\d{4}-\d{2}-\d{2}) from commit `([^`]+)` with Python ([\d.]+)", text)
    res = {}
    for m in re.finditer(r"^\| (ch\d\d|capstone-[a-h]) \| (PASS|FAIL) \| (\d+) \| (\d+) \| (\d+) \|", text, re.M):
        res[m.group(1)] = (m.group(2), f"{m.group(3)} tests, {m.group(4)} failed, {m.group(5)} skipped")
    return res, (stamp.group(1), stamp.group(2), stamp.group(3)) if stamp else ("?", "?", "?")


def gpu_name(env: dict) -> str:
    gpus = env.get("gpus") or []
    if gpus and isinstance(gpus[0], dict) and gpus[0].get("name"):
        return gpus[0]["name"]
    g = env.get("gpu")
    if isinstance(g, dict):
        return g.get("name") or "GPU"
    return g or "no GPU"


def l2_rows(pid: str, root: Path) -> list[str]:
    l2 = root / ("starter-kit" if pid.startswith("capstone") else "lab") / "l2" / "results"
    rows = []
    for b in sorted(p for p in l2.glob("*") if (p / "results.json").is_file()):
        r = json.loads((b / "results.json").read_text(encoding="utf-8"))
        e = json.loads((b / "environment.json").read_text(encoding="utf-8")) if (b / "environment.json").is_file() else {}
        inv = r.get("invariants") or {}
        status = r.get("status", "?")
        if status != "ran":
            result = f"not run ({status})"
        elif inv.get("passed"):
            result = "PASS (invariants passed)"
        else:
            fails = "; ".join(inv.get("failures") or [])[:140]
            result = f"FAIL: {fails}" if fails else "FAIL"
        hw = "CPU fallback (" + (e.get("cpu_model") or "CPU") + ")" if e.get("device") == "cpu" else \
             f"{gpu_name(e)}, {e.get('cpu_model', '')}".strip(", ")
        drv = next((g.get("driver_version") for g in e.get("gpus") or [] if isinstance(g, dict)), None)
        sw = ", ".join(x for x in [f"Python {e['python']}" if e.get("python") else "",
                                   f"PyTorch {e['torch']}" if e.get("torch") else "",
                                   f"CUDA {e['cuda_runtime']}" if e.get("cuda_runtime") else "",
                                   f"driver {drv}" if drv else "", "WSL2" if e.get("wsl") else ""] if x)
        lim = "quick (smoke) sizes" if e.get("quick") else ""
        if e.get("device") == "cpu":
            lim = (lim + "; " if lim else "") + "no GPU: GPU-only invariants skipped"
        elif "Laptop" in gpu_name(e):
            lim = (lim + "; " if lim else "") + "laptop GPU on WSL2, not an H100-class host"
        rows.append(f"| {pid} | L2 `{b.name}` | {hw} | {sw} | {(e.get('run_utc') or '?')[:10]} | {result} | {lim or '—'} |")
    return rows


def handson_row(pid: str, root: Path) -> str | None:
    if pid.startswith("capstone"):
        return None
    hd = root / "lab" / "handson"
    if not hd.is_dir():
        if pid[2:] in WAVE_B:
            return f"| {pid} | Hands-on | — | — | — | not built yet (wave B needs Docker; docs/HANDS_ON_LABS.md) | — |"
        return None
    runs = sorted(p for p in (hd / "results").glob("*") if (p / "environment.json").is_file())
    if not runs:
        return f"| {pid} | Hands-on | — | — | — | no reference run committed | — |"
    run = runs[0]
    e = json.loads((run / "environment.json").read_text(encoding="utf-8"))
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "handson.py"), "check", pid, run.name], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"(\d+)/(\d+) checks passed(?:, (\d+) skipped)?", proc.stdout)
    m2 = re.search(r"(\d+) passed, (\d+) failed, (\d+) skipped", proc.stdout)
    if m and proc.returncode == 0:
        result = f"PASS ({m.group(1)}/{m.group(2)} checks" + (f", {m.group(3)} skipped" if m.group(3) else "") + ")"
    elif m2 and m2.group(2) == "0" and proc.returncode == 0:
        n = int(m2.group(1)) + int(m2.group(3))
        result = f"PASS ({m2.group(1)}/{n} checks" + (f", {m2.group(3)} skipped" if m2.group(3) != "0" else "") + ")"
    else:
        last = (proc.stdout.strip().splitlines() or ["no output"])[-1][:100]
        result = f"FAIL (rc {proc.returncode}: {last})"
    cpu = e.get("cpu") if isinstance(e.get("cpu"), str) else (e.get("cpu") or {}).get("model", "")
    hw = f"{gpu_name(e)}, {cpu}".strip(", ")
    g = e.get("gpu")
    drv = g.get("driver") if isinstance(g, dict) else None
    if not drv and isinstance(g, str) and g.count(",") >= 2:
        drv = g.split(",")[2].strip()
    sw = ", ".join(x for x in [f"kernel {e.get('kernel', '?')}", f"Python {e.get('python', '?')}",
                               f"driver {drv}" if drv else ""] if x)
    lim = "single machine; WSL2" if e.get("wsl") else "single machine"
    if pid == "ch09":
        lim += "; qdisc/bridge modules loaded with insmod (not persistent)"
    return f"| {pid} | Hands-on `{run.name}` | {hw} | {sw} | {(e.get('captured_at') or '?')[:10]} | {result} | {lim} |"


def main() -> int:
    l1, (l1_date, l1_commit, l1_py) = l1_results()
    rows = []
    for pid, root in packages():
        st, detail = l1.get(pid, ("?", "no result"))
        rows.append(f"| {pid} | L1 (laptop) | any x86-64/ARM laptop; tested on Windows 11 host | Python {l1_py}, "
                    f"pinned runtime (docker/requirements.lock) | {l1_date} | {st} ({detail}) | — |")
        rows += l2_rows(pid, root)
        h = handson_row(pid, root)
        if h:
            rows.append(h)
        readme = root / ("starter-kit" if pid.startswith("capstone") else "lab") / "README.md"
        if re.search(r"L3", readme.read_text(encoding="utf-8")):
            rows.append(f"| {pid} | L3 (multi-node RDMA) | — | — | — | not run: no multi-node RDMA fabric was available | "
                        "instructions only; results must come from the reader's own lab fabric |")
    def clean(row: str) -> str:
        cells = row.strip().strip("|").split(" | ")
        return "| " + " | ".join(c.replace("|", "/").strip() for c in cells) + " |"
    rows = [clean(r) for r in rows]
    today = dt.date.today().isoformat()
    OUT.write_bytes((
        "# Lab validation matrix\n\n"
        "What every lab tier was validated on, when, and with what result. Generated from committed evidence by "
        f"`scripts/make_validation_matrix.py` on {today}; nothing in this table is typed by hand.\n\n"
        "- **L1** results come from the package test suite ([TEST_RESULTS.md](TEST_RESULTS.md), commit "
        f"`{l1_commit}`): the reference solution passes every check, the starter fails gracefully, and every "
        "exercise's reference outputs regenerate.\n"
        "- **L2** bundles are `[MEASURED]` on the host named, and are valid only for that host. A laptop GPU is not "
        "an H100-class host: L2 results validate the *method* and its invariants, not ORION's numbers.\n"
        "- **Hands-on** reference runs are re-checked by `scripts/handson.py check` when this file is generated.\n"
        "- **L3** extensions have not been run by the author; they need a multi-node RDMA fabric. Treat their "
        "instructions as unvalidated until you run them on your own lab fabric.\n\n"
        "| Package | Tier / bundle | Hardware tested | Software | Date | Result | Known limitations |\n"
        "|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n").encode("utf-8"))
    n_fail = sum("| FAIL" in r for r in rows)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} rows, {n_fail} failing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
