# Chapter 19 — Exercise Answer Key (INSTRUCTORS ONLY)

Canonical assumptions (Reference Cluster "Reliability assumptions", `[ILLUSTRATIVE]`): node MTBF ≈
1,536 node-hours; restart overhead R ≈ 15 min. All arithmetic checked twice.

## Knowledge checks

**K1.** MTBF_job = 1,536 h / N; interruptions/day = 24 / MTBF_job.

| Nodes | Job MTBF | Interruptions/day |
|---|---|---|
| 8 | 192 h | 0.125 |
| 32 | 48 h | 0.5 |
| 128 | 12 h | 2 |
| 512 | 3 h | 8 |

**K2.** (a) Pending: the remap is recorded but inactive until reset → drain when free (or exclude at
the next restart), reset, verify pending cleared, diagnostics, return. (b) Failure: no spare row → the
memory cannot be repaired → quarantine and RMA. (c) Remap applied, nothing pending → healthy; monitor
only (quarantining it wastes a good GPU). *Marking:* 2 pts each; common mistake: treating (c) as a fault.

**K3.** Xid 13 — usually application (illegal instruction/address); tell the user; investigate hardware
only if it recurs across different jobs/users on the same GPU. Xid 79 — hardware/PCIe/power: GPU fell off
the bus → drain, capture `nvidia-bug-report.sh`, cold reboot, diagnostics, likely RMA if repeated.
Xid 94 — contained ECC error: affected contexts killed, GPU continues → restart the job, drain the node
when convenient, then reset the GPU (Xid 95, uncontained, would mean drain immediately); check the row remapper. Must note that meanings are per NVIDIA's current Xid document.

**K4.** Correctable: fixed by the link (replay), counted only. Non-fatal uncorrectable: a transaction
lost, link usable; device driver must recover. Fatal: link unreliable; device reset/link retrain
needed. Gen5 x16 ≈ 63 GB/s per direction theoretical (≈ 50–55 GB/s achievable); x8 halves it to ≈ 31.5
GB/s theoretical (≈ 25–27 achievable) — below a 400 Gb/s (50 GB/s) NIC's line rate.

**K5.** Each rank's watchdog measures time since *its own* oldest incomplete collective; ranks block at
different points so their timers expire in arbitrary order 10 min after the fault. Localise with the
flight recorder (ranks behind — minimum completed sequence) and the transport errors at stall onset
(NET/IB status 12 endpoints).

**K6.** Fault domain = what failed (the `mlx5_3` link: HCA port, optics, cable). Scheduling unit =
what the scheduler can remove: the node, because a TP = 8 rail-optimized job needs all 8 rails. They
coincide for a job that uses only some GPUs/rails of a node (e.g. a 4-GPU inference replica on GPUs 4–7
can keep running), or when the fault domain is itself a node (PSU).

**K7.**

| | Memory isolation | Fault isolation | Performance isolation |
|---|---|---|---|
| Whole GPU | Full (one tenant) | Full | Full |
| MIG | Hardware-partitioned memory | Instance-level (most errors contained to the instance; some GPU-wide errors still affect all) | Dedicated SMs/memory bandwidth slices |
| Time-slicing | Separate address spaces, but no capacity limits (one client can exhaust GPU memory) | None (a fatal fault can take down co-resident clients) | None (contention for SMs and bandwidth) |

**K8.** Different VRFs/VNIs stop A and B addressing each other, but both tenants' traffic shares spine
links and switch buffers. B's incast or heavy collectives fill shared queues; ECN marks and PFC pauses
then slow A's flows (pause propagation, head-of-line blocking). Mitigations: place large tenants on
separate leaf groups / spine planes; separate QoS classes with buffer allocation; tenant-aware rate
limits; congestion-control tuning.

## Worked problems

**W1.**
(a) M = 48 h = 2,880 min. τ_opt = √(2 × 1 × 2,880) = 75.9 min. Overhead = 1/75.9 + (37.95 + 15)/2,880 =
0.0132 + 0.0184 = 0.0316 → goodput 96.8 %.
(b) M = 180 min, τ = 19. R = 15: 1/19 + (9.5 + 15)/180 = 0.0526 + 0.1361 = 0.1887 → 81.1 %. R = 5:
0.0526 + (9.5 + 5)/180 = 0.0526 + 0.0806 = 0.1332 → 86.7 %. (τ_opt in Young's model does not depend
on R.)
(c) Difference 0.0556 × 4,096 GPUs × 24 h = 5,461 GPU-h/day ≈ $16,400/day `[MODELED]`.
*Marking:* 3/4/3. Common mistake: using hours and minutes inconsistently.

**W2.**
(a) Per attempt 4.096 µs × 2²⁰ = 4.295 s; budget ≈ 8 × 4.295 = 34.4 s. All four flaps (≤ 14 s) survive.
(b) Real failures (dead peer, partition) are reported 34.4 − 8.6 = 25.8 s later: 25.8 s × 4,096 GPUs =
29.4 GPU-h per event — small next to the 10-min watchdog (683 GPU-h) — but every flap now stalls the
whole job for up to 14 s *and the flaky link stays in service*. Recommendation: a longer IB timeout is a
reasonable ride-through, **combined with** flap-rate quarantine (FMEA F03), since survival hides a
component that will eventually fail hard. Accept other well-argued positions.
(c) Failures/day = 512 × 24 / 1,536 = 8. Nodes in repair ~ Poisson(8 × MTTR). 3 days: mean 24, P99
quantile k = 36 (P(≤ 36) = 0.992) → 7.0 % of 512. 5 days (canonical): mean 40, k = 55 (P(≤ 55) = 0.990) →
10.7 %. The pool sits outside the partition, so it is extra capex; a mean-sized pool (24 or 40) would run
short roughly half the time. Common mistake: adding a flat margin instead of using the quantile.

## Hands-on lab — reference results and planted anomalies

| Output | Reference |
|---|---|
| Stuck ranks | 64 (local rank 5, orionxl-n193–n256, pp 3); leaves orionxl-be-leaf-p06-r5 / p07-r5 |
| Endpoint scores (job 900211) | orionxl-n212 mlx5_5 = 3, orionxl-n211 = 2, orionxl-n213 = 1 (same for 900198) |
| Bad ports | orionxl-be-leaf-p06-r5 Ethernet20/1: 4 link-downs, FEC +203,903, RX marginal −5.6 to −6.4 dBm (last −6.39); host TX −5.8 dBm |
| GPU actions | orionxl-n389/3 drain_reset_validate; orionxl-n046/6 monitor; orionxl-s00/2 quarantine_rma |
| Hypotheses | H1 proven_cause; H2 real_fault_not_cause; H3, H4, H5 correlation_only; H6 refuted |
| Checkpoint | ckpt-0084 (ckpt-0085 metadata uncommitted) |
| Attempt 2 metrics | RPO 31.03 min; RTO 49.97 min; 5,529.6 GPU-h |
| Attempt 1 metrics | RPO 12.73 min; RTO 39.43 min; 3,561.2 GPU-h |
| Retry policy | repeat offender orionxl-n212 → auto-restart blocked until excluded |
| Restart plan | orionxl-n212 → orionxl-s01 (ranks 1688–1695); orionxl-n389 → orionxl-s03 (ranks 3104–3111) |
| FMEA | top F03 (336); F07 DETECTION_INCONSISTENT (re-scored 200); F11 OUT_OF_RANGE; action set F03, F06, F07, F12 |
| Isolation | 10 violations (see check.py) |

**Planted anomalies (do not distribute):**
1. *First reporter* rank 817 (orionxl-n103) logs the earliest watchdog line — innocent.
2. *Real fault, not cause*: orionxl-n389 GPU3 Xid 63 / row remap pending at 02:58:41; its ranks completed
   88213. Must be reset before reuse, not blamed.
3. *Healthy distractor*: orionxl-n046 GPU6 has one correctable remapped row, nothing pending — monitor only.
4. *Background AER*: corrected Physical-Layer RxErr on orionxl-n451's NIC every ~40 min all night.
5. *Consequence*: orionxl-be-spine-p06-03 PFC spike at 03:41:20, after the link drop.
6. *Survived flaps*: the 6 s and 5 s flaps did not hang the job (below the 8.6 s retry budget) — teaches
   the mechanism; the 14 s flaps did.
7. *Repeat offender*: attempt 1 failed on the same link and was auto-restarted on the same nodes.
8. *Unsafe checkpoint*: ckpt-0085 logged as "complete" with 4,096/4,096 shards but metadata uncommitted.
9. *Spare pool (declared variation)*: the pool is 55 nodes (Poisson P99 at 5-day MTTR); 47 are already
   standing in for nodes in repair, so `spares.csv` lists the 8 still assigned. *Unhealthy spares*: orionxl-s00 failed acceptance (DBE, remap failure in gpu_health), orionxl-s02 in repair,
   orionxl-s05 reserved.
10. *FMEA data quality*: F07 detection 2 with control "none"; F11 occurrence 0 (out of range).
11. *Isolation*: cluster-admin binding for an acme service account; VNI 10020 shared (borealis, cobalt);
    P_Key 0x8001 shared (acme, cobalt); borealis exports parent path `/lustre/projects`; borealis no GPU
    scrub; borealis secrets prefix `kv/tenants/`; cobalt time-slices GPUs shared with borealis; cobalt
    audit retention 30 days.

**Marking (lab README Section 8):** award full "proven vs correlated" marks only when each verdict cites
timing, locality, and mechanism, and when H1 is described as proven *pending intervention* (restart
without orionxl-n212). Deduct for quarantining orionxl-be-leaf-p06-r5 or the whole rail (blast-radius error), for
restoring ckpt-0085, or for picking orionxl-s00.

## Troubleshooting case T1

| Hypothesis | Evidence | Verdict |
|---|---|---|
| orion-n10 HCA mlx5_2 PCIe link downtrained to x8 after reboot | `LnkSta … Width x8 (downgraded)` vs `LnkCap x16`; 3,400 corrected AER RxErr since boot; node NIC TX ≈ 7 % lower | Root cause |
| Compute straggler | SM active identical across nodes | Rejected |
| Fabric/optics | Switch ports clean, no link-downs, no out-of-sequence | Rejected |
| Congestion | CNP handling normal | Rejected |

Arithmetic: Gen5 x16 ≈ 63 GB/s/dir theoretical → x8 ≈ 31.5 GB/s (≈ 25–27 achievable), below the
400 Gb/s = 50 GB/s NIC line rate, so rail 2 from orion-n10 is capped at ≈ half rate; every rail-2
collective step waits on it. Why SM activity does not single it out: this is a *network* straggler —
orion-n10's GPUs wait on their own slow transfers just as peers wait on them, so all nodes show the same
reduced activity; the per-node NIC throughput and the PCIe link state are the discriminators (unlike a
compute straggler, which is *busier* than its peers). Containment: fault domain = mlx5_2's PCIe
slot/riser/card; unit = node orion-n10. Draining stops new placement but does not move the running
job: take (or use the latest) checkpoint and `scontrol requeue <jobid>`. ORION has no spare nodes, so the
16-node job needs a 16th node from elsewhere — a free training node, or an inference node (orion-n25–n32)
borrowed through a lifecycle transition (Chapter 17) — or it waits for the repair. Restart pays off when
remaining runtime × 128 GPUs × 0.09 exceeds the ≈ 64 GPU-h restart cost (15 min lost work + 15 min
restart), i.e. beyond ≈ 5.6 h of remaining runtime. Fix: reseat the
HCA/riser, inspect the connector, re-check `LnkSta`; replace riser/card if it trains at x8 again.
Validate: `LnkSta` x16, AER corrected count ≈ 0 over 1 h, rail-2 NCCL test at baseline, job step time
within 2 % of baseline. Action item: acceptance test (Chapter 16) must compare `LnkSta` to `LnkCap` on
every boot.

## Design challenge D1 — reference approach

Assumptions: 512-node job, M = 3 h, τ = 19 min, δ = 1 min; failures 8/day, MTTR 5 days → mean 40 nodes in
repair (Poisson); one DP replica = 8 nodes.

| Option | Goodput (Young) | Capacity factor | Useful per fleet node |
|---|---|---|---|
| A: P99 pool of 55 outside the partition, R = 15 min | 1/19 + (9.5 + 15)/180 = 0.189 → 0.811 | 512 / 567 = 0.903 | 0.811 × 0.903 = 0.732 |
| B, re-packed: ⌊472 / 8⌋ = 59 replicas, R = 5 min | 1/19 + (9.5 + 5)/180 = 0.133 → 0.867 | 59 / 64 = 0.922 | 0.799 |
| B, not re-packed, expected: 64 × (1 − C(504,40)/C(512,40)) ≈ 30.8 replicas lost | 0.867 | 33.2 / 64 = 0.519 | 0.450 |
| B, not re-packed, worst: 40 distinct replicas lost | 0.867 | 24 / 64 = 0.375 | 0.325 |

Divisibility: DP = 59 is prime, so a global batch sized for 64 replicas cannot be split evenly; the job
must change micro-batches or accumulation steps (changing the effective batch, hence the LR schedule) or
run at the largest DP that divides the batch (e.g. 56 or 48), losing more replicas. Recommendation: B is
only better *with* topology-aligned re-packing and a validated batch/LR policy for changing DP; otherwise
A, or a hybrid (a smaller P90 pool of ≈ 48 for fast fixed-size restarts plus elastic fallback when it runs
dry). *Marking:* model 4, numbers 3, divisibility and recommendation 3.

## Reflection — guidance

- **R1:** "H1 is the cause" needs the intervention: the job running ≥ 2 × MTBF without rail-5 hangs after
  excluding orionxl-n212, and the link clean after the optic swap in a soak test.
- **R2:** A 15 s skew could place orionxl-n212's link-down *after* the NET/IB errors, breaking precedence;
  switch syslog (independent clock) and the 8.6 s mechanism would be needed to re-establish order.
- **R3:** It drains healthy nodes (capacity loss, spare exhaustion), and it can mask software bugs
  (collective mismatch) by "fixing" them with hardware churn; also floods repair queues.
- **R4:** The cluster-admin binding (A) or the parent-path export (B) — both allow cross-tenant data
  access; cluster-admin is broader (all secrets, all nodes). Accept either with reasoning.

## Outline-mandated exercises

- **M1:** Expect ≥ 12 rows across node, rack, leaf, storage, scheduler, control plane; corrected
  detection scores; severity ≥ 9 actioned regardless of RPN. Use Table 19.2 and `data/fmea.csv` as a
  model; deduct for detection scores inconsistent with controls.
- **M2:** Model: Table 19.7 plus a policy YAML in the lab's format; the learner's own tenant config must
  pass `check_isolation()` with zero violations.
- **M3:** Model: Section 19.10 table, with at least: repeated job crash of tenant A (scheduler/storage
  load), disabled backend port in A's allocation, A's storage quota exhaustion; abort criteria on
  non-target SLO burn; execution only on a dedicated partition. The tabletop report must list, per
  injection, expected vs walked-through behaviour, the gap (e.g. "no per-tenant rate limit on job
  restarts"), owner, and follow-up; deduct 3 points if absent.
- **M4:** Lab results above plus a Chapter 18-style postmortem whose action items include flap-rate
  quarantine, retry-policy gate, metadata-commit validation in checkpoint selection, and early hang
  detection.
