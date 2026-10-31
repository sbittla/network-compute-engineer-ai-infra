"""7.K1 — /31 vs /30 address consumption on ORION-256's point-to-point links.

Usage: python solve.py --out DIR

Counts the point-to-point links in the lab's intent dataset (lab/data/links.csv: 256 host links +
256 leaf-spine links) and the IPv4 addresses each prefix length consumes. [MODELED]
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
ADDRS_PER_PREFIX = {31: 2 ** (32 - 31), 30: 2 ** (32 - 30)}  # /31: both usable (RFC 3021); /30: net + 2 + bcast
KEY = {"links": 512, "slash31": 1024, "slash30": 2048}       # solutions/exercises-key.md 7.K1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    with (DATA / "links.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_type = Counter(r["link_type"] for r in rows)
    links = len(rows)
    use31 = links * ADDRS_PER_PREFIX[31]
    use30 = links * ADDRS_PER_PREFIX[30]

    # Every /31 in the dataset should carry exactly two host addresses, one per end.
    assert all(r["a_ip"].endswith("/31") and r["b_ip"].endswith("/31") for r in rows)
    assert links == KEY["links"] and by_type == {"host": 256, "fabric": 256}, (links, by_type)
    assert use31 == KEY["slash31"] and use30 == KEY["slash30"], (use31, use30)  # exact (tolerance 0)

    result = {
        "exercise": "7.K1", "evidence_label": "[MODELED]",
        "inputs": {"links_csv": "lab/data/links.csv", "host_links": by_type["host"], "fabric_links": by_type["fabric"]},
        "steps": {"addresses_per_slash31": ADDRS_PER_PREFIX[31], "addresses_per_slash30": ADDRS_PER_PREFIX[30]},
        "answer": {"links": links, "ipv4_addresses_slash31": use31, "ipv4_addresses_slash30": use30,
                   "rfc_ipv4_slash31": "RFC 3021", "rfc_ipv6_slash127": "RFC 6164", "ipv6_prefix_length": 127},
        "units": "IPv4 addresses", "tolerance": "exact",
    }
    md = f"""# 7.K1 — result `[MODELED]`

- Point-to-point links in `lab/data/links.csv`: {by_type['host']} host + {by_type['fabric']} fabric = **{links}**
- /31: {links} × {ADDRS_PER_PREFIX[31]} = **{use31:,} addresses** (RFC 3021)
- /30: {links} × {ADDRS_PER_PREFIX[30]} = **{use30:,} addresses**
- IPv6 equivalent: /127 (RFC 6164)
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("7.K1 ok:", use31, use30)


if __name__ == "__main__":
    main()
