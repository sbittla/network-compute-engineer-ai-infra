# 13.6 — Eight NICs retransmitting at the same step: worked solution

**Probability argument (one sentence).** If each NIC independently began retransmitting at a given
step with probability *p* (say 10⁻³), the chance that eight specific NICs on eight different nodes
start at the *same* step is about p⁸ ≈ 10⁻²⁴, so a single shared cause is overwhelmingly more likely.

**What they share (Section 13.9, step 5).** In ORION's rail-optimized backend, the eight NICs with the
same local index (here index 2, one per node) all connect to the **same rail leaf, `orion-be-leaf-r2`**.
They also share that leaf's configuration (PFC/ECN profile, buffer settings, firmware) and possibly a
batch of optics installed together. NICs on one node share the node. NICs on one rail share the leaf.
A per-index pattern across nodes therefore points at the rail, not at eight NICs.

**Suspect:** the `orion-be-leaf-r2` switch, or a change applied to it at about that time, for example a
configuration push, a firmware upgrade or a degraded optics bank.

**Confirming checks:**

- Leaf-side port counters on `orion-be-leaf-r2` (FEC/symbol errors, discards, ECN marks, PFC pauses) for
  the eight NIC-facing ports, compared with leaves r0–r1 and r3–r7.
- The change log for the leaf around the onset step's timestamp.
- NIC counters on other rails staying flat (≈ 1 retransmission per step, as in the lab), which rules out
  a host-side or software cause.

In the lab bundle, rail 2 is flagged with onset at step 30: retransmissions of about 3,200 per step on
local index 2 on every node versus about 1 elsewhere `[SIMULATED]`.

**Common wrong answer.** Opening eight NIC replacement tickets.
