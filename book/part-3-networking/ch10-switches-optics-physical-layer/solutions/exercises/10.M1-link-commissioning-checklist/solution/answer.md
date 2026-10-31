# 10.M1 — Link commissioning checklist for ORION backend links

Thresholds are ORION policy `[ILLUSTRATIVE]` unless marked `[VENDOR-SPEC, 2026-10]`. Model:
Table 10.8 and the state machine of Figure 10.7 (Section 10.11). Acceptance thresholds are stricter
than in-service alert thresholds so that a new link starts with margin to lose.

| # | Area | What to check | Evidence source | Pass criterion | On failure |
|---|---|---|---|---|---|
| 1 | Port configuration | Speed, breakout, FEC mode, MTU, description | Running config vs intent diff (NOS `show running-config interface`, config management) | 400G, breakout as designed, RS-FEC (KP4) on, MTU 9216, description = cable ID | Fix config under change control; recheck |
| 2 | Transceiver compatibility | Module vendor PN, firmware, PMD type at both ends | NOS transceiver inventory; host `ethtool -m <if>` | PN on the approved list for the platform and NOS release; PMD equals schedule at both ends (DR4 ↔ DR4) | Replace the module with an approved part; never clean a wrong part |
| 3 | Optical power | Per-lane Rx and Tx at both ends | DOM: NOS transceiver DOM, `ethtool -m` | Rx ≥ −4.0 dBm per lane (policy; −5.9 dBm is the DR4 receiver minimum `[VENDOR-SPEC, 2026-10]`); lanes within 3 dB; Tx, bias, temperature inside module thresholds; measured loss within 1 dB of the design budget | Inspect/clean both ends (IEC 61300-3-35); re-measure; replace jumper, then optic |
| 4 | Lane health | Pre-FEC BER, FEC histogram, link training | NOS FEC counters; `ethtool -I --show-fec`; `mlxlink --rx_fec_histogram` on hosts | Pre-FEC BER < 10⁻⁶ (≥ 2.4 decades margin to 2.4 × 10⁻⁴); histogram tail empty above bin ≈ 8 | Clean and retest; swap optic; escalate to vendor if it persists |
| 5 | Error counters | FEC uncorrectable, FCS/CRC, link-down events | Counter deltas over the soak (switch and host) | Zero uncorrectable and zero FCS during a **≥ 30-minute loaded soak**; link-down counter unchanged | Do not accept; treat as a physical fault (Section 10.8.1) |
| 6 | Cable labelling and topology | Labels on both ends; LLDP neighbour | Physical audit/photo; LLDP vs cabling schedule | Both ends labelled with cable ID and endpoints; LLDP = schedule `b_device:b_port` | Re-label; trace and re-patch; keep routing disabled until LLDP matches |
| 7 | Baseline | Snapshot stored | Commissioning record | DOM, BER, counters with timestamp and module serials recorded | Repeat the snapshot |

**Soak.** At least 30 minutes of loaded traffic (e.g. an all-to-all or rail-pinned all-reduce at
line rate) before acceptance; links return to service after any repair through the same gates.

**Common mistakes.** No soak; acceptance thresholds equal to alert thresholds (−5.9 dBm or 10⁻⁵ at
acceptance leaves no margin); using module-programmed alarms (−6/−9 dBm) as pass criteria.
