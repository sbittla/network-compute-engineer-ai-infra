# 20.11.4 — Missing evidence for the RDMA MTU claim: model answer

**Relies on:** manuscript Section 20.11, Step 1 (Table 20.12 `[MODELED]`: +5.9 % wire-efficiency ceiling, ≈ 3.8×
fewer packets), LAB_STANDARDS Section 5 (measurement rules), and the W-TRAIN reference workload in
docs/REFERENCE_CLUSTER.md.

## Model answer (≤ 150 words)

Section 20.11 shows only a `[MODELED]` ceiling. Missing:

1. **Measured step time** on W-TRAIN (L3) before and after, ≥ 5 repetitions each, warm-up stated, median and p95,
   one variable changed (no firmware or QoS change in the same window).
2. **Counter evidence** that the mechanism happened: NIC and switch packet counters showing ≈ 3.8× fewer packets
   per byte, `active_mtu` 4,096 read back on every NIC, QPs re-created.
3. **Evidence that the network is on the critical path.** With TP inside NVLink, DP and PP traffic partly
   overlaps compute; a 5.9 % ceiling rise on exposed communication may yield far less step-time gain, perhaps
   none. Profiles (exposed communication time per step) are needed to bound the expected effect.

Without these, the claim is "the bandwidth ceiling rose", not "training got faster".

## Marking (5 points)

Measured step time with method 2 · counter evidence 1 · critical-path argument 2.
