#!/usr/bin/env python3
"""Chapter 16 hands-on lab checker: is an acceptance bundle complete and physically sensible?

    python check.py results/<run-id>

It does not require the node to pass. It requires that every policy check has a status, that the
verdict follows from the statuses, that N/A was never counted as PASS, and that the measurements
behind the GPU, thermal, PCIe and disk checks are present and plausible. It re-derives what it can
from the raw outputs. Standard library only; exits 0 only if every check passes.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evaluate import load_telemetry  # noqa: E402

REQUIRED = ["environment.json", "summary.json", "report.md", "acceptance_record.json", "raw/host.json",
            "raw/gpu_stress.json", "raw/telemetry.csv", "raw/clock_event_counters_before.csv",
            "raw/clock_event_counters_after.csv", "raw/nvidia-smi-inventory-idle.txt", "raw/dmesg.txt"]
# Codes the chapter's Table 16.4 defines; each must appear in the bundle with a status.
CHAPTER_CODES = ["GPU_COUNT", "GPU_PRODUCT", "HBM_CAPACITY", "PCIE_DEGRADED", "NVLINK_DOWN", "ECC_DBE",
                 "HBM_ROW_REMAP_PENDING", "DCGM_DIAG_FAIL", "THERMAL_THROTTLE", "NIC_COUNT", "NIC_LINK_DOWN",
                 "NIC_SPEED", "NIC_MTU", "RDMA_PAIR_BW_LOW", "LINK_BER_HIGH", "GDR_PATH_FAIL", "NVME_COUNT",
                 "NVME_MEDIA_ERRORS", "NVME_DRIVE_SLOW", "STORAGE_THROUGHPUT_LOW", "NCCL_BUSBW_LOW", "XID_PRESENT",
                 "FW_OFF_MATRIX"]
MUST_BE_NA_ON_WSL = ["NVLINK_DOWN", "ECC_DBE", "DCGM_DIAG_FAIL", "RDMA_PAIR_BW_LOW", "GDR_PATH_FAIL", "NCCL_BUSBW_LOW"]


class Checker:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def run(self, name: str, fn: Callable[[], str]) -> None:
        try:
            self.rows.append(("PASS", name, fn()))
        except AssertionError as e:
            self.rows.append(("FAIL", name, str(e)))
        except Exception as e:  # noqa: BLE001
            self.rows.append(("FAIL", name, f"{type(e).__name__}: {e}"))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run = Path(sys.argv[1])
    ck, ctx = Checker(), {}

    def files() -> str:
        missing = [f for f in REQUIRED if not (run / f).is_file()]
        assert not missing, f"missing from the bundle: {missing} (did run.sh finish?)"
        ctx["s"] = json.loads((run / "summary.json").read_text())
        ctx["host"] = json.loads((run / "raw" / "host.json").read_text())
        ctx["gs"] = json.loads((run / "raw" / "gpu_stress.json").read_text())
        ctx["env"] = json.loads((run / "environment.json").read_text())
        return f"{len(REQUIRED)} files present"

    def coverage() -> str:
        checks = ctx["s"]["checks"]
        for c in checks:
            assert c["status"] in ("PASS", "WARN", "FAIL", "N/A"), f"{c['code']}: unknown status {c['status']}"
            assert c["evidence"] and c["criterion"], f"{c['code']}: no evidence or criterion recorded"
        have = " ".join(c["code"] for c in checks)
        missing = [k for k in CHAPTER_CODES if k not in have]
        assert not missing, f"chapter reason codes with no status: {missing}"
        return f"{len(checks)} checks, every Table 16.4 code has a status and evidence"

    def verdict() -> str:
        s = ctx["s"]
        st = [c["status"] for c in s["checks"]]
        want = "FAIL" if "FAIL" in st else "WARN" if "WARN" in st else "PASS"
        assert s["verdict_on_checks_that_ran"] == want, f"verdict {s['verdict_on_checks_that_ran']} but statuses imply {want}"
        counts = {k: st.count(k) for k in ("PASS", "WARN", "FAIL", "N/A")}
        assert counts == s["counts"], f"counts {s['counts']} != recomputed {counts}"
        if counts["N/A"] and want != "FAIL":
            assert s["decision"].startswith("NOT VALIDATED"), f"decision {s['decision']!r} with {counts['N/A']} N/A checks: N/A counted as PASS"
        if want == "FAIL":
            assert s["decision"].startswith("REJECTED"), f"decision {s['decision']!r} despite a FAIL"
        return f"verdict {want} and decision '{s['decision']}' follow from {counts}"

    def na_honest() -> str:
        kl = ctx["host"]["kernel_log"]
        by = {c["code"]: c for c in ctx["s"]["checks"]}
        get = lambda k: next(c for code, c in by.items() if code.startswith(k))  # noqa: E731
        # environment.json's "wsl" flag looks for "microsoft" in the kernel release, which a custom WSL2
        # kernel (e.g. the Soft-RoCE build) lacks; /dev/dxg is the GPU path only WSL2 has.
        if ctx["env"].get("wsl") or kl["dxg_device"]:
            for k in MUST_BE_NA_ON_WSL:
                assert get(k)["status"] == "N/A", f"{k} is {get(k)['status']} on WSL2, where it cannot run"
        x = get("XID_PRESENT")
        if not kl["nvidia_kernel_module_loaded"] and not kl["xid_lines"]:
            assert x["status"] == "N/A", "XID_PRESENT marked PASS from a kernel log the GPU driver never writes to"
        ecc = ctx["host"]["gpu"]["gpus"][0]["ecc_mode"]
        if ecc in ("[N/A]", "N/A", "Disabled"):
            assert get("ECC_DBE")["status"] == "N/A", "ECC check passed on a GPU with ECC off"
            assert get("HBM_ROW_REMAP_PENDING")["status"] == "N/A", "row-remap check passed with no ECC feeding it"
        return "checks that cannot run here are N/A, not PASS (ECC, row remap, DCGM, NVLink, RDMA, NCCL, Xid)"

    def telemetry() -> str:
        rows = load_telemetry(run / "raw" / "telemetry.csv")
        loaded = [r for r in rows if (r["util"] or 0) >= 90]
        secs = ctx["gs"]["stress"]["seconds"]
        assert len(loaded) >= secs, f"only {len(loaded)} loaded samples for a {secs:.0f} s stress at 500 ms (expected >= {secs:.0f})"
        tmax = max(r["temp_c"] for r in rows if r["temp_c"] is not None)
        assert 20 <= tmax <= 110, f"max temperature {tmax} C is implausible"
        clk = statistics.median(r["sm_mhz"] for r in loaded)
        mx = loaded[0]["sm_max_mhz"]
        assert 200 <= clk <= mx * 1.01, f"median SM clock {clk} MHz outside 200..max {mx}"
        tc = next(c for c in ctx["s"]["checks"] if c["code"] == "THERMAL_THROTTLE")
        if tmax >= 87:
            assert tc["status"] == "FAIL", f"max {tmax} C >= 87 C but THERMAL_THROTTLE is {tc['status']}"
        return f"{len(loaded)} loaded samples; max {tmax:.0f} C; median SM clock {clk:.0f} of {mx:.0f} MHz"

    def stress() -> str:
        st, p = ctx["gs"]["stress"], ctx["gs"]["identity"]
        w = [x["tflops"] for x in st["windows"]]
        assert st["seconds"] >= 30, f"stress ran {st['seconds']} s (< 30 s): too short to heat the GPU"
        assert len(w) >= st["seconds"] * 0.8, f"{len(w)} 1-second windows for a {st['seconds']:.0f} s stress"
        med = statistics.median(w)
        assert 0.5 <= med <= 2000, f"median {med:.1f} TFLOP/s is implausible"
        assert st["golden_checks"] >= st["seconds"] / 4, f"only {st['golden_checks']} golden checks"
        n = ctx["gs"]["numerics"]
        assert set(n) == {"cold", "hot"}, "numerics must be checked both cold and hot"
        for k, v in n.items():
            assert 0 <= v["fp32_err"] < 1 and 0 <= v["fp16_err"] < 1, f"{k} GEMM errors {v} not plausible"
            assert v["fp32_err"] < v["fp16_err"], f"{k}: FP32 error {v['fp32_err']:.1e} not below FP16 {v['fp16_err']:.1e}"
        return f"{st['seconds']:.0f} s stress, median {med:.1f} TFLOP/s on {p['name']}; numerics cold+hot recorded"

    def pcie() -> str:
        rows = [r for r in load_telemetry(run / "raw" / "telemetry.csv") if (r["util"] or 0) >= 90]
        g = ctx["host"]["gpu"]["gpus"][0]
        gen, width = statistics.median(r["pcie_gen"] for r in rows), statistics.median(r["pcie_width"] for r in rows)
        pc = next(c for c in ctx["s"]["checks"] if c["code"] == "PCIE_DEGRADED")
        degraded = gen < g["pcie_max"]["gen"] or width < g["pcie_max"]["width"]
        assert (pc["status"] == "FAIL") == degraded, f"PCIE_DEGRADED {pc['status']} but under load Gen{gen:g} x{width:g} vs max {g['pcie_max']}"
        return f"under load Gen{gen:g} x{width:g}, max Gen{g['pcie_max']['gen']} x{g['pcie_max']['width']}: {pc['status']}"

    def disks() -> str:
        dd = ctx["host"]["storage"]["data_disks"]
        assert dd, "no data disk was tested"
        for d in dd:
            timed = [r for r in d["runs"] if not r["warmup"]]
            assert len(timed) >= 3, f"/dev/{d['device']}: {len(timed)} timed fio runs (< 3)"
            assert all(r["rc"] == 0 for r in d["runs"]), f"/dev/{d['device']}: a fio run failed"
            assert all("--readonly" in r["cmd"] for r in d["runs"]), f"/dev/{d['device']}: fio ran without --readonly"
            bws = [r["bw_GBps"] for r in timed]
            assert all(0.01 <= b <= 60 for b in bws), f"/dev/{d['device']}: implausible GB/s {bws}"
        return "; ".join(f"/dev/{d['device']} " + ", ".join(f"{r['bw_GBps']:.2f}" for r in d["runs"] if not r["warmup"]) + " GB/s"
                         for d in dd) + " (read-only)"

    def memory() -> str:
        m = ctx["host"]["memory"]
        assert m["pattern_test"]["bytes"] >= 128 * 2**20, "host pattern test under 128 MiB"
        assert ctx["gs"]["memory_pattern"]["bytes"] >= 512 * 2**20, "GPU pattern test under 512 MiB"
        return f"host {m['pattern_test']['bytes'] / 2**20:.0f} MiB, GPU {ctx['gs']['memory_pattern']['bytes'] / 2**30:.2f} GiB pattern-tested"

    def report() -> str:
        text = (run / "report.md").read_text(encoding="utf-8")
        for needle in ("[MEASURED]", "N/A is not PASS", "Acceptance decision", "HX8 policy"):
            assert needle in text, f"report.md lacks {needle!r}"
        return "report.md has the verdict, the decision, the N/A explanation and the HX8 comparison"

    ck.run("bundle complete", files)
    if ctx:
        for name, fn in (("every chapter check has a status", coverage), ("verdict follows from statuses", verdict),
                         ("N/A is not PASS", na_honest), ("burn-in telemetry", telemetry), ("stress and numerics", stress),
                         ("PCIe under load", pcie), ("disk floor evidence", disks), ("memory tests", memory),
                         ("report", report)):
            ck.run(name, fn)
    for status, name, msg in ck.rows:
        print(f"{status}  {name}: {msg}")
    ok = all(r[0] == "PASS" for r in ck.rows)
    print(f"\n{sum(r[0] == 'PASS' for r in ck.rows)}/{len(ck.rows)} checks passed" + ("" if ok else " - bundle FAILS"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
