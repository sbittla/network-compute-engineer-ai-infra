# 13.17 — What simulated telemetry lacks: worked solution

The lab bundle is clean `[SIMULATED]`: every rank has every step, one sampling interval, and
independent planted causes. Real telemetry has at least these properties (any three suffice):

1. **Missing and late samples.** Agents restart, buffers overflow, ranks crash. A rank with no row for
   20 steps can be mistaken for "normal", and per-step medians computed over different rank sets move
   for reasons unrelated to the job. *Handling:* explicit gap markers and minimum-coverage rules before
   computing robust z.
2. **Clock skew between hosts.** Wall-clock timestamps from different nodes differ by microseconds to
   milliseconds, which is enough to invent or hide arrival skew. *Handling:* measure wait as collective
   duration minus post-arrival transfer on each rank's own clock (Section 13.7), or all-gather entry
   timestamps.
3. **Counter wraps and resets.** NIC hardware counters are cumulative since driver load. A reboot or
   driver reload resets them and a naive delta becomes hugely negative or positive, which looks like a
   retransmission storm. *Handling:* store deltas with reset detection.
4. **Mixed sampling intervals.** DCGM at 1 Hz, per-rank rows every 10 steps, and switch counters every
   30 s cannot be joined row by row. A 2 s throttle event can fall between samples.
5. **Interacting causes.** A throttled GPU slows its TP peers on the same node, so TP communication
   rises on eight ranks and points at NVLink. Overlapping collectives (TP, DP and PP at once) make the
   transfer time of one depend on the others. The lab's causes are separable by construction; real
   ones often are not.

Each of these pushes the diagnosis toward false positives on the network or false negatives on the GPU.
That is why the method insists on two independent fields per conclusion.
