"""10.K3 — RS(544,514) parameters, derived from n, k and the symbol size.

Usage: python solve.py --out DIR      Evidence label: [MODELED]
Inputs: RS(544,514) over GF(2^10) (IEEE 802.3 clause 91 "KP4"; manuscript Section 10.4.2).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

N_SYMBOLS = 544      # codeword length in symbols (prompt)
K_SYMBOLS = 514      # data symbols (prompt)
SYMBOL_BITS = 10     # GF(2^10) symbols (Section 10.4.2)


def solve() -> dict:
    parity = N_SYMBOLS - K_SYMBOLS
    t = parity // 2                      # RS corrects floor((n-k)/2) symbol errors
    codeword_bits = N_SYMBOLS * SYMBOL_BITS
    data_bits = K_SYMBOLS * SYMBOL_BITS
    return {
        "inputs": {"n": N_SYMBOLS, "k": K_SYMBOLS, "symbol_bits": SYMBOL_BITS},
        "steps": {
            "parity_symbols": f"n - k = {N_SYMBOLS} - {K_SYMBOLS} = {parity}",
            "correctable": f"t = (n - k) / 2 = {parity} / 2 = {t}",
            "codeword_bits": f"n x m = {N_SYMBOLS} x {SYMBOL_BITS} = {codeword_bits}",
            "data_bits": f"k x m = {K_SYMBOLS} x {SYMBOL_BITS} = {data_bits}",
            "code_rate": round(K_SYMBOLS / N_SYMBOLS, 4),
        },
        "answer": {"symbol_bits": SYMBOL_BITS, "symbols_per_codeword": N_SYMBOLS,
                   "parity_symbols": parity, "correctable_symbols": t, "codeword_bits": codeword_bits,
                   "uncorrectable_at_symbols": t + 1},
        "units": {"symbol_bits": "bit", "codeword_bits": "bit", "others": "symbols"},
        "evidence_label": "[MODELED]",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    r = solve()
    a = r["answer"]
    # Answer key (solutions/exercises-key.md, 10.K3): 10-bit, 544, 30, 15, 5,440 bits. Exact integers.
    assert (a["symbol_bits"], a["symbols_per_codeword"], a["parity_symbols"],
            a["correctable_symbols"], a["codeword_bits"]) == (10, 544, 30, 15, 5440)
    (out / "result.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# 10.K3 — RS(544,514) parameters `[MODELED]`", "",
          "| Parameter | Working | Value |", "|---|---|---|",
          f"| Symbol size | GF(2^10) | {a['symbol_bits']} bits |",
          f"| Symbols per codeword | n | {a['symbols_per_codeword']} |",
          f"| Parity symbols | {r['steps']['parity_symbols']} | {a['parity_symbols']} |",
          f"| Correctable symbols | {r['steps']['correctable']} | {a['correctable_symbols']} |",
          f"| Codeword size | {r['steps']['codeword_bits']} | {a['codeword_bits']:,} bits |", "",
          f"A codeword with {a['uncorrectable_at_symbols']} or more bad symbols is uncorrectable.", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
