# K7 — Discriminating tests: model answer

Sources: Section 24.12, Tables 24.14 and 24.14a; the concept is defined in Chapter 22 (Section 22.3.3).

**Definition.** A discriminating test is one whose outcome the competing hypotheses predict *differently*,
so its result eliminates at least one of them. A test that every hypothesis predicts the same way ("rerun
`all_reduce_perf`") adds no information.

**The test in Section 24.12.** Read the per-port counters and optic Rx power on the rail-3 leaf ↔ host links:
FEC corrected/uncorrectable codewords, CRC errors, PFC pause frames on priority 3 and ECN/CNP counts.

**Outcome observed → physical-layer degradation.** Errors isolated to one port (`orion-n11`: 18,422
uncorrectable codewords, 9,870 CRC errors, corrected rate 40× peers), Rx power −9.8 dBm against −1.5 to
−2.4 dBm on peers (≈ 8 dB low), and PFC pauses low everywhere `[ILLUSTRATIVE]`. This localizes the fault to
one optic or connector; the `rack-03` cabling audit is the probable but unproven trigger.

**Outcome that would point the other way → congestion.** PFC pauses and ECN/CNP increases spread across
*many* rail-3 ports, correlated with load, with clean FEC/CRC and normal Rx power everywhere. That pattern
is a PFC storm or incast, and the fix would be in traffic or QoS, not in an optic.

**Note.** The per-rail `ib_write_bw` (rail 3 at 212 vs ≈ 371 Gb/s) *localizes* the rail but does not by
itself separate the two hypotheses: both predict low bandwidth on rail 3.

**Common mistakes.** Choosing a test both hypotheses predict the same way; giving only the observed
outcome and not the one that would have pointed elsewhere.
