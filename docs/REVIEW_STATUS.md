# Review Status

Gate: weighted ≥ 9.5, no dimension < 9.0, labs valid (`python scripts/validate_labs.py`: solution,
starter, no-generator, docs), no open blocker/major findings (see [EDITORIAL_RUBRIC.md](EDITORIAL_RUBRIC.md)).
Independent-review history and finding → resolution tables are in each package's `review/REVIEW.md`.

**Status (2026-10-30): all 24 chapters, the capstone program (README + RUBRIC) and capstones A–H pass the internal gate at 9.50, with no open blocker/major/minor findings. `python scripts/validate_labs.py` → 32/32 labs valid (solution, starter, no-generator, docs).** External publication gates remain open — see [RELEASE_GATES.md](RELEASE_GATES.md).

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
