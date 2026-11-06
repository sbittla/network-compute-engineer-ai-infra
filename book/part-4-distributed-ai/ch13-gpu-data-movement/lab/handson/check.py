#!/usr/bin/env python3
"""Check a Chapter 13 hands-on results bundle for completeness and physical sense.

    python check.py results/<run-id>

Prints one PASS/FAIL line per check and exits 0 only if every check passes. Standard library only. It
tests mechanisms (pinned copies release the CPU; overlap hides copy time; more workers feed a starved GPU),
not this machine's numbers.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

REQUIRED = ["environment.json", "summary.json", "report.md", "step1-copies/copies.json",
            "step2-overlap/overlap.json", "step3-dataloader/loader.json", "step3-dataloader/gpu-before.csv"]


class Checker:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def run(self, name: str, fn) -> None:
        try:
            self.rows.append(("PASS", name, fn() or ""))
        except AssertionError as exc:
            self.rows.append(("FAIL", name, str(exc) or "assertion failed"))
        except Exception as exc:  # a malformed bundle must give a useful line, not a traceback
            tb = traceback.extract_tb(exc.__traceback__)[-1]
            self.rows.append(("FAIL", name, f"{type(exc).__name__}: {exc} (check.py:{tb.lineno})"))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    d = Path(sys.argv[1])
    C = Checker()
    sm: dict = {}

    def files():
        missing = [f for f in REQUIRED if not (d / f).is_file() or (d / f).stat().st_size == 0]
        assert not missing, f"missing or empty: {', '.join(missing)}"
        return f"{len(REQUIRED)} files present"
    C.run("bundle complete", files)

    def load():
        nonlocal sm
        sm = json.loads((d / "summary.json").read_text(encoding="utf-8"))
        for k in ("step1", "step2", "step3"):
            assert k in sm, f"summary.json lacks {k} (rerun summarize.py)"
        assert sm["environment"].get("gpu"), "environment.json records no GPU"
        assert (d / "report.md").read_text(encoding="utf-8").count("[MEASURED]") >= 8, "report.md labels too few numbers [MEASURED]"
        return sm["environment"]["gpu"]
    C.run("summary, environment and report", load)

    def s1():
        rows = sm["step1"]["rows"]
        assert len(rows) >= 3, "expected at least three buffer sizes"
        big = max(rows, key=lambda r: r["mib"])
        assert big["pinned_gb_per_s"] >= big["pageable_gb_per_s"], "pinned H2D should not be slower than pageable"
        assert big["pinned_cpu_blocked_ms"] < 0.2 * big["pageable_cpu_blocked_ms"], \
            "a non_blocking copy from pinned memory should release the CPU much sooner than one from pageable memory"
        assert big["pin_every_batch_gb_per_s"] < big["pinned_gb_per_s"], "pinning per batch cannot be faster than reusing a pinned buffer"
        assert 0.3 < big["pinned_gb_per_s"] < 130, f"implausible pinned rate {big['pinned_gb_per_s']} GB/s"
        return (f"{big['mib']} MiB: pinned {big['pinned_gb_per_s']} vs pageable {big['pageable_gb_per_s']} GB/s; "
                f"CPU held {big['pinned_cpu_blocked_ms']} vs {big['pageable_cpu_blocked_ms']} ms; pin call {big['pin_memory_call_ms']} ms")
    C.run("Step 1 pinned vs pageable", s1)

    def s2():
        x = sm["step2"]
        se, op = x["serial"], x["overlap_pinned"]
        assert se["copy_hidden_fraction"] <= 0.05, f"the serial schedule shows {se['copy_hidden_fraction']:.0%} overlap: timestamps are wrong"
        assert op["copy_hidden_fraction"] >= 0.5, f"only {op['copy_hidden_fraction']:.0%} of copy time overlapped compute on two streams"
        assert op["wall_ms"] < se["wall_ms"] * 0.9, "the overlapped schedule is not faster than the serial one"
        assert op["wall_ms"] >= 0.95 * x["ideal_overlap_wall_ms"], "overlapped wall time below max(copy, compute): impossible"
        tot = se["sum_copy_ms"] + se["sum_compute_ms"]
        assert 0.9 * tot <= se["wall_ms"] <= 1.3 * tot, f"serial wall {se['wall_ms']} ms is not ≈ copy + compute {tot:.1f} ms"
        return f"serial {se['wall_ms']} ms -> overlapped {op['wall_ms']} ms; {op['copy_hidden_fraction']:.0%} of copy hidden"
    C.run("Step 2 overlap proven by timestamps", s2)

    def s3():
        x = sm["step3"]
        cfg = x["configs"]
        assert len(cfg) >= 8, "the DataLoader sweep has fewer than 8 configurations"
        ceiling = x["gpu_only"]["samples_per_s"]
        assert all(c["samples_per_s"] <= 1.1 * ceiling for c in cfg), "a configuration beat the GPU-only ceiling"
        w0, best = x["workers0"], x["best"]
        assert best["samples_per_s"] >= 1.5 * w0["samples_per_s"], "more workers did not speed up a CPU-bound input pipeline"
        assert w0["data_wait_fraction"] >= 0.3, f"with no workers the loop waited only {w0['data_wait_fraction']:.0%} for data: not input-bound"
        assert best["gpu_busy_fraction"] > w0["gpu_busy_fraction"], "the best configuration should keep the GPU busier than workers 0"
        return (f"workers 0: {w0['samples_per_s']:.0f}/s, GPU busy {w0['gpu_busy_fraction']:.0%}; best ({best['config']}): "
                f"{best['samples_per_s']:.0f}/s, GPU busy {best['gpu_busy_fraction']:.0%}; ceiling {ceiling:.0f}/s")
    C.run("Step 3 DataLoader feeds the GPU", s3)

    w = max(len(n) for _, n, _ in C.rows)
    for status, name, msg in C.rows:
        print(f"{status:<4} {name:<{w}}  {msg}")
    passed = sum(1 for s, _, _ in C.rows if s == "PASS")
    print(f"\n{passed}/{len(C.rows)} checks passed [{d}]")
    return 0 if passed == len(C.rows) else 1


if __name__ == "__main__":
    sys.exit(main())
