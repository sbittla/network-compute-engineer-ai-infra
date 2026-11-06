# K6 — Reading a ceiling fraction

Source: manuscript Section 1.6 (the three readings of the ceiling fraction). Ceiling fraction =
T_lower_bound / T_observed.

**Greater than 1.0.** The profile claims the workload did its work faster than the hardware's peak rate
allows, which is physically impossible, so the *data* is wrong, not the hardware. Typical causes: a
bits-for-bytes unit error, a counter that sums TX and RX (bidirectional), two NICs' counters aggregated,
a double-counted field, or an observed time from the wrong window. Lab row W12 is the example: 40 GB in
0.49 s implies ≈ 81 GB/s through a 50 GB/s NIC (fraction 1.62). Fix the data with its owner before
drawing any conclusion.

**0.1.** The largest throughput bound explains only a tenth of the observed time, so no bandwidth or FLOP
ceiling is what limits the workload. Something outside the model dominates: per-operation latency (many
small collectives), CPU kernel-launch overhead, synchronization waits, queueing, or stragglers. Tuning
the "dominant" resource will not help. Look for serialization instead, for example with an Nsight Systems
timeline. Lab row W16 (batch-1 eager-mode decode, fraction ≈ 0.21, below the lab's 0.25 threshold) is
the example.

The meaningful band is roughly 0.3–0.9; the 0.25 threshold is a teaching convention of this chapter,
not an industry standard.

**Marking note:** the key gives 2 points; this folder scores it out of 4.
