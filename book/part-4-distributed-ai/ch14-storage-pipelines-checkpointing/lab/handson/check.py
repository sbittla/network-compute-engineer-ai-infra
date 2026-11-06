#!/usr/bin/env python3
"""Chapter 14 hands-on lab checker: is a results bundle complete and physically sensible?

    python check.py results/<run-id>

Prints PASS/FAIL per check and exits 0 only if every check passes. Standard library only; it reads
the bundle and recomputes what it can from the raw fio and checkpoint outputs.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from summarize import daly, fio_read, young  # noqa: E402

REQUIRED = ["environment.json", "summary.json", "report.md", "raw/fio_jobs.json", "raw/ckpt_bench.json",
            "raw/fio_sweep.log", "raw/ckpt_bench.log"]


class Checker:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def run(self, name: str, fn: Callable[[], str]) -> None:
        try:
            self.rows.append(("PASS", name, fn()))
        except AssertionError as e:
            self.rows.append(("FAIL", name, str(e)))
        except Exception as e:  # noqa: BLE001 -- report, never crash
            self.rows.append(("FAIL", name, f"{type(e).__name__}: {e}"))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run = Path(sys.argv[1])
    ck = Checker()
    ctx: dict = {}

    def files() -> str:
        missing = [f for f in REQUIRED if not (run / f).is_file()]
        assert not missing, f"missing from the bundle: {missing} (did run.sh finish?)"
        ctx["s"] = json.loads((run / "summary.json").read_text())
        ctx["jobs"] = json.loads((run / "raw" / "fio_jobs.json").read_text())
        ctx["ck"] = json.loads((run / "raw" / "ckpt_bench.json").read_text())
        env = json.loads((run / "environment.json").read_text())
        for k in ("kernel", "cpu", "mem_gib", "gpu", "tools"):
            assert env.get(k) not in (None, ""), f"environment.json lacks {k}"
        return f"{len(REQUIRED)} files present; environment recorded ({env['gpu']})"

    def fio_complete() -> str:
        jobs = ctx["jobs"]["jobs"]
        bad = [j["name"] for j in jobs if j["rc"] != 0]
        assert not bad, f"{len(bad)} fio jobs failed: {bad[:5]}"
        reps = ctx["jobs"]["meta"]["reps"]
        direct = [j for j in jobs if j.get("step") == "ext4_direct"]
        assert len(direct) == 8 * reps, f"{len(direct)} O_DIRECT jobs, expected 2 patterns x 4 QDs x {reps} reps"
        assert reps >= 3, f"only {reps} repetitions; the chapter asks for >= 5 (3 is the minimum this checker accepts)"
        for step in ("ext4_buffered_cold", "ext4_buffered_warm"):
            n = sum(j.get("step") == step for j in jobs)
            assert n == 8, f"{n} {step} jobs, expected 8"
        unreadable = [j["name"] for j in jobs if fio_read(run / "raw" / "fio" / f"{j['name']}.json") is None]
        assert not unreadable, f"raw fio JSON missing or unreadable: {unreadable[:5]}"
        return f"{len(jobs)} fio jobs, all rc 0 with raw JSON; {reps} repetitions of the O_DIRECT sweep"

    def recompute() -> str:
        d = ctx["s"]["fio"]["ext4_direct"]["randread-4k-qd32"]
        js = [j for j in ctx["jobs"]["jobs"] if j.get("step") == "ext4_direct" and j["pattern"] == "randread-4k" and j["qd"] == 32]
        iops = sorted(fio_read(run / "raw" / "fio" / f"{j['name']}.json")["iops"] for j in js)
        mid = iops[len(iops) // 2] if len(iops) % 2 else (iops[len(iops) // 2 - 1] + iops[len(iops) // 2]) / 2
        assert math.isclose(mid, d["iops_median"], rel_tol=1e-6), f"summary IOPS {d['iops_median']} != raw median {mid}"
        return f"summary matches the raw fio JSON (randread 4k QD32 median {mid:,.0f} IOPS)"

    def qd_scaling() -> str:
        d = ctx["s"]["fio"]["ext4_direct"]
        i1, i32 = d["randread-4k-qd1"]["iops_median"], d["randread-4k-qd32"]["iops_median"]
        assert i32 > 3 * i1, f"O_DIRECT random IOPS QD32 {i32:,.0f} not > 3 x QD1 {i1:,.0f}: is the queue depth real? (psync?)"
        mono = [d[f"randread-4k-qd{q}"]["iops_median"] for q in (1, 4, 16, 32)]
        assert all(b >= 0.9 * a for a, b in zip(mono, mono[1:])), f"IOPS fall as QD rises: {mono}"
        return f"O_DIRECT 4 KiB random IOPS scale {i32 / i1:.1f}x from QD1 to QD32"

    def littles_law() -> str:
        worst = []
        for k, v in ctx["s"]["fio"]["ext4_direct"].items():
            ratio = v["littles_law_qd"] / v["qd"]
            worst.append((abs(ratio - 1), k, ratio))
            assert 0.8 <= ratio <= 1.1, (f"{k}: IOPS x mean latency = {v['littles_law_qd']:.1f} vs QD {v['qd']}: "
                                         "the queue depth is not what fio was asked for")
        w = max(worst)
        return f"IOPS x latency within 20 % of QD for all 8 O_DIRECT cells (worst {w[1]}: {w[2]:.2f})"

    def page_cache() -> str:
        r = ctx["s"]["fio"]["ratios"]
        assert r["warm_cache_over_direct_randread_qd1"] > 5, (
            f"warm-cache 4k random reads only {r['warm_cache_over_direct_randread_qd1']:.1f}x O_DIRECT: was the cache really warm?")
        assert r["buffered_cold_randread_iops_qd32_over_qd1"] < r["direct_randread_iops_qd32_over_qd1"], (
            "cold buffered random reads scaled with QD as well as O_DIRECT: was the cache dropped?")
        meta = ctx["jobs"]["meta"]
        warm = ctx["s"]["fio"]["page_cache_bytes_during_warm"]
        assert warm >= 0.8 * meta["size_gib"] * 2**30, f"page cache {warm / 2**30:.2f} GiB < 80 % of the test file during warm runs"
        return (f"warm cache {r['warm_cache_over_direct_randread_qd1']:.0f}x O_DIRECT at QD1; cold buffered QD32/QD1 "
                f"{r['buffered_cold_randread_iops_qd32_over_qd1']:.2f}x vs O_DIRECT {r['direct_randread_iops_qd32_over_qd1']:.1f}x")

    def ninep() -> str:
        meta = ctx["jobs"]["meta"]
        if meta.get("p9_skipped"):
            return "9P step skipped: not a WSL host (recorded in fio_jobs.json)"
        r = ctx["s"]["fio"]["ratios"]
        assert r["ext4_over_9p_seqread_qd32_bw"] > 2, f"ext4 only {r['ext4_over_9p_seqread_qd32_bw']:.1f}x 9P for sequential reads"
        return f"ext4 {r['ext4_over_9p_seqread_qd32_bw']:.0f}x faster than 9P sequentially; 9P IOPS QD32/QD1 {r['p9_randread_iops_qd32_over_qd1']:.2f}"

    def ckpt_ran() -> str:
        c = ctx["s"]["checkpoint"]
        assert c.get("status") == "ran", f"checkpoint step did not run: {c.get('reason')}"
        raw = ctx["ck"]
        assert raw["swap_used_bytes_end"] - raw["swap_used_bytes_start"] < 0.05 * raw["state_bytes"], (
            "swap grew by more than 5 % of the state during the run: the host paged; timings are not valid")
        for k, m in c["methods"].items():
            assert m["n"] >= 3, f"{k}: {m['n']} timed repetitions (< 3)"
            assert m["bytes_on_disk"] >= 0.95 * c["state_bytes"], f"{k}: {m['bytes_on_disk']} B on disk < state {c['state_bytes']} B"
        return f"{c['state_bytes'] / 1e9:.3f} GB state, 3 methods x {c['methods']['sync']['n']} reps, no paging"

    def ckpt_shape() -> str:
        m = ctx["s"]["checkpoint"]["methods"]
        s, a, t = m["sync"], m["dcp_async"], m["thread"]
        for k, x in (("dcp_async", a), ("thread", t)):
            assert x["blocking_s_median"] < s["completion_s_median"], f"{k} blocks {x['blocking_s_median']:.3f} s >= sync save"
            assert x["completion_s_median"] > x["blocking_s_median"], f"{k}: completion before blocking ended"
            assert x["steps_during_total"] > 0, f"{k}: no training steps ran during the persist"
        snap = t["snapshot_GBps_median"]
        assert 1 <= snap <= 70, f"pinned D2H snapshot {snap:.2f} GB/s is implausible (paging below 1; above any PCIe x16 Gen5)"
        return (f"blocking sync {s['completion_s_median']:.3f} s > dcp_async {a['blocking_s_median']:.3f} s > "
                f"thread {t['blocking_s_median']:.3f} s; snapshot {snap:.1f} GB/s")

    def ckpt_load() -> str:
        c = ctx["s"]["checkpoint"]
        ld, sync = c["load"], c["methods"]["sync"]["completion_s_median"]
        assert ld["cold"]["s_median"] < 20 * sync, f"cold dcp.load {ld['cold']['s_median']:.1f} s > 20 x save: paging?"
        assert ld["warm"]["s_median"] <= ld["cold"]["s_median"] * 1.1, "warm-cache load slower than cold"
        return f"dcp.load cold {ld['cold']['GBps_median']:.2f} GB/s, warm {ld['warm']['GBps_median']:.2f} GB/s"

    def consistency() -> str:
        cs = ctx["s"]["checkpoint"]["consistency"]
        assert cs["live_state_changed_meanwhile"], "training did not change the state during the persist: the test proves nothing"
        assert cs["differ_from_state_at_call"] == 0, (
            f"{cs['differ_from_state_at_call']} tensors in the async checkpoint differ from the state at the call")
        return f"async checkpoint equals the state at the call ({cs['tensors']} tensors, {cs['steps_during_persist']} steps ran)"

    def young_daly() -> str:
        c = ctx["s"]["checkpoint"]
        rows = c["young_daly"]
        assert rows, "no Young/Daly rows"
        for y in rows:
            msec = y["mtbf_h"] * 3600
            assert math.isclose(y["tau_young_s"], young(y["delta_s"], msec), rel_tol=1e-6), "tau_young != sqrt(2 delta M)"
            assert math.isclose(y["tau_daly_s"], daly(y["delta_s"], msec), rel_tol=1e-6), "tau_daly mismatch"
            assert abs(y["tau_daly_s"] / y["tau_young_s"] - 1) < 0.05, "Young and Daly differ by > 5 % although delta << M"
        by = {(y["mtbf_h"], y["method"]): y for y in rows}
        h = rows[0]["mtbf_h"]
        assert by[(h, "dcp_async")]["tau_young_s"] < by[(h, "sync")]["tau_young_s"], "async interval not shorter than sync"
        return (f"MTBF {h:g} h [ASSUMED]: tau* sync {by[(h, 'sync')]['tau_young_s']:.0f} s, "
                f"dcp_async {by[(h, 'dcp_async')]['tau_young_s']:.0f} s")

    def labels() -> str:
        text = (run / "report.md").read_text(encoding="utf-8")
        for lab in ("[MEASURED]", "[MODELED]", "[ASSUMED]"):
            assert lab in text, f"report.md has no {lab} label"
        return "report.md labels measured, modelled and assumed values"

    ck.run("bundle complete", files)
    if ctx:
        for name, fn in (("fio jobs complete", fio_complete), ("summary matches raw", recompute),
                         ("queue depth scales IOPS", qd_scaling), ("Little's law", littles_law),
                         ("page cache inflation", page_cache), ("9P vs ext4", ninep),
                         ("checkpoint ran cleanly", ckpt_ran), ("sync vs async shape", ckpt_shape),
                         ("checkpoint load", ckpt_load), ("async consistency", consistency),
                         ("Young/Daly", young_daly), ("report labels", labels)):
            ck.run(name, fn)
    for status, name, msg in ck.rows:
        print(f"{status}  {name}: {msg}")
    ok = all(r[0] == "PASS" for r in ck.rows)
    print(f"\n{sum(r[0] == 'PASS' for r in ck.rows)}/{len(ck.rows)} checks passed" + ("" if ok else " - bundle FAILS"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
