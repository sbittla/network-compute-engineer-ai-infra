#!/usr/bin/env python3
"""Turn a Chapter 15 hands-on run's raw outputs into summary.json and report.md. Standard library only.

    python3 analyze.py results/<run-id>
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

# Qwen2.5-1.5B-Instruct (config.json): 28 layers, 2 KV heads (GQA), head_dim 128, BF16 KV
LAYERS, KV_HEADS, HEAD_DIM, KV_ELEM_BYTES = 28, 2, 128, 2
KV_BYTES_PER_TOKEN = 2 * LAYERS * KV_HEADS * HEAD_DIM * KV_ELEM_BYTES  # 28,672 B
HEADROOM = 0.90  # Table 15.3a admission headroom
PRESSURE_SEQ_TOKENS = 1024 + 512


def pct(xs: list[float], p: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def r(x: float | None, nd: int = 2) -> float | None:
    return None if x is None else round(x, nd)


def load_run(path: Path) -> tuple[list[dict], dict]:
    reqs, run = [], {}
    for line in path.read_text().splitlines():
        o = json.loads(line)
        if o.get("kind") == "run":
            run = o
        else:
            reqs.append(o)
    return reqs, run


def run_stats(path: Path) -> dict:
    reqs, run = load_run(path)
    ok = [q for q in reqs if "error" not in q and q.get("ttft_s") is not None]
    gaps = [g for q in ok for g in q.get("gaps_ms", [])]
    out_tok = sum(q.get("completion_tokens") or 0 for q in ok)
    in_tok = [q.get("prompt_tokens") or q["prompt_len"] for q in ok]
    ttft = [q["ttft_s"] * 1000 for q in ok]
    tpot = [q["tpot_ms"] for q in ok if q.get("tpot_ms")]
    return {
        "requests": len(reqs), "errors": len(reqs) - len(ok),
        "prompt_tokens_mean": r(statistics.mean(in_tok), 1) if in_tok else None,
        "output_tokens_per_request": statistics.median([q.get("completion_tokens") or 0 for q in ok]) if ok else None,
        "chunks_per_token": r(sum(q["chunks"] for q in ok) / out_tok, 3) if out_tok else None,
        "ttft_ms_p50": r(pct(ttft, 50)), "ttft_ms_p95": r(pct(ttft, 95)),
        "tpot_ms_p50": r(pct(tpot, 50)), "tpot_ms_p95": r(pct(tpot, 95)),
        "itl_ms_p50": r(pct(gaps, 50)), "itl_ms_p95": r(pct(gaps, 95)), "itl_ms_p99": r(pct(gaps, 99)),
        "itl_ms_max": r(max(gaps) if gaps else None),
        "wall_s": r(run.get("wall_s"), 3),
        "output_tok_per_s": r(out_tok / run["wall_s"], 1) if run.get("wall_s") else None,
        "req_per_s": r(len(ok) / run["wall_s"], 3) if run.get("wall_s") else None,
    }


def prom(path: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        m = re.match(r"^(vllm:[A-Za-z0-9_:]+)(\{[^}]*\})?\s+(\S+)", line)
        if m:
            try:
                out[m.group(1)] = out.get(m.group(1), 0.0) + float(m.group(3))
            except ValueError:
                pass
    return out


def first(d: dict, *names: str) -> float | None:
    for n in names:
        if n in d:
            return d[n]
    return None


KV_NAMES = ("vllm:kv_cache_usage_perc", "vllm:gpu_cache_usage_perc")
PREEMPT_NAMES = ("vllm:num_preemptions_total", "vllm:num_preemptions")
HIT_NAMES = ("vllm:prefix_cache_hits_total", "vllm:gpu_prefix_cache_hits_total", "vllm:prefix_cache_hits")
QUERY_NAMES = ("vllm:prefix_cache_queries_total", "vllm:gpu_prefix_cache_queries_total", "vllm:prefix_cache_queries")


def series(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def metric_name_used(raw: Path) -> str | None:
    for p in sorted(raw.glob("metrics-*-start.prom")):
        d = prom(p)
        for n in KV_NAMES:
            if n in d:
                return n
    return None


def series_stats(path: Path) -> dict:
    s = [x for x in series(path) if "error" not in x]
    kv = [first(x, *KV_NAMES) for x in s]
    kv = [v for v in kv if v is not None]
    pre = [first(x, *PREEMPT_NAMES) for x in s]
    pre = [v for v in pre if v is not None]
    return {
        "samples": len(s),
        "kv_usage_max_pct": r(max(kv) * 100, 1) if kv else None,
        "kv_usage_p50_pct": r(pct(kv, 50) * 100, 1) if kv else None,
        "running_max": max((x.get("vllm:num_requests_running", 0) for x in s), default=None),
        "waiting_max": max((x.get("vllm:num_requests_waiting", 0) for x in s), default=None),
        "preemptions": (pre[-1] - pre[0]) if len(pre) > 1 else None,
    }


def server_info(raw: Path, name: str) -> dict:
    cfg_p = raw / f"server-{name}.json"
    if not cfg_p.exists():
        return {}
    info = json.loads(cfg_p.read_text())
    st = (raw / f"server-{name}.startup_s").read_text().strip() if (raw / f"server-{name}.startup_s").exists() else ""
    info["started"] = st.isdigit()
    info["startup_s"] = int(st) if st.isdigit() else None
    logp = raw / f"server-{name}.log"
    text = logp.read_text(errors="replace") if logp.exists() else ""

    def grab(rx: str, cast=float):
        m = re.findall(rx, text)
        return cast(m[-1].replace(",", "")) if m else None

    info["weights_gib"] = grab(r"Model loading took ([\d.]+) GiB")
    info["kv_memory_gib"] = grab(r"Available KV cache memory: ([\d.]+) GiB")
    info["kv_tokens"] = grab(r"GPU KV cache size: ([\d,]+) tokens", int)
    info["max_concurrency_at_max_len"] = grab(r"Maximum concurrency for [\d,]+ tokens per request: ([\d.]+)x")
    info["free_at_startup_gib"] = grab(r"Free memory on device \(([\d.]+)/[\d.]+ GiB\) on startup")
    info["weights_plus_non_torch_gib"] = grab(r"Actual usage is ([\d.]+) GiB for consumed memory")
    info["peak_activation_gib"] = grab(r"([\d.]+) GiB for peak activation")
    info["cudagraph_gib"] = grab(r"([\d.]+) GiB for CUDAGraph memory")
    info["compiled_from_cache"] = "Directly load AOT compilation" in text
    m = re.search(r"vllm:cache_config_info\{([^}]*)\}", (raw / f"metrics-{name}-start.prom").read_text()
                  if (raw / f"metrics-{name}-start.prom").exists() else "")
    if m:
        labels = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        info["num_gpu_blocks"] = int(labels["num_gpu_blocks"]) if labels.get("num_gpu_blocks", "").isdigit() else None
        info["block_size"] = int(labels["block_size"]) if labels.get("block_size", "").isdigit() else None
    if not info["started"]:
        # The root cause is the first exception message (e.g. "ValueError: Free memory on device ..."),
        # not the APIServer's closing "Engine core initialization failed" line.
        lines = text.splitlines()
        root = [ln for ln in lines if re.search(r"(ValueError|RuntimeError|OutOfMemoryError|MemoryError): (?!Engine core)", ln)]
        errs = root or [ln for ln in lines if re.search(r"Error|error:|insufficient|not enough|No available memory", ln)]
        msg = errs[0] if errs else (st or "unknown")
        info["start_error"] = re.sub(r"^\(\w+ pid=\d+\)\s*(ERROR [^\]]*\]\s*)?", "", msg.strip())[-300:]
    if info.get("kv_tokens") is None and info.get("num_gpu_blocks") and info.get("block_size"):
        info["kv_tokens"] = info["num_gpu_blocks"] * info["block_size"]
    return info


def main() -> int:
    run = Path(sys.argv[1])
    raw = run / "raw"
    env = json.loads((run / "environment.json").read_text())
    summary: dict = {"lab": "ch15-serve-an-llm", "run_id": run.name,
                     "model": env.get("tools", {}), "kv_bytes_per_token": KV_BYTES_PER_TOKEN,
                     "kv_metric_name": metric_name_used(raw)}

    # Step 1: concurrency sweep
    sweep = {}
    for p in sorted(raw.glob("load-sweep-c*-r*.jsonl")):
        c, rep = map(int, re.match(r"load-sweep-c(\d+)-r(\d+)", p.stem).groups())
        st = run_stats(p)
        st.update({f"kv_{k}": v for k, v in series_stats(raw / f"metrics-sweep-c{c}-r{rep}.jsonl").items()
                   if k in ("kv_usage_max_pct", "running_max", "preemptions")})
        sweep.setdefault(c, []).append(st)
    summary["sweep"] = {
        "workload": "closed loop, C concurrent clients; prompt uniform 256-1024 tokens (random token IDs), "
                    "output exactly 128 tokens (ignore_eos); N = max(16, 4C) requests per repetition",
        "by_concurrency": {},
    }
    for c in sorted(sweep):
        reps = sweep[c]
        keys = ["ttft_ms_p50", "ttft_ms_p95", "tpot_ms_p50", "itl_ms_p50", "itl_ms_p95", "itl_ms_p99",
                "output_tok_per_s", "req_per_s", "kv_kv_usage_max_pct", "kv_running_max"]
        row = {"repetitions": len(reps), "errors": sum(x["errors"] for x in reps),
               "chunks_per_token": reps[0]["chunks_per_token"], "prompt_tokens_mean": reps[0]["prompt_tokens_mean"]}
        for k in keys:
            vals = [x[k] for x in reps if x.get(k) is not None]
            row[k] = r(statistics.median(vals)) if vals else None
            if k in ("output_tok_per_s", "ttft_ms_p50", "tpot_ms_p50") and vals:
                row[k + "_range"] = [r(min(vals)), r(max(vals))]
        summary["sweep"]["by_concurrency"][str(c)] = row

    # Step 2: prefix caching off vs on
    pref = {}
    for mode, server in (("off", "base"), ("on", "prefix-on")):
        for c in (1, 8):
            p = raw / f"load-prefix-{mode}-c{c}.jsonl"
            if not p.exists():
                continue
            st = run_stats(p)
            before = prom(raw / f"metrics-prefix-{mode}-c{c}-end.prom")
            start = prom(raw / f"metrics-prefix-{mode}-c{c}-start.prom")
            hits = (first(before, *HIT_NAMES) or 0) - (first(start, *HIT_NAMES) or 0)
            queries = (first(before, *QUERY_NAMES) or 0) - (first(start, *QUERY_NAMES) or 0)
            st["prefix_hits_tokens"] = hits
            st["prefix_queries_tokens"] = queries
            st["prefix_hit_rate"] = r(hits / queries, 3) if queries else 0.0
            pref[f"{mode}-c{c}"] = st
    summary["prefix_caching"] = {
        "workload": "shared prefix 1,536 tokens + 64 unique tokens per request; output 16 tokens; "
                    "c=1 (24 requests) and c=8 (48 requests); identical prompts in both modes",
        "results": pref}
    for c in (1, 8):
        a, b = pref.get(f"off-c{c}"), pref.get(f"on-c{c}")
        if a and b and a["ttft_ms_p50"] and b["ttft_ms_p50"]:
            summary["prefix_caching"][f"ttft_p50_speedup_c{c}"] = r(a["ttft_ms_p50"] / b["ttft_ms_p50"])

    # Step 4: capacity vs --gpu-memory-utilization (theory -> usable, Table 15.3a style)
    servers = {}
    for p in sorted(raw.glob("server-*.json")):
        name = p.stem[len("server-"):]
        servers[name] = server_info(raw, name)
    summary["servers"] = servers
    total_mib = None
    m = re.search(r",\s*(\d+) MiB", env.get("gpu") or "")
    if m:
        total_mib = int(m.group(1))
    total_b = total_mib * 2**20 if total_mib else None
    ws = [x["weights_gib"] for x in servers.values() if x.get("weights_gib")]
    weights_b = statistics.median(ws) * 2**30 if ws else None
    cap = {"gpu_total_bytes": total_b, "weights_bytes": weights_b, "rows": []}
    if total_b and weights_b:
        theo_tokens = (total_b - weights_b) / KV_BYTES_PER_TOKEN
        cap["theoretical_kv_tokens"] = int(theo_tokens)
        cap["theoretical_seqs_4096"] = int(theo_tokens // 4096)
        for name, s in sorted(servers.items(), key=lambda kv: kv[1].get("gpu_memory_utilization", 0)):
            if not name.startswith("util"):
                continue
            u = s["gpu_memory_utilization"]
            row = {"server": name, "gpu_memory_utilization": u, "started": s["started"]}
            frac_tokens = (total_b * u - weights_b) / KV_BYTES_PER_TOKEN
            row["after_fraction_kv_tokens"] = int(max(frac_tokens, 0))
            if s["started"] and s.get("kv_tokens"):
                kv = s["kv_tokens"]
                bs = s.get("block_size") or 16
                row.update(engine_kv_tokens=kv, engine_kv_gib=s.get("kv_memory_gib"),
                           runtime_reserve_gib=r((total_b * u - weights_b - kv * KV_BYTES_PER_TOKEN) / 2**30, 3),
                           seqs_4096=kv // 4096, seqs_4096_with_headroom=int(kv // 4096 * HEADROOM),
                           usable_over_theoretical=r(int(kv // 4096 * HEADROOM) / max(cap["theoretical_seqs_4096"], 1), 3),
                           seqs_pressure_1536=kv // (-(-PRESSURE_SEQ_TOKENS // bs) * bs),
                           free_at_startup_gib=s.get("free_at_startup_gib"),
                           non_torch_gib=r((s.get("weights_plus_non_torch_gib") or 0) - s["weights_gib"], 2)
                           if s.get("weights_plus_non_torch_gib") else None,
                           peak_activation_gib=s.get("peak_activation_gib"), cudagraph_gib=s.get("cudagraph_gib"))
            else:
                row["start_error"] = s.get("start_error")
            cap["rows"].append(row)
        # Table 15.3a walk for the 0.80 setting, with this GPU's measured numbers
        w = next((x for x in cap["rows"] if x["gpu_memory_utilization"] == 0.8 and x.get("engine_kv_tokens")), None)
        if w:
            naive = cap["theoretical_seqs_4096"]
            frac = int(w["after_fraction_kv_tokens"] // 4096)
            eng = w["seqs_4096"]
            cap["walk_util_0_80"] = [
                {"step": "Theoretical: GPU memory - weights", "kv_tokens": cap["theoretical_kv_tokens"], "seqs_4096": naive},
                {"step": "Memory fraction 0.80 (--gpu-memory-utilization)", "kv_tokens": w["after_fraction_kv_tokens"], "seqs_4096": frac},
                {"step": "Runtime reserve: non-torch + peak activation + CUDA graphs (engine profile)",
                 "kv_tokens": w["engine_kv_tokens"], "seqs_4096": eng, "reserve_gib": w["runtime_reserve_gib"]},
                {"step": "Block rounding (16-token blocks; 4,096 = 256 blocks exactly)", "kv_tokens": w["engine_kv_tokens"], "seqs_4096": eng},
                {"step": "Admission headroom: run at <= 90 % KV usage", "kv_tokens": int(w["engine_kv_tokens"] * HEADROOM),
                 "seqs_4096": w["seqs_4096_with_headroom"]},
            ]
            cap["usable_fraction_of_naive"] = r(w["seqs_4096_with_headroom"] / naive, 3)
            cap["book_table_15_3a_usable_fraction"] = round(140 / 186, 3)
    summary["capacity"] = cap
    c1 = summary["sweep"]["by_concurrency"].get("1", {})
    if weights_b and c1.get("tpot_ms_p50"):
        # every decode step at batch 1 reads all weights once (KV is small next to 3 GB of weights)
        summary["sweep"]["implied_weight_read_gb_per_s_c1"] = r(weights_b / (c1["tpot_ms_p50"] / 1000) / 1e9, 1)

    # Step 3: KV pressure and preemption at two memory settings
    pres = {}
    for p in sorted(raw.glob("load-pressure-u*.jsonl")):
        u = p.stem[len("load-pressure-u"):]
        st = run_stats(p)
        st.update(series_stats(raw / f"metrics-pressure-u{u}.jsonl"))
        pres[u] = st
    summary["pressure"] = {"workload": "32 concurrent clients, 64 requests, prompt 1,024 tokens, output 512 tokens "
                                       "(peak 32 x 1,536 = 49,152 tokens of KV demand)", "by_util": pres}

    # Step 5: --max-num-seqs
    mns = {}
    for p in sorted(raw.glob("load-mns*-c32.jsonl")):
        m_ = int(re.match(r"load-mns(\d+)-c32", p.stem).group(1))
        st = run_stats(p)
        st.update(series_stats(raw / f"metrics-mns{m_}-c32.jsonl"))
        srv = servers.get("base" if m_ == 64 else f"mns{m_}", {})
        st["engine_kv_tokens"] = srv.get("kv_tokens")
        mns[str(m_)] = st
    summary["max_num_seqs"] = {"workload": "32 concurrent clients, 96 requests, prompt uniform 256-1024, output 128; "
                                           "--gpu-memory-utilization 0.80", "by_max_num_seqs": mns}

    # Host memory during the run
    hm = raw / "hostmem.tsv"
    if hm.exists():
        rows = [ln.split("\t") for ln in hm.read_text().splitlines()[1:] if ln.strip()]
        summary["host_memory"] = {"min_available_mib": min(int(x[1]) for x in rows),
                                  "max_server_rss_mib": max(int(x[2]) for x in rows), "samples": len(rows)}
    el = raw / "elapsed_s"
    summary["elapsed_s"] = int(el.read_text()) if el.exists() else None

    (run / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (run / "report.md").write_text(report(summary, env))
    print(f"wrote {run / 'summary.json'} and {run / 'report.md'}")
    return 0


def report(s: dict, env: dict) -> str:
    M = "`[MEASURED]`"
    L = [f"# Chapter 15 hands-on: serve an LLM (run `{s['run_id']}`)", "",
         f"GPU: {env.get('gpu')}; kernel {env.get('kernel')}; captured {env.get('captured_at')}.",
         f"Tools: {'; '.join(f'{v}' for v in env.get('tools', {}).values())}.",
         f"KV-usage metric exposed by this vLLM: `{s.get('kv_metric_name')}`.", "",
         "## Step 1: latency and throughput against concurrency", "", s["sweep"]["workload"] + ".", "",
         "| C | TTFT p50 ms | TTFT p95 ms | TPOT p50 ms | ITL p50 ms | ITL p99 ms | output tok/s | req/s | peak KV % |",
         "|---|---|---|---|---|---|---|---|---|"]
    for c, x in s["sweep"]["by_concurrency"].items():
        L.append(f"| {c} | {x['ttft_ms_p50']} | {x['ttft_ms_p95']} | {x['tpot_ms_p50']} | {x['itl_ms_p50']} | "
                 f"{x['itl_ms_p99']} | {x['output_tok_per_s']} | {x['req_per_s']} | {x['kv_kv_usage_max_pct']} |")
    L += ["", f"All values {M} (step 1), median over repetitions. Weights / TPOT at C=1 = "
          f"{s['sweep'].get('implied_weight_read_gb_per_s_c1')} GB/s of weight reads per decode step (derived from {M} values).", "",
          "## Step 2: prefix caching off vs on", "", s["prefix_caching"]["workload"] + ".", "",
          "| Mode, C | TTFT p50 ms | TTFT p95 ms | prefix hit rate | output tok/s |", "|---|---|---|---|---|"]
    for k, x in s["prefix_caching"]["results"].items():
        L.append(f"| {k} | {x['ttft_ms_p50']} | {x['ttft_ms_p95']} | {x['prefix_hit_rate']} | {x['output_tok_per_s']} |")
    sp = [f"C={c}: {s['prefix_caching'].get(f'ttft_p50_speedup_c{c}')}x" for c in (1, 8)]
    L += ["", f"TTFT p50 speed-up from prefix caching: {', '.join(sp)} {M} (step 2).", "",
          "## Step 3: KV pressure and preemption", "", s["pressure"]["workload"] + ".", "",
          "| --gpu-memory-utilization | peak KV % | preemptions | max running | max waiting | TTFT p95 ms | ITL p99 ms | ITL max ms | output tok/s |",
          "|---|---|---|---|---|---|---|---|---|"]
    for u, x in s["pressure"]["by_util"].items():
        L.append(f"| {u} | {x['kv_usage_max_pct']} | {x['preemptions']} | {x['running_max']} | {x['waiting_max']} | "
                 f"{x['ttft_ms_p95']} | {x['itl_ms_p99']} | {x['itl_ms_max']} | {x['output_tok_per_s']} |")
    cap = s["capacity"]
    L += ["", f"All values {M} (step 3).", "", "## Step 4: KV capacity, theory against usable", "",
          f"KV bytes per token = 2 x {LAYERS} x {KV_HEADS} x {HEAD_DIM} x {KV_ELEM_BYTES} = {KV_BYTES_PER_TOKEN:,} B. "
          f"GPU memory {cap.get('gpu_total_bytes')} B; weights {cap.get('weights_bytes')} B (engine log) {M}.",
          f"Theoretical (all memory minus weights): {cap.get('theoretical_kv_tokens'):,} tokens = "
          f"{cap.get('theoretical_seqs_4096')} sequences of 4,096 tokens." if cap.get("theoretical_kv_tokens") else "", "",
          "| util | free at start GiB | after fraction, tokens | engine KV tokens | reserve GiB (non-torch / activation / graphs) | 4k seqs | with 90 % headroom | usable / theoretical |",
          "|---|---|---|---|---|---|---|---|"]
    for x in cap["rows"]:
        if x.get("engine_kv_tokens"):
            L.append(f"| {x['gpu_memory_utilization']} | {x.get('free_at_startup_gib')} | {x['after_fraction_kv_tokens']:,} | {x['engine_kv_tokens']:,} | "
                     f"{x['runtime_reserve_gib']} ({x.get('non_torch_gib')} / {x.get('peak_activation_gib')} / {x.get('cudagraph_gib')}) | "
                     f"{x['seqs_4096']} | {x['seqs_4096_with_headroom']} | {x['usable_over_theoretical']} |")
        else:
            L.append(f"| {x['gpu_memory_utilization']} | | {x['after_fraction_kv_tokens']:,} | refused to start: {str(x.get('start_error'))[:200]} | | | | |")
    if cap.get("walk_util_0_80"):
        L += ["", "Table 15.3a, walked on this GPU at --gpu-memory-utilization 0.80:", "",
              "| Step | KV tokens | 4k sequences |", "|---|---|---|"]
        for w in cap["walk_util_0_80"]:
            L.append(f"| {w['step']} | {w['kv_tokens']:,} | {w['seqs_4096']} |")
        L += ["", f"Usable / naive: {cap['usable_fraction_of_naive']} here; the chapter's TP = 4 FP8 replica: "
                  f"140 / 186 = {cap['book_table_15_3a_usable_fraction']} `[MODELED]`."]
    L += ["", f"Engine KV tokens and weights {M} (step 4, engine start-up log); the other columns are arithmetic on them.",
          "", "## Step 5: --max-num-seqs under the same 32-client load", "", s["max_num_seqs"]["workload"] + ".", "",
          "| --max-num-seqs | max running | max waiting | TTFT p50 ms | TTFT p95 ms | TPOT p50 ms | output tok/s | engine KV tokens |",
          "|---|---|---|---|---|---|---|---|"]
    for m_, x in sorted(s["max_num_seqs"]["by_max_num_seqs"].items(), key=lambda kv: int(kv[0])):
        L.append(f"| {m_} | {x['running_max']} | {x['waiting_max']} | {x['ttft_ms_p50']} | {x['ttft_ms_p95']} | "
                 f"{x['tpot_ms_p50']} | {x['output_tok_per_s']} | {x['engine_kv_tokens']} |")
    hm = s.get("host_memory", {})
    L += ["", f"All values {M} (step 5).", "", "## Host memory", "",
          f"Lowest MemAvailable during the run: {hm.get('min_available_mib')} MiB; largest server process-tree RSS: "
          f"{hm.get('max_server_rss_mib')} MiB {M}. Whole run: {s.get('elapsed_s')} s {M}.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
