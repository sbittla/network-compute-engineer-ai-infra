# 10.H1 — Link-health analyzer and commissioning report (instructor solution)

**Reference run.** `python lab/check.py --impl solution` → `13/13 checks passed`; the captured
report is `solutions/lab/outputs/check_solution.txt`, and the lab checks this exercise relies on are
listed in `outputs/lab_checks.json`. Data are `[SIMULATED]`; rates and margins `[MODELED]`.

**Expected totals.** 64 ports: 7 physical (all critical), 2 higher-layer (refer), 55 healthy;
commissioning overall **FAIL**, **57/64 accepted** (7 failures, 2 referrals).

**Model `diagnosis.md`** (evidence → layer → hypothesis → first safe action → missing hardware evidence):

| Port | Evidence (600 s window) | Layer / primary | Root-cause hypothesis | First safe action |
|---|---|---|---|---|
| Ethernet7 | Lane 2 Rx −7.8 dBm, other lanes ≈ −1.4 dBm (6.4 dB imbalance); BER 2.6e-6 stable | physical / `RX_POWER_LOW` (+`LANE_IMBALANCE`), critical | Dirty or damaged end-face on one MPO fiber; −7.8 dBm is below the −5.9 dBm DR4 receiver minimum even though the module's −9 dBm alarm has not fired | Schedule a node drain via the scheduler; inspect/clean both ends; replace the jumper if it fails inspection |
| Ethernet12 | 18,342 discards, 16,000 ECN marks/s, 3,500 PFC pause tx/s; FEC, FCS and DOM clean | higher_layer / `CONGESTION`, refer | Incast toward node n12's downlink | Hand to the Chapter 9 congestion workflow; do **not** clean |
| Ethernet21 | Pre-FEC BER 4.0e-6 → 1.6e-4 (0.18 decades margin), no uncorrectables yet, Rx ≈ −3.4 dBm | physical / `PRE_FEC_BER_HIGH` (+rising), critical | Degrading far-end laser or creeping contamination; Table 10.1: ≈ 1 uncorrectable per 80 days *now*, but the trend reaches the cliff soon | Compare NIC-side Tx/bias; drain the node now, then clean/replace |
| Ethernet27 | 45,210 oversize frames; port MTU 1500, hosts send 9000-byte frames | higher_layer / `OVERSIZE_FRAMES`, refer | MTU left at default (Chapter 7) | Fix port MTU under change control; no optics work |
| Ethernet35, 36 | LLDP shows spine-1 Ethernet28/27 instead of 27/28; error-free | physical / `MISCABLED`, critical | Jumpers swapped at the patch panel; eBGP /31 mismatch would remove two ECMP members | Keep routing disabled on both; trace and re-patch to the schedule |
| Ethernet40 | 1,180 uncorrectable CW, 1,104 FCS in 600 s at an average BER of only 3.4e-5 (≈ 0.85 decades margin); DOM normal | physical / `CRC_ERRORS` (+`FEC_UNCORRECTABLE`, `PRE_FEC_BER_HIGH`), critical | Bursty errors (impossible under random errors at that margin): damaged cable or reflection | Routing-policy drain of the uplink (−3.1 % raw, −12.5 % ECMP-aware for spine-1, Chapter 7 Section 7.9), inspect, swap cable then optic |
| Ethernet45 | Link down, Rx −40 dBm (LOS); installed 400G-SR8 where the schedule says 400G-DR4 | physical / `OPTIC_MISMATCH` (+`LINK_DOWN`), critical | Wrong part (850 nm MMF optic on SMF facing DR4) | Replace the module with DR4; do **not** clean or replace the fiber |
| Ethernet50 | 6 link-down events in 600 s; 40 uncorrectable CW / 31 FCS around transitions | physical / `LINK_FLAP` (+`CRC_ERRORS`, `FEC_UNCORRECTABLE`), critical | Mechanical seating, failing optic or firmware; errors are a consequence of the flaps | Drain the node; reseat/inspect, check firmware and far end; replace optic if it repeats |

**Decoys (not faults).** Ethernet2: counters were cleared 240 s before T1, so naive `t1 − t0` is hugely
negative; the reset-aware delta uses the T1 value, and rates for that port cover only 240 s of data,
so say they are underestimated. Ethernet18: busy port with BER 6.5e-7, ≈ 1.5 × 10⁸ corrected
codewords, 400 ECN marks/s and 60 PFC/s — all under policy limits; corrected codewords are normal
(Exercise 10.K2).

**Still needed on hardware.** Far-end (NIC/spine) DOM and counters per faulty link, FEC histograms,
end-face inspection images, host-side LLDP, and a loaded soak after repair (commissioning gates,
Section 10.11).
