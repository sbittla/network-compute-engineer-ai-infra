#!/usr/bin/env python3
"""Generate the Capstone B telemetry bundle for the ORION-256 backend fabric.

A 30-minute capture (2026-10-12 10:00–10:30 UTC) of a rail-optimized RoCEv2 fabric running W-TRAIN on the default
24-node training partition (n01-n24) while n25-n32 serve inference:
  leaf_cli/orion-be-leaf-rN.txt.gz   8 rail leaves, CLI-text counter tables, polled every ~60 s
  spine_stream.jsonl.gz           4 spines, streaming-telemetry-style JSON lines, every ~60 s
  nic/orion-nNN.txt.gz         32 hosts x 8 NICs, `ethtool -S` + RDMA hw_counters, every ~120 s
  topology.csv                    every backend link (leaf port <-> NIC, leaf uplink <-> spine port)
  device_profiles.yaml            per-platform formats, timestamp encodings, counter widths
  maintenance.yaml                change calendar for the capture window
  ground_truth.sha256             SHA-256 of the injected-fault keys (scoring without revealing them)

All values are [SIMULATED]: a counter generator driven by a simple traffic model. It does not model
switch-buffer dynamics, PFC/ECN control loops, or NIC firmware behaviour. Counter names on the NIC side
follow the mlx5 driver's ethtool and RDMA hw_counters naming; switch-side names are vendor-neutral.

Re-running produces byte-identical files (seeded RNG; gzip mtime fixed at 0).

Usage:
    python tools/generate_data.py [--out ../data] [--seed 4242]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

T0 = datetime(2026, 10, 12, 10, 0, 0, tzinfo=timezone.utc)
EPOCH0 = int(T0.timestamp())
MINUTES = 30
N_HOSTS, N_RAILS, N_SPINES = 32, 8, 4
GB = 1e9
U32 = 2**32
N_TRAIN = 24          # default split (REFERENCE_CLUSTER): n01-n24 training, n25-n32 inference
INFER_SCALE = 2 / 30  # inference nodes carry ~2 GB/s per backend NIC [ILLUSTRATIVE]
FEC_BASE = 1.5e5      # healthy 400G PAM4 links still correct ~1e5 codewords/s [ILLUSTRATIVE]
NIC_INIT_RANGE = {  # plausible "since boot" starting values per NIC counter
    "rxb": (1e13, 9e13), "txb": (1e13, 9e13), "rxp": (1e5, 1e8), "txp": (1e5, 1e8),
    "disc": (0, 40), "crc": (0, 5), "cnp_s": (1e8, 1e10), "cnp_h": (1e8, 1e10), "ecn": (1e8, 1e10),
    "oos": (0, 2000), "lat": (0, 3),
}

LEAF_COLS = ["InOctets", "OutOctets", "InDiscards", "OutDiscards", "FCSErrors", "FECCorrected",
             "FECUncorr", "RxPause3", "TxPause3", "EcnMarked3"]


def leaf(r: int) -> str:
    return f"orion-be-leaf-r{r}"


def host(n: int) -> str:
    return f"orion-n{n + 1:02d}"


def spine(j: int) -> str:
    return f"orion-be-spine-{j + 1}"


def uplink_port(j: int, k: int) -> str:      # leaf side: uplink k (0..7) to spine j
    return f"Ethernet1/{33 + j * 8 + k}"


def spine_port(r: int, k: int) -> str:       # spine side: link k from leaf r
    return f"Ethernet1/{r * 8 + k + 1}"


class Model:
    """Per-minute rates (units per second) for every switch port and NIC, then cumulative counters."""

    def __init__(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)
        rng = self.rng
        M = MINUTES
        # ---- leaf host ports: rates[leaf r][port n][counter] -> array(M)
        self.leaf_rates: dict[tuple[int, str], dict[str, np.ndarray]] = {}
        for r in range(N_RAILS):
            for n in range(N_HOSTS):
                base_tx = 30 * GB * (1 + 0.04 * rng.standard_normal(M))  # host -> leaf (InOctets)
                base_rx = 30 * GB * (1 + 0.04 * rng.standard_normal(M))  # leaf -> host (OutOctets)
                d = {
                    "InOctets": base_tx, "OutOctets": base_rx,
                    "InDiscards": np.zeros(M), "OutDiscards": np.abs(0.02 * rng.standard_normal(M)),
                    "FCSErrors": np.zeros(M),
                    "FECCorrected": FEC_BASE * (1 + 0.2 * rng.standard_normal(M)).clip(0.2),
                    "FECUncorr": np.zeros(M),
                    "RxPause3": 3 * (1 + 0.3 * rng.standard_normal(M)).clip(0.1),
                    "TxPause3": 3 * (1 + 0.3 * rng.standard_normal(M)).clip(0.1),
                    "EcnMarked3": 3000 * (1 + 0.2 * rng.standard_normal(M)).clip(0.2),
                }
                if n >= N_TRAIN:   # inference nodes orion-n25..n32: light backend traffic, little congestion
                    for c in ("InOctets", "OutOctets"):
                        d[c] = d[c] * INFER_SCALE
                    d["EcnMarked3"] = d["EcnMarked3"] * 0.03
                self.leaf_rates[(r, f"Ethernet1/{n + 1}")] = d
            for j in range(N_SPINES):
                for k in range(8):
                    d = {
                        "InOctets": 5 * GB * (1 + 0.08 * rng.standard_normal(M)),
                        "OutOctets": 5 * GB * (1 + 0.08 * rng.standard_normal(M)),
                        "InDiscards": np.zeros(M), "OutDiscards": np.zeros(M), "FCSErrors": np.zeros(M),
                        "FECCorrected": FEC_BASE * (1 + 0.2 * rng.standard_normal(M)).clip(0.2),
                        "FECUncorr": np.zeros(M),
                        "RxPause3": 1 * (1 + 0.3 * rng.standard_normal(M)).clip(0.1),
                        "TxPause3": 1 * (1 + 0.3 * rng.standard_normal(M)).clip(0.1),
                        "EcnMarked3": 400 * (1 + 0.2 * rng.standard_normal(M)).clip(0.2),
                    }
                    self.leaf_rates[(r, uplink_port(j, k))] = d
        self._inject()

    # Minute index m covers [m*60, (m+1)*60) and shows up in the poll at minute m+1.
    def _inject(self) -> None:
        rng = self.rng
        M = MINUTES
        L = self.leaf_rates
        # ---- F3: ECN marking disabled on leaf r6 for the whole capture -> PFC does the work
        for p, d in ((p, d) for (r, p), d in L.items() if r == 6):
            d["EcnMarked3"][:] = 0
            if int(p.split("/")[1]) <= 32:
                d["RxPause3"] *= 50
                d["TxPause3"] *= 130
            else:
                d["TxPause3"] *= 40
        # ---- benign: synchronized burst (checkpoint all-gather) during minute 11 on every W-TRAIN host port
        for r in range(N_RAILS):
            for n in range(N_TRAIN):
                L[(r, f"Ethernet1/{n + 1}")]["RxPause3"][11] = 15000 * (1 + 0.1 * rng.random())
                L[(r, f"Ethernet1/{n + 1}")]["TxPause3"][11] = 2000 * (1 + 0.1 * rng.random())
                L[(r, f"Ethernet1/{n + 1}")]["EcnMarked3"][11] *= 20
        # ---- F1: stuck receiver on orion-n17 rail 5 from minute 15: NIC transmits pause continuously
        p17 = L[(5, "Ethernet1/17")]
        p17["RxPause3"][15:] = 50000 * (1 + 0.05 * rng.standard_normal(M - 15))
        p17["OutOctets"][15:] = 0.02 * GB
        p17["InOctets"][15:] *= 0.3
        for n in range(N_HOSTS):
            if n == 16:
                continue
            d = L[(5, f"Ethernet1/{n + 1}")]
            d["TxPause3"][15:] = 2500 * (1 + 0.1 * rng.standard_normal(M - 15))   # HoL spreading (symptom)
            d["InOctets"][15:] *= 0.45
            d["OutOctets"][15:] *= 0.45
        for j in range(N_SPINES):
            for k in range(8):
                L[(5, uplink_port(j, k))]["TxPause3"][15:] = 600 * (1 + 0.1 * rng.standard_normal(M - 15))
        # ---- F4: ECMP polarization on leaf r1 uplinks (whole capture), drops on the hot links
        weights = np.ones(32)
        hot = [3, 11, 19, 27]
        cold = [0, 5, 9, 14, 22, 30]
        weights[hot] = 3.2
        weights[cold] = 0.15
        weights *= 32 / weights.sum()
        for idx in range(32):
            j, k = divmod(idx, 8)
            d = L[(1, uplink_port(j, k))]
            d["OutOctets"] = d["OutOctets"] * weights[idx]
            if idx in hot:
                d["OutDiscards"] = 800 * (1 + 0.2 * rng.standard_normal(M)).clip(0.1)
        # ---- F2: degrading receive path on leaf r2 Ethernet1/50 (uplink to spine 3, k=1)
        p = L[(2, "Ethernet1/50")]
        ramp = np.zeros(M)
        ramp[4:] = np.geomspace(1e5, 3e7, M - 4)       # pre-FEC errors climbing: corrected codewords trend up
        p["FECCorrected"] = p["FECCorrected"] + ramp
        p["FCSErrors"][18:] = 5 + 45 * rng.random(M - 18)
        p["FECUncorr"][20:] = 1 + 4 * rng.random(M - 20)
        # ---- benign one-off FCS glitches (single interval) on three random switch ports
        self.glitches = []
        for _ in range(3):
            r = int(rng.integers(0, N_RAILS))
            n = int(rng.integers(0, N_HOSTS))
            m = int(rng.integers(2, M - 2))
            L[(r, f"Ethernet1/{n + 1}")]["FCSErrors"][m] = 1 / 60
            self.glitches.append((leaf(r), f"Ethernet1/{n + 1}", m + 1))
        # ---- benign: planned reboot of orion-n30 during minute 16: its 8 leaf ports carry nothing
        for r in range(N_RAILS):
            d = L[(r, "Ethernet1/30")]
            d["InOctets"][16] = 0.0
            d["OutOctets"][16] = 0.0
        # ---- benign: leaf r7 maintenance, optic swap on two uplinks, minutes 19-23 admin-down
        for port in ("Ethernet1/41", "Ethernet1/42"):
            d = L[(7, port)]
            for c in ("InOctets", "OutOctets", "EcnMarked3", "FECCorrected", "RxPause3", "TxPause3"):
                d[c][19:24] = 0.0

    # ---------------------------------------------------------------------------------------------
    def cumulative(self, rates: np.ndarray, t: float, initial: float, reset_at: float | None = None) -> float:
        """Integrate a per-minute piecewise-constant rate from 0 (or from reset_at) to time t (s)."""
        start = 0.0 if reset_at is None or t < reset_at else reset_at
        base = initial if reset_at is None or t < reset_at else 0.0
        total = 0.0
        m0 = int(start // 60)
        for m in range(m0, MINUTES):
            lo, hi = max(m * 60.0, start), min((m + 1) * 60.0, t)
            if hi <= lo:
                if m * 60.0 >= t:
                    break
                continue
            total += rates[m] * (hi - lo)
        return base + total


def gz_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0, compresslevel=9) as f:
        f.write(text.encode("utf-8"))
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    ap.add_argument("--seed", type=int, default=4242)
    args = ap.parse_args()
    out: Path = args.out
    (out / "leaf_cli").mkdir(parents=True, exist_ok=True)
    (out / "nic").mkdir(parents=True, exist_ok=True)
    model = Model(args.seed)
    rng = np.random.default_rng(args.seed + 1)
    L = model.leaf_rates

    # Initial counter values (accumulated since boot / last clear)
    init: dict[tuple, float] = {}
    for key, d in L.items():
        for c in d:
            if c in ("InOctets", "OutOctets"):
                init[key + (c,)] = float(rng.uniform(1e14, 9e14))
            elif c in ("RxPause3", "TxPause3"):
                init[key + (c,)] = float(rng.uniform(1e6, 2e9))
            elif c in ("FECCorrected", "EcnMarked3"):
                init[key + (c,)] = float(rng.uniform(1e8, 1e11))
            else:
                init[key + (c,)] = float(rng.integers(0, 50))
    init[(4, "Ethernet1/7", "TxPause3")] = 4_294_964_000.0      # 32-bit pause counter about to wrap

    # Poll times (seconds after T0)
    leaf_t = {r: [k * 60 + 1 + float(rng.uniform(0, 2)) for k in range(MINUTES + 1)] for r in range(N_RAILS)}
    spine_t = {j: [k * 60 + 2 + float(rng.uniform(0, 2)) for k in range(MINUTES + 1)] for j in range(N_SPINES)}
    nic_t = {n: [k * 120 + 3 + float(rng.uniform(0, 3)) for k in range(MINUTES // 2 + 1)] for n in range(N_HOSTS)}
    leaf7_clear = 19 * 60 + 30.0            # operator clears counters on leaf r7 during maintenance
    spine2_clear = 16 * 60 + 40.0           # unplanned "clear counters" on spine-2 (operator habit)
    host30_reboot = 16 * 60 + 20.0          # NIC counters restart from zero after the planned reboot

    def iso(t: float) -> str:
        return datetime.fromtimestamp(EPOCH0 + t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ---- leaf CLI text
    for r in range(N_RAILS):
        lines = []
        ports = [f"Ethernet1/{i}" for i in range(1, 65)]
        for t in leaf_t[r]:
            lines.append(f"{leaf(r)}# show interfaces counters")
            lines.append(f"Timestamp: {iso(t)}")
            lines.append(f"{'Port':<14}" + "".join(f"{c:>18}" for c in LEAF_COLS))
            for p in ports:
                vals = []
                for c in LEAF_COLS:
                    v = model.cumulative(L[(r, p)][c], t, init[(r, p, c)],
                                         reset_at=leaf7_clear if r == 7 else None)
                    v = int(v)
                    if c in ("RxPause3", "TxPause3"):
                        v %= U32
                    vals.append(v)
                lines.append(f"{p:<14}" + "".join(f"{v:>18}" for v in vals))
            lines.append("")
        (out / "leaf_cli" / f"{leaf(r)}.txt.gz").write_bytes(gz_bytes("\n".join(lines) + "\n"))

    # ---- spine JSON lines: spine port (r, k) on spine j mirrors leaf r uplink (j, k)
    recs = []
    for k_poll in range(MINUTES + 1):
        for j in range(N_SPINES):
            t = spine_t[j][k_poll]
            reset = spine2_clear if j == 1 else None
            updates = []
            for r in range(N_RAILS):
                for k in range(8):
                    lk = (r, uplink_port(j, k))
                    d = L[lk]

                    def cum(c_spine_from: str) -> int:
                        return int(model.cumulative(d[c_spine_from], t, init[lk + (c_spine_from,)] * 1.01,
                                                    reset_at=reset))
                    name = spine_port(r, k)
                    updates.append({"path": f"/interfaces/interface[name={name}]/state/counters",
                                    "values": {"in-octets": cum("OutOctets"), "out-octets": cum("InOctets"),
                                               "in-discards": 0, "out-discards": cum("InDiscards"),
                                               "in-fcs-errors": 0}})
                    updates.append({"path": f"/qos/interfaces/interface[name={name}]/ext/pfc-ecn",
                                    "values": {"rx-pause-3": cum("TxPause3"), "tx-pause-3": cum("RxPause3"),
                                               "ecn-marked-3": cum("EcnMarked3") // 3}})
            recs.append(json.dumps({"timestamp_ns": int(round((EPOCH0 + t) * 1e9)), "device": spine(j),
                                    "updates": updates}, separators=(",", ":")))
    (out / "spine_stream.jsonl.gz").write_bytes(gz_bytes("\n".join(recs) + "\n"))

    # ---- NIC ethtool -S + hw_counters; NIC (n, r) mirrors leaf r port n
    nic_init_rng = np.random.default_rng(args.seed + 2)
    for n in range(N_HOSTS):
        blocks = []
        for t in nic_t[n]:
            reset = host30_reboot if n == 29 else None
            for r in range(N_RAILS):
                d = L[(r, f"Ethernet1/{n + 1}")]
                base = (n, r)

                def c(rate: np.ndarray, scale: float = 1.0, key: str = "") -> int:
                    k = base + (key,)
                    if k not in init:
                        lo, hi = NIC_INIT_RANGE[key]
                        init[k] = float(nic_init_rng.uniform(lo, hi))
                    return int(model.cumulative(rate * scale, t, init[k], reset_at=reset))
                zeros = np.zeros(MINUTES)
                crc = zeros.copy()
                oos = 0.2 * np.ones(MINUTES)
                if n == 23 and r == 2:          # F5: host-side receive errors on orion-n24 mlx5_2
                    crc[11:] = 20 + 40 * np.linspace(0, 1, MINUTES - 11)
                    oos[11:] = 15 + 10 * np.linspace(0, 1, MINUTES - 11)
                stats = [
                    ("rx_vport_rdma_unicast_bytes", c(d["OutOctets"], 0.995, "rxb")),
                    ("tx_vport_rdma_unicast_bytes", c(d["InOctets"], 0.995, "txb")),
                    ("rx_prio3_pause", c(d["TxPause3"], 1.0, "rxp")),
                    ("tx_prio3_pause", c(d["RxPause3"], 1.0, "txp")),
                    ("rx_discards_phy", c(zeros, 1.0, "disc")),
                    ("rx_crc_errors_phy", c(crc, 1.0, "crc")),
                ]
                hw = [
                    ("np_cnp_sent", c(d["EcnMarked3"], 0.5, "cnp_s")),
                    ("rp_cnp_handled", c(d["EcnMarked3"], 0.48, "cnp_h")),
                    ("np_ecn_marked_roce_packets", c(d["EcnMarked3"], 1.0, "ecn")),
                    ("out_of_sequence", c(oos, 1.0, "oos")),
                    ("local_ack_timeout_err", c(zeros, 1.0, "lat")),
                ]
                blocks.append(f"### collected_at={EPOCH0 + int(t)} host={host(n)} dev=mlx5_{r} "
                              f"netdev=ens{r}np0 rail={r}")
                blocks.append("NIC statistics:")
                blocks += [f"     {k}: {v}" for k, v in stats]
                blocks.append(f"RDMA hw_counters (/sys/class/infiniband/mlx5_{r}/ports/1/hw_counters):")
                blocks += [f"     {k}: {v}" for k, v in hw]
        (out / "nic" / f"{host(n)}.txt.gz").write_bytes(gz_bytes("\n".join(blocks) + "\n"))

    # ---- topology
    topo = ["a_device,a_interface,b_device,b_interface,rail,link_role"]
    for r in range(N_RAILS):
        for n in range(N_HOSTS):
            topo.append(f"{leaf(r)},Ethernet1/{n + 1},{host(n)},mlx5_{r},{r},host")
        for j in range(N_SPINES):
            for k in range(8):
                topo.append(f"{leaf(r)},{uplink_port(j, k)},{spine(j)},{spine_port(r, k)},{r},fabric")
    (out / "topology.csv").write_text("\n".join(topo) + "\n", encoding="utf-8", newline="\n")

    profiles = {
        "provenance": "SIMULATED capture; vendor-neutral switch formats; mlx5-style NIC counter names",
        "platforms": {
            "leaf_cli": {"devices": "orion-be-leaf-r*", "format": "cli_text", "files": "leaf_cli/*.txt.gz",
                         "timestamp": "ISO-8601 UTC in a 'Timestamp:' line", "poll_interval_s": 60,
                         "counter_width_bits": {"default": 64, "RxPause3": 32, "TxPause3": 32},
                         "max_plausible_rate_per_s": {"RxPause3": 2.0e6, "TxPause3": 2.0e6},
                         "notes": "Pause counters are 32-bit on this platform (older ASIC SDK)."},
            "spine_stream": {"devices": "orion-be-spine-*", "format": "jsonl", "files": "spine_stream.jsonl.gz",
                             "timestamp": "timestamp_ns: integer nanoseconds since Unix epoch, UTC",
                             "poll_interval_s": 60, "counter_width_bits": {"default": 64},
                             "notes": "Interface counters use OpenConfig-style leaf names; PFC/ECN under a "
                                      "vendor extension path."},
            "nic_ethtool": {"devices": "orion-n*", "format": "ethtool_text", "files": "nic/*.txt.gz",
                            "timestamp": "collected_at: integer seconds since Unix epoch, UTC",
                            "poll_interval_s": 120, "counter_width_bits": {"default": 64},
                            "notes": "Host agent concatenates `ethtool -S <netdev>` and the RDMA hw_counters "
                                     "directory for each NIC."},
        },
    }
    (out / "device_profiles.yaml").write_text(yaml.safe_dump(profiles, sort_keys=False, width=100),
                                              encoding="utf-8", newline="\n")
    maint = {"windows": [
        {"id": "CHG-20817", "device": "orion-n30", "start": "2026-10-12T10:15:00Z", "end": "2026-10-12T10:19:00Z",
         "description": "Planned reboot for kernel patch. orion-n30 is an inference node (default split "
                        "n25-n32); the router drained its replica first. W-TRAIN runs on n01-n24, unaffected."},
        {"id": "CHG-20822", "device": "orion-be-leaf-r7", "start": "2026-10-12T10:19:00Z",
         "end": "2026-10-12T10:25:00Z",
         "description": "Replace optics on Ethernet1/41-42 (uplinks to orion-be-spine-2); counters cleared."},
    ]}
    (out / "maintenance.yaml").write_text(yaml.safe_dump(maint, sort_keys=False, width=100),
                                          encoding="utf-8", newline="\n")

    truth = sorted([
        "orion-n17:mlx5_5|pfc_storm",
        "orion-be-leaf-r2:Ethernet1/50|link_degradation",
        "orion-be-leaf-r6:*|ecn_misconfig",
        "orion-be-leaf-r1:*|ecmp_imbalance",
        "orion-n24:mlx5_2|link_degradation",
    ])
    onset = {  # (fault onset UTC, detection tolerance s): alerts must FIRE inside [onset, onset + tolerance]
        "orion-n17:mlx5_5|pfc_storm": ("2026-10-12T10:15:00Z", 600),
        "orion-be-leaf-r2:Ethernet1/50|link_degradation": ("2026-10-12T10:04:00Z", 1200),
        "orion-be-leaf-r6:*|ecn_misconfig": ("2026-10-12T10:00:00Z", 600),
        "orion-be-leaf-r1:*|ecmp_imbalance": ("2026-10-12T10:00:00Z", 600),
        "orion-n24:mlx5_2|link_degradation": ("2026-10-12T10:11:00Z", 600),
    }
    rows = sorted(f"{hashlib.sha256(k.encode()).hexdigest()} {onset[k][0]} {onset[k][1]}" for k in truth)
    (out / "ground_truth.sha256").write_text(
        "# <sha256 of '<device>:<interface>|<fault_class>'> <fault onset UTC> <detection tolerance s>\n"
        "# Device-level faults use interface '*'. An alert matches a fault only if it FIRES within\n"
        "# [onset, onset + tolerance]; earlier or non-matching alerts are false positives.\n"
        + "\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote telemetry bundle to {out} (glitches: {len(model.glitches)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
