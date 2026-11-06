# Pre-publication review: facilities, capacity/economics, performance engineering and capstones

**Nature of this review.** AI-assisted specialist technical review (Claude, acting as a data-center
facilities, capacity/economics and performance-engineering reviewer). It is **not** an independent
external human review and does not replace one, nor a qualified facilities engineer's review of any
real plan.

**Date:** 2026-11-05

**Scope.** Concise print edition `concise/ch02.md`, `ch21.md`, `ch22.md`, `ch23.md`, `ch24.md`, and the
matching full manuscripts (`book/part-*/chNN-*/manuscript.md`) where a fix applied there too; capstone
program `capstones/README.md`, `capstones/RUBRIC.md`, `capstones/capstone-*/README.md` and each starter
kit's `check.py`. Canonical values: `docs/REFERENCE_CLUSTER.md`, `docs/VERIFIED_FACTS.md`,
`concise/back/a-reference-configuration.md`. `cover/KDP_description.html` was read only.

**Checks run.** `python scripts/build_concise.py --check` after edits: ch02 3,993, ch21 3,954, ch22 4,000,
ch23 3,967, ch24 3,975 words, all OK (after the follow-up: ch02 3,993, ch21 3,977, ch22 4,000) (ch14 FAIL at 4,001 words belongs to another reviewer's in-progress
edit and was not touched). `python -m pytest docker/harness/test_package.py --pkg <capstone> -q` for all
eight capstones: 5 passed, 5 skipped each. Follow-up harness runs: ch02 94 passed, ch21 86 passed, ch22 86 passed.

## Findings

Severity: **major** = could mislead a reader or a purchasing decision; **minor** = wrong or
inconsistent detail that does not change a conclusion; **info** = process note.

| ID | Location | Severity | Finding | Resolution |
|---|---|---|---|---|
| FEC-01 | `concise/ch02.md` §2.3 | minor | "Four 8U nodes leave 13U … empty" does not add up: 48U − 4 × 8U = 16U. The manuscript elevation also has 3U of patch cassettes and an OOB switch | **Fixed** (concise): "Four 8U nodes plus 3U of patching and an OOB switch leave 13U" |
| FEC-02 | `concise/ch21.md` §21.6 | minor | "≈ 143 L/min of water … ≈ 7 % more for a glycol mix" reads as volumetric flow. 4.18 / 3.90 = 1.072 is the *mass*-flow ratio. With Chapter 2's PG25 values the volumetric increase is (4.18 × 0.997) / (3.90 × 1.02) = 1.048, ≈ 5 % | **Fixed** (concise): "≈ 7 % more mass flow" (the manuscript already said mass flow) |
| FEC-03 | `ch21` Table 21.3 (concise + manuscript) | major | The TCO table, which feeds the canonical $3.00/GPU-h, was labelled `[ILLUSTRATIVE]` but never said the prices are not quotes. Readers who "size, buy and operate" clusters (KDP copy) could treat it as a price basis | **Fixed** (both): the caption adds "prices are teaching assumptions, not purchasing quotes" |
| FEC-04 | `ch21` Figure 21.2 (concise + manuscript) | minor | The "Node PSUs (N+1)" label contradicts Chapter 2. HX8 has 3 + 3 PSUs of 3.0 kW. One feed gives 9.0 kW against a 9.59 kW DC peak, so the node is not feed-redundant at peak. For PSU (not feed) failures it is N+2 (⌈9.59/3.0⌉ = 4 needed of 6) | **Fixed** (both): label is now "Node PSUs (3 per feed)" |
| FEC-05 | `ch22` §22.6 (concise + manuscript) | minor | The MDE formula uses the normal (z) approximation, which understates the MDE at the small n it is applied to. With a two-sample t-test (df = 2n − 2) the MDE is ≈ 0.22 s, not 0.19 s, at n = 5, and ≈ 0.33 s, not 0.25 s, at n = 3. The chapter's conclusions still hold (the 1.39 s validated gain is far above either value) | **Fixed**: concise gives the t-test values inline. To stay word-neutral at the 4,000-word cap it drops a redundant "(Table 22.3)" reference. The manuscript adds one sentence |
| FEC-06 | `capstones/README.md`, all eight `capstone-*/README.md` scenarios | major | No capstone brief, and not the program index, said that ORION, ORION-XL and Halcyon AI are fictional. Capstone A frames the work as "the eight weeks before a purchase order", with prices and a vendor quote | **Fixed**: one sentence in the index, plus a "Fictional setting" note under each brief's Scenario heading (illustrative H100-class values or synthetic data; not a real system, a vendor specification or a purchasing quote). Harness passes for all eight |
| FEC-07 | `concise/ch02.md` §2.7 vs `ch21` Table 21.1 | minor | The utilization example uses goodput 0.90 (0.85 × 0.40 × 0.90 = 0.306). Chapter 21's canonical ladder uses 0.88. Both are `[ILLUSTRATIVE]`. Chapter 23's 0.90 is an SLO target, which is consistent | **Fixed** (follow-up). REFERENCE_CLUSTER.md has no explicit goodput, but its canonical $4.72/useful GPU-h is derived from 0.88, so 0.88 is canonical. ch02 now uses 0.85 × 0.40 × 0.88 = 0.299, "≈ 30 %" (concise and manuscript); the manuscript's Table 2.8, "10 % goodput loss" and "rest of the illustrative 10 %" now read 88 % / 12 %. ch02 exercises use their own stated 92 % variation and no solver asserts 0.90, so nothing changed there |
| FEC-08 | `ch21` §21.6 vs `ch02` §2.5 | minor | Two different illustrative synchronous-swing cases. ch21: 250 W/GPU (650 → 400 W), GPU-side DC only, 64 kW on ORION-256 and ≈ 1.0 MW on ORION-XL. ch02: 400 W/GPU (700 → 300 W), node AC, ≈ 109 kW and ≈ 1.74 MW. ch21 refers the reader to ch02 for the mechanism, so the numbers look contradictory | **Fixed** (follow-up). The two passages use different assumptions and bases (GPU board DC power, 650 → 400 W, vs node AC input including PSU losses, 700 → 300 W), so they are not a contradiction. ch21 now calls its case "a milder case than Chapter 2's", says it is GPU power, and cites ch02's ≈ 109 kW AC. The manuscript also gives ≈ 1.74 MW and says to size against the larger swing unless measured. ch21 exercise K7 uses the same 250 W case and stays consistent |
| FEC-09 | `ch21` Table 21.1, `ch22` Pitfall | minor | `DCGM_FI_DEV_GPU_UTIL` is named without noting that DCGM 4.7 deprecates it for `DCGM_FI_DEV_GPU_UTIL_RATIO` (1613, 0–1), per VERIFIED_FACTS | **Fixed** (follow-up). The concise ch21 Table 21.1 and the ch22 Pitfall now name `DCGM_FI_DEV_GPU_UTIL_RATIO` (DCGM 4.7); the ch22 manuscript Pitfall too (the ch21 manuscript already had it). ch22 stays at 4,000 words after three wording trims |
| FEC-10 | `concise/ch24.md` §24.4 | info | The `[OBSERVED, 2026-10-30]` job-posting register is correctly dated and limited (purposive sample of 42 roles, mostly US, no hyperscaler). The book states "treat the file as stale after 2026-11-29". On the review date that leaves 24 days | **Open (release gate).** If the print edition ships after 2026-11-29, refresh the register and its date, or relabel the section as a dated historical snapshot |
| FEC-11 | `cover/KDP_description.html` (read-only) | minor | (a) "One reference cluster, ORION" does not say ORION is fictional or illustrative. (b) "the extensions run on one real GPU" is wrong for capstone L3 extensions, which need ≥ 2 RDMA-connected GPU nodes (e.g. Capstones E, G, H). (c) Lab, exercise and checklist counts (32 / 484 / 69) were not verified in this review | **Reported to the editor.** Not edited |

No errors were found in ch23 or ch24 arithmetic, the remaining ch02/ch21/ch22 models, or the capstone
worked numbers (recomputations below).

## Recomputations

### Chapter 2 — power, cooling, floor
- Node: 5,600 + 700 + 700 + 400 + 340 + 200 + 1,350 + 300 = 9,590 W DC. ÷ 0.94 = 10,202 W ≈ 10.2 kW ✓. GPUs are 58 % and fans 14 % ✓.
- PSUs: 5 × 3.0 = 15 kW (one PSU lost) ✓. One feed: 3 × 3.0 = 9.0 kW < 9.59 kW ✗. Feed-loss cap: 0.95 × 9.0 = 8.55 kW, 9.59 − 8.55 = 1.04 kW, ÷ 8 = 130 W, so 700 → **570 W** ✓.
- Circuit: √3 × 415 × 60 = 43,128 VA; × 0.80 × 0.95 = **32.78 kW**; × 2 = **65.55 kW/side** ✓. Rack 4 × 10.2 + 0.2 = 41.0 kW; × 1.10 = 45.1 kW; headroom 20.45 kW (31.2 %) ✓. Sizing at sustained 34.2 kW under-sizes by (41.0 − 34.2)/41.0 = 16.6 % ✓. 90 % plan: 0.9 × 65.55 = 59.0 kW ✓. Alert 0.8 × 65.55 = 52.4 kW ✓.
- 2N vs N+1: 2N 50 % usable, 3+1 75 % usable ✓.
- Swing: 8 × 400 W = 3.2 kW DC ÷ 0.94 = 3.40 kW AC/node. × 32 = 108.9 kW (28.5 % of 382) ✓. × 512 = 1.74 MW ✓. With a 500 W floor: 8 × 200 ÷ 0.94 = 1.70 kW/node, 54.5 kW and 0.87 MW ✓.
- Restart step: 32 × (10.2 − 2.5) = 246 kW (12.3 % of 2.0 MW) ✓. 512 × 7.7 = 3.94 MW > 0.4 × 8 MW = 3.2 MW ✓. 64 × 7.7 = 493 kW per group ✓.
- Air: 41.0 ÷ (1.006 × 15) = 2.717 kg/s ÷ 1.20 = 2.264 m³/s × 2,118.9 = **4,798 CFM** ✓. Residual 10.25 kW → 1,199 CFM ✓.
- Liquid: 0.75 × 41.0 = 30.75 kW ÷ (3.90 × 10) = 0.7885 kg/s ÷ 1.02 × 60 = **46.4 L/min** ✓. CDU 8 × 30.75 = 246 kW, 82 % of 300 kW ✓. Halving ΔT: flow ×2, pressure drop ×4, pump power ×8 (square-law/affinity) ✓. Low-flow alert 0.85 × 46.4 = 39.4 L/min ✓.
- Troubleshooting physics: 0.75 × 34.2 = 25.65 kW. 31.0 L/min × 1.02 ÷ 60 = 0.527 kg/s → ΔT = 12.5 K. 33.4 + 12.5 = 45.9 °C ✓ (morning: 30.1 + 12.5 = 42.6 ✓; rack-05 at 46.0 L/min → 41.8 vs 41.7 ✓). Clock ratio 1,548/1,830 = 0.846. Step 19.6/17.4 = +12.6 % ✓. Restart 0.25 h × 256 = 64 GPU-h ✓.
- Floor: 4 × 135 + 170 + 60 + 50 = 820 kg ÷ 0.72 m² = 1,139 kg/m² (5.1 % margin on 1,200) ✓. Over 1.44 m², 569 kg/m² ✓.
- BOM: links 256 + 256 = 512; ports 768; single-port optics 1,024; twin-port 256 + 384 = 640 ✓. Injection 102.4 Tb/s, bisection 51.2 Tb/s per direction ✓. OOB 32 + 12 + 2 + 8 + 32 = 86 ✓.
- Pod: 328 + 32 + 18 + 4 = 382 kW × 1.25 = 477.5 kW ✓. Energy: (273.6 + 54.0) × 1.25 × 8,760 = 3,587 MWh × $0.08 = **$287k** ✓.

### Chapter 21 — capacity, TCO, $/GPU-hour ladder, design comparison, capping
- Usable factor: 0.97 × 0.922 × 0.95 = **0.8496** ✓. Repair: 32/1,536 × 24 = 0.5 failures/day × 5 d = 2.5 nodes = 7.8 % ✓. Poisson(2.5): P(≤4) = 0.891, P(≤5) = 0.958, so p90 is 5 nodes = 15.6 %, giving 0.97 × 0.844 × 0.95 = 0.778 ✓.
- Energized: 10.2 ÷ 8 × 1.12 = 1.428 kW/GPU. 800 kW → ⌊70.0⌋ = 70 nodes = 560 GPUs. 420 kW → 288. 1,500 kW → 1,048 ✓.
- ORION-XL ladder: 4,096 → 3,973 → 3,663 → 3,480 → 2,958 → 2,396 (58.5 %) ✓.
- **TCO:** capex (32 × $405k + $2.0M) = $14.96M ÷ 4 = $3.740M. Power 32 × 8.5 × 1.12 = 304.64 kW × 1.25 × 8,760 × 0.08 = $0.267M. Space 365.57 kW × $130 × 12 = $0.570M. Support 0.08 × 14.96 = $1.197M. Staff $0.960M. **Total $6.734M** ✓.
- **Ladder:** 256 × 8,760 = 2,242,560 GPU-h. $6.734M ÷ 2,242,560 = **$3.003/nominal GPU-h** ✓ (canonical $3.00 at $0.08/kWh). ÷ (0.8496 × 0.85) = **$4.16/allocated** ✓. ÷ 0.88 = **$4.72/useful** ✓. Shares: capex 55.5 %, support 17.8 %, electricity 4.0 % ✓.
- Sensitivities: allocation 0.75 → $5.36 (+13 %). Goodput 0.80 → $5.20 (+10 %). $0.15/kWh → power $0.500M, total $6.967M → $4.89 (+3.5 %). 10 % server discount (−$1.024M capex) → $6.396M → $4.49 (−5 %). 5-year amortization → $5.986M → $4.20 (−11 %). All ✓.
- Build vs rent: 3.00/(0.85 a) < 6.00 ⇒ a > 0.588 ✓.
- Design comparison: A ⌊1,000/11.424⌋ = 87 nodes. B ⌊1,000/16.016⌋ = 62 nodes; B's cooling ⌊1,000/11.44⌋ = 87, so power binds ✓. Spine efficiency 1/1.075 = 0.930 ✓. Useful: A 696 × 0.6355 = 442.3, B 496 × 2.2 × 0.93 × 0.6355 = 644.9 ✓. TCO A: 8.809 + 0.784 + 1.550 + 2.819 + 2.610 = $16.57M. TCO B: 12.40 + 0.701 + 1.549 + 3.968 + 1.860 = $20.48M ✓. Units per $M 26.69 / 31.49 ✓. Facility power 1.118 / 1.000 MW ✓. Per GPU-year $23,810 / $41,286 ✓. Break-even multiplier 2.2 × (26.69 × 20.48)/644.9 = 1.865 ≈ 1.86 ✓. Unscaled network: 0.386 + 0.075 + 0.150 = 0.611, 1.636× → 516 units, 25.2 per $M ✓.
- Cost per token: 304.64 kW × 17.4 s = 1.472 kWh IT, × 1.25 = 1.840 kWh, ÷ 4.19 M tokens = 0.439 kWh/M tokens = $0.035. Total cost: 256 × 17.4/3,600 × $4.72 ÷ 4.19 = **$1.39 per M tokens**. Electricity 2.5 % ✓.
- Capping (legacy hall, 29.50 kW plan): 700 W → 10.2 kW, 2/rack, 32.0 node-eq. 650 W → 9.8 kW, 3/rack, 47.5. 550 W → 45.4. 400 W → 37.9. Unused budget 9.1 / 0.1 / 2.5 / 6.1 kW ✓. +48 % ✓. A fourth node needs ≤ 347 W ✓. With base 4.69 kW: 3 × 9.89 = 29.7 > 29.5; 600 W → 28.5 kW, 48 × 0.972 = 46.7 (lab curve has 600 W = 0.972) ✓. Job capping: 0.055 × 192 = 10.6 GPU-eq for 4.8 kW; uniform 28.8 kW ✓.
- Forecast table rows all reproduce (e.g. 560 × 0.8496 = 475.8; 420/0.85 = 494.1; gap −18.3) ✓. Cap mitigation ⌊800/10.224⌋ = 78 nodes → 624 → 530 → 501 ✓. 2029Q4: 94.7/0.85 → 112 GPUs ✓. Stranded cost 464 × 2,190 × $3.00 = **$3.05M/quarter** ✓.
- Utilization decomposition: 0.25 × 44 + 0.66 × 0.742 × 96 = 11.0 + 47.0 = 58.0 % ✓. Allocation 0.74 ✓. Free GPUs 0.66 × 0.258 × 256 = 44 = 16 + 28 ✓.

### Chapter 22 — step budget, statistics, A/B validation
- Table 22.1 sums to 17.90 s, and every share reproduces ✓. 17.4/17.9 × 40 % = 38.9 % MFU ✓. Expected maximum of n normals: 1.42σ (n = 8), 2.07σ (n = 32) ✓.
- DP: 70e9/32 × 2 B = 4.375 GB. Ring 4.38 → 7.66 GB at 45 GB/s → 0.10 / 0.17 s. Exposed 0.03 / 0.10 s ✓.
- **MDE:** (1.96 + 0.84) × 0.11 × √(2/5) = 0.195 s ✓ as a z-approximation. The t-based values are (2.306 + 0.889) × 0.11 × 0.632 = 0.222 s (n = 5) and (2.776 + 0.941) × 0.11 × 0.816 = 0.334 s (n = 3), hence FEC-05. The HC3 interval 8.3 ± 1.96 × 1.7 = 5.0–11.6 % ✓.
- Factorial attribution: means 17.40 / 22.40, Δ 5.00 s (+28.7 %). effect_P 8.40, effect_S 1.40, P×S 0.00, period 0.10. Check: 17.40 + 0.10 + 4.20 + 0.70 = 22.40 ✓. Shares 84/14/2 % ✓.
- TP model: 4,096 × 8,192 × 2 = 67.1 MB; 128 × 20 × 4 = 10,240 all-reduces × 117.4 MB = 1.202e12 B. ÷ 360 GB/s = 3.34 s. ÷ 150 → 8.01 s. ÷ 90 → 13.36 s. Implied 102 GB/s ✓.
- Dataloader: ρ = 16/17.4 = 0.92. 0.10 × 14 = 1.4 s. Fix: 4.0 s interval (ρ = 0.23); lead 8 × 17.4 = 139 s > 34 s ✓.
- Weak scaling: 942.7 vs 915.3 tokens/s/GPU, E = 0.971. Gap 0.52 = 0.07 + 0.33 + 0.12 ✓. A/B validation 18.86 − 17.47 = 1.39 s, far above the MDE under either approximation ✓.
- Troubleshooting: 13.9 × 1,830/1,620 = 15.70 s → 19.7 s ✓. DP = 7 break-even 1/0.875 − 1 = 14.3 % ✓. 4,194,304/17.9 = 234,000 tokens/s ✓.

### Chapter 23 — design review and mini-capstone
- Leaf 32 × 400G = 12.8 Tb/s each way. NVLink/NIC 450/50 = 9×. Bubble 3/128 = 2.3 %. Memory 1.12 TB/32 = 35 GB. Rack 40.8 ≤ 45 kW (9.3 % headroom). Ingest 241,100 × 4 B ≈ 1 MB/s ✓.
- Step 1.7616e18 / 1.0127e17 = 17.39 s. Steps 476,837. Wall time 96.00 d, 106.7 d at 0.90. MFU 0.35 → 19.88 s → 109.7 d → 121.9 d > 120 (fails) ✓.
- Young/Daly: τ = √(2 × 60 × 172,800) = 4,554 s. 1.32 % + 1.84 % = 3.16 %. 225.9 GPU-h/failure × 53 = 12,000 GPU-h. Async (δ = 5 s) 1.28 %. Doubled PFS (δ = 35.5 s) 2.5 %. M = 24 h → τ = 3,220 s ✓.
- Meta comparison: 54 × 24/419 = 3.09 h × 64 = 198 h ✓. Change batch: 832 vs 224 GPU-h ✓. FMEA 192 / 14 ✓. Backlog 2.25 / 2.00 ✓. B-02 356/8 = 44.5 GB/s (89 % of line rate). B-04 0.191 s. B-05 2.64 % ✓.

### Chapter 24 — career register and interview arithmetic
- Idle hour 256 × $3.00 = $768. 5 % for 30 days: 0.05 × 256 × 720 × 3.00 = $27,648 ✓ (uses the canonical nominal rate).
- Readiness Σw = 17, Σ = 13.333 → 78.4 %. Claimed 25/8 = 3.1, evidenced 20/8 = 2.5 ✓.
- Register: 54 − 4 = 50 rows, 50 − 8 = 42 roles (16 %), 25 + 11 + 6 = 42, RDMA 16 + 7 + 19 = 42. Synthetic 61 − 10 − 11 − 6 − 3 = 31 ✓.
- 1,024-GPU fabric: 32 leaves, 16 spines, 2 links per pair, 48 switches, k²/2 = 2,048. ECMP 32 × (31/32)³² = 11.6, 1 − (31/32)³¹ = 0.63 ✓.
- Case study: 1 − 2.10/2.29 = 8.3 %, × 128 × 144 = 1,530 GPU-h × $3.00 = $4,590 ✓.
- Interview: 222.6 GPUs. TP 1.20 TB → 3.3 s on NVLink, 30 s on a NIC. Floor-δ τ = 2,058 s (34 min), 1.7 %. MFU 32 % → 21.75 s. PP = 5: 3.0 % bubble and 17.4 s ✓.
- Troubleshooting round: busbw = algbw × 2 × 127/128 (181.44 → 360.04, 103.69 → 205.76). 0.571 = 212/371. Go-back-N 371/(1 + 50 × 0.015) = 212 Gb/s ✓.

### Capstone worked numbers spot-checked
- F: 980/1.6 = 612.5 s. Resume 903 s. 192 × 0.501 = 96 GPU-h. 137 interruptions/yr. Poisson(1.875) P(≤2) = 0.711. Spares 140,160 GPU-h ✓.
- G: τ = √230,400 = 480 s. Lag 392 s (65 %). 1,698 GPU-h × 7.5/day = 12,735 (13.8 %). Incident 2,471.5 GPU-h ✓.
- H: prefill 73.9 ms. Decode 23.1 ms. KV capacity 1,330,566 tokens. KV emit 9.3 GB/s. Fan-in 40 % / 79 % / 95 % ✓.
- E: thresholds 92.5 / 71 / 76 / 20 %. Ring NVLink bound 257 GB/s. Burn-in 960 GPU-h. Rollout 896 GPU-h ✓.

## Mermaid diagrams vs prose

| Figure | Verdict |
|---|---|
| 2.1 power one-line | Matches prose (2N from switchgear; PSUs 1–3 on A, 4–6 on B) |
| 2.2 cooling loops | Matches (30 → 40 °C TCS, 25 % residual to air) |
| 21.2 power chain | PSU label fixed (FEC-04); otherwise matches |
| 22.1 hypothesis tree | Matches §22.3/§22.4 leaves and tests |
| 23.1 workflow, 23.2 failure domains | Match Table 23.2 blast radii |
| 24.1 interview arc | Segments sum to 45 min, as stated |

## Generalization and labels

H100- and ORION-specific power and cooling values are scoped "H100-class" and `[ILLUSTRATIVE]` (ch02
§2.1, Table 2.1, Table 2.4 "depends on the specific hall and platform"). The ch21 design PUEs are
declared variations. ch23's 50 kW row is a declared variation. Modeled and simulated results carry
`[MODELED]`/`[SIMULATED]`, and none reads as a measurement. The single `[MEASURED]` row in ch23 (B-06,
linter wall time) is genuinely measurable on a laptop. ch24's register is `[OBSERVED, 2026-10-30]`
with its stale-after date stated (FEC-10).

## Capstone reproducibility verdict (release gate)

Starter-kit checker results, run 2026-11-05 from each `starter-kit/` with `python check.py`, all match
the quoted "expected first result":

| Track | Quick start | Prerequisites | Deliverables | Scoring (weights sum 100; RUBRIC.md) | Evidence requirements | Checker (quoted = actual) | Verdict |
|---|---|---|---|---|---|---|---|
| A 256-GPU cluster | ✓ | ✓ | ✓ Required artifacts table | ✓ | ✓ labels per artifact; realism boundary | 1/16 (15 TODO) | **Pass** |
| B Telemetry | ✓ | ✓ | ✓ | ✓ | ✓ | 0/14 (14 TODO) | **Pass** |
| C Training perf | ✓ | ✓ | ✓ | ✓ | ✓ manifest, repetitions | 0/12 (12 TODO) | **Pass** |
| D Inference platform | ✓ | ✓ | ✓ | ✓ | ✓ | 0/11 (11 TODO) | **Pass** |
| E Fleet lifecycle | ✓ | ✓ (table) | ✓ | ✓ | ✓ realism boundary, submission checklist | 1/17 | **Pass** |
| F Game day | ✓ | ✓ (table) | ✓ | ✓ | ✓ | 2/11 | **Pass** |
| G 512-node FT | ✓ | ✓ (table) | ✓ | ✓ | ✓ "SIMULATED" first-page rule | 1/11 | **Pass** |
| H Disaggregated serving | ✓ | ✓ (table) | ✓ | ✓ | ✓ | 1/11 | **Pass** |

Gaps found: the fictional-setting statement was missing from every brief and from the index (FEC-06,
fixed). Briefs A–D have no per-brief submission checklist. The program index §7 covers it, so no
change was made. Harness `test_package.py` passed for all eight after the edits.
