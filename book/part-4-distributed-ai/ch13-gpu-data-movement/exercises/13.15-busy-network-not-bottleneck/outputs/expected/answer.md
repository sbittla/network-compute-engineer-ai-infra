# 13.15 — A busy network is not a bottleneck: worked solution

"The network is busy" describes a counter, not a cause. Three different situations produce high NIC
utilization (Section 13.8):

1. **Synchronization.** Ranks waited for a straggler with the network idle. Then the last rank arrived
   and everyone transferred at once. The burst is near line rate (≈ 359 Gb/s in the lab
   `[SIMULATED]`), but its *duration* is normal (transfer ≈ 120 ms). The network is doing its job
   quickly. The time is lost in the wait before it.
2. **A slow network.** Retransmissions or congestion make transfers take longer at a *lower* burst
   rate (rail 2 in the lab: 222 Gb/s, transfer 198 ms). The link stays "busy" longer precisely
   because it is delivering less.
3. **Genuine volume.** The transfer is long *and* near line rate. Only this case means "the network
   is the bottleneck" in the capacity sense.

**What to compare instead:**

- burst rate during the transfer phase versus line rate (400 Gb/s per NIC);
- transfer time after the last arrival versus its healthy baseline;
- wait time before the last arrival;
- retransmission and ECN/PFC counters.

Step-averaged utilization blurs all of these. The lab's step average of ≈ 45 Gb/s looks idle while
hiding 360 Gb/s bursts. A busy network is evidence only when transfer time rises for everyone with a
burst rate that explains it.
