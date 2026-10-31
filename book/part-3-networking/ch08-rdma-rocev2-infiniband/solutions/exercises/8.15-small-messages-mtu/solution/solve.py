"""8.15 — Which RDMA message sizes survive a leaf port left at MTU 1500 when the QP path MTU is 4,096.

Usage: python solve.py --out DIR

Packetizes each RDMA WRITE of the `ib_write_bw -a` sweep (2 B ... 8 MiB) at path MTU 4,096 and checks
every resulting IP packet (IPv4 20 + UDP 8 + BTH 12 [+ RETH 16 on the first/only packet] + payload +
ICRC 4) against the 1,500-byte port MTU. Also models ibv_rc_pingpong's defaults (4,096-byte SENDs,
path MTU 1,024: docs/VERIFIED_FACTS.md) and the DF ping probes. [MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

IPV4, UDP, BTH, RETH, ICRC = 20, 8, 12, 16, 4
PORT_MTU = 1500
KEY = {"last_passing_row": 1024, "only_1024_ip_b": 1084, "only_2048_ip_b": 2108, "pingpong_passes": True}


def packets(msg: int, path_mtu: int, first_ext: int) -> list[int]:
    """IP packet sizes of one message; first_ext = extra header bytes on the first packet (RETH for WRITE)."""
    sizes, left, first = [], msg, True
    while left > 0:
        pay = min(path_mtu, left)
        sizes.append(IPV4 + UDP + BTH + (first_ext if first else 0) + pay + ICRC)
        left -= pay
        first = False
    return sizes


def fits(msg: int, path_mtu: int, first_ext: int) -> bool:
    return max(packets(msg, path_mtu, first_ext)) <= PORT_MTU


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    sweep = [2 ** k for k in range(1, 24)]                     # perftest -a: 2 B ... 8 MiB (23 rows)
    rows = {m: {"largest_ip_packet_b": max(packets(m, 4096, RETH)), "passes": fits(m, 4096, RETH)} for m in sweep}
    passing = [m for m, r in rows.items() if r["passes"]]
    last_pass = max(passing)
    assert passing == [m for m in sweep if m <= 1024]           # every row up to 1,024 passes, none after
    pingpong = fits(4096, 1024, 0)                              # SEND has no RETH; default path MTU 1,024
    forced_1024 = all(fits(m, 1024, RETH) for m in sweep)       # discriminating test: ib_write_bw -m 1024
    ping = {"df_8972_b": 8972 + 28 <= PORT_MTU, "df_1472_b": 1472 + 28 <= PORT_MTU}

    assert last_pass == KEY["last_passing_row"]
    assert rows[1024]["largest_ip_packet_b"] == KEY["only_1024_ip_b"] and rows[2048]["largest_ip_packet_b"] == KEY["only_2048_ip_b"]
    assert pingpong is KEY["pingpong_passes"] and forced_1024 and ping == {"df_8972_b": False, "df_1472_b": True}
    assert rows[8192]["largest_ip_packet_b"] == 4156                    # 4,096-byte first packet with RETH

    result = {
        "exercise": "8.15", "evidence_label": "[MODELED]",
        "inputs": {"port_mtu_b": PORT_MTU, "qp_path_mtu_b": 4096, "headers_b": {"ipv4": IPV4, "udp": UDP, "bth": BTH, "reth": RETH, "icrc": ICRC}},
        "steps": {"sweep": {str(m): r for m, r in rows.items()}},
        "answer": {"last_passing_perftest_row_b": last_pass, "ibv_rc_pingpong_default_passes": pingpong,
                   "ib_write_bw_m1024_full_sweep_passes": forced_1024, "df_ping": ping},
        "units": "bytes", "tolerance": "exact",
    }
    table = "\n".join(f"| {m:,} | {r['largest_ip_packet_b']:,} | {'pass' if r['passes'] else 'dropped'} |"
                      for m, r in rows.items() if m <= 16384)
    md = f"""# 8.15 — result `[MODELED]`

Port MTU {PORT_MTU} B; QP path MTU 4,096; RDMA WRITE (RETH on the first packet).

| Message (B) | Largest IP packet (B) | At a 1,500-byte port |
|---|---|---|
{table}

- Last perftest row that completes: **{last_pass:,} B**; every larger size sends at least one packet > 1,500 B.
- `ibv_rc_pingpong` defaults (4,096 B SENDs at path MTU 1,024): largest packet {max(packets(4096, 1024, 0)):,} B → passes = {pingpong}.
- `ib_write_bw -m 1024`: full sweep passes = {forced_1024}; DF ping 8,972 B passes = {ping['df_8972_b']}, 1,472 B passes = {ping['df_1472_b']}.
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("8.15 ok")


if __name__ == "__main__":
    main()
