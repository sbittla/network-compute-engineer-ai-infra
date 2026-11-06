# K2 — PCIe Gen 1 at idle: defect or power management?

**Verdict: not a defect.** Under burn-in load GPU 0 reports Gen 5 x16, which is the expected link.

**Mechanism.** GPUs (and many NICs) lower the PCIe link *speed* when idle as a power-saving
measure (link-speed power management); the driver retrains to the maximum speed as soon as the
device is busy. `pcie.link.gen.current = 1` on an idle HX8 therefore says nothing about health.
The *width* (`pcie.link.width.current = 16`) is the important field at idle, and it is correct.

**What would make it a defect (Table 16.4, `PCIE_DEGRADED`):**
1. The link stays below Gen 5 **under load** (read `pcie.link.gen.current` during burn-in or a
   bandwidth test, never at idle). That indicates a signal-integrity problem (riser, retimer,
   connector) or a BIOS setting capping the link.
2. The **width** is below x16 at any time. Width does not change with load, so x8 means lanes
   failed to train: a seating, lane, or signal-integrity fault. Bandwidth halves: Gen5 x16 is
   32 GT/s × 16 × 128/130 / 8 ≈ 63.0 GB/s per direction, x8 ≈ 31.5 GB/s per direction
   `[MODELED]` — below a 400 Gb/s (50 GB/s) NIC's line rate if it is the NIC's link.

**Common wrong answers.** Failing the node on idle Gen 1 (about half the GPUs in the lab data show
`gen_idle = 1` as a distractor); checking only speed and ignoring width; quoting bidirectional
bandwidth as the per-direction figure.

Source: Section 16.5 ("Discovery and PCIe topology"), Table 16.4; lab planted fault orion-n11
(GPU3 x8 under load).
