# 12.17 — Three real NCCL behaviours the alpha-beta simulation cannot show

The lab's logs follow t = α + factor × S/B plus noise. Real sweeps show:

1. **Algorithm and protocol switches.** NCCL's tuner changes from LL to LL128 to Simple and from tree to
   ring (or NVLS) at size thresholds. *Appearance:* knees and steps in the time-vs-size curve, sometimes
   a non-monotonic busbw (a dip just after a switch point) — a single α-β line fits poorly across them.
2. **Channel-count and topology decisions that vary between launches.** Different channel counts or
   ring orders after a restart, or a NIC that fails to initialize. *Appearance:* bimodal results — the
   same command gives two distinct plateaus across launches; INFO logs show different `Channel` lines.
3. **Congestion-control dynamics on RoCEv2.** ECN marking, DCQCN rate cuts and PFC pauses (Chapter 9),
   especially with other jobs on the spines. *Appearance:* jitter that grows with size and node count,
   occasional slow iterations, plateaus below the idle-fabric value, and correlation with switch PFC/ECN
   counters.

Also acceptable: NVLS/CollNet (SHARP) behaviour and its buffer limits (single-node plateaus near the
NVLink rate, sudden drops at registration limits); PCIe/NVLink contention from other traffic (dips
during checkpoints); retransmission timeouts after packet loss (rare multi-millisecond outliers);
GPU clock or power throttling (slow drift over a long sweep).
