# 8.13 — RDMA readiness validator and perftest analyzer (reference solution)

All lab data are synthetic: inventories are `[ILLUSTRATIVE]` captures and perftest results are
`[SIMULATED]`. Reference implementation: `solutions/lab/readiness.py` and
`solutions/lab/perftest_analysis.py`. `python lab/check.py --impl solution` reports **15/15 PASS**.
In the student release (no `lab/tools/`) it reports 14 PASS + 1 SKIP. The named checks and their PASS
lines are in `outputs/lab_checks.json`; planted faults are in `solutions/lab/PLANTED_FAULTS.md`.
Relies on manuscript Sections 8.7, 8.8, 8.10, 8.11 and Table 8.10.

## Reference readiness summary

```text
Nodes checked: 8; ready: 2; findings: 16
orion-n01 READY | n02 FIRMWARE | n03 LINK_SPEED, PORT_STATE | n04 QOS_PFC
n05 GID_INDEX (all 8 devices) | n06 MTU (mlx5_3), PEERMEM | n07 ADDRESS_PLAN (mlx5_2, mlx5_3) | n08 READY
```

| Node | Finding(s) | What a good report says |
|---|---|---|
| n02 | FIRMWARE (mlx5_5: 28.36.2024 vs baseline 28.39.1002) | RMA spare shipped with old firmware; update before admission |
| n03 | PORT_STATE + LINK_SPEED (mlx5_6 down, Polling, `Speed: Unknown!`) | One root symptom (no link partner), two checks fail: cable, optic or switch port (Chapter 10) |
| n04 | QOS_PFC (mlx5_1: PFC on priority 4, not 3) | RoCE is lossy on that NIC under incast |
| n05 | GID_INDEX ×8 (`NCCL_IB_GID_INDEX=2` → RoCE v1) | One node-level config error showing on all 8 devices: v1 is not routable (8.4) |
| n06 | MTU (mlx5_3 netdev 1500 → `active_mtu 1024`), PEERMEM (`nvidia_peermem` absent) | Cite both the `ip link` and `ibv_devinfo` evidence lines; GDR falls back to host staging |
| n07 | ADDRESS_PLAN ×2 (rail-2/rail-3 addresses swapped) | Each NIC holds the other rail's /31; the GID check still passes, so each check covers a different failure |

Distractors that must not fire: `transport: InfiniBand (0)` on RoCE devices, LID 0, link-local GIDs at
index 0/1, `lo`, an empty `expansion-rom-version`.

## perftest analysis

```text
perftest: n05-n06 rail 5 BW flag (plateau 202.4 Gb/s vs fleet median 388.6) -> orion-n05 mlx5_5 PCIe x8
          n07-n08 rail 2 TAIL flag (p99.9 29.2 us vs fleet median 3.44 us)
```

32 pair/rail rows. A healthy pair's n½ is 8,192 B. Exactly one NIC has `LnkSta` below `LnkCap`.

## Task 8 diagnosis (model `diagnosis.md`, data `[SIMULATED]`)

**n05–n06, rail 5, bandwidth.** Plateau 202.4 Gb/s against a fleet median of 388.6 Gb/s (≈ 52 %).
- *Mechanism:* `orion-n05 mlx5_5` trained at **PCIe Gen5 x8**. x8 ≈ 252 Gb/s raw and ≈ 200–220 Gb/s
  achievable after protocol overhead (docs/VERIFIED_FACTS.md), which matches the ≈ 202 Gb/s plateau.
- *Supporting evidence:* small-message rate unchanged (the message-rate-bound region is not PCIe
  bandwidth-limited, so this is not the NIC pipeline); n½ shifts down (to ≈ 4,096 B) because the lower
  ceiling is reached sooner; `pcie_link.csv` shows LnkSta x8 (downgraded).
- *Next discriminating test:* `lspci -vv -s <bdf>` LnkSta after a cold boot, AER errors in `dmesg`
  (Chapter 3), reseat or inspect the riser, swap the slot; then rerun and confirm the plateau recovers.

**n07–n08, rail 2, tail latency.** p99.9 29.2 µs against a fleet median of 3.44 µs (≈ 8.5×), while
typical latency (≈ 1.9 µs) and bandwidth are normal.
- *Ranked hypotheses:* (1) host jitter on one end (polling thread not pinned, C-states or frequency
  scaling, IRQs on the polling core); (2) PFC pauses or congestion on rail 2 during the run; (3) a
  marginal link with FEC-corrected bursts.
- *Typical latency is normal*, so this is not a path-length or MTU issue.
- *Next tests:* rerun pinned with `numactl`/`taskset`; repeat against a different rail-2 peer to
  localize the problem to n07 or n08; read the `ethtool -S` pause counters and the switch queue/PFC
  counters for the run window; check FEC corrected/uncorrected counters (Chapter 10).
- **The `[SIMULATED]` data cannot discriminate between these. Saying so is required for full marks.**

## Common mistakes

Reporting n05 as eight unrelated problems. Calling n06's PEERMEM finding proof that GDR is broken (it
proves the mechanism is absent; GDR working needs a `--use_cuda` test). Diagnosing the TAIL pair with
certainty from simulated data. Hard-coding answers in the starter.
