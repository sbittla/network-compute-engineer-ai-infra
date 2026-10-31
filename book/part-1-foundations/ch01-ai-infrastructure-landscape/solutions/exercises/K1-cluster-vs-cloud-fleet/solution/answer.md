# K1 — Five properties of an AI training cluster

Source: manuscript Section 1.1; ORION values from `docs/REFERENCE_CLUSTER.md`. Numbers are `[MODELED]`
from `[ILLUSTRATIVE]` parameters.

1. **Coupling.** A synchronous job's step ends only when the slowest of 256 ranks finishes; W-TRAIN's
   modeled step is 17.4 s at 40 % MFU. A cloud fleet's requests are independent; one slow VM affects only
   its own tenants.
2. **Bandwidth per server.** Each `HX8` has 8 × 400 Gb/s = 3.2 Tb/s of backend RDMA plus 2 × 200 Gb/s
   frontend, against 25–100 Gb/s for a typical cloud server.
3. **Traffic pattern.** East-west, synchronized collectives with few, large, low-entropy flows (DP
   all-reduce 7.66 GB per GPU per step on one rail); cloud traffic is many small, high-entropy flows
   that ECMP spreads well.
4. **Power density.** ≈ 41 kW of IT load per GPU rack (4 × 10.2 kW + 0.2 kW), several times a
   conventional 5–15 kW rack.
5. **Failure semantics.** One node fault stops the whole job: MTBF_job = MTBF_node / n = 1,536 h / 32 =
   **48 h** for ORION. In a cloud fleet a node failure removes 1/n of capacity.

Also accepted: goodput economics (1 % of ORION's goodput ≈ $56,000 per year at $2.50/GPU-hour
`[ILLUSTRATIVE]`).

**Marking note:** the key gives 2 points; this folder scores it out of 4 (the key's 2 points × 2) so
that half credit (correct idea without numbers) is an integer.
