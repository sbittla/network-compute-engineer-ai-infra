# Editorial Review — Chapter 9: Congestion Control and Lossless-Fabric Engineering

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 8.90 | FAIL |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.48 | FAIL (D9 < target, weighted < 9.5) |
| 3 | 2026-10-29 | Author self-review, iteration 3 | 9.50 | PASS (internal, pending independent review) |
| 4 | 2026-10-29 | Independent review iteration 1 | 9.20 | FAIL -> author fixes below |
| 5 | 2026-10-29 | Author re-score after fixes | 9.50 | pending independent re-review |
| 6 | 2026-10-29 | Independent review iteration 2 | 9.50 | PASS; 4 minors closed (see below) |

## Scores by dimension (latest, iteration 3)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20% | 9.5 | PFC frame format, quanta arithmetic, ECN codepoints, DCQCN algorithm and paper parameters, headroom decomposition, dynamic thresholds, and Guo et al.'s storm/slow-receiver/deadlock findings are stated as a practitioner would. Uncertain items are explicitly hedged: 802.1Qbb delay bounds at 400G, watchdog defaults, mlx5 counter names, UEC 1.0 feature optionality. No invented flags; commands limited to `ethtool -S`, `rdma statistic show link`, `mlnx_qos -i`, `dcb pfc show`, `lspci -vv`, `scontrol update`, perftest flags, and SONiC `show` commands inside a vendor note. |
| D2 | Depth and production realism | 15% | 9.5 | Failure signatures with counter-level evidence (Tables 9.3–9.4), the "root = congested but not receiving pause" rule, storm vs incast discrimination, slow-receiver scenario traced to PCIe x8 downtrain with arithmetic, headroom deficit case (T1), cross-rail incast as a rank-mapping smell. |
| D3 | Pedagogy and clarity | 15% | 9.5 | Progression queue → ECN → PFC → risks → DCQCN → incast → telemetry → alternatives; ten captioned figures including the required NIC↔switch data path (Fig. 9.9) and a troubleshooting tree (Fig. 9.10); worked example with every step and an explicit interpretation of each simulated column. |
| D4 | Hands-on lab quality | 15% | 9.5 | Realistic on-call task; seeded byte-identical generator; planted counter reset, telemetry gap, benign decoy, victim decoy, four config faults; digests in check.py avoid leaking answers; starter fails gracefully with TODO per check; partial implementations give mixed PASS/TODO; L2/L3 extension with real commands and manifest fields; runs in ≈ 1 s. |
| D5 | Exercises and assessment | 10% | 9.5 | K1–K8, W1–W2, H1, all three outline exercises (O1–O3), T1, D1, R1–R4; every item tagged ★/tier/evidence; key with arithmetic verified twice by script, marking splits, common mistakes, planted anomalies documented. |
| D6 | Measurement rigor and evidence labelling | 10% | 9.5 | Every figure labelled MODELED/SIMULATED/ILLUSTRATIVE/VENDOR-SPEC; simulation results carry a cannot-conclude list in the text, lab, and report; experiment design specifies warm-up, ≥ 5 interleaved repetitions, percentiles, spread, manifest. |
| D7 | Cross-layer integration | 5% | 9.5 | ORION QoS intent, rail-optimized topology, W-TRAIN step time; links to Chapters 3, 7, 8, 10, 12, 13, 14, 15, 16, 18, 20 and Capstone B; troubleshooting crosses network → PCIe → scheduler. |
| D8 | Operational realism and safety | 5% | 9.5 | Runbook RB-FAB-09 with signals/thresholds/severity/first action; safe vs unsafe actions; Safety callouts on every fault-injection or config-change activity (lab fabric only). |
| D9 | Editorial polish | 5% | 9.5 | Acronyms defined on first use; figures/tables numbered sequentially; Mermaid syntax checked; units consistent (Gb/s vs GB/s, KB = 10³ B); 9,995 words (`wc -w`), inside the 7,000–10,000 budget. |

Weighted = 0.20×9.5 + 0.15×9.5 + 0.15×9.5 + 0.15×9.5 + 0.10×9.5 + 0.10×9.5 + 0.05×9.5 + 0.05×9.5 + 0.05×9.5 = **9.50**.

## Findings

| ID | Iter | Severity | Location | Finding | Resolution |
|---|---|---|---|---|---|
| F1 | 1 | major | manuscript | 10,294 words, over the 10,000 budget. | Tightened prose (9.1, 9.2, 9.3, 9.5, 9.9, 9.10, 9.12, summary, reading list); merged the storm-vs-incast table into Table 9.4. Now 9,995. |
| F2 | 1 | major | 9.5, Fig. 9.5 | HOL example drew two hosts sharing one leaf port — impossible on point-to-point Ethernet. | Reworked as two QPs on one sender NIC; extended the victim explanation to spine ports. |
| F3 | 1 | major | lab/check.py | Initial check required template ECN to lower *peak* queue; the model correctly shows identical peaks (the first RTT is outside feedback's reach). The check encoded a wrong expectation. | Check now requires lower pause time and more CNPs; manuscript Section 9.10 explains why peaks are equal, with arithmetic (1,000 + 1.2 µs × 550 KB/µs = 1,660 KB). |
| F4 | 1 | major | 9.4 headroom table | Asserted that IEEE 802.1Qbb bounds response time "per link speed" for 400G — not verified. | Softened to "standards bound parts of it; use vendor per-ASIC, per-speed values". |
| F5 | 1 | major | 9.7 step 5 | Headroom figure (≈ 94 KB/port) inconsistent with Table 9.2's 30 m host ports (83.5 KB). | Reconciled: 12 × 83,496 B ≈ 1,002 KB; lab model's 1,128 KB explicitly tied to 50 m runs. |
| F6 | 1 | minor | throughout | DSCP, ECMP, QP, MTU, PCIe, SRE, NCCL, KV, BTH, FEC, CRC, gNMI, ASIC, RED not defined on first use. | Defined inline. |
| F7 | 1 | minor | Mermaid | Semicolons inside sequence-diagram notes can terminate statements. | Replaced with commas; all four Mermaid blocks re-checked. |
| F8 | 1 | minor | key, lab anomalies | Gap divisor stated as 12 s; data shows previous sample at t = 298, so 14 s (7× inflation if divided by 2 s). | Corrected after inspecting the data. |
| F9 | 1 | minor | key K5 | "Raising Xoff reduces headroom" is implementation-dependent and misleading. | Replaced with the mechanism: raising Xoff delays the pause and leaves more bytes buffered. |
| F10 | 2 | minor | 9.12 | Hypothesis table lacked an explicit physical-layer check command. | Added `ethtool -S … rx_corrected_bits_phy` read with a 60 s re-sample. |
| F11 | 2 | minor | key T1 | Answer did not notice that the 15 m and 30 m ports are also under-provisioned by the 5 m profile. | Added the 5,000 B and 12,500 B shortfalls and why they have not (yet) dropped. |
| F12 | 2 | minor | lab/README | Starter run instructions did not say the narrative must be hand-written. | Added explicit hand-edit step and rubric weight for the narrative. |

No open blocker or major findings.

## Release-gate items outstanding

- Independent technical review by a practising RoCEv2/InfiniBand fabric engineer (headroom model,
  watchdog semantics, DCQCN defaults on current NIC firmware).
- Verify mlx5 counter names (`rx_prio3_pause_transition`, `tx_pause_storm_*_events`,
  `np_ecn_marked_roce_packets`) against the kernel documentation for the target driver release.
- Verify the SONiC command list in the Section 9.8 vendor note on a current release.
- Verify UEC 1.0 feature optionality (trimming, LLR, CBFC) against the published specification.
- Execute the L3 extension (incast A/B) on a lab fabric and record a manifest; compare direction of
  change with the SIMULATED result.

---

## Independent review iteration 1 + author fixes (2026-10-29)

Independent reviewer score: **9.20 (FAIL)**. Also applied the shared-doc changes made after the first draft:
`docs/VERIFIED_FACTS.md` (new), canonical names in `docs/REFERENCE_CLUSTER.md`, its RTTs (≈ 4 µs same-rail,
≈ 5 µs cross-rail and worst case) and 900 s restart, and the `docs/LAB_STANDARDS.md` rule that the student
release strips `lab/tools/`.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| NAMES | major | Non-canonical host and switch names (`hx8-NN`, `leaf-rR`, `spine-S`). | Renamed everywhere (manuscript, data, generator, checker, key, exercises) to `orion-nNN` (1-based: leaf port eth1/N ↔ orion-nN), `orion-be-leaf-rR`, `orion-be-spine-S`. Data regenerated; root, storm and QoS digests in check.py updated (label and victim digests are unchanged). |
| R9-01 | major | Generator leaks answers; nothing SKIPs without it. | Planted-fault spec moved to `solutions/lab/planted_faults.yaml`, which the generator loads (single source of truth). New `data_determinism` check regenerates into a temp dir and compares bytes; it reports **SKIP** when `lab/tools/` or the spec is absent (verified by renaming `lab/tools`: solution 14/14 + 1 SKIP, exit 0; starter fails gracefully). Removed the lab README's generator command; the chapter card and manifest mark the generator instructor-only. Key documents the full planted-fault list and points to the YAML. |
| R9-02 | major | §9.12: PCIe Gen5 x8 achieves ≈ 200–220 Gb/s, not 252. | eth1/18 tx now 212.6 Gb/s. Text: 252 Gb/s raw, ≈ 200–220 Gb/s achievable `[VENDOR-SPEC, 2026-10]`. H2/H3, root cause, and key R3 aligned. |
| R9-03 | major | §9.12: victim ports showed ECN marks with a 37–51 KB watermark, below Kmin, contradicting Table 9.4. | Marks set to 0 on eth1/3, eth1/9, eth1/22; eth1/18 (3.4 MB watermark, above Kmax) now ≈ 2.1 M marks/s. Reworded: the victims are the paused senders' QPs to *other* destinations. The same rule was applied to the lab data: baseline marks are 0 (watermark < every Kmin). Mark rates now follow each switch's profile (leaf-r3 Kmin 1,500 KB → 0.5–1.1 M/s at a 2.6–3.8 MB watermark; spines and leaf-r4 above Kmax → ≈ 6 M/s). The benign busy port moved to `orion-be-leaf-r4` eth1/7 (Kmin 150 KB), because a leaf-r3 port with a 250 KB watermark could not be marked. |
| R9-04 | major | §9.1 "50 µs stall leaves 2.5 MB" had no mechanism. | Replaced: NAK recovery ≈ 1 RTT plus the in-flight window (≈ 200–250 KB; Ch 8 §8.11); tail loss waits for the ACK timeout, 4.096 µs × 2^20 ≈ 4.3 s `[VENDOR-SPEC, 2026-10]`; cross-reference Ch 8 §8.6. §9.10 config C is now qualified as best-case NAK-style selective repeat that ignores go-back-N window resends and tail timeouts. The sim config description and the report's cannot-conclude list match. |
| R9-05 | minor | Unclear what t_resp = 1 µs covers; "(FEC). the" typo. | Defined t_resp (PFC generation at the receiver plus action at the upstream port, across MAC/PHY/FEC). Noted the 802.3 worst case of ≈ 905 quanta ≈ 1.16 µs, labelled unverified, and its +7,900 B per port. Typo fixed. |
| R9-06 | major | RTT inconsistent with REFERENCE_CLUSTER and Ch 8. | §9.3 BDP: 200 KB same-rail (4 µs), 250 KB cross-rail (5 µs). Worked example: Kmin 7.5 × BDP. Summary updated. Lab `fabric_intent.base_rtt_us` = 4.0 (the audit result is unchanged). Headroom keeps its cable-length basis. |
| R9-07 | minor | "51.2 Tb/s switch with 64 × 400G" contradicts VERIFIED_FACTS. | Now "64 × 400G = 25.6 Tb/s of ports in use"; the 64 MB buffer is marked an `[ILLUSTRATIVE]` assumption. |
| R9-08 | minor | "Each extra lossless priority doubles headroom". | Now "adds the same amount again" (§9.4 and summary). |
| R9-09 | minor | headroom_kb 1,128 unexplained. | Added a `headroom_basis` field to sim_configs.yaml (12 × 93,496 B = 1,121,952 B ≈ 1,122 KB, rounded up to 12 × 94 KB); the lab README states the same. |
| R9-10 | minor | DCQCN T/B values unverified; no sender-side limit. | Kept g, N, K, Kmin, Kmax, Pmax as reported. T, B and the increase steps are now directed to the paper's table, labelled unverified. Added the RP rate-reduction monitor period `[VENDOR-SPEC]`. |
| R9-11 | minor | Selective-repeat claim unlabelled; no recovery counters named. | Labelled `[VENDOR-SPEC, 2026-10]`; named mlx5 `out_of_sequence` and `packet_seq_err`. |
| R9-12 | minor | T1 had two uplinks to the same spine at 15 m and 100 m. | Redesigned: eth1/33 → orion-be-spine-1 (20 m, same network rack) vs eth1/57 → orion-be-spine-4 (100 m, far rack), following the lab's port-bundle convention. Key recomputed (20 m needs 78,496 B, a 7,500 B shortfall). The key now **requires** learners to say that zero discards cannot prove eth1/33 is safe, and that H2 (spine-4) is tested against other leaves. |
| CUTS | — | Length. | Removed the §9.5 storm-vs-incast paragraph (Table 9.4 covers it), cut TIMELY/Swift/HPCC to one sentence, cut the pause-refresh derivation to one clause, and merged the summary bullets. Manuscript is 10,095 words (≤ 10,500). |

**Re-verification:** `python lab/check.py --impl solution` gives 15/15 PASS, exit 0. Starter: TODOs, exit 1, no
traceback. With `lab/tools` renamed, `data_determinism` SKIPs: solution exit 0, starter fails gracefully.
`python scripts/validate_labs.py ch09` gives 1/1 valid. Regenerating the data twice gives byte-identical files
(1.5 MB). Every changed number was recomputed (headroom 70,996 / 78,496 / 118,496 B; BDP 200/250 KB;
905 × 1.28 ns = 1,158 ns).

### Author re-score after fixes

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | Weighted |
|---|---|---|---|---|---|---|---|---|---|
| 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.50 |

This is the author's score and is pending independent re-review. Still open as release-gate items: the
unverified 802.3 response-time bound, DCQCN T/B values, mlx5 and SONiC counter/command names, and UEC 1.0
feature optionality.

---

## Independent review iteration 2 + author fixes (2026-10-29)

Independent re-review: **9.50 (PASS)**. Four minor findings were raised to protect the pass. All four are closed.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R9-13 | minor | Six samples on orion-be-leaf-r4 eth1/7 (the benign busy window) showed ECN marks while the watermark was below that leaf's 150 KB Kmin. | The generator now floors the watermark at Kmin whenever it adds marks (155–250 KB). Data regenerated twice: byte-identical. A script check over all ports finds 0 samples with marks > 0 below the switch's Kmin. Episode, root, victim and QoS answers are unchanged, so no checker digest changed. The key now says 155–250 KB. |
| R9-14 | minor | §9.4 implied that the 802.3 ≈ 905-quanta bound covers the whole t_resp. | Removed the 905-quanta figure. t_resp is now defined as the receiver's time to generate the pause plus the paused port's time to react. Standards bound only the second part, so a real design uses the vendor's per-ASIC figure for the whole term. |
| R9-15 | minor | §9.12 used `ethtool -S eth6`, not an ORION netdev name. | Replaced with `ens7np0` (mlx5_6), consistent with Chapter 8's mlx5_3 ↔ `ens4np0`. The §9.8 commands now use `ens4np0` instead of `eth3`. |
| DCQCN | minor | The wording "read T, B … from the paper's table [unverified here]" was weak. | Now: T = 55 µs and B = 10 MB in the paper's evaluation (verify against Zhu et al., 2015), and NIC defaults differ, for example in NVIDIA DOCA `[VENDOR-SPEC, 2026-10]`. |

**Re-verification:**
- Solution: 15/15 PASS.
- `python scripts/validate_labs.py ch09`: every column OK (solution pass, starter fails gracefully, no-generator pass, docs ok).
- Manuscript: 10,090 words.

| R9-16 | Minor | §9.12 said "the job restarts on a spare node"; ORION-256 has no spare nodes (VERIFIED_FACTS). | Reworded: the job waits for repair or restarts at DP = 7 (224 GPUs) with a batch/LR adjustment; ≈ 900 s per restart. |
