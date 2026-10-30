# Capstone A — Instructor Grading Guide

INSTRUCTOR ONLY. Removed from the student edition by `scripts/make_student_release.py`.

Use with the [capstone rubric](../../RUBRIC.md) and its grader worksheet. This guide gives the
Capstone A-specific evidence for each dimension, the planted issues in the dataset, the numbers the
reference model produces, and the failure patterns we see most often.

## 1. Reference numbers (all `[MODELED]` from `[ILLUSTRATIVE]` inputs)

Run `python check.py --impl solution` in `starter-kit/` to reproduce them.

| Quantity | Option A (rail 1:1) | Option B (ToR 2:1) |
|---|---|---|
| Leaves / spines / switches | 8 / 4 / 12 | 8 / 2 / 10 |
| Host links / leaf–spine links | 256 / 256 | 256 / 128 |
| Uplinks per leaf per spine | 8 | 8 |
| Host links by medium | 224 MM (7–10 m) + 32 SM (70 m, rack-08) | 256 DAC (2 m, in-rack) |
| Fabric links by medium | 128 DAC (in network rack) + 128 MM (7 m) | 112 MM + 16 SM (rack-08) |
| Transceivers | 768 | 256 |
| GPU rack max / sustained | 40.8 / 34.0 kW | 41.944 / 35.144 kW (adds ToR leaf + 16 optics) |
| Network rack max (each) | 8.336 kW | 1.592 kW |
| 2N violations (max / sustained) | rack-05 / none | rack-05 / rack-05 |
| N+1 cooling violations | row D (40.8 kW vs 30 kW usable) | row D (41.976 kW vs 30 kW) |
| Total IT max / sustained | 364.5 / 310.1 kW | 360.2 / 305.8 kW |
| BOM total | $12,616,976 | $12,077,152 |
| $/hour (4-year straight-line + energy at PUE 1.3, $0.10/kWh) | $400.39 | $384.42 |

Option C: 6 leaves (ceil(256/48)), 2 spines, 3:1, with three design-rule warnings. The 256 host links do
not divide evenly into 48-port leaves, 6 leaves cannot carry 8 rails one-to-one, and 48 downlinks do
not map whole rails. A learner who prices option C without rejecting it on design rules has missed
the point.

Communication model (W-TRAIN, compute time 17.394 s at 40 % MFU):

| Scenario | Bytes per GPU per step | Option A (any layout) step | Option B best layout | Option B, launcher hostfile |
|---|---|---|---|---|
| baseline_3d (TP8 PP4 DP8) | DP 7.656 GB; PP 1.074 GB per boundary per direction | 17.516 s (exposed max(0, 0.191 − 0.07) = 0.121 s), contention 1.0 | 17.516 s (dp_contiguous, sorted: DP 1.0, PP 2.0; PP hidden in 1F1B) | 17.707 s (DP 2.0: exposed 0.313 s) |
| fsdp_dp32 (TP8 DP32, ZeRO-3) | 50.86 GB | 17.776 s | 17.776 s (sorted: 1.0) | 18.157 s (DP 2.0) |

$/M training tokens: A baseline $0.4645; B baseline $0.4459–0.4508; A FSDP $0.4714; B FSDP $0.4526 (best)
to $0.4623 (hostfile). Break-even effective contention for B FSDP against A: **2.94**.

**Modeling choice, PP exposure (`[ILLUSTRATIVE]`, deliberate per capstone):** A's model treats 1F1B
pipeline send/recv as fully hidden (exposure 0), while Capstone C's generator exposes 50 % of it. A's
choice makes the PP-contention leg of planted issue P7 cost-free in step time. Credit learners who
notice this and bound it (e.g., 1.07 GB / 40 GB/s × contention × 50 % ≈ 0.03–0.05 s on option B).

## 2. Planted issues and why they are there

| # | Planted issue | Where | What a strong submission does | Teaches |
|---|---|---|---|---|
| P1 | Vendor quote C looks cheapest but breaks rail alignment | `design_inputs.yaml` option C | Rejects on design rules before cost, explains rail/leaf mapping | Design rules first, price second (Ch 7) |
| P2 | rack-08 is in an overflow position: 50.8 m routed, 55.9 m with 10 % slack → 70 m stock | `floorplan.csv` D10 | Notices that every rack-08 link needs SM optics (70 m stock > the 50 m MM site policy, which is `[ILLUSTRATIVE]`; OM4 module reach is ≈ 70–100 m), adds SM spares as a separate SKU, and flags rack-08 as an operational outlier | Reach budgets and cable plans (Ch 10) |
| P3 | Position A07 (rack rack-05) has 63 A feeds | `facility.yaml` | Computes 34.42 kW usable per feed, finds 2N violated at 40.8 kW max, proposes re-feed and an interim plan, and quantifies a power cap (≈ 500 W per GPU to reach 8.6 kW per node) together with its straggler risk | 2N means one feed carries the rack; derates (Ch 2, 21) |
| P4 | Units trap: feeds are given as volts and amps, not kW | `facility.yaml` | Uses √3 × V × I × PF × derate. Learners who treat kVA as kW, forget √3, or forget the derate get the wrong pass/fail on rack-05 | Electrical arithmetic (Ch 2) |
| P5 | Row D has only 2 × 30 kW air units (N+1 usable 30 kW) | `facility.yaml` | Flags rack-08 cooling, proposes an added unit or rear-door heat exchanger, and states the interim risk if run at N | Cooling redundancy (Ch 21) |
| P6 | The launcher's hostfile is in inventory order, not rack order | `hostfile_job4471.txt` | Shows that option B's 2:1 is invisible with sorted dp-contiguous ranks and doubles DP time with the hostfile order, while option A is insensitive. Proposes topology-aware rank ordering (sorted hostfile, Slurm topology plugin) as a control | Oversubscription depends on placement (Ch 7, 12, 17) |
| P7 | The PP-versus-DP placement trade-off on option B | model | Notices that dp_contiguous makes DP local but PP cross-rack, and that pp_contiguous does the reverse; explains that DP bytes dominate | Joint placement (Ch 11, 13) |

The perfect-ECMP assumption (A-06 in the assumptions register) is not a planted bug, but it is the
assumption a distinction-level submission attacks. With 32 single-path flows hashed onto 16 uplinks,
the expected maximum uplink load is about 5 flows (Monte Carlo, see EXEMPLAR §4). That is above the
2.94 break-even and reverses the cost/performance ranking for FSDP on option B.

## 3. Dimension-by-dimension expectations

| Dimension | Exemplary (90–100 % of weight) | Proficient (70–89 %) | Developing (50–69 %) | Insufficient (< 50 %) |
|---|---|---|---|---|
| Problem framing (10) | Testable success criteria; register ranked by sensitivity; top 3 have validation plans | Register complete; sensitivity informal | Assumptions listed, not quantified | Assumptions implicit |
| Architecture and correctness (20) | All counts, media, power and cooling correct; option C rejected on design rules; data paths GPU→spine drawn | Minor count or labelling slips; analysis correct | One planted issue (P2–P5) missed or a wrong 2N interpretation | Wrong topology arithmetic; facility issues missed |
| Implementation (15) | 16/16 checks; one command regenerates pack numbers; tests or notebook extend the model | 16/16; reproducible with some manual steps | 12–15 checks | < 12 checks or numbers not reproducible |
| Measurement and analysis (20) | Layout × option × scenario table, sensitivity with break-even, ECMP attack; modeled and measured kept apart | Table and sensitivity present; break-even missing | Single best-case comparison only | Modeled numbers presented as measured: cap this dimension at 40 % |
| Reliability, security, ops (15) | Blast radius per option, owned facility mitigations, staged acceptance with entry/exit, security section concrete | Most present, some owners missing | Generic FMEA | Absent |
| Judgment (10) | Recognizes scheduler dependence; states what changes the decision; no over-claiming | Sound recommendation, few caveats | Recommendation follows price only | No recommendation or contradicts evidence |
| Communication (10) | Five-minute memo; consistent figures; reviewer can reproduce in 30 minutes | Clear but long | Hard to follow; figures uncaptioned | Disorganized |

## 4. Common failure patterns

1. **Comparing two feeds against the rack for 2N.** Under 2N, either feed must carry the whole rack.
   Using 2 × 34.42 kW hides the rack-05 violation.
2. **Using sustained power for 2N and cooling sizing.** Breakers and cooling are sized for maximum (and
   transient) load. Sustained power is the right input for energy cost.
3. **Declaring option B "free" because sorted ranks show contention 1.0.** The real launcher order is in
   the dataset for a reason.
4. **Assuming the 2:1 penalty is 2× step time.** Only the exposed fraction of communication shows up in
   step time. With exposure = max(0, T_DP − 70 ms) the modeled penalty of option B with the launcher order is 1.1 % (baseline) to 2.1 % (FSDP), and it grows with collisions and with communication-heavy
   scenarios. Learners who overstate the penalty have the right instinct and the wrong arithmetic.
5. **Forgetting the switch-side optics in power.** Option A's network racks draw 8.3 kW, not 6 kW.
6. **Pricing optics per link instead of per end.** That halves the optics line.
7. **Acceptance plan without counts or pass criteria.** "Test all links" is not a plan. 512 links,
   768 optics and 256 rail-pair tests is.
8. **Measured/modeled confusion.** Any `[MEASURED]` label needs a manifest. Laptop runtimes of the model
   are not measurements of anything relevant.

## 5. Viva / presentation questions

1. A rail leaf fails in option A. What happens to the running W-TRAIN job, and what happens in option B
   when a ToR leaf fails? Which would you rather operate, and why? *Expected:* option A loses rail R on
   all 32 nodes, so no node is lost and shrinking DP does not help. The choices are to wait for repair,
   to restart on 7 rails by excluding `mlx5_R` (≈ 12.5 % less inter-node bandwidth, with PXN/cross-rail
   traffic through the spines), or to take the job down. Option B loses 4 nodes (one TP8 × PP4 replica),
   so a DP = 7 restart (−12.5 %, with a batch/LR adjustment) or waiting are the choices (runbook RB-1a/1b).
2. Your model says option B costs 0.4 % in step time with the launcher's order. Name two effects that
   would make the real penalty larger, and the measurement that would reveal each.
3. Why does option A's uplink traffic stay near zero for W-TRAIN? Which workload would change that?
4. Show the 2N arithmetic for rack-05. What power cap per GPU fits, and why might you still not want to run
   W-TRAIN on capped nodes?
5. How would you detect, during acceptance, that two rails were swapped at the patch panel on one node?
6. What is the single assumption you would spend the first week of hardware access validating?

## 6. Grading the extensions

- L2 evidence is credited in *Measurement and analysis* only with a manifest (template in
  `starter-kit/manifest.yaml`), at least five runs or a 30-minute power log, and stated spread.
- L3 oversubscription experiments must hold nodes, NCCL version and message sizes constant and change
  only the rank order. Without that, award no more than proficient.
