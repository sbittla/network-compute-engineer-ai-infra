# Editorial Review — Chapter 10

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.08 | Fail (D1, D9 < 9.0; majors open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.48 | Fail (< 9.5) |
| 3 | 2026-10-29 | Author self-review, iteration 3 | 9.50 | Pass (internal, pending independent review) |
| I1 | 2026-10-29 | Independent review, iteration 1 | 9.08 | Fail |
| I2 | 2026-10-29 | Independent review, iteration 2 | 9.28 | Fail |
| I3 | 2026-10-29 | Independent review, iteration 3 | 9.50 | **Pass** (R3-01 minor fixed) |

## Scores by dimension (latest, iteration 3)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20% | 9.5 | KP4 parameters, 425 Gb/s line-rate derivation, codeword rate, binomial FEC table, PMD table, and dB arithmetic re-verified with Python. Vendor/standard values labelled `[VENDOR-SPEC, 2026-10]` with verify notes; vendor CLI shown only as labelled examples. Residual risk: exact NOS command spellings and IEEE clause numbers need external verification. |
| D2 | Depth and production realism | 15% | 9.5 | CRC stomping and upstream localization, bursty vs random errors, FEC histogram tails, lane-imbalance below alarm thresholds, miscabling invisible to error counters on a /31 eBGP fabric, host-link vs uplink drain costs, rate vs Poisson sparing. |
| D3 | Pedagogy and clarity | 15% | 9.5 | Mechanism → numbers → evidence → pitfalls in every section; worked example with every step; required NIC↔switch data-path diagram; counter-to-layer map ties diagrams to diagnosis. |
| D4 | Hands-on lab quality | 15% | 9.5 | Realistic two-snapshot analyzer with 9 planted conditions + 2 decoys (counter reset, busy-but-healthy port), physical vs higher-layer split, commissioning report, BOM/spares, generated cabling schedule; byte-identical regeneration checked; digest avoids leaking answers; L2/L3 extension with real commands and manifest fields. |
| D5 | Exercises and assessment | 10% | 9.5 | Full standard set + 10.M1–M3 outline exercises + 10.M4 deliverable; difficulty and tier tags; evidence lines; key with arithmetic, marking, common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10% | 9.5 | Tables and computed values labelled; simulated vs modeled kept distinct; L3 extension requires ≥ 5 snapshot pairs with median/spread; binomial-model limits stated. |
| D7 | Cross-layer integration | 5% | 9.5 | ORION addressing/fabric numbers reused (8 leaves, 4 spines, 512 links, 17.4 s step); links to Ch 5, 7, 8, 9, 12, 14, 16–19, 21 and Capstones A/B/G. |
| D8 | Operational realism and safety | 5% | 9.5 | Runbook table with thresholds/escalation, drain-before-touch for both link classes, laser safety, lab-only fault injection. |
| D9 | Editorial polish | 5% | 9.5 | Acronyms defined on first use, figures/tables captioned and sequentially numbered, consistent units, relative links to existing folders. Some source lines exceed 100 characters (renders correctly). |

Weighted (iteration 3): 0.20×9.5 + 0.15×9.5×3 + 0.10×9.5×2 + 0.05×9.5×3 = **9.50**.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | manuscript §10.4.3 | Margin for a 3 × 10⁻⁵ link stated as 1.9 decades; correct value log10(8) = 0.9 decades. | Fixed (it. 1→2); all margins recomputed. |
| F2 | Major | manuscript | 11,008 words (`wc -w`), above the 10,000 ceiling. | Trimmed to 9,993 without removing mandated content (it. 2–3). |
| F3 | Major | manuscript (throughout) | Acronyms used before definition: ASIC, PAM4, NRZ, MMU, PFC, ECN, QSFP-DD, OSFP, OIF, SMF/MMF, MPO, CWDM, LLDP, BFD, ECMP, NCCL, NOS, RMA, DSP. | Fixed (it. 2). |
| F4 | Minor | §10.15 evidence | `packet_seq_err` is a requester-side counter; shown on the receiving NIC. | Removed; `out_of_sequence` retained (it. 2). |
| F5 | Minor | §10.15 tests | ECMP hash location stated at the leaf; corrupted direction is spine→leaf so the hash is at spine-2. | Fixed (it. 2). |
| F6 | Minor | §10.13 | Worked example said "analyzer flags warning" for a 2.7 dB imbalance, contradicting the lab's 3 dB policy. | Reworded as a > 2 dB review list (it. 3). |
| F7 | Minor | Review question 1 | Corrected codewords per hour inconsistent with stated BER. | Fixed to ≈ 8 × 10⁷/h (it. 2). |
| F8 | Minor | exercises 10.M2 P3; key Ethernet18 | Corrected-CW counts inconsistent with BER (P3 1.2e6 → 5.1e6; Ethernet18 1.7e10 → 1.5e8). | Fixed (it. 2). |
| F9 | Minor | §10.1 | "Most RoCEv2 NICs use go-back-N" over-generalized. | Hedged; selective repeat noted (it. 2). |
| F10 | Minor | Table 10.2 | SR8 connector "2 × MPO-12" doubtful. | Changed to MPO-16 or MPO-24 (it. 2). |
| F11 | Minor | §10.10 | "No error counter anywhere" for miscabling ignored BGP-down alarms. | Clarified (it. 2). |
| F12 | Minor | Prerequisites | Links to sibling manuscripts that may not exist yet. | Linked to chapter folders (it. 2). |
| F13 | Minor | lab/check.py | Message referenced "Ch 7" for ORION BOM numbers. | Now "ORION reference" (it. 2). |

## Release-gate items outstanding

- Independent technical review by a practising AI-fabric/optics engineer (especially Table 10.2,
  DR4 power limits from IEEE 802.3bs clause 124, the 2.4 × 10⁻⁴ KP4 design point, and the claim that
  400GBASE-R interleaves two codewords).
- Verify vendor command examples against current releases: `ethtool -I --show-fec`, mlx5 counter
  names, `mlxlink -m/-c`, Arista EOS `show interfaces ... phy detail`, SONiC
  `show interfaces transceiver eeprom --dom`.
- L3 extension not yet executed on hardware; L2 `ethtool -m` output is illustrative.
- Shared-doc note: REFERENCE_CLUSTER.md states 64 × 400G leaf ports on a 51.2 Tb/s-class ASIC. This
  chapter resolves it explicitly as 64 single-port 400G modules (25.6 Tb/s used); the reference doc
  could state that assumption so other chapters agree.

---

## Independent review iteration 1 + author fixes (2026-10-29)

Independent reviewer score: **9.08** (gate fail). The author fixed every finding, working only in ch10.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | DR4 Rx warn −6.0 / alarm −9.0 dBm sat below the −5.9 dBm receiver minimum | Policy is now warn −4.0 / critical −5.9 dBm. Module-programmed −6/−9 are kept as informational only. Updated in thresholds.yaml (regenerated), code (`rx_power_low_crit_dbm`), runbook, Table 10.8, Figure 10.4 caption, DOM section, key (Ethernet7 and M2-P5 now critical; totals 6 critical / 1 warning), and check.py (critical = 6). Ethernet21 Rx moved to ≈ −3.4 dBm so it stays a pure BER case. Classification digest unchanged. |
| R-02 | Major | §10.15 blamed a same-rail job on a spine link | Scenario is now an MoE variant whose expert-parallel all-to-all runs with a stray `NCCL_PXN_DISABLE=1`, so cross-rail traffic crosses the spines. Postmortem removes the variable. |
| R-03 | Major | Uplink drain cost given as raw 3.1 % only | Added ECMP-aware ingress 4 × 7 × 400 = 11.2 Tb/s (−12.5 %), with the reason: the spine keeps advertising, remote leaves still send it 1/4, and it delivers spine→leaf over 7 links. Cites Section 7.9 and Table 7.8. Applied in §10.13, §10.15 and the key. |
| R-04 | Major | No derivation of pre-FEC BER from counters | Added BER ≈ Δcorrected_bits / (425e9 · Δt) with a worked number (4.2e-9). States the line-rate assumption, why codeword counts can't give BER, and the low bias from uncorrectable codewords. |
| R-05 | Major | 10.T1 put checkpoint traffic on the backend | Trigger is now a nightly MoE all-to-all job; the exercise states that checkpoints use frontend/storage NICs. Key updated. |
| R-06 | Minor | NIC CRC count inconsistent with leaf FCS | Now +452 per NIC; 6 × ≈ 450 ≈ 2,700 vs 2,731 is stated. |
| R-07 | Minor | Frame size and BFD timing not aligned with Ch07 | Frame is 62 B overhead → 4,158 B (4,174 with RETH), serialization 83.5 ns. BFD 300 ms × 3 ≈ 0.9 s. |
| R-08 | Minor | Lengths and figure values didn't match the CSV | Generator pins Ethernet14 = 43 m, Ethernet21 = 38 m, Ethernet40 = 12 m. Canonical names applied (orion-n01..32 on EthernetNN; rack-04/rack-06). Figure 10.4 is now the NIC end of Ethernet14 and matches the worked example. |
| R-09 | Minor | SONiC port naming | Now Ethernet160 (port 21 under 8-lane naming). |
| R-10 | Minor | Check naming and bytecode | Link-budget case renamed. `sys.dont_write_bytecode = True` added; `__pycache__` folders removed. |
| R-11 | Minor | Table 10.4 mixed dBm and dB | Split into dBm→mW and dB→fraction-remaining tables. |
| R-12 | Minor | Missing example outputs | Added `ethtool -I --show-fec`, `mlxlink --rx_fec_histogram --show_histogram`, and SONiC `show interfaces counters fec-stats` (new Figure 10.6; commissioning figure renumbered to 10.7). All labelled ILLUSTRATIVE / VENDOR-SPEC 2026-10 verify. The mlxlink flags are confirmed in the NVIDIA MFT docs; the exact SONiC FEC column names could not be confirmed from public docs and are flagged as such. |
| Cuts | — | Length | Media table shrunk, NVIDIA note compressed, §10.1 scale paragraph removed, Agrawal dropped. Manuscript is 10,359 words (`wc -w`). |

### Re-scores (author, after fixes)

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | Weighted |
|---|---|---|---|---|---|---|---|---|---|
| 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | **9.50** |

Validation: `check.py --impl solution` 13/13; starter 1/13 (TODOs, no traceback); `validate_labs.py ch10` OK.
Outstanding: verify the SONiC `fec-stats` columns and the mlxlink histogram layout on real releases. The external review gates are unchanged.

---

## Independent review iteration 2 + author fixes (2026-10-29)

Independent re-review score: **9.28**. The author fixed every item, working only in ch10.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R2-01 | Blocker | `dataset_reproducible` would FAIL in the student release, which strips `lab/tools/`. Docs also pointed students at the generator. | The check now returns SKIP when the generator is absent. SKIP is excluded from the required count, so the solution still exits 0. Lab README and chapter README file map now say "instructor copy only". `validate_labs.py ch10` passes all columns, including no-generator. |
| R2-02 | Major | Ethernet21 (pre-FEC BER 1.6e-4) was graded warning while the runbook pages at ≥ 1e-4 | Added `pre_fec_ber_crit: 1.0e-4` to thresholds.yaml (regenerated); the classifier and starter docstring use it. Ethernet21 is now critical, and check.py expects critical = 7. Key totals (7 critical / 0 warning), M1 and M4 marking, lab README, and the runbook row (warn vs critical actions) are aligned. The classification digest is unchanged. |
| R2-03 | Minor | Non-canonical `spine-2` / `leaf-r5` in §10.15 | Uses `orion-be-spine-2` in prose. The evidence table uses abbreviations S2/L5 with a footnote mapping them to canonical names. |
| R2-04 | Minor | Figure 10.5 mixed a cumulative counter with a windowed histogram | Labelled: `ethtool` blocks are cumulative since link up; the histogram covers a 600 s window after `--clear_histogram`. The caption explains why they are not comparable. |

Re-scores (author): D1–D9 all 9.5 → weighted **9.50**. Manuscript 10,408 words (`wc -w`). Validation: solution 13/13; starter 1/13 (graceful); no-generator pass.


---

## Independent review iteration 3 (2026-10-29)

Passed at 9.50. R3-01 (minor): key row for Ethernet21 now says "drain now (host link: coordinate a node drain through the scheduler), then clean/replace", matching the critical runbook action.
