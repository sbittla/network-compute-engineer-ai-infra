#!/usr/bin/env python3
"""Closed-loop streaming load generator for an OpenAI-compatible completions endpoint (Chapter 15 lab).

Each of C workers sends requests back to back until N requests have finished. Prompts are lists of token
IDs, so prompt length is exact; output length is fixed with max_tokens = min_tokens and ignore_eos, so
every request decodes exactly the stated number of tokens. Streaming (server-sent events) gives the time
of every chunk, hence TTFT and every inter-token gap.

    python loadgen.py --url http://127.0.0.1:18015 --model ch15-qwen --concurrency 8 --num-requests 32 \
        --prompt-min 256 --prompt-max 1024 --output-tokens 128 --out run.jsonl

Shared-prefix mode (--shared-prefix P --suffix S): every prompt is the same P random tokens followed by S
tokens unique to the request, which is the workload prefix caching is built for.

One JSON object per request is written to --out; the last line is a {"kind": "run"} record with the
configuration and wall time. Needs aiohttp (installed with vLLM).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import time

import aiohttp

VOCAB_LO, VOCAB_HI = 1000, 30000  # ordinary BPE tokens of the Qwen2.5 vocabulary; no special tokens


def make_prompts(a: argparse.Namespace) -> list[list[int]]:
    rng = random.Random(a.seed)
    prompts = []
    if a.shared_prefix:
        prefix = [rng.randrange(VOCAB_LO, VOCAB_HI) for _ in range(a.shared_prefix)]
        for _ in range(a.num_requests):
            prompts.append(prefix + [rng.randrange(VOCAB_LO, VOCAB_HI) for _ in range(a.suffix)])
    else:
        for _ in range(a.num_requests):
            n = rng.randint(a.prompt_min, a.prompt_max)
            prompts.append([rng.randrange(VOCAB_LO, VOCAB_HI) for _ in range(n)])
    return prompts


async def one(session: aiohttp.ClientSession, a: argparse.Namespace, rid: int, prompt: list[int], t0: float) -> dict:
    body = {
        "model": a.model, "prompt": prompt, "max_tokens": a.output_tokens, "min_tokens": a.output_tokens,
        "ignore_eos": True, "temperature": 0.0, "stream": True,
        "stream_options": {"include_usage": True},
    }
    rec = {"kind": "request", "id": rid, "prompt_len": len(prompt), "start_s": time.perf_counter() - t0}
    chunk_t: list[float] = []
    usage = None
    start = time.perf_counter()
    try:
        async with session.post(f"{a.url}/v1/completions", json=body) as resp:
            if resp.status != 200:
                rec["error"] = f"HTTP {resp.status}: {(await resp.text())[:200]}"
                return rec
            buf = b""
            async for raw in resp.content:
                buf += raw
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line.startswith(b"data:"):
                        continue
                    data = line[5:].strip()
                    if data == b"[DONE]":
                        continue
                    msg = json.loads(data)
                    if msg.get("usage"):
                        usage = msg["usage"]
                    ch = msg.get("choices") or []
                    if ch and ch[0].get("text"):
                        chunk_t.append(time.perf_counter() - start)
    except Exception as e:  # noqa: BLE001 - record and continue; the analysis counts errors
        rec["error"] = f"{type(e).__name__}: {e}"
        return rec
    end = time.perf_counter() - start
    rec.update(e2e_s=end, chunks=len(chunk_t))
    if chunk_t:
        rec["ttft_s"] = chunk_t[0]
        rec["gaps_ms"] = [round((b - c) * 1000, 3) for c, b in zip(chunk_t, chunk_t[1:])]
    if usage:
        rec["prompt_tokens"] = usage.get("prompt_tokens")
        rec["completion_tokens"] = usage.get("completion_tokens")
        n = rec["completion_tokens"] or 0
        if n > 1 and chunk_t:
            rec["tpot_ms"] = (chunk_t[-1] - chunk_t[0]) / (n - 1) * 1000
    return rec


async def main_async(a: argparse.Namespace) -> None:
    prompts = make_prompts(a)
    queue: asyncio.Queue[int] = asyncio.Queue()
    for i in range(len(prompts)):
        queue.put_nowait(i)
    results: list[dict] = []
    timeout = aiohttp.ClientTimeout(total=a.timeout)
    conn = aiohttp.TCPConnector(limit=a.concurrency)
    async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
        t0 = time.perf_counter()

        async def worker() -> None:
            while True:
                try:
                    i = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                results.append(await one(session, a, i, prompts[i], t0))

        await asyncio.gather(*(worker() for _ in range(a.concurrency)))
        wall = time.perf_counter() - t0
    with open(a.out, "w") as f:
        for r in sorted(results, key=lambda r: r["id"]):
            f.write(json.dumps(r) + "\n")
        f.write(json.dumps({"kind": "run", "label": a.label, "concurrency": a.concurrency,
                            "num_requests": a.num_requests, "prompt_min": a.prompt_min, "prompt_max": a.prompt_max,
                            "shared_prefix": a.shared_prefix, "suffix": a.suffix,
                            "output_tokens": a.output_tokens, "seed": a.seed, "wall_s": wall}) + "\n")
    ok = [r for r in results if "error" not in r]
    toks = sum(r.get("completion_tokens") or 0 for r in ok)
    print(f"{a.label}: c={a.concurrency} n={len(results)} errors={len(results) - len(ok)} "
          f"wall={wall:.2f}s out_tok/s={toks / wall:.1f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://127.0.0.1:18015")
    ap.add_argument("--model", default="ch15-qwen")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--num-requests", type=int, default=16)
    ap.add_argument("--prompt-min", type=int, default=256)
    ap.add_argument("--prompt-max", type=int, default=1024)
    ap.add_argument("--output-tokens", type=int, default=128)
    ap.add_argument("--shared-prefix", type=int, default=0)
    ap.add_argument("--suffix", type=int, default=64)
    ap.add_argument("--seed", type=int, default=15)
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--label", default="run")
    ap.add_argument("--out", required=True)
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
