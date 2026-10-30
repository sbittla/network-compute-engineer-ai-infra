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
