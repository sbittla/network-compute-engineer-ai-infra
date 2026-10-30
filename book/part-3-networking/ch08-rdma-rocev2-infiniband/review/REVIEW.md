# Editorial Review — Chapter 8: RDMA, RoCEv2, and InfiniBand

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 8.90 | FAIL (D1, D9 < 9.0; 4 major) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.475 | FAIL (weighted < 9.5; D9 = 9.0) |
| 3 | 2026-10-29 | Author self-review, iteration 3 | 9.50 | PASS (internal; pending independent review) |

## Scores by dimension (latest — iteration 3)

| # | Dimension | Weight | Iter 1 | Iter 2 | Iter 3 | Justification (iteration 3) |
|---|---|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 8.5 | 9.5 | 9.5 | Verbs semantics, QP transitions, BTH fields, RoCEv1/v2 annexes, LID ranges, P_Key membership, credit-based FC, ACK-timeout formula, and CQE status codes checked. Go-back-N cost model corrected. Version-sensitive items (NCCL env defaults, selective repeat, adaptive routing, mlx5 counter names, `show_gids`/`mlnx_qos`) labelled vendor-specific or `[VENDOR-SPEC, 2026-10]`. |
| D2 | Depth and production realism | 15 % | 9.0 | 9.5 | 9.5 | Failure signatures with counters (out_of_sequence vs packet_seq_err vs local_ack_timeout_err), tail-loss expected-cost model, MTU at three layers, GID-index trap, PortXmitData ×4 trap, pingpong default-MTU trap, switch-side gaps. |
| D3 | Pedagogy and clarity | 15 % | 9.0 | 9.5 | 9.5 | Mechanism-first progression (cost of kernel → verbs → wire → IB → loss → MTU → rails → comparison → tools); worked example predicts then interprets; 7 figures with captions including the mandated TCP-vs-RDMA and NIC↔switch data paths. |
| D4 | Hands-on lab quality | 15 % | 9.0 | 9.5 | 9.5 | Real admission-pipeline task; byte-identical seeded data; 7 planted readiness faults (16 findings) + 2 perftest anomalies + distractors; hashed expectations give progress without spoilers; clean-node false-positive check; L3 extension with exact commands and manifest fields. |
| D5 | Exercises and assessment | 10 % | 9.0 | 9.5 | 9.5 | 20 exercises: 7 knowledge, 2 worked, 3 outline-mandated (data paths, RoCE/IB comparison, readiness checklist), lab + L3, troubleshooting, design, 4 reflection; all tagged ★/tier/evidence; key has arithmetic, marking points, and common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.0 | 9.5 | 9.5 | All tables captioned with labels; worked-example measurement reports repetitions and spread; synthetic perftest labelled `[SIMULATED]`; MODELED formulas shown; L3 requires ≥ 5 runs, warm-up, NUMA pinning, manifest. |
| D7 | Cross-layer integration | 5 % | 9.0 | 9.5 | 9.5 | ORION addressing, QoS, HX8 topology, PCIe Gen5 ceiling, NUMA, Slurm/Kubernetes drain, NCCL, Chapters 3/5/7/9/10/12/13/17/19/20 and Capstones A/B/H cross-referenced. |
| D8 | Operational realism and safety | 5 % | 9.5 | 9.5 | 9.5 | 17-item checklist with read-only flags, alert thresholds, drain-first safe actions, no switch changes from host incidents, Safety callouts on perftest and L3. |
| D9 | Editorial polish | 5 % | 8.5 | 9.0 | 9.5 | Iteration 3 polish: acronyms defined on first use; all 7 figures and 11 tables captioned and numbered in order; spelling normalised (British prose, `[MODELED]` labels as specified); relative links verified (links to Chapters 5 and 13 resolve once those parallel packages land — folders exist); 9,998 words by `wc -w`. |

Weighted (iteration 3) = 0.20×9.5 + 0.15×9.5 + 0.15×9.5 + 0.15×9.5 + 0.10×9.5 + 0.10×9.5 + 0.05×9.5 +
0.05×9.5 + 0.05×9.5 = **9.50**. Lowest dimension: 9.5 (all dimensions).

Iteration 2 weighted = 9.025 (D1–D8 at 9.5, i.e. 0.95 × 9.5) + 0.05 × 9.0 = 9.025 + 0.450 = 9.475 — below
the 9.5 gate, so a third (polish) iteration was required.

Iteration 1 weighted = 0.20×8.5 + 0.15×9.0×3 + 0.10×9.0×2 + 0.05×9.0 + 0.05×9.5 + 0.05×8.5 = 1.70 + 4.05 +
1.80 + 0.45 + 0.475 + 0.425 = 8.90.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | manuscript §8.6 | Mid-message go-back-N penalty counted the whole remainder of the message (and later double-counted detection + waste). Only ≈ one bandwidth-delay product is wasted (≈ 1 RTT). | Rewritten: ≈ 48 packets ≈ 4.0 µs ≈ 9 %; added tail-loss expected-cost model (p × T_ack) with arithmetic; key 8.9 aligned. |
| F2 | Major | manuscript (whole) | 12,417 words, above the 10,000 ceiling. | Removed redundant tools table and IB/perftest output duplication; tightened prose; 9,998 words. |
| F3 | Major | manuscript §8.13 | Scenario cited a 64-node job; ORION has 32 nodes. | Changed to a 16-node job. |
| F4 | Major | manuscript §8.11 vs lab data | Worked example commissions `orion-n01` rail 3 as healthy while the lab planted an MTU fault on exactly that NIC. | Moved the MTU fault to `orion-n06` rail 3; regenerated data and checker hashes; PLANTED_FAULTS and key updated. |
| F5 | Minor | manuscript §8.10 | `ib_read_lat` described both as half-RTT and full-RTT. | Clarified: write/send lat report half a ping-pong; read lat times a full READ. |
| F6 | Minor | exercises 8.15 | Evidence implied `ibv_rc_pingpong -s 4096` fails under a 1,500-byte switch MTU; its default path MTU is 1,024, so it would pass. | Evidence now says default pingpong passes; key explains the trap and uses `-m 1024` in perftest as the discriminating test. |
| F7 | Minor | manuscript §8.13 | GID-index root-cause narrative (host group "lacking link-local entries" where index 2 was correct) was not self-consistent. | Rewritten as a hard-coded value copied from a group with different GID-table ordering. |
| F8 | Minor | manuscript | Acronyms PFC, ECN, ECMP, DCQCN, HCA, SFD, FCS, VCRC, TSO/GRO, NAPI used before definition. | Defined or rephrased. |
| F9 | Minor | manuscript §8.12/runbook | Claimed the lab automates checklist items 1–12; it does not check item 11 (`NCCL_IB_TC`). | Corrected to items 1–10, 12, and 13 (correlation). |
| F10 | Minor | manuscript §8.6 | Chapter 9 relies on Chapter 8 introducing the DCQCN roles. | Added notification/reaction/congestion point definitions tied to `np_`/`rp_` counters. |
| F11 | Minor | lab data | Perftest campaign looks healthy on NICs that the inventory shows as faulty. | Documented in lab README: perftest campaign predates the 2026-10-12 inventory; independent evidence. |
| F12 | Minor | manuscript tables | Worked-example and alert tables lacked captions/labels after renumbering. | Captions added; Tables 8.1–8.11 numbered in order; cross-references in lab README and key updated. |
| F14 | Minor | all files | Mixed "modeled"/"modelled" spelling in prose. | Normalised to "modelled" (labels stay `[MODELED]`). |
| F15 | Minor | manuscript §8.10 | Tools intro still pointed at a removed table and repeated the label sentence. | Rewritten to reference Table 8.10. |
| F13 | Minor | key 8.4 | RoCEv1 drop explanation ("not for a MAC on the segment") imprecise. | Rewritten: frame addressed to leaf MAC but non-IP, so unroutable. |

No open blocker or major findings.

## Verification performed

- Arithmetic re-checked twice: Table 8.4 (82-byte overhead; 92.6 / 96.2 / 98.0 %; 370.3 / 384.6 /
  392.1 Gb/s; 45.2 / 23.5 / 11.97 Mpps), Table 8.3 (67.1 ms, 1.07 s, 4.29 s; ×8), n½ = 4,261 B,
  BW(4 KiB) = 192 Gb/s, BW(8 KiB) = 258 Gb/s, PCIe Gen5 x16 = 504 Gb/s raw, BDP 196 KB ≈ 48 packets,
  2 MiB = 42.8 µs, tail-loss 39 % goodput at p = 10⁻³ / `timeout` 14, `NCCL_IB_TC` = 106, key 8.8/8.9/8.15.
- `python lab/check.py --impl solution` → 14/14 PASS; `python lab/check.py` → 14 TODO, exit 1, no traceback;
  `python scripts/validate_labs.py ch08` → OK. Generator re-run → byte-identical files.

## Release-gate items outstanding

- Independent review by a practising RDMA/fabric engineer (outline release gate).
- Verify against current primary documentation: perftest option list and output columns;
  `ibv_rc_pingpong` default path MTU; `dcb app`/`dcb pfc` output formats; mlx5 `hw_counters` names;
  `show_gids` format; NCCL `NET/IB` warning format and `NCCL_IB_TIMEOUT`/`NCCL_IB_RETRY_CNT` defaults;
  which NIC generations/firmware enable selective repeat by default.
- Run the L3 extension on real hardware and record a `[MEASURED]` manifest; compare to Section 8.11.

---

## Independent review iteration 1 + author fixes (2026-10-29)

Independent score: **9.23 (FAIL)**. Lab valid and deterministic; arithmetic verified. The author re-read
docs/VERIFIED_FACTS.md (new), the updated docs/REFERENCE_CLUSTER.md (canonical names, RTTs), and
docs/LAB_STANDARDS.md (generator stripped from student release; regeneration checks must SKIP).

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R8-01 | Major | §8.6 "tail loss dominates" and key 8.9(d) assume the QP idles after each message. | Assumption stated ("isolated messages"); added that, for back-to-back traffic, the next packet triggers a NAK, so timeout exposure is per burst; 8.9(d) reworded to isolated messages, with the back-to-back case and a common-mistake note in the key. |
| R8-02 | Major | Checklist treated `nvidia_peermem` loaded as GDR proof. | Item 12 now marked "necessary, not sufficient"; new item 15 checks ACS/IOMMU (`lspci -vvv` ACSCtl); item 19 adds `ib_write_bw --use_cuda=<gpu>` per rail. |
| R8-03 | Major | No memlock check. | New item 16: `ulimit -l` unlimited in a shell, inside a Slurm job, and inside the container. New item 17: per-rail `ip rule`/`ip route table`/`ip neigh`. Policy routing moved out of item 7. |
| R8-04 | Minor | "No tuning knobs" for `ibv_rc_pingpong`. | Knobs listed (-d/-g/-s/-n/-m); default path MTU 1,024 passes through 1,500-MTU switch ports, so use `-m 4096`; checklist item 19 uses `-m 4096`. |
| R8-05 | Minor | Step 6 tied BDP to PFC headroom; RTT not from REFERENCE_CLUSTER. | Headroom described as cable/response terms on one link (Chapter 9). RTTs are 4 µs same-rail and 5 µs cross-rail; exercise 8.9 and its key recomputed at 5 µs (60 packets, 5.0 µs, 23 %). |
| R8-06 | Minor | "51.2 Tb/s-class" leaf; ECMP-collision claim applied to same-rail traffic; exercise 8.9 rails unstated. | Table 8.6 now says `orion-be-leaf-r3`, 64 × 400G = 25.6 Tb/s in use, with re-derived latency budget (1.4–1.9 µs one way, cross-rail +0.5–0.8 µs, consistent with the 4/5 µs RTTs). §8.4 states that same-rail traffic crosses one leaf, so ECMP collisions affect cross-rail traffic only. Exercise 8.9 is GPU 2 → GPU 5 (different rails). |
| R8-07 | Minor | Item 9 lacked trust-mode evidence. | Item 9 adds `dcb apptrust show dev <if>` or `mlnx_qos -i <if>`, with criterion trust = DSCP. |
| R8-08 | Minor | NCCL WARN format unversioned. | Labelled as the NCCL 2.2x format `[VENDOR-SPEC, 2026-10]`, version-dependent. Timeout defaults now explicit: 18 up to 2.22, 20 from 2.23. |
| R8-09 | Minor | Lab-coverage statements were inconsistent. | One wording everywhere (manuscript §8.12 and runbook, lab README, key): "automates items 1–10 and 12 and correlates item 13 with perftest results". |
| R8-10 | Minor | "NCCL registers buffers at communicator creation." | Corrected: internal buffers are registered at connection setup (possibly lazily); user buffers are registered with `ncclCommRegister`. |
| R8-11 | Minor | BTH figure misaligned; timeout = 0 not explained. | Figure 8.5 redrawn with all rows 66 columns wide; T_ack line notes that timeout = 0 means infinite. |
| Cuts | — | Requested cuts. | Removed the perfquery subsection (its traps folded into §8.5), the Table 8.1 lead-in (folded into the caption), and the §8.9 closing paragraph. Merged summary bullets and corrected the go-back-N bullet (≈ 1 RTT per mid-stream loss). |
| Names | — | Canonical names. | Lab nodes renamed `orion-n01`…`n08` (`rack-01`/`rack-02`); data regenerated; hashes updated. Perftest flags are now n05-n06 rail 5 (PCIe x8, 202 Gb/s, within the 200–220 Gb/s x8 range) and n07-n08 rail 2. Exercise 8.15 uses `rack-04` = n13–n16. Leaves named `orion-be-leaf-rR`. |
| Policy | — | Generator stripped in the student release. | `check.py` gained `data_regenerates_identically`, which SKIPs when `lab/tools/` is absent. Verified: with tools present, 15/15 PASS; with tools renamed, 14/14 PASS + 1 SKIP (exit 0); starter exits 1 in both cases. Lab README no longer tells students to run the generator. |

Manuscript length after fixes: 10,269 words (`wc -w`, ≤ 10,500 per coordinator). `python
scripts/validate_labs.py ch08` → OK.

Author re-score after fixes: D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 9.5, D8 9.5, D9 9.5 →
weighted 9.5. This is pending independent re-review.

---

## Independent review iteration 2 + author fixes (2026-10-29)

Independent re-review: **PASS at 9.50** (no margin). The author closed the remaining minors:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R8-12 | Minor | The chapter README file map listed `tools/generate_data.py` with no instructor-only marking. | Now marked "instructor copy only (stripped from student release)". |
| R8-13 | Minor | Stale 0-based references remained after the move to `orion-n01`…`n08`. | PLANTED_FAULTS TAIL row now reads "n07 or n08". The generator docstring now reads "n01..n08". The `perftest_analysis.py` docstring example is now "n05-n06" in both the solution and starter copies. |
| R8-14 | Minor | Lab-coverage wording did not note that item 9 is only partly automated. | All four places (manuscript §8.12, manuscript runbook, lab README, key 8.12) now read identically: "the lab automates items 1–10 (item 9: DSCP map only) and 12 and correlates item 13 with perftest results". |

`python scripts/validate_labs.py ch08` → all columns OK. Manuscript 10,286 words.
