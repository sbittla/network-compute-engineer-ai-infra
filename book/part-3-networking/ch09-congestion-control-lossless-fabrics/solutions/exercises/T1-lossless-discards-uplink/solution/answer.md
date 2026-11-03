# T1 — Lossless discards on one uplink (worked solution)

Evidence `[ILLUSTRATIVE]`; headroom arithmetic `[MODELED]` (`solve.py`). Relies on manuscript Section
9.4 (headroom formula, Table 9.3, the pitfall "longest links first"), Section 9.5 (watchdog, storms),
and the K5 reasoning. Conventions: r = 50 B/ns, MTU 9,216 B, t_resp = 1 µs, 5 ns/m.

## (a) Ranked hypotheses

1. **Undersized headroom on the 100 m uplink (eth1/57).** The buffer profile was computed for
   `cable_length = 5m`, the likely default applied when the leaf was replaced. Discards appear **only**
   on the longest port. eth1/33 has the **same pause rate** (2,880 vs 2,950 /s) and an equally deep
   watermark, but no discards. The only material difference between them is cable length, which is
   exactly the term the profile gets wrong.
2. **Slow PFC response on `orion-be-spine-4`.** A larger effective t_resp would also overflow headroom,
   and eth1/33 faces a *different* spine, so this cannot be excluded from this table alone. Test: other
   leaves' 100 m links to spine-4 show no discards, which points back to leaf-r5's profile.
3. **Lossy traffic mis-mapped into TC 3** (trust or DSCP-map error on the new leaf). WRED drops would
   then appear on *all* busy TC 3 ports, not one. Unlikely.
4. **Physical-layer errors** (Chapter 10). CRC/FCS drops are counted as interface errors, not TC 3
   discards. Check the error counters to exclude it.

## (b) Headroom provided vs needed for the 100 m uplink

Provided (profile, L = 5 m): L / v = 25 ns → 2 × 50 × 25 = 2,500 B
H = 18,432 + 2,500 + 50,000 + 64 = **70,996 B**.

Needed (L = 100 m): L / v = 500 ns → 2 × 50 × 500 = 50,000 B
H = 18,432 + 50,000 + 50,000 + 64 = **118,496 B**.

Deficit = 118,496 − 70,996 = **47,500 B per pause event** (≈ 40 % short). In a worst-case pause, up to
47.5 KB arrive with nowhere to go, which explains the 1,214 discards in 5 minutes.

## (c) eth1/33: same pause rate, no discards. Is it safe?

eth1/33 (20 m) needs 18,432 + 2 × 50 × 100 + 50,000 + 64 = **78,496 B**, so it is **7,500 B (≈ 10 %)
short** against the 70,996 B provided. Why no discards yet:
- the formula is a worst case (two maximum-size frames in flight, the full response time), and that is
  rarely realized together;
- buffer-cell rounding may cover part of a small deficit.

**The evidence cannot prove eth1/33 is safe.** Zero discards in one 5-minute window is absence of
evidence, not a guarantee. Under worst-case alignment the port is short and can drop. The same applies
to the 30 m host downlinks (need 83,496 B, **12,500 B short**). They have not dropped yet, but they are
under-provisioned and must be fixed in the same change.

## (d) Safe fix and validation

**Fix (via the change pipeline):**
1. Raise a change with Fabric team approval. Set the per-port cable length, or the explicit headroom,
   to the real values from the cabling database (30 m downlinks, 20 m / 100 m uplinks) on
   `orion-be-leaf-r5`.
2. Apply it as a canary in a maintenance window, with a rollback plan (the saved current profile).
3. Verify that the vendor recomputes headroom per port, and that the shared pool still meets its
   minimum after the larger reservation.

**Validation criteria:**
- **zero TC 3 discards over ≥ 24 h** including training peaks;
- the headroom watermark (where exposed) stays below its new reservation;
- pause behaviour unchanged (similar rates; the fix is buffer, not policy);
- NCCL jobs on rail 5 show no retransmission-driven slowdowns;
- a **fleet audit** comparing every leaf's cable-length/headroom settings against the cabling database,
  and a replacement-runbook step that sets them.

## Common mistakes

Calling eth1/33 "fine" (−2 points). Raising Xoff (it delays the pause and makes overflow worse). Using
4,096 B as the MTU. Disabling PFC on the port.
