# 20.5 — Idempotent node/network configuration validator: reference solution

**Relies on:** manuscript Sections 20.3.1–20.3.4 (idempotency, reconciler), 20.9 (dry-run default), 20.10
(audit records), and the RoCE `active_mtu` rule of Section 20.11. Reference implementation and its
demonstration: `solve.py` in this folder `[SIMULATED]` (an L1 fixture of `orion-n06`, whose eth3 came back
from a reimage at IP MTU 1,500 with `active_mtu` dragged to 1,024).

## Design

- **Read through machine-readable interfaces.** `ip -j link show dev <netdev>` (JSON, `mtu` field);
  `ethtool -i <netdev>` (`firmware-version`); `ibv_devinfo -d <ibdev>` (`active_mtu`);
  `/sys/class/net/<netdev>/speed` (Mb/s, 400000 for 400 Gb/s). The host adapter and the fixture adapter
  expose the same `run()` / `set_mtu()` interface, so the same logic runs at L1 and L2.
- **Checks per backend NIC** (eth0–eth7 / mlx5_0–mlx5_7 only; never the frontend NICs): IP MTU 9,000; RDMA
  `active_mtu` 4,096; firmware in the approved list {28.42.1000, 28.43.1014}; speed 400,000 Mb/s.
- **Exit codes:** 0 in sync; 1 drift found; 2 cannot determine. A missing tool, an absent device or an
  unparsable output is code 2, never "in sync".
- **`--apply` is dry run by default**; `--no-dry-run` is required to write. It remediates **only** the IP MTU,
  then reads back. Firmware and speed drift are reported, not fixed: they belong to the Chapter 16 lifecycle.
- **One JSON audit line per check and per action:** `target, netdev, key, before, after, result` with result
  `in_sync`, `drift`, `dry-run`, `changed`, `failed` or `cannot_determine`.

## Evidence (from `solve.py`)

| Run | Exit | Drift lines | Dry-run actions | Changed actions |
|---|---|---|---|---|
| 1 validate | 1 | 2 (eth3 host_mtu 1,500; eth3 active_mtu 1,024) | 0 | 0 |
| 2 `--apply` (dry run) | 1 | 2 | 1 | 0 |
| 3 `--apply --no-dry-run` | 0 | 2 (before-state recorded) | 0 | 1 |
| 4 `--apply --no-dry-run` again | 0 | 0 | 0 | **0** |
| 5 `ibv_devinfo` missing | **2** | — | — | — |

Run 3's action line is
`{"action": "set_mtu", "before": 1500, "after": 9000, "key": "host_mtu", "netdev": "eth3", "readback_rdma_active_mtu": 4096, "result": "changed", ...}`.
The read-back shows `active_mtu` returning to 4,096 on its own: on RoCE it is the minimum of the port's maximum
RDMA MTU and the largest IB MTU that fits under the netdev MTU (2,048 + headers does not fit in 1,500, so it
was 1,024). Run 4 plans zero actions: the second-run no-op is the idempotency proof. Exactly one write was made
across all runs.

## Marking (10 points)

Machine-readable reads 2 · exit codes 1 · no mutation by default 2 · apply touches only IP MTU and the second
run is a no-op 2 · JSON audit lines 2 · missing tool is "cannot determine" 1.

**Common wrong answers.** Treating an `ibv_devinfo` failure as in sync. Changing the MTU on every interface,
including the frontend NICs. Scraping `ifconfig` text. No second-run evidence. Reporting `active_mtu` drift as
a separate remediation instead of re-reading it after the netdev fix (credit read-back verification).
