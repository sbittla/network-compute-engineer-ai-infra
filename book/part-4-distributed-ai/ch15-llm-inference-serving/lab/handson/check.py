#!/usr/bin/env python3
"""Check a Chapter 15 hands-on results directory: complete, and physically sensible.

    python check.py results/<run-id>

Exit 0 only if every check passes. The checks test physics and mechanism, not equality with the
reference run: batching raises throughput, a bigger batch slows each decode step, prefix caching cuts
TTFT on a shared prefix, a small KV pool fills and preempts, and --max-num-seqs caps the running batch.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CONC = ["1", "2", "4", "8", "16", "32"]
results: list[tuple[bool, str, str]] = []


def check(name: str, ok: bool, why: str = "") -> None:
    results.append((bool(ok), name, why))


def get(d: dict, *path, default=None):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return default
        d = d[p]
    return d


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run = Path(sys.argv[1])
    for f in ("environment.json", "summary.json", "report.md"):
        check(f"C0 {f} present", (run / f).is_file(), f"missing {run / f}")
    raw = run / "raw"
    need_raw = ["server-base.log", "hostmem.tsv", "nvidia-smi.csv", "metrics-base-start.prom"]
    missing = [f for f in need_raw if not (raw / f).is_file()]
    check("C0 raw outputs present", not missing, f"missing raw/{', raw/'.join(missing)}")
    if not (run / "summary.json").is_file():
        return report()
    s = json.loads((run / "summary.json").read_text())
    env = json.loads((run / "environment.json").read_text()) if (run / "environment.json").is_file() else {}
    rep = (run / "report.md").read_text() if (run / "report.md").is_file() else ""
    check("C0 report labels numbers [MEASURED]", rep.count("[MEASURED]") >= 5, "report.md needs [MEASURED] labels")
    check("C0 environment records GPU and vLLM version", bool(env.get("gpu")) and any("0." in str(v) for v in env.get("tools", {}).values()),
          "environment.json lacks the GPU or tool versions")
    check("C0 KV-usage metric found in /metrics", s.get("kv_metric_name") in ("vllm:kv_cache_usage_perc", "vllm:gpu_cache_usage_perc"),
          f"no KV usage gauge recognised (got {s.get('kv_metric_name')})")

    # Step 1
    by = get(s, "sweep", "by_concurrency", default={})
    have = [c for c in CONC if c in by]
    check("S1 sweep covers C = 1, 2, 4, 8, 16, 32", have == CONC, f"have C = {', '.join(have) or 'none'}")
    if have:
        errs = sum(by[c].get("errors", 0) for c in have)
        check("S1 no request errors in the sweep", errs == 0, f"{errs} failed requests")
        cpt = [by[c].get("chunks_per_token") for c in have]
        check("S1 streaming delivered about one chunk per token", all(x and 0.5 <= x <= 1.01 for x in cpt),
              f"chunks per output token {cpt}: ITL is per chunk, so it must be close to per token")
        lo, hi = by[have[0]], by[have[-1]]
        tl, th = lo.get("output_tok_per_s") or 0, hi.get("output_tok_per_s") or 0
        check("S1 batching raises throughput (C=32 >= 4x C=1)", th >= 4 * tl > 0,
              f"output tok/s {tl} at C={have[0]} vs {th} at C={have[-1]}")
        pl, ph = lo.get("tpot_ms_p50") or 0, hi.get("tpot_ms_p50") or 0
        check("S1 a bigger batch slows each decode step (TPOT C=32 > C=1)", ph > pl > 0,
              f"TPOT p50 {pl} ms at C=1 vs {ph} ms at C=32")
        check("S1 decode is far cheaper than per-request time (TPOT C=1 in 1-100 ms)", 1 <= pl <= 100,
              f"TPOT p50 at C=1 is {pl} ms")
        fl, fh = lo.get("ttft_ms_p50") or 0, hi.get("ttft_ms_p50") or 0
        check("S1 TTFT grows with concurrency", fh > fl > 0, f"TTFT p50 {fl} ms at C=1 vs {fh} ms at C=32")
        tps = [by[c].get("output_tok_per_s") or 0 for c in have]
        check("S1 throughput per user falls as C rises (tok/s/C at 32 < at 1)", tps[-1] / 32 < tps[0],
              f"per-client tok/s {tps[0]:.1f} at C=1 vs {tps[-1] / 32:.1f} at C=32")

    # Step 2
    pr = get(s, "prefix_caching", "results", default={})
    for c in ("1", "8"):
        off, on = pr.get(f"off-c{c}"), pr.get(f"on-c{c}")
        if not (off and on):
            check(f"S2 prefix caching off and on measured at C={c}", False, "missing prefix-off or prefix-on results")
            continue
        check(f"S2 prefix cache hits only when enabled (C={c})", (on.get("prefix_hit_rate") or 0) >= 0.5 and (off.get("prefix_hit_rate") or 0) == 0,
              f"hit rate off={off.get('prefix_hit_rate')} on={on.get('prefix_hit_rate')}")
        a, b = off.get("ttft_ms_p50") or 0, on.get("ttft_ms_p50") or 0
        check(f"S2 prefix caching cuts TTFT p50 on a shared prefix (C={c}, >= 1.3x)", b > 0 and a / b >= 1.3,
              f"TTFT p50 off {a} ms vs on {b} ms")

    # Step 3
    pres = get(s, "pressure", "by_util", default={})
    if len(pres) < 2:
        check("S3 pressure workload run at two memory settings", False, f"have {list(pres)}")
    else:
        us = sorted(pres, key=float)
        small, big = pres[us[0]], pres[us[-1]]
        check("S3 the small KV pool fills (peak KV usage >= 90 %)", (small.get("kv_usage_max_pct") or 0) >= 90,
              f"peak KV {small.get('kv_usage_max_pct')} % at util {us[0]}")
        check("S3 the small KV pool preempts running sequences", (small.get("preemptions") or 0) > 0,
              f"preemptions {small.get('preemptions')} at util {us[0]}")
        check("S3 the large KV pool does not preempt", (big.get("preemptions") or 0) == 0,
              f"preemptions {big.get('preemptions')} at util {us[-1]}")
        # A recompute preemption throws away a sequence's KV; when it is readmitted its prompt and the tokens
        # generated so far are prefilled again, so that user sees one very long token gap.
        si, bi = small.get("itl_ms_max") or 0, big.get("itl_ms_max") or 0
        check("S3 preemption stalls a sequence (ITL max small pool >= 3x large pool)", bi > 0 and si >= 3 * bi,
              f"ITL max {si} ms (small pool) vs {bi} ms (large)")
        check("S3 no request errors under pressure", small.get("errors") == 0 and big.get("errors") == 0, "requests failed")

    # Step 4
    cap = get(s, "capacity", default={})
    rows = [r for r in cap.get("rows", []) if r.get("engine_kv_tokens")]
    check("S4 at least three --gpu-memory-utilization settings started", len(rows) >= 3, f"{len(rows)} started")
    if rows:
        kv = [r["engine_kv_tokens"] for r in rows]
        check("S4 KV tokens rise with --gpu-memory-utilization", all(b > a for a, b in zip(kv, kv[1:])),
              f"engine KV tokens by util: {kv}")
        th = cap.get("theoretical_kv_tokens") or 0
        check("S4 engine KV < (fraction x memory - weights) < theoretical",
              all(r["engine_kv_tokens"] < r["after_fraction_kv_tokens"] < th for r in rows),
              "the Table 15.3a ordering must hold: each subtraction lowers capacity")
        ratio = [r.get("usable_over_theoretical") for r in rows]
        # 0 is a real answer at a small fraction: the pool holds less than one 4k sequence with 10 % headroom.
        check("S4 usable / theoretical 4k sequences in [0, 1), > 0 at the largest setting",
              all(x is not None and 0 <= x < 1 for x in ratio) and (ratio[-1] or 0) > 0, f"ratios {ratio}")
        res = [r.get("runtime_reserve_gib") for r in rows]
        check("S4 runtime reserve is positive and under 3 GiB", all(x is not None and 0 < x < 3 for x in res), f"reserves {res} GiB")

    # Step 5
    mn = get(s, "max_num_seqs", "by_max_num_seqs", default={})
    if not {"4", "64"} <= set(mn):
        check("S5 --max-num-seqs 4 and 64 measured", False, f"have {sorted(mn)}")
    else:
        for m, x in mn.items():
            check(f"S5 running batch never exceeds --max-num-seqs {m}", (x.get("running_max") or 0) <= int(m),
                  f"max running {x.get('running_max')}")
        a, b = mn["4"], mn["64"]
        check("S5 a cap of 4 makes requests wait", (a.get("waiting_max") or 0) >= 16, f"max waiting {a.get('waiting_max')}")
        check("S5 a cap of 4 raises TTFT and lowers throughput",
              (a.get("ttft_ms_p50") or 0) > (b.get("ttft_ms_p50") or 0) and (a.get("output_tok_per_s") or 0) < (b.get("output_tok_per_s") or 0),
              f"TTFT p50 {a.get('ttft_ms_p50')} vs {b.get('ttft_ms_p50')} ms; tok/s {a.get('output_tok_per_s')} vs {b.get('output_tok_per_s')}")
        check("S5 a cap of 4 gives the fastest decode step (TPOT)", (a.get("tpot_ms_p50") or 1e9) < (b.get("tpot_ms_p50") or 0),
              f"TPOT p50 {a.get('tpot_ms_p50')} vs {b.get('tpot_ms_p50')} ms")

    # Host memory. MemAvailable is shared with everything else in the WSL VM, so the pass condition is on the
    # lab's own footprint (the server process tree) and on no server dying of memory exhaustion.
    hm = s.get("host_memory", {})
    mem_mib = (env.get("mem_gib") or 0) * 1024
    rss = hm.get("max_server_rss_mib") or 0
    check("H host memory was watched; the server tree fits (peak RSS < 85 % of host memory)",
          hm.get("samples", 0) > 10 and mem_mib > 0 and 0 < rss < 0.85 * mem_mib,
          f"samples {hm.get('samples')}, peak server RSS {rss} MiB of {mem_mib:.0f} MiB")
    oom = [p.name for p in sorted(raw.glob("server-*.log"))
           if re.search(r"OutOfMemoryError|MemoryError|Cannot allocate memory|\bKilled\b", p.read_text(errors="replace"))]
    check("H no server died of host or GPU memory exhaustion", not oom, f"out-of-memory in {', '.join(oom)}")
    low = hm.get("min_available_mib")
    if low is not None and low < 200:
        print(f"NOTE  lowest MemAvailable was {low} MiB (shared with the rest of the VM); "
              "close other memory-heavy work if a server is killed during start-up")
    return report()


def report() -> int:
    for ok, name, why in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  -- {why}"))
    bad = sum(not ok for ok, _, _ in results)
    print(f"\n{len(results) - bad}/{len(results)} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
