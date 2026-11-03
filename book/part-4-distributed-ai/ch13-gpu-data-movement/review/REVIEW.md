# Editorial Review — Chapter 13

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.15 | Fail (D2 < 9.0; major findings open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | Pass (internal); awaiting independent review |

## Scores by dimension (latest, iteration 2)

| Dim | Score | Justification |
|---|---|---|
| D1 Technical accuracy (20 %) | 9.5 | Copy/crossing counts consistent across tables, worked example, and key; GDR evidence per VERIFIED_FACTS (channel `/GDRDMA` lines, peer-memory or dma-buf); clocks-event naming current; SW thermal slowdown used at 89–90 °C. |
| D2 Depth (15 %) | 9.5 | PCIe-uplink/DRAM bound for host-staged path quantified; `utilization.gpu` spin trap; masking stragglers; rail common-factor reasoning; instrumentation guidance. |
| D3 Pedagogy (15 %) | 9.5 | Required GPU↔GPU, GPU↔NIC, and end-to-end diagrams with captions; decision table for the three causes; worked incident with real rows. |
| D4 Lab (15 %) | 9.5 | 64-rank bundle with three overlapping planted causes, masking, and a decoy; robust statistics; deterministic; L2/L3 extensions. |
| D5 Exercises (10 %) | 9.5 | Standard set + O1–O3 (13.9–13.11) with complete key and marking guidance. |
| D6 Evidence (10 %) | 9.5 | SIMULATED data, MODELED analyses, ILLUSTRATIVE latencies, VENDOR-SPEC validation plan. |
| D7 Cross-layer (5 %) | 9.5 | References Ch 5 for mapping without duplicating it; numbers from Ch 11/12; links Ch 18/19/22 and capstones. |
| D8 Ops/safety (5 %) | 9.5 | Runbook thresholds and owners; read-only validation plan; safety callouts on ACS/IOMMU and throttling. |
| D9 Polish (5 %) | 9.5 | Canonical names (`orion-nNN`, `orion-be-leaf-r2`); figures/tables numbered. |

Weighted = **9.50**.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| 13-1 | Major | §13.11 | "≈ 6 GPU-hours/day per percentage point" arithmetic wrong | Corrected: +0.39 s ≈ 2.2 % ≈ 0.022 × 256 × 24 ≈ 140 GPU-h/day |
| 13-2 | Major | §13.7 | No guidance on how to obtain per-rank phase telemetry | Added instrumentation subsection (CUDA events, arrival skew without synchronized clocks, join keys) |
| 13-3 | Major | lab data | Rank 37 reported `hw_thermal_slowdown` at temperatures where only SW slowdown applies (VERIFIED_FACTS) | Generator now emits `sw_thermal_slowdown`; data regenerated; checks re-run |
| 13-4 | Minor | data, manuscript | `hx8-*` hostnames | Canonical `orion-n21`–`orion-n28`; leaf `orion-be-leaf-r2` |
| 13-5 | Minor | manuscript | 6,931 words (< 7,000) | Added instrumentation content; now 7,238 |

## Release-gate items outstanding

- Hardware validation of Table 13.5 (perftest `--use_cuda`, GDR-off control) on an HX8-class pair.
- Confirm DCGM profiling field IDs (1002–1004) and nvidia-smi `clocks_event_reasons.*` names on the
  publication-time driver.
- Host-staged PCIe/DRAM model (§13.11) should be compared with a measured GDR-off run.

## Independent review iteration 1 + author fixes (2026-10-30)

Independent score 9.20 (fail). validate_labs: all columns OK.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | No mlx5 counter names or flight-recorder variables | New subsection "Where the network and hang evidence comes from": Table 13.4a (`packet_seq_err`, `local_ack_timeout_err`, `out_of_sequence`, `np_ecn_marked_roce_packets`, `np_cnp_sent`, `rp_cnp_handled`, `rx_prio3_pause`), sysfs `hw_counters` and `rdma statistic` commands, `nic_retx` mapping, and `TORCH_NCCL_TRACE_BUFFER_SIZE` / `_DUMP_ON_TIMEOUT` / `_DEBUG_INFO_TEMP_FILE` / `TORCH_NCCL_ENABLE_TIMING=1` (possible `TORCH_FR_BUFFER_SIZE`), all VENDOR-SPEC |
| R-02 | Major | Learners sent to the generator for column meanings | Column table added to lab README; `job_manifest.yaml` now carries column definitions, including the ≈ 25 ms optimizer residual in `step_ms` |
| R-03 | Minor | Non-GDR path described as copy-engine D2H/H2D | NCCL kernel stores to / loads from pinned host buffers; §13.3, Fig 13.3, Table 13.2, §13.11, Summary, key fixed |
| R-04 | Minor | "every ring channel crosses rail 2" | Collective gated by the channels on rail 2 |
| R-05 | Minor | ≈ 150× ratio | ≈ 123× (1.20 TB / 9.81 GB) in §13.1, Summary, Ex 13.1 |
| R-06 | Minor | Fig 13.3 node labels | `orion-n03` / `orion-n04`, `orion-be-leaf-r2`, `orion-be-spine-S` |
| R-07 | Minor | Latency budget vs ≈ 4 µs RTT; ECC row-remap as slowdown | Hardware ≈ 2 µs one way (≈ 4 µs RTT) plus 2–5 µs NCCL software per hop; row-remap replaced by "application clocks locked low" |
| R-08 | Minor | Table 13.5 gaps | ACSCtl pass = `ReqRedir- CmpltRedir-`; DMA-BUF evidence (`--use_cuda_dmabuf`, NCCL INFO); "Enabled for GPU…/HCA…" distance-only caveat; §13.11 uplink marked ILLUSTRATIVE |
| Coord. | Major | Drain/spare pattern | Runbook and incident table: checkpoint, drain (does not move the job), restart without the node or wait for repair |
| Docs | Major | Generator references | Removed or marked instructor copy only |

Author re-score (iteration 3): all dimensions 9.5 → 9.50. Manuscript 7,806 words.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent score 9.38 (one major). validate_labs: all columns OK.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R2-01 | Major | "Clock ≥ 1,950 MHz" validation conflicts with the ≈ 1,830 MHz sustained baseline | Criterion now "SM clock within ≈ 3 % of the peer median under the same load and no thermal clocks-event reasons for 30 min (≈ 1,830 MHz on a dense burn-in)"; Table 13.6 note states that this lighter fine-tuning job's ≈ 1,973 MHz peer clock is a load variation and that throttling is judged against peers under the same load |
| R2-02 | Minor | Job on n21–n28 overlaps inference nodes n25–n32 | Moved to training nodes `orion-n17`–`n24` (generator, data, manuscript, lab/instructor READMEs, manifest); rank 12 → `orion-n18`, 37 → `orion-n21`, 51 → `orion-n23`; checks unchanged and passing |
| R2-03 | Minor | Stale "regardless of what Chapter 11 assumed" | "Chapter 11's step model uses this window (≈ 98 ms exposed)" |
| R2-04 | Minor | `ib_write_lat` reports half the RTT | Reworded: ≈ 2 µs one way is what `ib_write_lat` prints (half the ≈ 4 µs round trip) |

## Independent review r1 (2026-11-01)

Reviewer scores: D1 9.0 · D2 9.0 · D3 9.5 · D4 9.5 · D5 9.0 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.5 → **9.28**
(2 major, 8 minor). check.py at review time: solution 10/10, starter 1/10 graceful.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| N13-01 | Major | Key 13.13 root cause (Fabric Manager down, job runs 3× slow) contradicts NVSwitch behaviour and §13.2 | Verified (CUDA returns "system not yet initialized" without Fabric Manager, so the job fails at start). Key, `answer.md` and `meta.yaml` marking rewritten: primary cause degraded NVLink on one n09 GPU (6 of 18 links, `NV6` vs `NV18`, ≈ 3× TP time); secondary container without IPC/P2P → `via SHM`; Fabric Manager kept as a rejected hypothesis with the reason; tests add `nvlink -e`/DCGM NVLink error fields; busbw expectation uses the book threshold (> ≈ 400 GB/s ⇒ NVLS, ring ≈ 360–380). §13.2 now says a job "does not start, rather than running slowly". `marking.json` regenerated |
| N13-02 | Major | PXN absent; rule 1 and Table 13.2 incomplete | New §13.3 paragraph "PXN: the third policy" consistent with VERIFIED_FACTS (mechanism, ≤ PXB eligibility separate from `NCCL_NET_GDR_LEVEL`, `NCCL_PXN_DISABLE`/`NCCL_P2P_PXN_LEVEL`, `(proxyRank)` channel line, Chapter 12 cross-ref); Table 13.2 PXN row; rule 1 amended; Table 13.5 row 11 (check `(proxyRank)` lines for cross-rail traffic); Summary bullet. Key 13.9's PXN marks are now taught |
| N13-03 | Minor | Latency components sum to 2.4–3.0 µs, text says ≈ 2 µs | Components trimmed and the sum shown explicitly: 1.83–2.33 µs ≈ 2 µs, consistent with `ib_write_lat` RTT/2 |
| N13-04 | Minor | Fig 13.1 fallback shown as cross-socket PCIe P2P | Relabelled as NCCL SHM transport through pinned host DRAM (`via SHM`); caption explains `NCCL_P2P_LEVEL` gating |
| N13-05 | Minor | "≈ 123×" from rounded inputs | "≈ 122× (1.20 TB / 9.81 GB = 122.3)" in §13.1, Summary, key 13.1, 13.1 answer; solver assertion moved to 122 ± 1.0 (outputs unchanged, re-run) |
| N13-06 | Minor | Ex 13.3 omits NODE | Prompt (exercises.md + folder README, kept verbatim), title, index, meta marking, answer and key now cover five labels; GPU 0 ↔ NIC 2 = NODE (PHB accepted if justified); default GDR ≈ PXB so NODE/SYS host-staged. §13.3 now defines all five labels with the book-wide definitions |
| N13-07 | Minor | No NVLink error telemetry | §13.2 adds `nvidia-smi nvlink -e` and DCGM NVLink CRC/replay/recovery fields `[VENDOR-SPEC, 2026-10]`; Table 13.3 intra-node row extended; runbook row "NVLink error rate rising → Fleet, drain at checkpoint" |
| N13-08 | Minor | L2 report: wrong Table 13.5 rows; "negotiated" link is really max capability | `experiment.py` now cites "rows 2-3, 5-8 and 11" and labels the ceiling "maximum-capability link" (kept max: an idle laptop link trains down, so current values are not a ceiling). The same text-only strings were corrected in both committed bundles; no measured value was touched. Lab README wording aligned |
| N13-09 | Minor | Unlabelled comparative figures | `[ILLUSTRATIVE]` on "5–10×", "order of magnitude slower" and "several µs more per message" |
| N13-10 | Minor | Receive-only GDR state not taught | §13.11 paragraph: `NCCL_NET_GDR_READ` gates the send side; `/GDRDMA` on `[receive]` lines only; uplink load halves to 15.3 GB per direction (≥ 0.28 s), DRAM 61.3 GB per socket `[MODELED]` |
| Next-0.5 D4 | — | Checker case for missing rows | New check `missing_samples`: drops 5 % of rows and blanks 1 % of `compute_ms` (seed 13); requires stragglers [12, 37] and rank-37 onset 20–22. Lab README Task 2 acceptance, 11-check counts (README, exercise 13.12 prompt/meta/answer, `lab_checks.json`) and golden reports updated; realism boundary notes it |
| Next-0.5 D9 | — | Table 13.4a appears before Table 13.4 | Renumbered to Table 13.3a (manuscript, lab README) |
| Flight recorder | — | `TORCH_FR_BUFFER_SIZE` default stated flatly as 2,000 | Checked PyTorch main `FlightRecorder.hpp`: `getCvarInt({"TORCH_FR_BUFFER_SIZE", "TORCH_NCCL_TRACE_BUFFER_SIZE"}, 2000)`. Text now says the default is version-dependent (2,000 in current source; some older releases 0 = off) and to set it explicitly |

Rejected: none. Tests after the fixes: `check.py --impl solution` 11/11 PASS; `--impl starter` 1/11 PASS,
graceful; `validate_labs.py ch13` OK (no-generator pass); package harness (`test_package.py`, run locally)
78 passed; `copyedit_lint.py` 0 findings in ch13.

Shared-doc follow-up (not edited here): REFERENCE_CLUSTER Figure R.1 calls GPU0↔NIC2 "PXB/PHB-class";
under the book-wide definitions it is NODE (PHB only if both root ports share one host bridge), never PXB.

Author re-score: D1 9.5 · D2 9.5 · D3 9.5 · D4 10 · D5 9.5 · D6 10 · D7 9.5 · D8 9.5 · D9 9.5 → 9.63.

## Independent review r2 (2026-11-01)

Reviewer scores: D1 9.5 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.0 → **9.475**
(0 major, 6 minor). check.py at review time: solution 11/11, starter 1/11 graceful.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R13-01 | Minor | Rule 1 says any other NIC is `NODE`, but the sibling NIC in the same switch complex is `PXB` | Verified against VERIFIED_FACTS (PXB = several switches, no host bridge; GDR allowed at default). §13.3 now explains the sibling pair (PIX on a single switch, PXB on a two-level HGX-class complex); rule 1 distinguishes sibling `PXB` (GDR kept, two extra switch hops), other complex `NODE`, cross-socket `SYS`; Figure 13.2 caption says GPU3/NIC3 are omitted and SW1 is drawn as one switch. Ex 13.3 answer and key give GPU 0 ↔ NIC 1 as the PXB example |
| R13-02 | Minor | `ethtool -S eth2` non-canonical | `ethtool -S ens3np0` (NIC 2, rail i ↔ ens{i+1}np0) `[ILLUSTRATIVE]` |
| R13-03 | Minor | `[MODELED]` on a qualitative table | Table 13.7 caption: `[ILLUSTRATIVE]` qualitative comparison; quantified in Section 13.11 |
| R13-04 | Minor | Acronyms expanded after first use; PCIe never expanded | Acronym table (30 entries, Chapter 16 format) placed before the learning objectives; the scattered later expansions removed |
| R13-05 | Minor | 13.9 s unexplained | "13.92 s / 128 × 2/3 ≈ 72 ms (13.92 s of compute per GPU per step, Chapter 11, Section 11.10 Step 1; 128 micro-batches = 1,024 / DP 8; backward ≈ 2/3)" |
| R13-06 | Minor | No own end-to-end step diagram | New Figure 13.4: one W-TRAIN step on one GPU (compute 13.92 s; TP 1.20 TB, 4.11 s, 3.08 s exposed; PP 2.15 GB, 0.055/0.028 s; bubble 0.33 s; DP 7.66 GB, 0.170 s, 72 ms hidden, 0.098 s exposed; sum 17.45 s), all from Chapter 11 §11.10 `[MODELED]` |
| Next-0.5 D2 | — | PCIe AER signature; NVLink degradation in per-rank data | New §13.3 paragraph on GPU↔NIC link degradation (`LnkSta` vs `LnkCap`, AER `CESta` bits, `aer_dev_correctable`/`nonfatal`/`fatal`, dmesg) `[VENDOR-SPEC, 2026-10]`; §13.9 step 5 describes the node-wide TP-phase signature (Ex 13.13) |
| Next-0.5 D5 | — | Point splits for 13.15–13.18 | Key now lists the 3 × 1-pt elements per item, matching each `meta.yaml` |
| Next-0.5 D8 | — | Abort criterion for the Fabric rollback | Table 13.6a: abort and restore last known-good if rail-2 retransmissions are not near baseline within 10 min or another rail's counters rise; escalate to change review |
| Next-0.5 D4 | — | Machine-checked findings file | Not done in this round: it changes the lab contract and the 25-pt report rubric; recorded as a candidate for the next lab revision |

Rejected: none. Tests: `check.py` solution 11/11, starter 1/11 graceful; `validate_labs.py ch13` OK;
package harness 78 passed; `copyedit_lint.py` 0 findings in ch13. Manuscript 9,375 words (target
7,000–10,000).

Shared-doc follow-up: REFERENCE_CLUSTER Figure R.1 should say whether each "PCIe SWn" is one switch or
a two-level complex (it decides PIX vs PXB for GPU 2k ↔ NIC 2k+1), and its caption's "PXB/PHB-class"
for GPU0↔NIC2 should read NODE.

Author re-score (estimate; independent re-review pending): D1 9.5 · D2 10 · D3 9.5 · D4 9.5 · D5 10 ·
D6 10 · D7 10 · D8 10 · D9 9.5 → 9.73.
