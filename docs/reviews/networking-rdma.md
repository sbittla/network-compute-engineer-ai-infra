# Networking and RDMA specialist review: Chapters 7–10 (concise edition)

**Nature of this review.** This is an AI-assisted specialist review (Claude, prompted as a data-center
networking and RDMA reviewer). It is **not** an independent external human review and does not replace
one before publication.

**Date:** 2026-11-05

**Scope.** The published text of `concise/ch07.md` (Ethernet and data-center network foundations),
`concise/ch08.md` (RDMA, RoCEv2 and InfiniBand), `concise/ch09.md` (congestion control and lossless
fabrics) and `concise/ch10.md` (switches, optics, cabling and physical layer). I cross-checked the text
against the full-length manuscripts in `book/part-3-networking/ch07–ch10/manuscript.md`,
`docs/REFERENCE_CLUSTER.md`, `docs/VERIFIED_FACTS.md`, Appendix A and Appendix E. Review areas:
evidence labels, recomputed models, technical correctness, generalization and ORION scoping,
simulated-result caveats, Mermaid diagrams against the prose, lab safety of commands, and
version-sensitive references. No web research was done. The labs and other chapters were not changed.

**Outcome.** I found no arithmetic error in any important model: every number I recomputed matches the
text (see "Recomputations"). The one major finding is a cross-chapter design inconsistency (N1).
Findings: 0 blockers, 1 major, 11 minor. All 12 are now fixed. N1, N3, N11 and N12 were first recorded
as open and were then resolved in a second pass at the coordinator's request. After the edits,
`python scripts/build_concise.py --check` reports ch07 3,930, ch08 3,999, ch09 4,000 and ch10 3,920
words, all OK. ch14 is outside this scope and is owned by another reviewer.

**Tests after the N1 change (ch09 package):**
- `python -m pytest docker/harness/test_package.py --pkg "<ch09 path>" -q` → 86 passed.
- `python docker/harness/generate_outputs.py <ch09 path>` regenerated the committed D1 outputs; no other
  exercise output changed.
- `python scripts/make_expected_outputs.py ch09` → "expected outputs written: 20 exercises, 1
  labs/starter kits". Besides D1, the other changes are the commit hash and test timings.
- `python scripts/validate_labs.py` → 32/32 labs valid.

## Findings

| ID | Chapter / section | Severity | Finding | Resolution |
|---|---|---|---|---|
| N1 | Ch 9 §9.4 Table 9.1, §9.7 step 5, takeaways; vs Ch 10 Fig 10.2 and §10.5 | major | Chapter 9 sizes host-port PFC headroom at L = 30 m (83,496 B; 6.5 MB per leaf). Chapter 10 says ORION host trunks run ≈ 30–45 m and uses a 43 m host link, and the Ch 9 lab assumes 50 m. Headroom must cover the **longest** run. At 45 m, H = 18,432 + 22,500 + 50,000 + 64 = 90,996 B, so the 30 m figure under-reserves ≈ 7.5 KB per host port for the design the book itself describes. Chapter 9 also says that undersized headroom shows up "longest links first". | **Fixed (second pass).** Host ports are now sized at 50 m, matching the lab's assumption: 2 × 50 × 250 = 25,000 B, H = 93,496 B ≈ 93.5 KB. The leaf total is 32 × 93,496 + 32 × 118,496 = 6,783,744 B ≈ 6.8 MB. **Concise ch09:** Table 9.1 and its caption ("Size for the longest host run (≈ 45 m, Chapter 10)"); the 50 m/250 ns example; leaf total and static-worst-case sentence; §9.7 step 5 (12 × 93,496 ≈ 1,122 KB; the lab rounds to 1,128 KB); takeaways (≈ 93–119 KB, ≈ 6.8 MB). **Manuscript ch09:** Table 9.3 and a caption explaining the longest-run rule; leaf total; production note (6.8 MB ×2). In §9.7 step 2, the "coincidence with the 30 m headroom" remark is replaced by "Xoff is independent of headroom"; step 5 and the takeaways are updated too. **Exercise D1:** the prompt now says host ports at 50 m (exercises.md and the exercise README). Updated `solve.py` (KEY h50 = 93,496, leaf = 6,783,744), `answer.md` (×4), `meta.yaml` marking criterion, the key's D1 and O2 entries, and O2's `answer.md` (6.8 MB). Committed and learner-expected outputs were regenerated. T1 is deliberately unchanged: its 30 m port is a specific cable in that exercise's evidence table, not the design sizing, so "need 83,496 B" stays correct there. The per-PG Xoff of 83 KB is unchanged. Ch 10, Appendix A and REFERENCE_CLUSTER quote no headroom totals, so none needed edits. |
| N2 | Ch 8 Worked example step 5 | minor | "the WRITE Only frame (82 B plus 20 B preamble and gap)" reads as double-counting, because §8.6 defines 82 B as the per-packet overhead *including* the preamble and gap. The number is in fact the frame: 14 + 20 + 8 + 12 + 16 (RETH) + 4 (2 B payload padded) + 4 (ICRC) + 4 (FCS) = 82 B. 102 × 8 / 400 Gb/s = 2.04 ns is correct. | **Fixed:** "82 B with RETH and a 2-byte payload padded to 4, plus 20 B preamble and gap". This matches the manuscript's wording. |
| N3 | Ch 8 Troubleshooting, discriminating test | minor | `ib_write_bw` "passes at 385.77 Gb/s average for 65,536-byte messages". The chapter's own single-QP model (Step 4) predicts 8 × 65,536 / (86.96 + 1,337.5 ns) = 368 Gb/s at 64 KiB, so the "measurement" beats the validated model by 5 %. The model is a serialized (non-pipelined) bound, while real perftest overlaps messages. Readers comparing the two will be confused. | **Fixed (second pass).** I corrected the illustrative measurement to match the model. Concise: "passes at 366.32 Gb/s average for 65,536-byte messages (Step 4 model: 368)". Manuscript perftest listing: peak 366.84, average 366.32, MsgRate 0.698700 Mpps (= 366.32 × 10⁹ / 524,288), plus a sentence comparing it with the worked example's Step 4 model: 8 × 65,536 / (86.96 + 1,337.47 ns) = 368 Gb/s; 366.32 / 368.07 = 99.5 %. |
| N4 | Ch 7 Fig 7.1, Ch 8 Fig 8.2, Ch 10 Fig 10.2 | minor | ORION topology and data-path figures had no evidence label. Item 4 requires ORION to be unmistakably illustrative in diagrams. | **Fixed:** added `[ILLUSTRATIVE]` to all three captions. |
| N5 | Ch 9 Fig 9.1 | minor | "A congestion tree from the lab dataset": nothing marks the dataset as synthetic, so the figure could read as observed telemetry. | **Fixed:** "from the lab's synthetic dataset `[SIMULATED]`". |
| N6 | Ch 8 Table 8.3 | minor | This qualitative RoCEv2-vs-IB assessment table had no label, while the neighbouring decision tables are labelled. | **Fixed:** added `[ILLUSTRATIVE]`. |
| N7 | Ch 9 Hands-on box | minor | The text says "`lab/handson/` runs it through a real `tc` RED queue" but does not say where. A reader might apply `tc` qdiscs to a real interface. The lab confines everything to throwaway namespaces and veths (lab README). | **Fixed:** "runs it, inside throwaway network namespaces, through a real `tc` RED queue". |
| N8 | Ch 10 §10.2 | minor | Ch 10 says ORION uses a 51.2 Tb/s-class ASIC but plans with 64 MB of buffer, and then notes that 160 MB is typical at 51.2 Tb/s. Appendix A defines 64 MB as the 25.6 Tb/s-class value. Without a note, this reads as an inconsistency. The manuscript explains that it is deliberately conservative. | **Fixed:** "ORION plans conservatively with ≈ 64 MB per rail leaf (Appendix A's 25.6 Tb/s-class value)". |
| N9 | Ch 10 §10.4 | minor | "Host links are optical (GPU racks are tens of meters from network racks)" was stated as a general rule. Many fabrics use DAC or AEC to an in-rack or adjacent ToR, as Table 10.4 itself says. | **Fixed:** "ORION's host links are optical (its GPU racks …)". |
| N10 | Ch 10 Troubleshooting | minor | `NCCL_PXN_DISABLE` was tagged "`[VENDOR-SPEC, 2026-10 — verify]`". Appendix E (row checked 2026-11-03 against NCCL 2.32.3) records it as verified, so the hedge is stale. | **Fixed:** removed "— verify". |
| N11 | Ch 9 §9.8 | minor | "RoCE sent with DSCP 0 (`NCCL_IB_TC` unset)" is an oversimplification. When `NCCL_IB_TC` is unset, the NIC or driver can still apply a device-default traffic class (for example the mlx5 per-device `traffic_class` setting or an RDMA-CM ToS). Unset NCCL does not always mean DSCP 0 on the wire. | **Fixed (second pass).** Concise: "RoCE sent with DSCP 0 (`NCCL_IB_TC` unset, no NIC default)". Manuscript §9.8 mismatch table: "or NCCL's `NCCL_IB_TC` unset with no NIC or driver default traffic class configured: if one is set, it applies instead". |
| N12 | Ch 8 §8.2 | minor | "RDMA WRITE is one-sided: … no RECV and no target CQE" is true only for plain WRITE. WRITE-with-immediate consumes a RECV and produces a target CQE, and NCCL's IB transport uses it to signal completion. An engineer reading counters or RNR errors could be misled. | **Fixed (second pass).** Concise: "no RECV and no target CQE (WRITE-with-immediate, used by NCCL, consumes a RECV and yields one)". The manuscript already qualified WRITE-with-immediate; I added "NCCL's IB/RoCE transport uses it to signal that a transfer has landed". |

Things checked and found correct (no finding): /31 and ASN plan; RFC 3021, 6164, 7938, 8326, 2992,
7130 and 8950 statements; MSS behaviour across an MTU mismatch; the giant-versus-ICMP directional
mechanism in the Ch 7 incident; FRR `MULTIPATH_NUM`/`zebra -e` (Appendix E); QP state machine; BTH,
RETH and ICRC field sizes; ToS 106 and "26 → DSCP 6"; the GID-index table and the RoCEv1/0x8915
mechanism; `NCCL_IB_TIMEOUT` 18→20 at 2.23; NCCL WARN format by version; IB SM, LID, VL and credit
statements; `ibv_rc_pingpong` default MTU 1,024; the PFC quanta limit; the dynamic-threshold formula;
DCQCN CP/NP/RP roles and paper parameters; PFC storms, watchdog and deadlock statements; IRN, TIMELY,
Swift, HPCC and UET hedging; RS(544,514), 257/256 and 425 Gb/s; DR4 power limits (clause 124 via
Appendix E); cut-through FCS stomping; counter-to-layer map; IEC 61300-3-35, 60825-1, TIA-568.3-D and
TIA-606. Lab-safety notes are present in Ch 7 (§7.7 Safety), Ch 8 (perftest Safety), Ch 9 (operating
notes) and Ch 10 (drain procedure and lab-only fault injection). The incast model (Table 9.4) states
what it simplifies (single queue, fluid, no additive increase) and what it cannot give (magnitudes,
multi-hop behaviour, real NIC DCQCN). Mermaid diagrams match the prose: 8 leaves × 32 down/32 up, 4
spines, 8 links per pair; the 10.100.3.3/.5 addressing in Fig 8.2; the pipeline order in Fig 10.1; the
tree root rule in Fig 9.1.

## Recomputations

**Ch 7 — fabric sizing and ECMP**
- Leaves: 32 × 8 = 256 endpoints; 64/2 = 32 down, 32 up; ⌈256/32⌉ = 8. Spines: 8 × 32 = 256 uplinks /
  64 = 4; 32/4 = 8 links per pair; spine ports 8 × 8 = 64 ✓.
- Clos limits: k²/2 = 2,048 (k = 64) and 8,192 (k = 128); k³/4 = 65,536 and 524,288 ✓. 4,096 GPUs >
  2,048, so ORION-XL needs three tiers at radix 64 ✓.
- Capacity: 32 × 400 = 12.8 Tb/s per leaf; bisection 4 spines × 32 links × 400 G = 51.2 Tb/s = ½ ×
  8 × 12.8 ✓. Cabling 256 + 256 = 512, optics 1,024 ✓. 512 /31s → 1,024 addresses; 64 links per
  spine → 128 addresses in 10.101.s.0/24 ✓; idx = 8 × 2 + 1 = 17 → .34/.35 ✓.
- Frames: 9,000 + 14 + 4 + 4 = 9,022, which leaves 194 B under 9,216 ✓. RoCEv2 14 + 20 + 8 + 12 + 4,096
  + 4 + 4 = 4,158; + 16 RETH = 4,174 ✓. DF ping 9,000 − 28 = 8,972 ✓.
- ECMP: 8!/8⁸ = 40,320/16,777,216 = 0.240 %; 8(1 − (7/8)⁸) = 5.25 ✓. Re-ran a Monte Carlo (200,000
  trials, seed 1): max load 1: 0.24 %, 2: 49.94 %, 3: 40.94 %, ≥ 4: 8.88 % ✓.
- Polarization: h ≡ 0 (mod 4) ⇒ h mod 8 ∈ {0, 4} → 2 of 8 ✓. Modulo 32→31 keeps 31/992 = 3.1 % ✓.
  Hash-threshold removal disrupts ¼ (middle member) to ½ (end member) ✓.
- Failures: 31 × 0.4 = 12.4; 4 × 7 × 0.4 = 11.2 (−12.5 %); (31 + 96) × 0.4 = 50.8; spine 3 × 32 × 0.4
  = 38.4; leaf min(24, 32) × 4 × 0.4 = 38.4; withheld prefix 3 × 8 × 0.4 = 9.6 ✓.
- W-TRAIN: 7.66/50 = 0.153 s (0.88 % of 17.4 s); 0.153 − 0.072 = 0.081 s (0.47 %); 7.66/44 = 0.174,
  0.102 s (0.59 %); 3 × 0.153 = 0.459, 0.387 s (2.2 %), 0.387/0.081 = 4.8× ✓. The 72 ms window matches
  VERIFIED_FACTS.
- Troubleshooting: binomial 64 × 1/16 = 4, σ = √(64 × 1/16 × 15/16) = 1.94 ✓. BFD 300 ms × 3 = 0.9 s ✓.

**Ch 8 — RoCEv2 framing, transport and host**
- Overhead 8 + 14 + 20 + 8 + 12 + 4 + 4 + 12 = 82 B. Efficiency 1,024/1,106 = 92.6 % → 370.3 Gb/s,
  45.2 Mpps; 2,048/2,130 = 96.2 % → 384.6, 23.5 M; 4,096/4,178 = 98.0 % → 392.1, 11.97 M ✓. 1 −
  370.3/392.1 = 5.6 %; 45.2/11.97 = 3.78× ✓.
- ACK timer: 4.096 µs × 2¹⁴ = 67.1 ms (× 8 = 0.537 s); 2¹⁸ → 1.074 s (8.59 s); 2²⁰ → 4.295 s (34.4 s) ✓.
- Loss: 2 MiB/4 KiB = 512 packets; 2,097,152 × 8/392 G = 42.8 µs; BDP 49 GB/s × 4 µs = 196 KB ≈ 48
  packets; 48 × 4,096 × 8/392 G = 4.0 µs (9.4 %); 67.1 ms/42.8 µs ≈ 1,568×; p × T_ack = 67.1 µs →
  42.8/(42.8 + 67.1) = 39 % ✓.
- GID ::ffff:0a64:0303; ToS 26 × 4 + 2 = 106; 26 as a byte → DSCP 6 (0b011010 >> 2) ✓.
- Largest packet 20 + 8 + 12 + 16 + 4,096 + 4 = 4,156 B; frame 4,174 B ✓. PCIe Gen5 x16 32 × 16 ×
  128/130 = 504 Gb/s, 80–85 % → 403–428 Gb/s; x8 252 → 202–214 Gb/s ✓.
- n½ = 392 × 10⁹/(8 × 11.5 × 10⁶) = 4,261 B; 32,768/(86.96 + 83.59) = 192.1 Gb/s; 65,536/(86.96 +
  167.18) = 257.9 Gb/s ✓; at 64 KiB the model gives 368 Gb/s (see N3).
- Latency 0.5 + 0.002 + 0.03 + 0.25 + 0.6 = 1.38 µs to 0.7 + 0.002 + 0.03 + 0.4 + 0.8 = 1.93 µs ✓.
  Node payload 8 × 392 = 3,136 Gb/s ≈ 392 GB/s ✓.

**Ch 9 — PFC headroom, ECN and incast**
- Buffer 1 MB / 50 GB/s = 20 µs ✓. BDP 50 GB/s × 4 µs = 200 KB, × 5 µs = 250 KB ✓. PFC 65,535 × 512
  bit / 400 Gb/s = 83.9 µs ✓.
- Headroom as first published (30 m): 18,432 + 2 × 50 × 150 (15,000) + 50,000 + 64 = 83,496 B. 100 m:
  18,432 + 50,000 + 50,000 + 64 = 118,496 B. Leaf total 2,671,872 + 3,791,872 = 6,463,744 B (arithmetic
  correct). For N1: 45 m → 90,996 B, so the 30 m value is short. The adopted 50 m value is 18,432 +
  25,000 + 50,000 + 64 = 93,496 B; leaf 32 × 93,496 = 2,991,872, + 3,791,872 = 6,783,744 B ≈ 6.8 MB;
  12 × 93,496 = 1,121,952 B ≈ 1,122 KB, which still holds the 600 KB that arrives during t_resp ✓.
- Spine-2 priority 4: 64 × 118,496 = 7,583,744 B ✓.
- Incast: 12 × 400 − 400 = 4.4 Tb/s = 550 KB/µs; per PG 50 − 50/12 = 45.8 KB/µs, 83/45.8 = 1.81 µs;
  12 × 83 ≈ 1,000 KB/550 = 1.82 µs; 4,000/550 = 7.3 µs; 48 MB/50 GB/s = 960 µs; 12 × 50 × 1 = 600 KB
  vs 12 × 83,496 = 1,001,952 B; 12 × (83 + 94) = 2,124 KB ✓.
- DCQCN: ⌈log₂ 12⌉ = 4; α = (1 − g) · 1 + g = 1, so each CNP halves; 4 + 3 × 50 = 154 ≈ 155 µs ✓.
- Kmin: 1,500/200 = 7.5 × BDP; 150/200 = 0.75 × BDP; 150/550 = 0.27 µs ✓. Peak queue 1,000 + 1.2 × 550
  = 1,660 KB ✓. Table 9.4 ratios: 862.8/113.6 = 7.6×; 862.8/960 = 90 %; 1,256.8/960 = 1.31×;
  17.84/48 = 37 %; 3,875.2/960 = 4.04× ✓. Tail timeout 4.3 s at timeout 20 matches Appendix E ✓.
- Troubleshooting: 417,000/60 = 6,950/s; PCIe x8 32 × 128/130 × 8 = 252 Gb/s ✓; DP 7 = 8 × 4 × 7 =
  224 GPUs ✓.

**Ch 10 — PHY, FEC, optics and spares**
- 53.125 GBd × 2 = 106.25 Gb/s; 400 × 257/256 × 544/514 = 400 × 1.0625 = 425 Gb/s; FEC overhead 5.84 %;
  425 × 10⁹/5,440 = 78.1 M codewords/s ✓. 20 log₁₀ 3 = 9.54 dB ✓. RS t = (544 − 514)/2 = 15 ✓.
- Table 10.1 recomputed (symbol error p_s = 1 − (1 − BER)¹⁰, P(≥ 16 of 544), mpmath at 60 digits):
  3.2e-6 → 2.68e-42; 1e-5 → 2.14e-34; 1.6e-4 → 1.85e-15 → 1 per 79.9 days; 2.4e-4 → 8.15e-13 → 1 per
  4.36 h ✓. Margins log₁₀(75) = 1.88, log₁₀(24) = 1.38, log₁₀(1.5) = 0.18 ✓. At 3e-5, P = 8.3e-27, which
  supports "essentially never" ✓.
- Buffer 64 MB × 8/25.6 Tb/s = 20 µs; 160 MB/51.2 Tb/s = 25 µs; 4,174 × 8/400 G = 83.5 ns ✓.
- Link budget 0.043 × 0.4 = 0.017 dB + 2 × 0.5 = 1.02 dB; −2.9 − 1.02 = −3.92 dBm, margin to −5.9 =
  1.98 dB; +0.5 − 1.02 = −0.52 dBm, 5.4 dB ✓ (DR4 limits as Appendix E). Worked example 0.3 + 3.4 =
  3.7 dB, excess 2.68 dB, headroom 2.5 dB, siblings −0.7 to −1.0 → 2.4–2.7 dB below ✓.
- BER 1,083,224/(425 × 10⁹ × 600) = 4.25 × 10⁻⁹; corrected codewords 3.2e-6 × 425e9 = 1.36 M/s = 1.74 %
  of 78.1 M ✓; acceptance BER < 1e-6 → log₁₀ 240 = 2.38 ≈ 2.4 decades ✓.
- Optics power 1,024 × 12 W = 12.3 kW (> the 10.2 kW HX8 maximum in Appendix A) ✓. Miscabling 2/32 =
  6.25 % ✓. Spares ⌈30.72⌉ = 31, ⌈10.24⌉ = 11; λ = 1,024 × 0.01 × 30/365 = 0.842, P(X ≤ 1…4) = 0.794,
  0.946, 0.989, 0.998, so 4 spares are needed for ≥ 99 % ✓. Inventory 8 × 64 + 4 × 64 = 768 ports ✓.
  Troubleshooting 6 × 450 = 2,700 vs 2,731 ✓.

## Files changed

- `concise/ch07.md` — N4.
- `concise/ch08.md` — N2, N3, N4, N6, N12.
- `concise/ch09.md` — N1, N5, N7, N11.
- `concise/ch10.md` — N4, N8, N9, N10.
- `book/part-3-networking/ch08-rdma-rocev2-infiniband/manuscript.md` — N3, N12.
- `book/part-3-networking/ch09-congestion-control-lossless-fabrics/`:
  - `manuscript.md` — N1, N11.
  - `exercises.md` and `exercises/D1-second-lossless-class/README.md` — N1 (D1 prompt).
  - `solutions/exercises/D1-second-lossless-class/{solution/solve.py, solution/answer.md, meta.yaml, outputs/*}` — N1.
  - `solutions/exercises/O2-why-not-pfc-everywhere/solution/answer.md` — N1.
  - `solutions/exercises-key.md` — N1.
  - Regenerated `exercises/*/outputs/expected/` and `lab/expected/` via `make_expected_outputs.py`.

N2, N8 and N9 were concise-only wording issues: the manuscript already gives the 82 B breakdown,
explains the conservative 64 MB figure and describes the host cabling. N4–N7 and N10 are
concise-edition labels and hedges. No change was committed.
