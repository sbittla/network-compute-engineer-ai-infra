# 10.K5 — 400GBASE-DR4 vs 400GBASE-FR4

Values `[VENDOR-SPEC, 2026-10]` per IEEE 802.3bs/802.3cu and Table 10.2 (Section 10.5.2).

| | 400GBASE-DR4 | 400GBASE-FR4 |
|---|---|---|
| Medium | Single-mode fiber (SMF) | Single-mode fiber (SMF) |
| Connector | MPO-12 (parallel) | Duplex LC |
| Fibers used | 8 (4 Tx + 4 Rx; 4 of 12 positions dark) | 2 (1 Tx + 1 Rx) |
| Wavelengths | 1 × 1310 nm on each of 4 parallel fibers | 4 CWDM wavelengths (1271/1291/1311/1331 nm) multiplexed on one fiber |
| Lane structure | 4 × 100 Gb/s PAM4, one lane per fiber | 4 × 100 Gb/s PAM4, one lane per wavelength |
| Reach | 500 m | 2 km |

**Can a DR4 module link to an FR4 module? No.** The two use different connectors (MPO-12 vs duplex
LC), a different lane structure (four parallel fibers at one wavelength vs four wavelengths on one
fiber) and different optical specifications, so the light one transmits is not what the other's
receiver expects; no patch cord fixes that.

**Related but different.** A DR4 port *can* break out to four 100GBASE-DR modules (each one lane, one
fiber pair, 1310 nm) with an MPO-to-4×LC breakout; that is a breakout, not FR4 interoperability.

**Why it matters operationally.** A link with mismatched optics stays down with LOS on all lanes; the
fix is the part, not cleaning (lab port Ethernet45 is the same lesson with SR8 vs DR4). DR4's eight
fibers also cost four times the trunk fiber count of FR4, which drives the 10.D1 choice for long
cross-hall runs.

**Common wrong answers.** "FR4 uses 8 fibers"; "both use MPO"; "they interoperate at reduced reach".
