# R4 — Evidence needed before claiming production-ready (model answer)

**Source:** manuscript Sections 23.7–23.9 (benchmark evidence, failure exercise, backlog); key R4.

**Model answer (≈ 140 words).** An L1 capstone is a reviewed design, not a production system. Before
claiming production-ready I would still need:
1. **Hardware validation at target scale** — a 32-node `all_reduce_perf` sweep, 5 runs on an isolated
   fabric with a manifest, replacing the `[MODELED]` A-06 = 40 GB/s per rail.
2. **Acceptance tests passing on every node** (Chapter 16), including the GDRDMA smoke test (A-11 from
   Section 23.12) and a fleet firmware-consistency gate.
3. **Facilities sign-off** on 40.8 kW per rack at maximum power, measured during burn-in.
4. **An executed failure exercise**, not a tabletop: rail-leaf failure with TTD/TTM/TTR and lost
   GPU-hours `[MEASURED]`.
5. **Re-verified, dated vendor specifications** for NIC firmware and switch OS interoperability.
6. **Security review and on-call ownership**: runbooks reviewed, owners for every assumption.

**Deduct for** generic items ("more testing") or fewer than four.
