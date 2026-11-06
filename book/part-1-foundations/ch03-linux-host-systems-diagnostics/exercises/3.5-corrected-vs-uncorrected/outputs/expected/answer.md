# 3.5 — Corrected versus uncorrected errors

Source: manuscript Section 3.4 ("Memory errors") and Section 3.6 ("Advanced Error Reporting (AER)");
lab thresholds `aer_corrected_warn_per_bdf: 10` and `edac_ce_warn: 5` in
`lab/data/orion_hx8_baseline.yaml` `[ILLUSTRATIVE]`.

| Event | Consequence | Rule type | Suggested first action |
|---|---|---|---|
| PCIe AER **corrected** (e.g. RxErr, BadTLP) | The link layer retried the packet; small bandwidth and latency cost | **Rate per BDF** (warn at ≥ 10 per capture or per hour) | Correlate with `LnkSta` and the device's load; schedule inspection |
| PCIe AER **uncorrected non-fatal** | One transaction failed; the driver may recover | **Presence** | Drain at the next checkpoint; collect logs |
| PCIe AER **uncorrected fatal** | The link is unreliable and needs a reset; the device may be lost | **Presence** | Drain immediately; hardware RMA path |
| EDAC **CE** | Corrected DRAM error; a rising rate on one DIMM predicts a future UE | **Rate per DIMM** | Trend it; plan DIMM replacement at the next window |
| EDAC **UE** | Uncorrectable data loss; process or host crash | **Presence** | Drain and replace the DIMM |

**Why the split matters.** Corrected events happen on healthy hardware (link training, hot-plug, cosmic
rays), so alerting on their mere presence floods on-call. The lab's reference node `orion-n01` has two
historical corrected AER events on NIC 4 weeks apart and must *not* warn. A burst on one BDF (37 in
fifteen minutes on `orion-n07`, together with a width downgrade) is a fault. Uncorrected events mean
data or a transaction was actually lost, so a single occurrence is enough.

**Common wrong answer:** one rule for all five ("alert on any error"), or counting each AER detail line as a
separate event (four lines per event inflates counts 4×).
