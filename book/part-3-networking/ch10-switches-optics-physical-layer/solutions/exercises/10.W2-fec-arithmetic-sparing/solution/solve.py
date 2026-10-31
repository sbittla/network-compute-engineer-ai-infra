"""10.W2 — FEC arithmetic and Poisson sparing at ORION-XL scale.

Usage: python solve.py --out DIR      Evidence label: [MODELED] (inputs [ILLUSTRATIVE])
Inputs: prompt parameters of exercises.md 10.W2; method Sections 10.2.1, 10.4.3 and 10.12.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

PORT_GBPS = 800.0
LANES = 8
TRANSCODE = 257 / 256          # 256b/257b
FEC = 544 / 514                # RS(544,514)
CODEWORD_BITS = 544 * 10
BER = 2e-5
BER_LIMIT = 2.4e-4
SYMBOL_FACTOR = 10             # p ~= 10 x BER (prompt)
N_OPTICS = 16_384
AFR = 0.015
LEAD_DAYS = 21
TARGETS = (0.95, 0.99)
RATE_POLICY = 0.03


def poisson_cdf(k: int, lam: float) -> float:
    term, total = math.exp(-lam), 0.0
    for i in range(k + 1):
        if i:
            term *= lam / i
        total += term
    return total


def solve() -> dict:
    line = PORT_GBPS * TRANSCODE * FEC
    cw_rate = line * 1e9 / CODEWORD_BITS
    margin = math.log10(BER_LIMIT / BER)
    p = SYMBOL_FACTOR * BER
    p_any = 1 - math.exp(-544 * p)
    lam = N_OPTICS * AFR * LEAD_DAYS / 365
    table = {k: round(poisson_cdf(k, lam), 4) for k in range(16, 27)}
    spares = {}
    for tgt in TARGETS:
        k = 0
        while poisson_cdf(k, lam) < tgt:
            k += 1
        spares[f"{int(tgt * 100)}%"] = k
    normal99 = lam + 2.326 * math.sqrt(lam)
    rate_spares = math.ceil(N_OPTICS * RATE_POLICY)
    return {
        "inputs": {"port_gbps": PORT_GBPS, "lanes": LANES, "ber": BER, "ber_limit": BER_LIMIT,
                   "optics": N_OPTICS, "afr": AFR, "lead_days": LEAD_DAYS, "rate_policy": RATE_POLICY},
        "a": {"overhead_factor": round(TRANSCODE * FEC, 6), "line_rate_gbps": round(line, 3),
              "lane_rate_gbps": round(line / LANES, 3), "codewords_per_s": round(cw_rate, 0)},
        "b": {"margin_decades": round(margin, 3), "symbol_error_p": p, "544p": round(544 * p, 4),
              "p_codeword_has_error": round(p_any, 4),
              "corrected_codewords_per_s": round(p_any * cw_rate, -4)},
        "c": {"lambda": round(lam, 3), "cdf": table, "spares": spares,
              "normal_approx_99": round(normal99, 2)},
        "d": {"rate_based_spares": rate_spares, "raw": round(N_OPTICS * RATE_POLICY, 2)},
        "units": {"line_rate": "Gb/s", "codewords": "codewords/s", "margin": "decades", "spares": "modules"},
        "evidence_label": "[MODELED]",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    r = solve()
    # Answer key 10.W2: 850 Gb/s, 156.25e6 CW/s; 1.08 decades, 0.103; lambda 14.14, 21 and 24 spares; 492.
    assert abs(r["a"]["line_rate_gbps"] - 850.0) < 1e-6
    assert abs(r["a"]["codewords_per_s"] - 156.25e6) < 1.0
    assert abs(r["b"]["margin_decades"] - 1.08) < 0.005 and abs(r["b"]["p_codeword_has_error"] - 0.103) < 0.001
    assert abs(r["c"]["lambda"] - 14.14) < 0.01
    assert r["c"]["spares"] == {"95%": 21, "99%": 24}
    assert abs(r["c"]["cdf"][23] - 0.9896) < 0.0005          # just misses 99 %, as the key says
    assert r["d"]["rate_based_spares"] == 492
    (out / "result.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    a, b, c, d = r["a"], r["b"], r["c"], r["d"]
    rows = " | ".join(str(k) for k in range(18, 25))
    vals = " | ".join(f"{c['cdf'][k]:.3f}" for k in range(18, 25))
    md = f"""# 10.W2 — FEC arithmetic and sparing `[MODELED]`

## (a)
line rate = {PORT_GBPS:.0f} x (257/256) x (544/514) = {PORT_GBPS:.0f} x {a['overhead_factor']} = {a['line_rate_gbps']} Gb/s
({LANES} lanes x {a['lane_rate_gbps']} Gb/s); codewords = {a['line_rate_gbps']}e9 / {CODEWORD_BITS} = {a['codewords_per_s']:,.0f} /s

## (b)
margin = log10({BER_LIMIT} / {BER}) = {b['margin_decades']} decades; p = {b['symbol_error_p']}; 544p = {b['544p']};
P(>=1) = 1 - e^(-{b['544p']}) = {b['p_codeword_has_error']} (about {b['corrected_codewords_per_s']:,.0f} corrected CW/s)

## (c)
lambda = {N_OPTICS} x {AFR} x {LEAD_DAYS}/365 = {c['lambda']}

| k | {rows} |
|---|---|---|---|---|---|---|---|
| P(X <= k) | {vals} |

spares: >= 95 % -> {c['spares']['95%']}; >= 99 % -> {c['spares']['99%']} (normal approx. {c['normal_approx_99']})

## (d)
rate-based: ceil({N_OPTICS} x {RATE_POLICY}) = ceil({d['raw']}) = {d['rate_based_spares']}
"""
    (out / "result.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
