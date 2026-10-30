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
