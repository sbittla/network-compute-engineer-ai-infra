"""13.7 -- One pipeline message (8.39 MB) with and without GPUDirect RDMA. [MODELED]

Usage: python solve.py --out DIR
Inputs: the prompt (M/t = 67.1 MB / 8; 45 GB/s effective NIC; 50 GB/s per staging copy) and the
copy/crossing counts of Table 13.2 (manuscript Section 13.4).
"""
import argparse
import json
from pathlib import Path

MSG_BYTES = 67.1e6 / 8    # M/t
NIC_BPS = 45e9            # effective NIC, B/s
COPY_BPS = 50e9           # per staging copy, B/s
FIXED_S = 10e-6           # [ILLUSTRATIVE] NCCL-hop fixed cost (Section 13.4)

PATHS = {
    # path: (host-DRAM copies, PCIe transfers)  -- Table 13.2
    "gdr": (0, 2),
    "host_staged": (2, 4),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    t_wire = MSG_BYTES / NIC_BPS
    t_copy = MSG_BYTES / COPY_BPS
    rows = {}
    for name, (copies, pcie) in PATHS.items():
        # unpipelined: each host copy is a serial stage before/after the wire transfer
        t = t_wire + copies * t_copy
        rows[name] = {"host_copies": copies, "pcie_transfers": pcie,
                      "pcie_MB": round(pcie * MSG_BYTES / 1e6, 2), "time_us": round(t * 1e6, 1)}
    # Key 13.7: 16.8 MB / 186 µs (GDR); 33.6 MB / 522 µs unpipelined bound (host-staged).
    assert abs(MSG_BYTES / 1e6 - 8.39) < 0.01
    assert abs(rows["gdr"]["pcie_MB"] - 16.8) < 0.05 and abs(rows["gdr"]["time_us"] - 186) < 1
    assert abs(4 * MSG_BYTES / 1e6 - 33.6) < 0.1
    assert abs(rows["host_staged"]["time_us"] - 522) < 1.5, rows

    result = {
        "inputs": {"msg_bytes": round(MSG_BYTES), "nic_Bps": NIC_BPS, "copy_Bps": COPY_BPS},
        "steps": {"t_wire_us": round(t_wire * 1e6, 1), "t_copy_us": round(t_copy * 1e6, 1),
                  "gdr_with_fixed_us": round((t_wire + FIXED_S) * 1e6, 1)},
        "answer": rows,
        "units": {"pcie_MB": "MB (1e6 B)", "time_us": "microseconds"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# 13.7 result `[MODELED]`", "",
             f"Message S = 67.1 MB / 8 = {MSG_BYTES/1e6:.2f} MB", "",
             "| Path | Host copies | PCIe transfers | PCIe bytes | Time |", "|---|---|---|---|---|"]
    for name, r in rows.items():
        lines.append(f"| {name} | {r['host_copies']} | {r['pcie_transfers']} | {r['pcie_MB']} MB | {r['time_us']} µs |")
    lines += ["", f"GDR: {MSG_BYTES:.3e} B / {NIC_BPS:.0e} B/s = {t_wire*1e6:.1f} µs (+ ≈ 10 µs fixed)",
              f"Host-staged unpipelined bound: {t_copy*1e6:.1f} + {t_wire*1e6:.1f} + {t_copy*1e6:.1f} = "
              f"{rows['host_staged']['time_us']} µs", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
