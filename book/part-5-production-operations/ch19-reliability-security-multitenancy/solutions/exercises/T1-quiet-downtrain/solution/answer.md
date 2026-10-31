# T1 — The quiet downtrain: worked solution

**Relies on:** Section 19.3 "PCIe AER and link retraining"; Section 19.6 (containment, fault domain vs
scheduling unit); Section 19.7 (no spares on ORION, requeue); Table 19.4 (straggler row); Chapter 18
power-cap case. Evidence `[ILLUSTRATIVE]`; arithmetic `[MODELED]`.

## 1. Hypotheses and discriminating evidence

| # | Hypothesis | Evidence for | Evidence against | Verdict |
|---|---|---|---|---|
| H1 | orion-n10 HCA `mlx5_2` PCIe link downtrained to x8 at the maintenance reboot | `LnkSta … Width x8 (downgraded)` vs `LnkCap x16`; 3,400 corrected Physical Layer RxErr since boot (peers 0–5); NIC TX 985 Gb/s vs 1,050–1,080 (6–9 % lower); onset matches the reboot | — | **Root cause** |
| H2 | Compute straggler on orion-n10 (clocks, power cap, thermal) | — | SM active 0.57 on all 16 nodes | Rejected |
| H3 | Fabric or optics fault on an orion-n10 port | — | All 8 switch ports clean; `link_downed` 0; `out_of_sequence` flat | Rejected |
| H4 | Congestion | — | `rp_cnp_handled` normal; only one node's TX is low | Rejected |

## 2. Bandwidth arithmetic

```text
Gen5 x16 = 32 GT/s × 16 × 128/130 / 8 = 63.0 GB/s per direction (≈ 50–55 achievable)
Gen5 x8  = 32 GT/s ×  8 × 128/130 / 8 = 31.5 GB/s per direction (≈ 25–27 achievable)
NIC line rate = 400 Gb/s = 50 GB/s
```

At x8, `mlx5_2` can move at most ≈ 25–27 GB/s (≈ 200–220 Gb/s), about half its line rate. Average NIC
TX is far below line rate on every node (≈ 133 Gb/s per NIC). The cap bites during communication
bursts, when every rail-2 transfer from orion-n10 runs at half speed and every rail-2 collective step
waits for it. That shows up as 7.5 % lower summed TX (985 vs ≈ 1,065 Gb/s mid-range) and a 9 % slower
job.

## 3. Why SM activity does not single out orion-n10

This is a **network** straggler. orion-n10's GPUs wait on their own slow rail-2 transfers just as the
peers wait on them, so all 16 nodes show the same reduced SM activity (0.57). In the Chapter 18 power-cap
case the straggler was a **compute** straggler. Its GPUs ran at lower clocks and were *busier* than
their peers (higher SM active) while the others idled at the barrier. Here, the discriminators are
per-node NIC throughput and the PCIe link state, not GPU activity.

## 4. Containment

- **Fault domain:** the `mlx5_2` PCIe path, meaning the slot, riser, connector or card (thousands of
  Physical Layer RxErr suggest signal integrity at the connector or riser).
- **Scheduling unit removed:** node orion-n10, because a rail-optimized 16-node job needs all 8 rails at
  full rate.
- **Action:** drain orion-n10 (`scontrol update nodename=orion-n10 state=drain reason="mlx5_2 PCIe x8
  downtrain"`). Draining does not move the running job. Take (or use the latest) checkpoint and
  `scontrol requeue <jobid>`. ORION has no spare nodes, so the 16-node job needs a 16th node from
  elsewhere: a free training node, or an inference node (orion-n25–n32) borrowed through a lifecycle
  transition (Chapter 17). Otherwise it waits for the repair.
- **Is restarting worth it?** The restart costs ≈ 15 min of lost work plus 15 min of restart, × 128 GPUs
  = 64 GPU-h. Running degraded wastes 128 × 0.09 = 11.5 GPU-h per hour. Break-even = 64 / 11.5 ≈ 5.6 h
  of remaining runtime. Requeue if more than that remains; otherwise let it finish and repair afterward.

## 5. Fix

Reseat the HCA and riser, inspect the connector for damage or debris, reboot, and re-check `LnkSta`.
If it trains at x8 again, replace the riser, then the card.

## 6. Validation criteria

- `lspci -vvv -s 3b:00.0`: `LnkSta` Speed 32GT/s, **Width x16**, equal to `LnkCap`.
- Corrected AER count ≈ 0 (fleet background) over 1 h of load.
- Rail-2 `ib_write_bw` and a rail-2 NCCL test at baseline bus bandwidth.
- Job step time within 2 % of baseline after the node returns.

**Prevention:** the Chapter 16 acceptance and boot-time health check must compare `LnkSta` with `LnkCap`
for every GPU and NIC on every boot and refuse to return a node with a downgraded link.

## Common wrong answers

- Blaming the switch or optics despite clean switch counters and zero link-downs.
- Expecting the slow node to show different SM activity.
- Stating x8 = 252 Gb/s as achievable, or mixing Gb/s and GB/s.
- "Drain the node" as the whole containment: draining does not move the running job.
