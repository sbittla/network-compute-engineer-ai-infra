# Editorial Review — Chapter 19

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.15 | Fail (open majors) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.53 | Pass (internal) |
| I-1 | 2026-10-30 | Independent reviewer, iteration 1 | 9.15 | Fail |
| I-2 | 2026-10-30 | Independent reviewer, iteration 2 | 9.50 | Pass |
| 3 | 2026-10-30 | Author fixes for iteration-2 findings | see below | Submitted |

## Scores by dimension (latest)

| # | Dimension | Weight | Iter 1 | Iter 2 | Justification (iteration 2) |
|---|---|---|---|---|---|
| D1 | Technical accuracy | 20 % | 9.0 | 9.5 | Xid table with 94/95 handling per docs/VERIFIED_FACTS.md; NCCL_IB_TIMEOUT default stated by version (18 ≤ 2.22, 20 ≥ 2.23); retry-budget arithmetic matches the lab timing; row-remapper semantics; DR4 RX-power thresholds; all labelled VENDOR-SPEC. |
| D2 | Depth and production realism | 15 % | 9.5 | 10 | Section 20.1 covered end to end: taxonomy, signatures, isolation path, containment with fault domain vs scheduling unit, evidence preservation, recovery, retry-loop cost quantified, spares sized. |
| D3 | Pedagogy and clarity | 15 % | 9.0 | 9.5 | Five figures (fault domains, isolation path, GPU↔HCA↔switch data path, recovery state machine, tenant layers); nine-step worked example. |
| D4 | Lab quality | 15 % | 9.5 | 9.5 | 12 checks; one flaky HCA, one ECC fault, NCCL timeout, plus five red herrings, unsafe checkpoint, bad spare, FMEA and isolation errors; SKIP without generator. |
| D5 | Exercises and assessment | 10 % | 9.0 | 9.5 | Standard set + M1–M4 covering risk register, isolation model, recovery test plan, 512-node incident evidence pack. |
| D6 | Measurement rigor / labels | 10 % | 9.0 | 9.5 | Canonical MTBF 1,536 h / restart 15 min used and labelled; proven-vs-correlated framework with intervention requirement. |
| D7 | Cross-layer integration | 5 % | 9.0 | 9.5 | orionxl-nNNN names; ties to Ch 5, 10, 14, 16–18, 20–21, Capstones F/G. |
| D8 | Operational realism and safety | 5 % | 9.5 | 9.5 | Read-only-until-step-4 runbook; safety callouts on resets and link disables. |
| D9 | Editorial polish | 5 % | 9.0 | 9.0 | 9,362 words; acronyms defined; some long tables. |

Weighted: iteration 1 = 0.20×9.0 + 0.15×9.5 + 0.15×9.0 + 0.15×9.5 + 0.10×9.0 + 0.10×9.0 + 0.05×(9.0 + 9.5 + 9.0) = 9.18; iteration 2 = 0.20×9.5 + 0.15×10 + 0.15×9.5 + 0.15×9.5 + 0.10×9.5 + 0.10×9.5 + 0.05×(9.5 + 9.5 + 9.0) = 9.55. Lowest dimension 9.0 (D9).

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | §19.3 Table 19.3 | Xid 94/95 actions did not match verified handling. | 94: drain when convenient, then reset; 95: drain immediately. Key K3 updated. |
| F2 | Major | §19.4, §19.11, W2 | NCCL_IB_TIMEOUT default stated without version. | Version-dependent default stated; lab assumes a 2.21-class build; W2 explores 20. |
| F3 | Major | Package | Node names (xl-nNNN, 0-based) not canonical. | orionxl-n001..n512 (1-based), orionxl-be-leaf-rR-gGG, orionxl-sNN spares; data regenerated; text and key updated. |
| F4 | Major | Reliability numbers | Needed to match the canonical assumptions. | MTBF 1,536 h, 48 h / 3 h job MTBF, restart 15 min used throughout (§19.1, §19.7, W1, W2). |
| F5 | Minor | §19.11 | Optic power interpretation lacked the receiver-sensitivity anchor. | Added DR4 ≈ −5.9 dBm sensitivity and warn/critical thresholds. |
| F6 | Major | lab/check.py | Failed with generator stripped. | SKIP without tools/; READMEs mark generator instructor-only. |
| F7 | Minor | §19.11 | "43 min" vs data 42.3 min. | Corrected to 42 min. |

## Release-gate items outstanding

- External review by a GPU-cluster reliability engineer; verify Xid table and row-remapper behaviour
  against current NVIDIA documents per GPU generation.
- Verify PyTorch watchdog default and flight-recorder variables for the PyTorch release in use.
- Run the L3 link-flap survival trials on a dedicated partition to convert the retry-budget model into
  `[MEASURED]` evidence.

## Independent review iteration 1 + author fixes (2026-10-30)

Independent score: 9.15 (fail). All findings resolved; data regenerated; labs re-validated.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | Spare pool undeclared, 3-day MTTR | Declared variation outside the partition, Poisson P99 at 5-day MTTR: mean 40 → 55 nodes (orionxl-s00–s54, 10.7 %); lab's 8 entries explained (47 already substituted); W2(c) key uses quantiles (36 at 3 d, 55 at 5 d) |
| R-02 | Major | Elastic granularity wrong | One DP replica = 8 nodes; re-packed 59 replicas (−7.8 %) vs not re-packed expected ≈ 33 left / worst 24; DP 59 batch divisibility; D1 and key recomputed |
| R-03 | Major | §20.1 checkpoint depth | New subsection: DCP `async_save`, Megatron `--async-save` (torch_dist), staging, persisting, commit consistency boundary; Table 19.6 metrics from the lab (72 s completion latency, unsafe window, detect/reschedule/restore decomposition) |
| R-04 | Minor | Watchdog citation | PyTorch 2.x `init_process_group` docs; `TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC`; large jobs raise timeouts |
| R-05 | Minor | MPS wording | Separate address spaces; gaps are capacity, performance, and shared fault exposure (manuscript, Table 19.7, K7 key) |
| R-06 | Minor | Missing Xids | 119/120 (GSP), 154, NVSwitch SXid and fabric-manager behaviour added |
| R-07 | Minor | −7.8 dBm steady unrealistic | DOM now marginal (−5.6 to −6.4 dBm) around DR4 sensitivity; host TX −5.8 dBm; arithmetic re-derived |
| R-08 | Minor | RTO vs canonical 15 min | Reconciled: watchdog + 16-min requeue + 12-min restore; improvement path stated |
| R-09 | Minor | Naming/addressing | orionxl-be-leaf-pPP-rR, orionxl-be-spine-p06-03, host links 10.(130+R) — data, checker, text |
| R-10 | Minor | Xid PCI format | Data now `(PCI:0000:5d:00)`; checker parses the Xid from events.jsonl |
| R-11 | Minor | M3, VNI vs P_Key | M3 requires a tabletop run report; tenants.yaml comments; switch-side P_Key enforcement |
| R-12 | Major | Spares conflict in T1 key and §19.13 | T1 key: checkpoint + `scontrol requeue`, borrow node or wait, break-even 5.6 h; §19.13 rewritten for the 24-node partition with a borrowed inference node |

Also fixed: GPUDirect RDMA evidence wording aligned with docs/VERIFIED_FACTS.md (`/GDRDMA` channel
lines; DMA-BUF); tables renumbered in order. Author re-score: D1 9.5, D2 10, D3 9.5, D4 9.5, D5 9.5, D6 9.5,
D7 9.5, D8 9.5, D9 9.0 → 9.55. Manuscript 9,988 words.

## Independent review iteration 2 + author fixes (2026-10-30)

Independent score history: 9.15 → 9.50.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R2-01 | Minor | Canonical restart includes detect | Reconciliation states detect + reschedule + restore + warm-up with early hang detection |
| R2-02 | Minor | Megatron async-save mechanics | Background process writes; finalisation (metadata commit) called from the training loop |
| R2-03 | Minor | Long lines | Prose paragraphs reflowed to ≤ 112 characters (tables unchanged) |
