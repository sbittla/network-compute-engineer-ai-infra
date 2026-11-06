# 10.R3 — What the L1 lab cannot tell you about `orion-be-leaf-r3`

The L1 lab analyzes two `[SIMULATED]` snapshots. An L3 commissioning run on real hardware would
show, among others:

1. **Real SerDes equalization and link training.** Whether each lane trained with healthy
   equalizer settings and eye margin; marginal CTLE/DFE settings produce bursty errors (Exercise
   10.R1) that a generated BER value cannot.
2. **Real FEC histograms and burst behaviour.** The distribution of corrected symbols per codeword
   reveals bursts (reflections, intermittent contact) before uncorrectables appear; the lab has
   only an average BER.
3. **DOM accuracy and drift.** Real module monitors have calibration error (often ± 2–3 dB on Rx) and
   drift with temperature and age; the lab's DOM values are exact.
4. **Real end-face contamination effects.** Contamination causes loss *and* back-reflection, changes
   when a connector is re-mated, and can be moved by cleaning; only inspection images and before/after
   DOM show it.
5. **Temperature-dependent margin.** Laser output and receiver sensitivity change with module
   temperature and airflow; a link with 0.5 dB margin at night can fail in the afternoon.
6. **NOS-specific counter semantics.** CRC stomping counters, counter clear behaviour and wrap,
   per-platform names; the lab uses one clean schema.
7. **Flap timing and debounce.** Link-down debounce, dampening and how quickly the NOS error-disables
   a flapping port.
8. **Impact on real RoCEv2 flows and NCCL.** Whether a given BER or flap actually slows collectives,
   triggers retransmissions or go-back-N recovery (Chapters 8 and 12).

Any four with a mechanism earn full marks.
