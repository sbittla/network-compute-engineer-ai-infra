# Tabletop evidence cards: rail-leaf failure on ORION-256

These cards make the Section 23.8 tabletop runnable as written. The facilitator reveals one card at
a time, in order, and the scribe timestamps each decision. All output is `[ILLUSTRATIVE]`: it is
abridged and invented for the fictional ORION cluster. Log formats follow
[VERIFIED_FACTS.md](../../../../../docs/VERIFIED_FACTS.md); verify them against the releases you run.

**Scenario.** A 256-GPU W-TRAIN job is running on `orion-n01`…`orion-n32` (the inference nodes are
borrowed). Checkpoints are taken every τ ≈ 76 min. At T₀, rail leaf 3 (`orion-be-leaf-r3`) loses
power to its switching ASIC.

## Card 1: T₀ + 5 s, switch telemetry

```text
orion-be-leaf-r3  Ethernet1/1-1/32  oper-status down   (32 host ports, NIC 3 / mlx5_3 of n01..n32)
orion-be-leaf-r3  Ethernet1/33-1/64 oper-status down   (32 uplinks, 8 to each spine)
```

*Ask:* what is the blast radius in GPUs lost, and in jobs affected?

## Card 2: T₀ + 8 s, routing

```text
orion-be-spine-1..4: BGP neighbor (AS 65104, rail leaf r3) on 8 uplinks each: Established -> Idle
```

*Ask:* does any other rail lose capacity? (No: the spines lose only leaf r3's paths.)

## Card 3: T₀ + 30 s, alert

```text
ALERT LeafDown severity=critical device=orion-be-leaf-r3 -> page Fabric on-call
```

*Measure:* time to detect (TTD) against the 2 min target.

## Card 4: T₀ + ≈ 35 s, NCCL on the ranks that own GPU 3 (abridged, NCCL 2.22+ format)

```text
orion-n14: NCCL WARN NET/IB: Got completion from peer 10.100.3.31<...> with status=12 ... hca mlx5_3
```

The peer is orion-n15's rail-3 address (10.100.3.(2n)+1, host side odd). Status 12 is `IBV_WC_RETRY_EXC_ERR`: the queue pair exhausted its retries. The delay depends on
`NCCL_IB_TIMEOUT` and the retry count.

*Ask:* why does NCCL not move rail 3's traffic to another NIC through PXN? (Section 23.5.)

## Card 5: T₀ + 10 min, framework watchdog

```text
[Rank 115] Watchdog caught collective operation timeout: WorkNCCL(... OpType=ALLREDUCE ...
  Timeout(ms)=600000) ran for 600043 milliseconds before timing out.
```

*Ask:* the job hung for 10 min (the default NCCL process-group timeout). Which automation should
have failed it at Card 3, and who owns it?

## Card 6: T₀ + 11 min, scheduler

```text
$ sacct -j 48213 --format=JobID,State,ExitCode,Elapsed
48213        FAILED      1:0     3-04:17:52
```

Requeue is held by policy until a human chooses the restart shape.

## Card 7: T₀ + 15 min, options

- The spare leaf is racked and pre-configured. Swap, cabling check and BGP verification take ≈ 3 h.
- The alternative is a restart now on 7 rails with `NCCL_IB_HCA=^=mlx5_3`. Expect the DP and PP
  traffic per remaining rail to rise by 8/7. Restart again on 8 rails after the swap.

*Decide:* who chooses, using what numbers? (The worked example found that no runbook named this
person.)

## Card 8: T₀ + 20 min, checkpoint

```text
latest validated checkpoint: step 21,840, written T₀ - 41 min, restore test PASS
```

*Measure:* lost work = 41 min × 256 GPUs ≈ 175 GPU-h since the checkpoint, plus the 11 min hang until
the job failed (256 × 11 min ≈ 47 GPU-h), plus one restart (256 × 900 s = 64 GPU-h): ≈ 286 GPU-h, plus
≈ 4.3 GPU-h for every minute the restart decision takes `[MODELED]`. The hang and the decision time
are the two terms automation and a named decider would remove (close-out).

## Facilitator close-out

Record TTD (Card 3), time to mitigate (job failed and the decision made), time to resume (first
nominal step after restart), and lost GPU-hours. Every gap goes into the backlog with an owner.
Expected gaps: no automation fails the job on a leaf-down alert (a 10 min hang), and no named
decider for the restart shape.
