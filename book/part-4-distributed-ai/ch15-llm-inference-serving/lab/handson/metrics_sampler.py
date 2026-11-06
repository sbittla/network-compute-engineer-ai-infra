#!/usr/bin/env python3
"""Poll a vLLM /metrics endpoint and record the KV cache and scheduler series (Chapter 15 lab).

    python3 metrics_sampler.py --url http://127.0.0.1:18015 --out kv.jsonl --interval 0.25 --duration 120
    python3 metrics_sampler.py --url http://127.0.0.1:18015 --snapshot snap.prom      # one raw scrape

Metric names changed across vLLM releases: KV usage is vllm:kv_cache_usage_perc in current releases and
vllm:gpu_cache_usage_perc in older ones. The sampler records whichever the server exposes, under the
key it was found with, and the analysis falls back from the new name to the old one. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request

KEEP = re.compile(r"^vllm:(kv_cache_usage_perc|gpu_cache_usage_perc|num_requests_running|num_requests_waiting|"
                  r"num_preemptions(_total)?|prefix_cache_(queries|hits)(_total)?|"
                  r"gpu_prefix_cache_(queries|hits)(_total)?|prompt_tokens_total|generation_tokens_total)$")
LINE = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+(\S+)")


def scrape(url: str) -> str:
    with urllib.request.urlopen(f"{url}/metrics", timeout=5) as r:
        return r.read().decode()


def parse(text: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        m = LINE.match(line)
        if m and KEEP.match(m.group(1)):
            try:
                out[m.group(1)] = out.get(m.group(1), 0.0) + float(m.group(3))
            except ValueError:
                pass
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://127.0.0.1:18015")
    ap.add_argument("--out")
    ap.add_argument("--snapshot")
    ap.add_argument("--interval", type=float, default=0.25)
    ap.add_argument("--duration", type=float, default=600)
    a = ap.parse_args()
    if a.snapshot:
        open(a.snapshot, "w").write(scrape(a.url))
        return
    t0 = time.time()
    with open(a.out, "w") as f:
        while time.time() - t0 < a.duration:
            try:
                rec = {"t": round(time.time() - t0, 3), **parse(scrape(a.url))}
            except Exception as e:  # noqa: BLE001 - the server may be going away at the end of a phase
                rec = {"t": round(time.time() - t0, 3), "error": str(e)}
            f.write(json.dumps(rec) + "\n")
            f.flush()
            time.sleep(a.interval)


if __name__ == "__main__":
    main()
