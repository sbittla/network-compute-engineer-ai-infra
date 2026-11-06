#!/usr/bin/env python3
"""Check a Chapter 5 hands-on results bundle for completeness and physical sense.

    python check.py results/<run-id>

Prints one PASS/FAIL line per check and exits 0 only if every check passes. Standard library only. It
tests mechanisms (no copy beats its link; large transfers beat small ones; pinned beats pageable), not
this machine's numbers.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

REQUIRED = [
    "environment.json", "summary.json", "report.md",
    "step1-discovery/nvidia-smi-L.txt", "step1-discovery/topo-m.txt", "step1-discovery/nvidia-smi-q.txt",
    "step1-discovery/lspci-D-nn.txt", "step1-discovery/lstopo.txt", "step1-discovery/numactl-hardware.txt",
    "step1-discovery/gpu-pci.csv", "step1-discovery/gpu-sysfs-lookup.txt",
    "step2-link-idle/link-idle.csv", "step3-bandwidth/sweep.json", "step3-bandwidth/bidir.json",
    "step4-under-load/link-load.csv", "step4-under-load/dmon-pcie.txt", "step4-under-load/hold.json", "step4-under-load/contend.json",
    "step5-affinity/cpu-first.json", "step5-affinity/cpu-last.json",
]


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
        for k in ("step1", "step2", "step3", "step4", "step5"):
            assert k in sm, f"summary.json lacks {k} (rerun summarize.py)"
        assert sm["environment"].get("gpu"), "environment.json records no GPU"
        rep = (d / "report.md").read_text(encoding="utf-8")
        assert rep.count("[MEASURED]") >= 10, "report.md labels fewer than 10 numbers [MEASURED]"
        return sm["environment"]["gpu"]
    C.run("summary, environment and report", load)

    def s1():
        x = sm["step1"]
        assert x["gpu_count"] >= 1, "nvidia-smi -L lists no GPU"
        assert "GPU0" in x["topo_m_columns"], "nvidia-smi topo -m did not print a GPU0 column"
        assert x["numa_nodes"] >= 1, "no NUMA node found in /sys/devices/system/node"
        if x["lspci_nvidia_functions"] == 0:
            assert not x["gpu_bdf_in_sysfs"], "the GPU is absent from lspci but its BDF is in sysfs: inconsistent capture"
        return (f"{x['gpu_count']} GPU, {x['lspci_nvidia_functions']} NVIDIA functions in lspci, {x['numa_nodes']} NUMA node(s), "
                f"{x['topo_m_nic_columns']} NIC columns")
    C.run("Step 1 discovery consistent", s1)

    def s2():
        x = sm["step2"]
        t = x["theoretical_gb_s_per_direction"]
        assert 0.2 < t < 130, f"implausible link rate {t} GB/s"
        assert x["pcie.link.width.current"]["max"] <= x["pcie.link.width.max"], "current width above the maximum"
        assert x["pcie.link.gen.current"]["max"] <= max(x["pcie.link.gen.max"], x.get("pcie.link.gen.gpumax") or 0), "current generation above the maximum"
        assert x["samples"] >= 5, f"only {x['samples']} idle link samples"
        return f"{x['link_label']}: {t} GB/s per direction"
    C.run("Step 2 link state and rate", s2)

    def s3():
        x = sm["step3"]
        t = sm["step2"]["theoretical_gb_s_per_direction"]
        big = x["at_256mib_gb_s"]
        for k in ("h2d_pinned", "d2h_pinned"):
            assert big[k] <= 1.02 * t, f"{k} {big[k]} GB/s exceeds the {t} GB/s link: timing is wrong"
            assert big[k] >= 0.4 * t, f"{k} {big[k]} GB/s is under 40 % of the {t} GB/s link: check the link or the run"
        assert big["h2d_pinned"] >= big["h2d_pageable"], "pinned H2D should not be slower than pageable at 256 MiB"
        assert x["at_64kib_gb_s"]["h2d_pinned"] < big["h2d_pinned"], "64 KiB copies should be slower than 256 MiB ones (fixed cost)"
        bi = x["bidir"]
        assert bi["concurrent_aggregate_gb_per_s"] <= 2.05 * t, "aggregate of both directions exceeds twice the link rate"
        assert bi["aggregate_over_best_unidirectional"] >= 0.8, "running both directions at once collapsed the throughput"
        return (f"256 MiB H2D pinned {big['h2d_pinned']} / pageable {big['h2d_pageable']} GB/s of {t}; "
                f"both directions {bi['aggregate_over_best_unidirectional']}x one")
    C.run("Step 3 bandwidth below the link, pinned >= pageable", s3)

    def s4():
        x = sm["step4"]
        ld, idle = x["link_under_load"], sm["step2"]
        assert ld["samples"] >= 5, "too few link samples under load"
        assert ld["pcie.link.gen.current"]["max"] >= idle["pcie.link.gen.current"]["min"], "link generation fell under load"
        assert x["dmon_samples"] >= 3, "nvidia-smi dmon captured fewer than 3 PCIe samples"
        assert 0.4 <= x["copy_under_gemm_ratio"] <= 1.15, f"copy under GEMM / alone = {x['copy_under_gemm_ratio']}: implausible"
        return f"gen under load {ld['pcie.link.gen.current']}, copy under GEMM ratio {x['copy_under_gemm_ratio']}"
    C.run("Step 4 under load", s4)

    def s5():
        x = sm["step5"]
        r = x["pinned_ratio_last_over_first"]
        if sm["step1"]["numa_nodes"] == 1:
            assert 0.8 <= r <= 1.25, f"one NUMA node, yet the CPU choice changed pinned H2D by {r}x: noisy run?"
        return f"pinned H2D last/first CPU = {r}"
    C.run("Step 5 CPU placement", s5)

    w = max(len(n) for _, n, _ in C.rows)
    for status, name, msg in C.rows:
        print(f"{status:<4} {name:<{w}}  {msg}")
    passed = sum(1 for s, _, _ in C.rows if s == "PASS")
    print(f"\n{passed}/{len(C.rows)} checks passed [{d}]")
    return 0 if passed == len(C.rows) else 1


if __name__ == "__main__":
    sys.exit(main())
