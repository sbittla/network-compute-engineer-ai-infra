# 3.17 — Arguing a threshold in `orion_hx8_baseline.yaml`

Example threshold: `aer_corrected_warn_per_bdf: 10` (lab severity policy `PCIE_AER_CORRECTED`).

**Tighter (for example 3).** Corrected errors are the early warning of a marginal link: retries add
latency variance before any uncorrected error or width drop appears. Section 3.11 shows how expensive a
degraded GPU link is (≈ 339 GPU-h/day), so catching a deteriorating link a few days earlier pays for many
false pages. On `orion-n07`, 37 events in fifteen minutes would be caught at either value, but a slower
deterioration would not.

**Looser (for example 50).** Corrected errors occur on healthy hardware: during link training at boot,
hot-plug, retimer recalibration, or short bursts with no later failure. The reference node `orion-n01`
has two historical events weeks apart. At ORION-XL scale (512 nodes, ≈ 40 PCIe endpoints each), a low
threshold pages on noise every day, and alert fatigue makes the real signal easier to miss.

**Evidence needed to set it.** The per-BDF corrected-error rate distribution across the fleet over weeks,
split by device class (GPU, NIC, NVMe), and correlated with later outcomes: uncorrected errors, width
downgrades, Xids, RMAs. Choose the threshold, ideally as a *rate* per hour rather than a count per
capture, that catches most links that later failed at an acceptable false-positive rate (for example
≤ 1 page per week fleet-wide). Re-check it after hardware or firmware changes.
