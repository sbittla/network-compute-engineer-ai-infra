# T1 — Token-2 stall in the disaggregated pool: worked solution

**Symptom.** Second-token latency p99 climbs from 24 ms to 180 ms every weekday 14:00–15:30. TTFT and
mean TPOT barely move. KV transfer p99 rises 4.3 → 160 ms (37×), while the request rate rises only 39 →
41 req/s (+5 %). Evidence is `[ILLUSTRATIVE]`.

**Ranked hypotheses.**

1. **The 64-GPU fine-tuning job landed on the decode nodes and shares their rail NICs in the lossless
   class.** ORION's partition model (Chapter 17) gives n25–n32 to Kubernetes only, so this needs a
   partition defect: the recent change most likely extended the Slurm `training` partition (or a
   reservation) to n25–n32, and the job took the idle GPUs 4–7 of `orion-n27`/`orion-n28`. NCCL
   would by default give those ranks their PIX NICs 4–7, and PXN cannot relay through GPUs 0–3
   (not job ranks). Traffic on rails 0–3 therefore means the job's ranks use NICs 0–3 directly,
   e.g. an `NCCL_IB_HCA` pin to `mlx5_0`–`mlx5_3` left over from a 4-GPU config, or cross-NIC
   selection (`NCCL_CROSS_NIC`); at SYS distance that traffic is host-staged. (A whole-node Slurm
   grant, blind to the Kubernetes pods, would also fit, but GPU sharing would then raise decode
   TPOT, which barely moved.)
   *For:* onset matches the job's 14:00–15:30 calendar slot. RX on each decode node rose 108 → 330 Gb/s.
   KV demand is about 107 Gb/s per decode replica (≈ 27 Gb/s per rail), so ≈ 220 Gb/s of *other* traffic
   arrives at those nodes. ECN marks rose ≈ 800× (40 → 31,000/s) and PFC pauses appeared (0 → 1,900/s).
   *Against:* not yet shown that the job runs there, and it should be impossible unless the partition
   definition is wrong.
2. **Fabric hot spot elsewhere (spine or leaf uplinks) caused by the job, spreading through PFC.** *For:*
   PFC propagates congestion upstream. *Against:* RX on the decode ports themselves rose, which points
   to local delivery.
3. **Higher KV demand.** *Against:* +5 % request rate cannot explain a 37× transfer p99. **Rejected.**
4. **A degraded NIC, optic or link on the decode side.** *Against:* periodic and calendar-aligned.
   Check symbol/FEC errors anyway (Chapter 10).

**Discriminating tests.**

- `squeue -j <jobid> -o %N` or `scontrol show job <jobid>`: the job's node list, intersected with
  `orion-n27`/`orion-n28`, plus `scontrol show partition training` and the merged change. An overlap,
  and `Nodes=` covering n25–n32, confirm H1 and its cause.
- On a decode node during the window: `ethtool -S <iface> | grep -E 'prio3_(bytes|pause)'` (mlx5-class
  counter names are driver-specific, `[VENDOR-SPEC, 2026-10]`). TC 3 bytes and pauses rise on the KV
  rails.
- Leaf telemetry on `orion-be-leaf-r0`–`r3`: per-port ECN and PFC counters. Only decode-facing ports hot
  means local (H1). Spine uplinks hot fabric-wide means H2.
- The job's `NCCL_DEBUG=INFO` output (a job-owner change): channel lines `… via NET/IB/<dev>` for the
  ranks on n27/n28 show the NIC per channel, and no `/GDRDMA` means host-staged. `NET/IB/0`–`3`
  confirms the mechanism; `NET/IB/4`–`7` sends you back to the allocation.

*Still needed:* the node list, NCCL NIC selection, and counters on non-decode ports for comparison.

**Immediate mitigation (safe, reversible).** Ask Platform to exclude `orion-n27`/`orion-n28` from the
fine-tune job's next run (job-level `--exclude`), then revert the partition change so `training` again
covers only n01–n24 once the running job reaches a checkpoint. Do not drain nodes running other jobs without their owners' agreement, and do **not**
change switch QoS during the incident.

**Structural fix (change control, Chapter 20).** ORION already has separate partitions, so enforce node
ownership (Chapter 17): each node belongs to exactly one scheduler, and a pre-merge policy check rejects
a Slurm partition that includes n25–n32 outside a declared lifecycle transition. If links must be shared, give KV its own traffic class with ECN and a guaranteed bandwidth
share (Chapter 9), and admit inference-pool nodes only to the inference scheduler.

**Validation.** Over the next five 14:00–15:30 windows: KV transfer p99 < 10 ms, token-2 ITL p99 < 30 ms
(baseline ≈ 24 ms; modeled mean worst case 21.1 ms), ECN marks on decode ports < 100/s, PFC pauses 0,
all compared with the 13:00–14:00 baseline.
