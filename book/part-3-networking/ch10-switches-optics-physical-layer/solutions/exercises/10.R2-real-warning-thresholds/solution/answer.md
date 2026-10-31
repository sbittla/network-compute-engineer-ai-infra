# 10.R2 — Setting real thresholds for pre-FEC BER and Rx power

**Model answer (≤ 150 words).** Start from data, not from the lab's numbers. (1) **Commissioning
baselines**: record pre-FEC BER and per-lane Rx power for every link at acceptance and build the
healthy distribution per optic type, vendor and link class (host link vs uplink, length band).
(2) Set the **warning** threshold well outside the healthy population — for BER, e.g. two to three
orders of magnitude above the median but still at least one decade below the KP4 limit of
2.4 × 10⁻⁴; for Rx power, a fixed margin (≈ 2 dB) above the receiver minimum plus a per-lane imbalance
rule. (3) Use **vendor specifications and module thresholds** as the outer bounds only. (4) Refine
with **failure history**: which BER or Rx trends preceded RMAs and incidents, and how long before.
Label thresholds `[ILLUSTRATIVE]` until this validation is done.

**Data needed.** Per-link baselines with module serials and dates; streaming telemetry history
(BER, DOM, FEC histograms) at ≤ 30 s; the RMA/incident log joined by cable ID and serial; vendor
datasheets (receiver sensitivity, alarm thresholds).

**Why this matters.** Alert thresholds set too close to the healthy median page on normal links;
thresholds equal to the module's programmed alarms (−9 dBm for a typical DR4) fire only after the
link is already below the −5.9 dBm receiver minimum (Section 10.7).
