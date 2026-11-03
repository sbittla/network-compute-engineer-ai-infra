# Editorial Review — Chapter 7

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 8.95 | Fail (D9 8.0, D3 8.5, D1 9.0; blockers open) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.43 | Fail (D1 9.0; one major open) |
| 3 | 2026-10-29 | Author self-review, iteration 3 | 9.50 | Pass (internal) — pending independent review |
| I1 | 2026-10-29 | Independent review, iteration 1 | 9.23 | Fail |
| I2 | 2026-10-29 | Independent review, iteration 2 | 9.35 | Fail |
| I3 | 2026-10-29 | Independent review, iteration 3 | 9.50 | **Pass** |

## Scores by dimension (latest — iteration 3)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 9.5 | Arithmetic verified twice (by hand and with the reference implementation): Clos limits, /31 counts, frame sizes (9,022 B; 4,158/4,174 B), ECMP collision probabilities (8!/8⁸ = 0.24 %; expected 5.25 links; Monte Carlo distribution reproduced with seed 1), resilient-hash 1/32, all failure capacities. RFC numbers, years, and authors checked. Vendor syntax (FRR, EOS-style, SONiC) labelled as dated vendor examples with "verify" notes; no invented flags in host commands. Residual risk: NOS-specific MTU semantics and timer defaults are inherently version-sensitive and are flagged as such. |
| D2 | Depth and production realism | 15 % | 9.5 | Failure signatures practitioners actually meet (BGP up across an MTU mismatch, `maximum-paths` collapse, shared-leaf-ASN route drops, bogus origin), ingress-vs-egress MTU drop mechanics, ECMP-aware vs raw capacity, rail-leaf as cluster-wide fault domain, drain procedure. |
| D3 | Pedagogy and clarity | 15 % | 9.5 | Progression L2 → addressing → MTU → BGP → ECMP → Clos → QoS → failure; worked example reuses every earlier concept with all arithmetic; three figures and ten numbered tables, each captioned. |
| D4 | Hands-on lab quality | 15 % | 9.5 | Realistic intent-validation task with six planted faults and three false-positive traps; deterministic seeded generator with a byte-identical regeneration check (T0); 19 checks with hints; L2 (containerlab/FRR) and L3 extensions with commands and manifest fields; runs in < 1 s. |
| D5 | Exercises and assessment | 10 % | 9.5 | Full standard set (8 KC, 2 WP, lab, troubleshooting, design, 4 reflection) + all three outline-mandated items + deliverable; every item has difficulty, tier, evidence; key has arithmetic, marking points, common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.5 | Every quantitative claim labelled MODELED / SIMULATED / ILLUSTRATIVE / VENDOR-SPEC; the Monte Carlo result states what it does not model; L3 extension requires a manifest before `[MEASURED]`. |
| D7 | Cross-layer integration | 5 % | 9.5 | ORION numbers throughout; W-TRAIN DP all-reduce volume (7.66 GB/GPU/step, 0.9 % of step) ties fabric to workload; links to Ch 2, 3, 5, 8–12, 19–20 and Capstones A/B. |
| D8 | Operational realism and safety | 5 % | 9.5 | Runbook table with signals, thresholds, safe actions, escalation; drain-before-change; explicit safety callouts; all failure exercises on models or dedicated labs. |
| D9 | Editorial polish | 5 % | 9.5 | Acronyms defined at first use; units consistent (Gb/s vs GB/s); 9,992 words (`wc -w`), within 7,000–10,000. |

Weighted: 0.20·9.5 + 0.15·9.5 + 0.15·9.5 + 0.15·9.5 + 0.10·9.5 + 0.10·9.5 + 0.05·9.5 + 0.05·9.5 + 0.05·9.5 = **9.50**.

## Findings

| ID | Iter | Severity | Location | Finding | Resolution |
|---|---|---|---|---|---|
| F1 | 1 | blocker | manuscript.md | 11,390 words, above the 10,000 limit. | Tightened prose in Sections 7.1–7.12, trade-offs, summary, and reading list without removing any mechanism, number, table, or figure; now 9,992. |
| F2 | 1 | major | §7.12 E2/E4 | Scenario inconsistent: long-lived connections would not produce failures that "differ per run", and 4/64 = 1/16 only holds if probes leave via one frontend leaf. | Symptom rewritten (hung nodes change at each restart, when connections re-establish with new source ports); sweep pinned to `fe-leaf-1` with `iperf3 -B`; topology of the dual-homed frontend stated. |
| F3 | 1 | major | §7.12 E4 | Sweep script used a fragile inline Python JSON parser that crashes on a stalled run. | Replaced with `timeout` + `jq '.end.sum_received.bits_per_second // 0'`; stalls count as 0. |
| F4 | 1 | major | §7.4 | "ICMP has no ports, so ping uses exactly one path" overstated hashing behaviour. | Hedged: most switches hash ICMP on addresses and protocol, so one ping ≈ one path. |
| F5 | 1 | minor | §7.8 | Referenced "Exercise 7.D" for QoS rules, but 7.D is the parallel-link design challenge. | Pointed to the lab stretch task (Exercise 7.L); stretch spec and model answer added. |
| F6 | 1 | minor | §7.3 | "IPv6 changes three things" followed by two. | "IPv6 adds two options." |
| F7 | 1 | minor | Listing 7.1 | `route-map HOST-LINKS` referenced but undefined; JSON listing contained a `//` comment (invalid JSON). | Inline note on what the route-map permits; label moved outside the JSON block. |
| F8 | 2 | major | check.py | No automated proof that `data/` matches the seeded generator; importing modules left `__pycache__` in starter/ and solutions/. | Added check T0 (regenerate to a temp dir, byte compare); `sys.dont_write_bytecode = True`; counts updated to 19 across README, lab README, exercises, key. |
| F9 | 2 | minor | exercises.md 7.T | NCCL log line format and traceroute evidence were vague. | Log line matches the NCCL "Got completion from peer … with error 12 … vendor err" form, with a version-variance note; traceroute evidence lists concrete hop addresses consistent with Table 7.2. |
| F10 | 3 | minor | key 7.T(b) | Which spine prefers the bogus path depends on BGP tie-breakers. | Key states the dependency explicitly (oldest-path vs router-ID comparison) instead of asserting a universal outcome. |

## Release-gate items outstanding

- Independent technical review by a practising data-center/AI fabric engineer (RELEASE_GATES.md).
- Verify vendor example syntax against current FRRouting, Arista EOS, and SONiC documentation at
  publication time (peer-group keyword spelling, `maximum-paths … ecmp …`, SONiC `config_db` keys,
  default port MTU values).
- L2 extension (containerlab + FRR) to be executed once end to end and its expected output captured.
- **Shared-doc note:** `docs/REFERENCE_CLUSTER.md` gives ORION switches 64 × 400G ports and a
  "51.2 Tb/s-class" ASIC, which uses only 25.6 Tb/s. Chapters 7 and 10 both assume one 400G port per
  cage (25.6 Tb/s in use) and say so explicitly; the reference doc should state this too.
- The leaf-spine /31 plan (`10.101.<spine>.0/24`) is this chapter's extension of the reference
  addressing plan; consider adding it to `docs/REFERENCE_CLUSTER.md` so later chapters reuse it.

---

## Independent review iteration 1 + author fixes (2026-10-29)

Independent review score: **9.23** (below gate). The author applied every finding below and aligned
the package with `docs/REFERENCE_CLUSTER.md` (canonical names, frontend ratios) and
`docs/VERIFIED_FACTS.md` (MTU semantics, FRR `MULTIPATH_NUM`, 25.6 Tb/s, `NCCL_IB_QPS_PER_CONNECTION`
default 1).

| Finding | Severity | Resolution |
|---|---|---|
| R-01 Frontend "3:1" is 1.5:1 by bandwidth | major | §7.12, §7.7, §7.11 and Figure 7.1 now give 3:1 by ports, 1.5:1 by bandwidth (9.6 : 6.4 Tb/s), and 1:1 as populated. `size_two_tier` gained `down_gbps` and returns `bandwidth_oversubscription`; check T1b asserts 1.5. E4 is unchanged, because each frontend leaf still has 16 uplinks. |
| R-02 7.T(b) tie-break contradiction | major | Added evidence item 8: `bgp bestpath compare-routerid` drift on spines 1 and 3 only, and no multipath-relax. The key now explains the 2-of-4 split: router-ID comparison on spines 1 and 3, the default eBGP oldest-path rule (RFC 5004 behaviour) on spines 2 and 4. Full-credit criterion and a fourth preventive control (remove the drift) added. |
| R-03 FRR `maximum-paths` capped by `MULTIPATH_NUM` / zebra `-e` | major | Sentence added after Listing 7.1. The runbook "ECMP group width" row now checks the next-hop count in `show ip route` first, then the cap. |
| R-04 Inline `!` comments after commands | minor | Moved onto their own lines in the FRR listing. |
| R-05 "4/64 = 1/16" and giants "1:1" | minor | Now "consistent with ≈ 1/16 (binomial 4 ± 1.9)". Giants increment only while failing connections are active. |
| R-06 Spine index naming | minor | Polarization example (§7.6) and key 7.K5 use `orion-be-spine-1..4`, with spine *s* receiving *h mod 4 = s − 1*. |
| R-07 K2 wording | minor | "each loses reachability to the other's prefixes" in the manuscript and key. |
| R-09 Status of the 10.101 plan | minor | Table 7.2 caption and manifest: "defined here and adopted by the reference plan". |
| R-10 Where VLANs/VRFs still appear | minor | About 80 words added in §7.2: frontend tenant, storage and management VRFs over EVPN-VXLAN, customer-facing inference isolation, per-rack OOB VLANs. |
| Canonical names | major | Manuscript, exercises, key, generator, solution, starter and checker now use `orion-nNN` (01–32), `orion-be-leaf-rR`, `orion-be-spine-S`, `orion-fe-leaf-NN`, `orion-fe-spine-S`. Host links are 1-based (`orion-nNN` ↔ leaf `Ethernet<NN>`, 10.100.r.(2·NN)/31, so .2–.65). Data regenerated (seed 7, byte-identical on rerun); check T2b updated (H-r3-n05 → Ethernet5). |
| VERIFIED_FACTS MTU semantics | major | §7.4 now says EOS/NX-OS routed `mtu` = IP MTU and Junos media MTU includes the L2 header, and that "+22 B" is a conservative portable rule. |
| Cuts | — | §7.1 prose under Table 7.1 condensed; "Beyond 5-tuple ECMP" folded into four bullets; Jupiter Rising dropped. Manuscript 10,106 words (`wc -w`), under the 11,000 ceiling. |

Validation: `check.py --impl solution` 19/19; `--impl starter` 1/19 (T0 data integrity), exit 1, no
traceback; `python scripts/validate_labs.py ch07` OK.

### Re-score (author, after fixes)

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | Weighted |
|---|---|---|---|---|---|---|---|---|---|
| 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | 9.5 | **9.50** |

Outstanding: re-score by the independent reviewer; vendor syntax re-verification at publication.

---

## Independent review iteration 2 + author fixes (2026-10-29)

Independent re-review: **9.35**. All iteration-1 fixes were verified with no regressions. The
reviewer projects 9.50 once the items below are fixed.

| Finding | Severity | Resolution |
|---|---|---|
| R2-01 T0 fails when `lab/tools/` is absent (student release), so a student can never reach exit 0 | blocker | `check.py` raises `Skipped` when the generator is missing and reports `SKIP  T0 … generator not shipped in student release`. SKIP results are excluded from the pass count, so exit 0 stays reachable. `validate_labs.py ch07` reports `no-generator=pass`. |
| R2-01 Learner docs pointed at the generator | blocker | The regenerate command is gone from lab/README.md. The data section and the chapter-card file map now say the generator is "instructor copy only". The manifest records the distribution rule. |
| R2-02 Host /31s span .2–.65, which crosses a /26 | minor | The Listing 7.1 route-map comment now gives the prefix-list as `10.100.3.0/25 le 31`. |

Validation: solution 19/19 (exit 0); starter 1/19 (exit 1, no traceback); no-generator copy passes
(T0 SKIP). Manuscript 10,109 words.

Re-score (author): D1–D9 all 9.5 → **9.50**.


---

## Independent review iteration 3 (2026-10-29)

Passed at 9.50 with no open findings.

---

## Independent review r1 (2026-11-01)

Reviewer scores: D1 9.0 · D2 9.5 · D3 9.5 · D4 9.5 · D5 9.5 · D6 9.5 · D7 9.5 · D8 9.5 · D9 9.0 →
weighted **9.38** (gate fail). Checker 19/19 solution, 1/19 starter (graceful).

| Finding | Severity | Resolution |
|---|---|---|
| N07-01 DP all-reduce "usually overlapped" contradicts VERIFIED_FACTS overlap window | major | Fixed. §7.10 Step 8 now models exposure as max(0, T_DP − 70 ms) with Chapter 11 cited for the window: aligned 0.153 s → **0.083 s ≈ 0.48 %** of 17.4 s; misaligned ×3 = 0.459 s → **0.389 s ≈ 2.2 %** `[MODELED]`. Conclusion kept: the larger exposure is PP activations and MoE all-to-all. No other file carried the old figures (grep). |
| N07-02 "Every major AI backend routes at the leaf" | minor | Fixed. "Most large RoCE backends route at the leaf"; per-rail L2 segments and a stretched L2 domain named as alternatives; IB has no IP routing in the fabric. Objective 1, the Key idea ("a routed AI backend such as ORION's"), "never on a GPU backend" → "rarely" and the trade-offs row aligned. |
| N07-03 Giant-at-ingress assumes L3 MTU = L2 max frame | minor | Fixed. Root cause states that on this platform the reverted default lowered both, and that NOSes which separate them drop at an egress MTU check instead (`[VENDOR-SPEC, 2026-10]`). |
| N07-04 Host multi-NIC sysctls; ECMP group table limits | minor | Fixed. §7.2 adds `rp_filter=2`, `arp_ignore=1`, `arp_announce=2` with the failure each prevents (`[VENDOR-SPEC, 2026-10]`, verify); runbook adds an "ECMP group / next-hop table utilization" row. |
| N07-05 Table 7.7 caption label format | minor | Fixed (Table 7.7 and Table 7.8 captions use backticked canonical labels). |
| N07-06 Exercise ID scheme | minor | Fixed by stating the convention in the exercises.md header (K/W/L/O/T/D/R, folder `<ID>-<slug>`). Not renumbered: folder names, meta.yaml and CI prompt-sync depend on the IDs. |
| N07-07 iperf3 control connection | minor | Fixed. Comment in the E4 sweep. |
| N07-08 Mid-sentence acronym expansions | minor | Fixed. NIC, RDMA and NCCL expanded at first natural use in "Prerequisites and connections"; Table 7.1 and §7.6 use the short forms; ASIC sentence reflowed. |
| D3 next-0.5: figure of the 7.12 path | advice | Added Figure 7.4 (directional failure mechanisms on `Et17/1`). |
| D4 next-0.5: host-link fault in the intent | advice | Not done: it would change the planted-fault count across generator, validator, checker, golden outputs, key and exercises. Deferred. |
| D9 "Table 7.8a" | advice | Renumbered: hypotheses Table 7.9, evidence checklist 7.10, trade-offs 7.11, runbook 7.12; references in exercises.md, 7.T folder and its answer updated. |
| Cross-chapter netdev naming | — | ORION canonical rail *i* ↔ `mlx5_i` ↔ `ens{i+1}np0` `[ILLUSTRATIVE]` stated in §7.2; rail-3 examples changed from `ens3np0` to `ens4np0`. |

Validation: solution 19/19; starter 1/19 (graceful); `validate_labs.py ch07` OK on all columns;
`copyedit_lint.py` 0 findings.

---

## Independent review r2 (2026-11-01)

Independent reviewer scores: D1 9.5, D2 9.5, D3 9.5, D4 9.0, D5 9.5, D6 9.0, D7 9.5, D8 9.5, D9 9.0 →
weighted **9.35** (gate fail). Findings: 0 blocker, 1 major, 14 minor. Every finding was checked
before it was changed; none was rejected.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R07-01 | Major | `orion-mini.clab.yml` does not exist; the harness experiment is framed as a GPU measurement. | Added `lab/l2/orion-mini/`: `render.py` (stdlib, deterministic, `--check` mode) and its committed output, `orion-mini.clab.yml` (2 spines, 4 rail leaves, 2 hosts, 16 links) plus `configs/daemons` and one `frr.conf` per switch. They use the chapter conventions (AS 65101 + r / 65100, loopbacks, idx = 8r so leaf-r3 ↔ spine-1 = 10.101.1.48/.49 as in Listing 7.1, host /31s, per-rail policy routing on the hosts, BFD, `timers 3 9`, `maximum-paths 64`). The YAML parses; the README states plainly that the fabric was not deployed in the course harness. The L2 commands now use the real container names, a cross-rail probe (n01 rail 0 → n02 rail 3), and a `netem` loss test so the BFD-versus-hold-timer comparison measures something. The harness section is renamed "ECMP hashing simulation": software only, no network touched, and the GPU only runs more trials. The CPU command comes first, and the only `[MEASURED]` figure is the simulator's speed. The manifest and chapter file map are updated. Committed results are unchanged. |
| R07-02 | Minor | Setup comment says the starter reports everything as TODO. | Now "T0 PASS (SKIP in the student release), all other checks TODO, exit 1". |
| R07-03 | Minor | Ping target 10.100.3.1 breaks the node numbering. | The probe now goes from 10.100.0.3 (n01 rail 0) to 10.100.3.5 (n02 rail 3). |
| R07-04 | Minor | Unlabelled derived and vendor numbers. | 12.5 % and "2 of 8 links" are labelled `[MODELED]`. The 20.4-link figure is shown as 32(1 − (31/32)³²) = 20.41 and labelled `[MODELED]`; the 97 % stays `[SIMULATED]`. The 51.2T port-configuration sentence is labelled `[VENDOR-SPEC, 2026-10]`. |
| R07-05 | Minor | ORION-XL two-tier framed as *the* decision. | Now a choice between the reference three-tier pod design and a radix-128 two-tier fabric, conditional on the 51.2 Tb/s-class switch option. |
| R07-06 | Minor | Modulo and hash-threshold disruption are not distinguished. | Hash-threshold (RFC 2992) moves about ¼–½ of flows, a rebuilt group behaves like modulo, and resilient hashing moves ≈ 1/32. The further-reading line is updated. |
| R07-07 | Minor | `best #9` but the first path is marked best. | `best #1` (exercises.md and the folder prompt). |
| R07-08 | Minor | NCCL WARN-format note is coarse. | 2.20–2.21 `status=12 opcode=0 len=0 …`; 2.22+ `NET/IB: … status=12 … hca mlx5_N` (both copies). |
| R07-09 | Minor | Key 7.T(a) cites a 1472-byte ping. | "default-size and 8,972 B pings; 1,400 and 8,948 B MSS fail alike". |
| R07-10 | Minor | "Roughly a dozen" prefixes. | "About twenty (8 rail aggregates and 12 loopbacks)". |
| R07-11 | Minor | "The line" has no clear referent. | "The `no bgp ebgp-requires-policy` line in Listing 7.1". |
| R07-12 | Minor | DP time uses line rate without saying so. | Marked as a best case, with the achievable-rate variant: 7.66 / 44 = 0.174 s, exposed 0.104 s ≈ 0.6 %. |
| R07-13 | Minor | Undefined acronyms. | Expanded EVPN-VXLAN, NOS, DF, ICMP, CoPP, LLDP, uRPF and LAG at first use. |
| R07-14 | Minor | Stray blank line in Further reading. | Removed. |
| R07-15 | Minor | 7.12 drain contradicts §7.9. | GRACEFUL_SHUTDOWN or prepend first; shutting the session is named as a deliberate shortcut for one ECMP member. |
| D2/D7/D8 advice | — | Convergence budget; direct capstone links; host-port giants. | §7.9 adds a convergence-budget paragraph (detect + BGP + FIB; graceful-restart-versus-BFD interplay; FIB-lag signature). Capstones A and B are now linked directly. The runbook gains a host-facing giant-counter row. |

Verification: `check.py` solution 19/19 and starter 1/19 (graceful); `validate_labs.py ch07` OK;
`copyedit_lint.py` 0 findings in ch07; package harness 78 passed; `render.py --check` OK. No exercise
outputs changed. Manuscript 10,968 words.
