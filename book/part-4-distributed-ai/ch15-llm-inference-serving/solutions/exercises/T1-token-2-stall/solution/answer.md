# T1 — Token-2 stall in the disaggregated pool: worked solution

**Symptom.** Second-token latency p99 climbs from 24 ms to 180 ms every weekday 14:00–15:30. TTFT and
mean TPOT barely move. KV transfer p99 rises 4.3 → 160 ms (37×), while the request rate rises only 39 →
41 req/s (+5 %). Evidence is `[ILLUSTRATIVE]`.

**Ranked hypotheses.**

1. **The 64-GPU fine-tuning job shares the decode nodes' NICs or rail ports in the lossless class.**
   *For:* onset matches the job's 14:00–15:30 calendar slot. RX on each decode node rose 108 → 330 Gb/s.
   KV demand is about 107 Gb/s per decode replica (≈ 27 Gb/s per rail), so ≈ 220 Gb/s of *other* traffic
   arrives at those nodes. ECN marks rose ≈ 800× (40 → 31,000/s) and PFC pauses appeared (0 → 1,900/s).
   *Against:* not yet shown that the job runs there. GPUs 4–7 of `orion-n27`/`orion-n28` are idle and
   schedulable.
2. **Fabric hot spot elsewhere (spine or leaf uplinks) caused by the job, spreading through PFC.** *For:*
   PFC propagates congestion upstream. *Against:* RX on the decode ports themselves rose, which points
   to local delivery.
3. **Higher KV demand.** *Against:* +5 % request rate cannot explain a 37× transfer p99. **Rejected.**
4. **A degraded NIC, optic or link on the decode side.** *Against:* periodic and calendar-aligned.
   Check symbol/FEC errors anyway (Chapter 10).

**Discriminating tests.**

- `squeue -j <jobid> -o %N` or `scontrol show job <jobid>`: the job's node list, intersected with
  `orion-n27`/`orion-n28`. An overlap confirms H1.
- On a decode node during the window: `ethtool -S <iface> | grep -E 'prio3_(bytes|pause)'` (mlx5-class
  counter names are driver-specific, `[VENDOR-SPEC, 2026-10]`). TC 3 bytes and pauses rise on the KV
  rails.
- Leaf telemetry on `orion-be-leaf-r0`–`r3`: per-port ECN and PFC counters. Only decode-facing ports hot
  means local (H1). Spine uplinks hot fabric-wide means H2.
- The job's `NCCL_DEBUG=INFO` output (a job-owner change) shows which NICs its ranks use.

*Still needed:* the node list, NCCL NIC selection, and counters on non-decode ports for comparison.

**Immediate mitigation (safe, reversible).** Ask Platform to exclude `orion-n27`/`orion-n28` from the
fine-tune job's eligible nodes for its next run (job-level `--exclude`, or a Slurm reservation for the
inference nodes). Do not drain nodes running other jobs without their owners' agreement, and do **not**
change switch QoS during the incident.

**Structural fix (change control, Chapter 20).** Separate node pools or partitions for inference and
training. If links must be shared, give KV its own traffic class with ECN and a guaranteed bandwidth
share (Chapter 9), and admit inference-pool nodes only to the inference scheduler.

**Validation.** Over the next five 14:00–15:30 windows: KV transfer p99 < 10 ms, token-2 ITL p99 < 30 ms
(baseline ≈ 24 ms; modeled mean worst case 21.1 ms), ECN marks on decode ports < 100/s, PFC pauses 0,
all compared with the 13:00–14:00 baseline.
