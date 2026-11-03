# Review Status

Gate: weighted ≥ 9.5, no dimension < 9.0, labs valid (`python scripts/validate_labs.py`: solution,
starter, no-generator, docs), no open blocker/major findings (see [EDITORIAL_RUBRIC.md](EDITORIAL_RUBRIC.md)).
Independent-review history and finding → resolution tables are in each package's `review/REVIEW.md`.

**Status (2026-10-30): all 24 chapters, the capstone program (README + RUBRIC) and capstones A–H pass the internal gate at 9.50, with no open blocker/major/minor findings. `python scripts/validate_labs.py` → 32/32 labs valid (solution, starter, no-generator, docs).** Since then (2026-10-31): G4 vendor-claim verification, G6 machine-assisted copyedit and G7 job-market refresh done; every lab runs in its own container and `python scripts/docker_labs.py ci` passes 32/32 packages (2,144 tests, 480 exercise folders with solutions and generated outputs). Remaining external gates: see [RELEASE_GATES.md](RELEASE_GATES.md).

## Independent re-review (2026-11-01 to 2026-11-03)

The chapters were re-scored by new reviewers who did not see the earlier scores or reviews. Round 1
(r1) found every chapter at or near the gate, with a book mean of **9.35**. Each chapter was then
revised. A second set of fresh reviewers (r2) scored the revised chapters, and the authors fixed
every r2 finding. The r2 reviewer then verified those fixes and re-scored. Finding → resolution
tables are in each package's `review/REVIEW.md` ("Independent review r1" / "r2").

**Result:** all 24 chapters pass the gate with no open blocker or major findings. The book mean is
**9.77** (range 9.55–9.93).

| Chapter | r1 (fresh reviewer) | After r2 fixes (verified) |
|---|---|---|
| ch01 | 9.45 | **9.90** |
| ch02 | 9.30 | **9.875** |
| ch03 | 9.50 | **9.85** |
| ch04 | 9.48 | **9.775** |
| ch05 | 9.35 | **9.55** |
| ch06 | 9.40 | **9.55** |
| ch07 | 9.38 | **9.68** |
| ch08 | 9.48 | **9.68** |
| ch09 | 9.25 | **9.60** |
| ch10 | 9.35 | **9.83** |
| ch11 | 9.38 | **9.75** |
| ch12 | 9.40 | **9.78** |
| ch13 | 9.28 | **9.80** |
| ch14 | 9.38 | **9.80** |
| ch15 | 9.50 | **9.80** |
| ch16 | 9.53 | **9.875** |
| ch17 | 9.18 | **9.78** |
| ch18 | 9.33 | **9.93** |
| ch19 | 9.40 | **9.78** |
| ch20 | 9.40 | **9.85** |
| ch21 | 8.80 | **9.68** |
| ch22 | 9.375 | **9.78** |
| ch23 | 9.325 | **9.78** |
| ch24 | 9.225 | **9.75** |

Caveats:

- The final scores come from the same r2 reviewer verifying fixes to its own findings. That
  reviewer never edited the text, but some generosity is likely.
- The capstones were not re-reviewed in this pass.
- These are internal editorial scores. Gates G1 (L2/L3 hardware), G2, G3, G5 and the human
  copyedit are still open (RELEASE_GATES.md).
- Three committed L2 GPU bundles carry errata and need a hardware rerun: ch04 (truncated trace
  window), ch14 (failed invariants under memory pressure) and ch24 (level scoring).
- Shared-fact changes from this pass are in REFERENCE_CLUSTER.md and VERIFIED_FACTS.md:
  - $3.00 per GPU-hour (Ch 21 TCO) and $0.08/kWh
  - 64 MB rail-leaf buffer
  - netdev naming
  - nvidia-smi topology terms
  - one NVLS threshold
  - DLC cooling, pod IT and rack-peak rules
  - verified DCGM 4.7 field IDs and NCCL WARN formats
- `concise/` has not been re-synced with these changes.

| Package | Independent score history | Status | Open next step |
|---|---|---|---|
| ch01 landscape | 9.05 → 9.50 → **9.50** | **PASS** | closed |
| ch02 data-center anatomy | 9.23 → 9.40 → **9.50** | **PASS** | closed |
| ch03 Linux host diagnostics | 9.25 → 9.35 → **9.50** | **PASS** | closed; safety guard re-verified (0 bypasses) |
| ch04 GPU architecture | 9.18 → 9.50 → **9.50** | **PASS** | closed |
| ch05 interconnects/topology | 8.85 → 9.33 → **9.50** | **PASS** | closed |
| ch06 GPU performance | 9.10 → 9.50 → **9.50** | **PASS** | closed |
| ch07 Ethernet/BGP | 9.23 → 9.35 → **9.50** | **PASS** | closed |
| ch08 RDMA/RoCE/IB | 9.23 → **9.50** | **PASS** | closed |
| ch09 congestion | 9.20 → **9.50** | **PASS** | closed |
| ch10 physical layer | 9.08 → 9.28 → **9.50** | **PASS** | closed |
| ch11 distributed training | 9.30 → 9.48 → **9.50** | **PASS** | closed |
| ch12 collectives/NCCL | 9.13 → 9.50 → **9.50** | **PASS** | closed |
| ch13 GPU data movement | 9.20 → 9.38 → **9.50** | **PASS** | closed |
| ch14 storage/checkpointing | 9.50 → 9.43 → 9.40 → **9.50** | **PASS** | closed |
| ch15 LLM inference | 9.13 → 9.43 → 9.50 → **9.50** | **PASS** | closed |
| ch16 fleet lifecycle | 9.35 → 9.40 → **9.50** | **PASS** | closed |
| ch17 Kubernetes/Slurm | 9.00 → 9.30 → **9.50** | **PASS** | closed |
| ch18 observability/SLOs | 9.23 → **9.50** | **PASS** | closed |
| ch19 reliability/security | 9.15 → **9.50** | **PASS** | closed |
| ch20 automation/safe change | 9.00 → **9.50** → **9.50** | **PASS** | closed |
| ch21 capacity/power | 9.03 → 9.48 → **9.50** | **PASS** | closed |
| ch22 cross-layer perf | 8.90 → 9.50 → 9.50 → **9.50** | **PASS** | closed |
| ch23 capstone guide | 8.85 → 9.475 → 9.375 → **9.50** | **PASS** | closed |
| ch24 career paths | 9.18 → 9.13 → 9.375 → **9.50** | **PASS** | closed |
| capstones README + RUBRIC | pass → **9.50** | **PASS** | closed |
| capstone A 256-GPU cluster | 9.30 → 9.475 → **9.50** | **PASS** | closed |
| capstone B telemetry | 9.30 → 9.325 → **9.50** | **PASS** | closed |
| capstone C training perf | 8.95 → 9.50 → **9.50** | **PASS** | closed |
| capstone D inference platform | 9.23 → 9.50 → **9.50** | **PASS** | closed |
| capstone E fleet lifecycle | 9.05 → 9.50 → **9.50** | **PASS** | closed |
| capstone F game day | 9.30 → 9.50 → **9.50** | **PASS** | closed |
| capstone G 512-node FT | 9.30 → 9.38 → **9.50** | **PASS** | closed |
| capstone H disaggregated serving | 8.68 → 9.28 → **9.50** | **PASS** | closed |

## Full findings — ch16 / ch17 / ch20 (independent review, iteration 1)

**ch16**
- R16-01 [major] §16.5, Table 16.4, acceptance_policy.yaml: 400 GB/s single-node busbw floor fails healthy nodes when NVLS is off (ring algbw ceiling ≈ 257 GB/s). State the NVLS assumption, record NCCL version/algorithm, baseline the non-NVLS figure separately.
- R16-02 [major] §16.8, key M2: "4 nodes = one DP replica → DP = 7" contradicts the per-rack cap of one node per wave. Define replica striping or drop the claim.
- R16-04 use `clocks_event_reasons.active` consistently; R16-05 Xid 94 vs 95 handling, map 63; R16-06 add the Diagnostic plugin to DCGM r3; R16-07 perftest iteration count and server flags; R16-03, R16-08, R16-09, R16-10 consistency notes.

**ch17**
- R17-01 [major] QOS GrpTRES limits need `AccountingStorageType=accounting_storage/slurmdbd` and `AccountingStorageEnforce=associations,limits,qos`; mention `QOSMaxGRESPerUser`.
- R17-02 [major] Rail-degraded node policy: use features/constraints/weights in Slurm and labels/affinity in Kubernetes; reserve DRAIN for GPU, Xid and all-rails faults.
- Minors R17-03..12: preempt/qos wording; 24/8 pool split vs the 32-node W-TRAIN gang; DRA GA in 1.34 (`resource.k8s.io/v1`); quota errors appear at creation; key K6; Kueue `spec.stopPolicy`; J06 vs J01 order; §17.11 reference; data consistency (P03/P04/48211/P10); Kueue TAS details in the key.

**ch20**
- R20-01 [major] Host MTU 9,216 does not break RoCE at path MTU 4096; TCP/IP black-holes instead.
- R20-02 [major] Vendor MTU conventions differ (EOS/NX-OS L3 `mtu` = IP MTU; Junos media MTU). Add a vendor note; describe the +22 B rule as a conservative portable policy.
- R20-03 [major] n06 shows host MTU 1500 with RDMA path MTU 4096, which is impossible; fix the data or make it an explicit plant.
- R20-04 [major] Explain the RoCE MTU-cap mechanism for racks 3–8.
- Minors R20-05..11: PFC ratio is 1.7–1.8×; firmware version timeline; SE ≈ 0.16 GB/s (≈14 SE); Step 5/7 framing; commit-confirm vendor row; hypergeometric ≈ 0.146; AC3 floor; r1..r8 vs leaf-r0..r7 naming collision.

Word budget: each fix list comes with matching cuts (see the review) to keep manuscripts at about 10,000 words.
