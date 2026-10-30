# Chapter 23 — Answer Key (instructor only)

All numbers verified twice. Values are `[MODELED]` from stated inputs unless labelled otherwise.

## A. Knowledge checks

**K1.** (1) *Workload* → a reviewer can recompute FLOPs, memory, communication. (2) *Numeric
objective* (e.g. finish 2 × 10¹² tokens in 120 days, goodput ≥ 0.90) → required throughput and
margin can be checked. (3) *Constraints* (45 kW per rack, 8 racks, budget) → rack count and power
invariants. (4) *Scope boundary* → reviewers know which subsystems are not their concern and which
interfaces must be specified. (5) *Evidence tier* → which numbers may be `[MEASURED]`.
*Marking:* 1 mark per element with a consequence; no credit for "requirements" without a number.

**K2.** Without an **owner**, nobody validates the assumption and nobody is paged when production
contradicts it; it silently becomes "fact". Without a **validation** plan, the assumption cannot be
falsified, so reviewers cannot tell a belief from a measured value; "TBD" is the classic symptom.
*Common mistake:* answering "for documentation". The point is accountability and falsifiability.

**K3.** The revisit trigger makes the decision self-monitoring: it names an observable condition that
would reopen it. Example: "Reopen if the per-GPU memory at TP = 8, PP = 4 exceeds 80 GB for a
planned model, or if the scheduler can place a TP group across nodes (detected by a placement audit
of `scontrol show job` node lists), or if NVLink-to-NIC bandwidth ratio falls below 4× on a new
platform." *Marking:* full credit requires a metric or event.

**K4.** A rack budget is a hard electrical limit (breaker, PDU rating after derating); exceeding it
trips the circuit regardless of average draw. Events: synchronized step-start power spikes across
all GPUs, burn-in or acceptance stress tests, firmware or driver changes that alter power capping,
a failed PDU feed concentrating load on the other feed.

**K5.** (a) Rack power failure: 4 nodes × 8 = 32 GPUs (12.5 % of 256); only jobs with ranks in that
rack are affected. (b) Rail-leaf failure: 0 GPUs lost, but NIC *r* of every one of the 32 nodes
loses connectivity, so every multi-node job using rail *r* hangs or fails (plan for job-fatal). The
difference: rail-optimised wiring makes a single switch a cross-cutting logical dependency of every
node, while a rack is a physically local group.

**K6.** D is scored high when the failure is *hard* to detect. Multiplying by D pushes quiet failures
up the list. Failures that "only make things slower" (firmware mismatch, GPUDirect RDMA disabled on
one node, a downtrained PCIe link) are hard to detect and silently waste goodput across many jobs for
a long time, whereas a loud failure is noticed and fixed. ORION example: NIC firmware mismatch,
S = 6, O = 4, D = 8, RPN = 192.

**K7.** (a) `[MEASURED]` allowed (the laptop really ran it; cite the manifest). (b) `[MODELED]`.
(c) `[MEASURED]` allowed for the laptop's parse time. (d) `[SIMULATED]`, stating what the
simulator does not capture. *Common mistake:* labelling (d) MEASURED because "we ran it".

**K8.** Approved; approved with conditions (each with an owner and date); rework (another review).
"Take it offline" has no owner, date or decision, so the review produced nothing accountable.

## B. Worked problems

**W1.**

1. GPU accounting: 34 × 8 = 272 ≠ 256. Declare `spares: 2` so (34 − 2) × 8 = 256 ✓. Parallelism:
   TP × PP × DP = 8 × 4 × 16 = 512 ≠ 256; the correct DP = 256 / (8 × 4) = 8.
2. Leaf ports: 34 down + 32 up = 66 > 64 ✗. Keeping both spares cabled needs 34 downlinks, so
   uplinks ≤ 64 − 34 = 30; equal per spine across 4 spines needs a multiple of 4 → 28 uplinks
   (7 per spine). Ports used 34 + 28 = 62 (2 free).
   - Oversubscription, all 34 active: 34 : 28 = 1.214 : 1. With the spares idle: 32 : 28 =
     1.143 : 1. (For rail-aligned W-TRAIN traffic, which stays inside the leaf, this has
     negligible effect; it matters for cross-rail traffic.)
   - Spine ports: 8 leaves × 7 = 56 of 64.
   - Backend cables: 8 × (34 + 28) = 496 (272 host–leaf + 224 leaf–spine). The bundle's 512 is
     wrong under every configuration considered here (the original 34 + 32 would need 528).
   - Accept also: do not cable spares to the backend (32 + 32 = 64, 1:1, 512 cables) at the cost of
     recabling during a swap; or use larger leaves. Any answer must state the claimed ratio
     consistently.
3. Max nodes per rack = floor(45 / 10.2) = floor(4.41) = 4. Racks = ceil(34 / 4) = ceil(8.5) = 9.
   With only 8 racks: (i) keep the 2 spares outside the GPU row or hold them unracked; (ii) obtain a
   larger rack budget from Facilities; (iii) enforce a node power cap ≤ 45 / 5 = 9.0 kW in the two
   5-node racks, which must be validated for throughput impact (MFU may drop) and enforced in
   firmware, not by convention. Option (iii) changes A-03 and A-04 and needs an ADR.
*Marking:* 4 / 6 / 4 marks for parts 1/2/3. *Common mistakes:* using sustained power (8.5 kW, giving
5 per rack); choosing 30 uplinks (not divisible by 4 spines); forgetting the cable count.

**W2.**

1. Variation: M = 24 h = 86,400 s (canonical 48 h halved). τ = sqrt(2 × 60 × 86,400) =
   sqrt(10,368,000) = 3,219.9 s ≈ 53.7 min. δ/τ = 60 / 3,219.9 = 1.863 %; τ/(2M) = 3,219.9 / 172,800 =
   1.863 % (equal at the optimum, a useful check); R/M = 900 / 86,400 = 1.042 %. Total waste = 4.77 %.
2. Lost per failure = τ/2 + R = 1,610 + 900 = 2,510 s; × 256 GPUs / 3,600 = 178.5 GPU-hours.
3. Goodput = 1 − 0.0477 − 0.05 = 0.9523 − 0.05 = 0.9023. Duration = 96.00 / 0.9023 = 106.39 days.
4. Reduce δ by validating asynchronous checkpointing: with δ = 5 s, τ = sqrt(2 × 5 × 86,400) =
   929.5 s; δ/τ = τ/(2M) = 0.538 % each → 1.08 % + R/M 1.042 % = 2.12 % total, saving ≈ 2.65 points
   of goodput (96.00 / 0.9288 = 103.36 days, ≈ 3.0 days shorter). Reducing R (faster requeue,
   pre-staged images; spare nodes only as an explicit variation, since ORION has none) is a strong second: at 900 s it is a fixed 1.04 % here, half of the remaining
   waste once δ is small. Increasing storage bandwidth only shrinks the 12.25 s floor inside δ and is
   the weakest lever. (Canonical M = 48 h for comparison: 3.16 % waste, Section 23.10.)
*Marking:* 3/2/2/3. *Common mistake:* using M in hours with δ in seconds.

## C. Lab (instructor notes)

### Planted findings in `bundle_kestrel_capA/` (20)

| # | Rule | Location | What was planted | Why it teaches |
|---|---|---|---|---|
| 1 | COMP-001 | design.md:Failure exercise | Section omitted | The most commonly skipped capstone artifact |
| 2 | GPU-001 | bom.yaml:gpu_nodes | 34 nodes, spares 0, total 256 | Spares added in prose but not in the BOM |
| 3 | GPU-002 | assumptions.yaml:workload.parallelism | DP = 16 (512 GPUs) | Parallelism copied from a larger design |
| 4 | PORT-001 | topology.yaml:rail_leaf | 34 + 32 = 66 > 64 | Adding nodes without re-checking leaf radix |
| 5 | PORT-002 | topology.yaml:claimed_oversubscription | "1:1" vs 34:32 | Asserted, not computed |
| 6 | CABLE-001 | bom.yaml:cables.backend_400g | 512 vs 528 | BOM not regenerated from topology |
| 7–8 | POWER-001 | bom.yaml:racks.rack-07, rack-08 | 5 × 10.2 = 51 kW > 45 kW | Sizing with sustained power |
| 9 | EVID-001 | benchmarks.md:B-03 | Empty label | |
| 10 | EVID-002 | benchmarks.md:B-05 | "ESTIMATED" | Invented label vocabulary |
| 11 | EVID-003 | benchmarks.md:B-02 | MEASURED, manifest "-" | Unreproducible measurement |
| 12 | EVID-004 | benchmarks.md:B-04 | 8-node busbw MEASURED at L1 | Physical claim from a laptop |
| 13 | NUM-001 | design.md:L18 | "400 Gb/s per port … non-blocking" | Unlabelled number, plus an unsupported claim |
| 14 | NUM-001 | design.md:L29 | "under 6 %" | Unlabelled performance claim |
| 15 | XREF-001 | design.md:A-12 | Cites A-12, not in register | Dangling assumption |
| 16 | COMP-002 | assumptions.yaml:A-07.validation | No validation plan for MTBF | Decision-critical assumption untestable |
| 17 | COMP-002 | slos.yaml:SLO-03.window | No window | SLO not evaluable |
| 18 | FD-001 | failure_domains.yaml:FD-06 | Storage metadata, redundancy none, no mitigation | Unmitigated SPOF |
| 19 | FD-002 | failure_domains.yaml:scheduler | Class not analysed | Control-plane blind spot |
| 20 | SLO-001 | slos.yaml:SLO-04.target | target "low" | Unmeasurable SLO |

Counts: 6 blocker (COMP-001, GPU-001, GPU-002, PORT-001, POWER-001 × 2), 14 major. Gate FAIL.

### Traps (must NOT be flagged)

- `topology.yaml` downlinks 34 = BOM count 34: PORT-004 is consistent. A learner who flags it has
  confused "inconsistent with the 256-GPU intent" with "inconsistent with the BOM".
- `FD-07` rack power has redundancy `none` but a real mitigation (DP replicas spread across racks).
  Not FD-001.
- `design.md` L28 contains "356 GB/s busbw (B-02) … 328 GB/s (B-04)": numbers attributed by ID; not NUM-001
  (the B-04 problem is caught by EVID-004 instead).
- `design.md` L19 "10.2 kW [VENDOR-SPEC, 2026-10]" is labelled; L20 relies on A-09.
- `B-06` (linter runtime, MEASURED, L1, unit s) is a legitimate laptop measurement.
- The reference bundle must produce zero findings; any finding there is a false positive.

### Triage memo: expected classification

Design defects (change what is built): GPU-001/002, PORT-001/002, CABLE-001, POWER-001 ×2, FD-001,
FD-002. Documentation/evidence defects (change what is claimed): COMP-001, COMP-002 ×2, EVID-001..004,
NUM-001 ×2, XREF-001, SLO-001. No linter false positives. Raise **POWER-001** or **PORT-001** first:
both are physical impossibilities that change rack count or switch SKU and therefore cost and
schedule; they share a root cause with GPU-001 (two spares added late without re-running the
arithmetic), so present them as one finding with three symptoms. Minimal fixes: see W1.
*Marking (15 points):* classification 6, minimal fixes 5, ordering with justification 4.

## D. Troubleshooting case T1

1. Sorted: 194.4, 208.8, 318.4, 324.0, 329.6. Median 318.4 GB/s; mean = 1,375.2 / 5 = 275.04 GB/s
   (34.4 GB/s per rail). The team reported the mean of a bimodal sample as if it were a single
   distribution, did not state that the fabric was shared, and drew a design conclusion (lower A-06 to
   34 GB/s per rail) from contaminated data. The "23 % loss" (1 − 275.0/356 = 22.7 %) compares a
   contaminated mean with a clean 2-node median; the clean runs (median 324.0 of runs 1, 3, 5) are
   only 9 % below B-02, consistent with 4-node latency terms and above A-06's 320 GB/s.
2. Ranked hypotheses: H1 interference from the other team's traffic on the shared fabric (strong
   prior: time correlation with their job, ≈ 10³× PFC pause increase in runs 2 and 4) → test: rerun
   ≥ 5 times with the fabric isolated (or in a reserved window) and record PFC/ECN counters per run.
   H2 a flapping or erroring link on one rail → test: per-port FEC/symbol-error and link-flap
   counters for runs 2 and 4 vs 1, 3, 5. H3 a straggling node (thermal throttling, CPU frequency) →
   test: per-rank timings / `nvidia-smi --query-gpu=clocks.sm,temperature.gpu --format=csv -l 1`
   during runs. H4 genuine 4-node scaling loss → test: compare isolated 2- and 4-node medians.
3. Corrected rows: keep runs 1, 3, 5 only as an *indicative* 4-node value, or better, mark the
   series invalid: "B-07 | all_reduce_perf busbw 8 GiB, 4 × 8 GPUs, shared fabric, contaminated
   (runs 2, 4 coincide with foreign traffic) | median 318.4 (min 194.4, max 329.6) | GB/s | MEASURED |
   L3 | manifests/l3-4node-shared.yaml" with a note that it is not used for design. No register
   change to A-06 until an isolated rerun exists; add a backlog item for it.
*Marking:* 3/4/3. *Common mistake:* deleting runs 2 and 4 silently (survivorship bias, Chapter 22).

## E. Design challenge D1

| Option | Leaves | Leaf ports used | Oversub | Spines (64-port) | Spine ports | Backend cables | Spine-crossing traffic |
|---|---|---|---|---|---|---|---|
| A: 1 leaf/rail, 48 down / 16 up | 8 | 64 / 64 | 3:1 | 4 (4 per leaf each) | 32 / 64 | 8 × 64 = 512 | Cross-rail only |
| B: 2 leaves/rail, 24 / 24 | 16 | 48 / 64 | 1:1 | 6 (4 per leaf each) | 64 / 64 | 16 × 48 = 768 | Cross-rail **and** same-rail between the two leaves |
| C: 1 × 128-port leaf/rail, 48 / 48 | 8 | 96 / 128 | 1:1 | 6 (8 per leaf each) | 64 / 64 | 8 × 96 = 768 | Cross-rail only |

Arithmetic: B uplinks 16 × 24 = 384 → 384 / 64 = 6 spines, 24 / 6 = 4 per spine per leaf, spine
ports 16 × 4 = 64. C uplinks 8 × 48 = 384 → 6 spines, 8 per spine per leaf, 8 × 8 = 64. A 51.2 Tb/s
ASIC at 400 Gb/s gives 51,200 / 400 = 128 ports, so C is feasible in principle; verify SKU and NIC
interoperability. Racks: 48 / 4 = 12; GPU-node power 48 × 10.2 = 489.6 kW max.

Recommended answer: **C** if a qualified 128-port leaf is available: rails stay single-hop for
W-TRAIN and cross-rail KV transfer gets 1:1. Otherwise **A** now (cheapest, 512 cables, no effect on
rail-aligned DP/PP) with an ADR revisit trigger such as "cross-rail bytes exceed 10 % of backend
bytes over a week, or KV-transfer p99 exceeds its budget"; B is the least attractive because it
pushes same-rail traffic onto spines and costs the most optics. Accept A or B with a sound argument
tied to the inference roadmap. *Marking:* arithmetic 10, ADR quality 6, recommendation logic 4.

## F. Reflection (guidance)

- **R1** Expect MFU (A-04) or checkpoint δ (A-08); cheapest test is a 64-GPU slice run or a
  single-node save timing at L2. Reward answers that state the decision that changes.
- **R2** Linter-blind errors: a consistent but wrong design (e.g. TP across nodes, lossless config
  that will cause pause storms, wrong workload model). Caught by layer reviewers with the checklist
  and the "what would make this fail?" question.
- **R3** Correlated failures: a bad firmware rollout affecting many NICs at once; rack power or
  cooling-loop events; infant mortality in a new batch. Clustered failures shorten effective M in
  bursts; a fixed interval tuned to the long-run average is too long during bursts, so adaptive
  intervals or burst-triggered checkpoints help.
- **R4** Hardware validation at L3 at target scale; facilities sign-off; vendor-spec re-verification
  dated; security review; acceptance tests passing on every node; an executed (not tabletop)
  failure exercise; on-call ownership and runbooks reviewed.

## G. Outline-mandated exercises

**M1.** Grade with [`capstones/RUBRIC.md`](../../../../capstones/RUBRIC.md) and the chosen brief. Pass
≥ 70/100 with no score below 50 % on technical correctness or measurement; distinction ≥ 90 with
reproducible evidence. Automatic deductions: any `[MEASURED]` physical claim from L1 (measurement
dimension capped at 50 %); linter gate FAIL without waivers.

**M2.** Full marks need: reviewers who are not authors; findings written *before* the meeting with
severities; contested findings discussed; explicit outcome; conditions with owners/dates; evidence
the bundle was updated (diff or changelog). Deduct for a review that is a presentation with no
recorded findings.

**M3.** Check that every slide claim carries its label, the failure-exercise report gives
TTD/TTM/TTR and lost GPU-hours with the correct tier label (tabletop values `[ILLUSTRATIVE]`), and
the backlog is ordered with stated criteria and a rationale reviewers could dispute.
