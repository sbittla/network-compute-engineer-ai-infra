"""7.K5 — Hash polarization when leaf and spine both use h mod n.

Usage: python solve.py --out DIR

Leaf: uplink i = h mod 32, uplink i goes to orion-be-spine-(i mod 4 + 1) (manuscript Section 7.6).
Spine: picks downstream link k = h mod 8 among its 8 links to the destination leaf (same function).
Enumerates every hash value in one full period (lcm(32, 8) = 32; we sweep 2**16 values to show the
pattern does not depend on the range) and records which spine links ever carry traffic. [MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LEAF_UPLINKS = 32
SPINES = 4
SPINE_LINKS_PER_LEAF = 8
HASH_SWEEP = 2 ** 16
KEY = {1: [0, 4], 2: [1, 5], 3: [2, 6], 4: [3, 7]}   # solutions/exercises-key.md 7.K5


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    used: dict[int, set[int]] = {s: set() for s in range(1, SPINES + 1)}
    for h in range(HASH_SWEEP):
        uplink = h % LEAF_UPLINKS
        spine = uplink % SPINES + 1
        used[spine].add(h % SPINE_LINKS_PER_LEAF)
    sets = {s: sorted(v) for s, v in used.items()}
    share = {s: len(v) / SPINE_LINKS_PER_LEAF for s, v in sets.items()}

    assert sets == KEY, sets                      # exact link sets
    assert all(abs(x - 0.25) < 1e-12 for x in share.values())

    result = {
        "exercise": "7.K5", "evidence_label": "[MODELED]",
        "inputs": {"leaf_uplinks": LEAF_UPLINKS, "spines": SPINES, "spine_links_per_dest_leaf": SPINE_LINKS_PER_LEAF,
                   "hash_values_swept": HASH_SWEEP},
        "steps": {"spine_s_receives": "h mod 4 = s - 1", "since_4_divides_8": "h mod 8 in {s - 1, s + 3}"},
        "answer": {"links_used_per_spine": {f"orion-be-spine-{s}": v for s, v in sets.items()},
                   "fraction_of_links_used": round(share[1], 4)},
        "units": "link index k (0-7)", "tolerance": "exact",
    }
    rows = "\n".join(f"| orion-be-spine-{s} | {v} | {len(v)} of {SPINE_LINKS_PER_LEAF} |" for s, v in sets.items())
    md = f"""# 7.K5 — result `[MODELED]`

Swept h = 0 … {HASH_SWEEP - 1}; leaf picks h mod 32, spine picks h mod 8.

| Spine | Links k used toward a destination leaf | Share |
|---|---|---|
{rows}

Each spine uses **25 %** of its downstream links; 6 of 8 stay idle.
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("7.K5 ok:", sets)


if __name__ == "__main__":
    main()
