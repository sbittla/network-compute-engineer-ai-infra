# Capstone E — Instructor Grading Guide (INSTRUCTOR ONLY)

This folder is removed from student releases by `scripts/make_student_release.py`. It contains the
planted-fault list, expected results, rubric interpretation, common failure patterns and oral
review questions. The reference solution is [reference/fleet.py](reference/fleet.py); an abridged
distinction-level submission is in [EXEMPLAR.md](EXEMPLAR.md).

## 1. Verifying the kit

```bash
cd capstones/capstone-e-fleet-lifecycle-automation/starter-kit
python check.py --impl solution     # 17/17 PASS, exit 0, ≈ 2 s
python check.py                     # 1/17 PASS (dataset check only), 16 TODO, exit 1
python ../../../scripts/validate_labs.py capstone-e
```

## 2. Planted anomalies and why each is there

| # | Where | What is planted | What a correct solution does | What it teaches |
|---|---|---|---|---|
| P1 | `acceptance_results.json` `orion-n33` | 7 GPUs visible, Xid 79 during burn-in, DCGM diag fail | Fails `gpu_count`, `xid_events`, `dcgm_diag`; node → repair, later retired (RMA) | A GPU that "fell off the bus" is a hardware/seating/power fault; count the per-device list, not only the summary field |
| P2 | `orion-n34` | NIC3 negotiated PCIe x8 | Fails `nic_pcie_link` only | Downtrained links halve host↔NIC bandwidth silently (Chapter 5); every rail must be checked, not just the first |
| P3 | `orion-n35` | Rail 5 link at 200 Gb/s | Fails `nic_link_speed` only | A slow rail in a rail-optimized fabric throttles every collective that touches it (Chapters 10, 12) |
| P4 | `orion-n36` | 89 °C max GPU temperature in burn-in | Fails `thermal` only | Thermal faults (blanking panels, cold-plate contact, airflow) appear as clock throttling later, not as errors |
| P5 | `orion-n37` | All values pass but the test ran 9 days *before* this week's reimage (factory evidence) | Fails `evidence_freshness` only | Evidence must postdate the image it vouches for; "all green" from the wrong run is not proof |
| P6 | `orion-n38` | 1,423 correctable ECC on GPU 3; 0 uncorrectable; 0 pending remaps | **Passes** | Red herring: correctable ECC is trended and alerted, not an admission gate. Students who gate on it reject a healthy node; strong students propose a *trend* rule |
| P7 | `orion-n39` | Burn-in exactly 12.0 h (= minimum) | **Passes** (≥) | Boundary semantics; the checker raises the minimum to 12.5 h and expects a failure, proving thresholds come from the policy |
| P8 | `inventory.csv` `orion-n10` | GPU 5 VBIOS from the old bundle (spares pool part) | Acceptance passes, compatibility `non_compliant: heterogeneous_vbios`, `admit` rejected, node stays `validated` | Repairs re-introduce old firmware; acceptance ≠ compliance |
| P9 | `orion-n20` (drained), `orion-n30` (schedulable) | GPU driver 570 on the golden image without the matching RDMA stack — matches `BLK-0001` exactly | Both `blocked`; undrain of orion-n20 rejected; remediation drains orion-n30 *then* reimages; orion-n20 reimage only | Explains last week's mystery (GDR fallback). Reliable evidence of the fallback is NCCL channel lines without the `/GDRDMA` suffix (e.g. `via NET/IB/0` instead of `via NET/IB/0/GDRDMA`) plus `lsmod | grep nvidia_peermem` (remembering DMA-BUF can provide GPUDirect RDMA without it); the topology-distance log lines do not prove peer-memory support [VERIFIED_FACTS] and finds a second, silent instance on the inference rack. The "blocked" row is a real pattern: a known-bad combination recorded so drift detectors can name it |
| P10 | `orion-n40` | BIOS 2.0.1 (vendor shipped newer than validated) | `unknown` with reason `bios:2.0.1!=1.9.0`; acceptance passes; `admit` rejected | Unknown is not "probably fine": fail closed; the fix is a downgrade to the validated BIOS or validating a new bundle |
| P11 | `events.jsonl` | `ev-0028` delivered twice | Second copy recorded as `duplicate`, no state change | At-least-once queues; idempotency by event ID |
| P12 | `events.jsonl` | `ev-0034` (undrain orion-n13) delivered before `ev-0033` (drain) | Sorting by (utc, event_id) gives drain → undrain → schedulable. In file order: undrain = noop, then drain → node stranded in `drained` | Out-of-order delivery silently strands capacity |
| P13 | `events.jsonl` | `ev-0026` admit of a failed node by a human; `ev-0027` fault_confirmed on a node running jobs; `ev-0030` retire of an already-retired node; `ev-0031` drain of a drained node | Rejected; rejected; noop; noop | Guards stop humans as well as bots; noop vs reject distinction |
| P14 | `canary_metrics.csv` S2 | Training canary orion-n01 busbw 415 vs training baseline mean 452.85 GB/s (−8.4 %); inference canary orion-n25 452.0 vs inference baseline 455.45 (−0.8 %); a naive gate on the mean of all canaries vs all baselines sees −4.5 % | Abort naming orion-n01 | Averaging canaries hides the regression the canary exists to catch |
| P15 | S3 | Soak 10 h < 24 h, metrics fine | Extend | Time-dependent failures (thermal, memory, firmware timers) need the soak |
| P16 | S4 | Xid on orion-n05, throughput fine | Abort | Hard errors beat performance; a fast but erroring node is not promotable |
| P17 | `audit_log.jsonl` | Record seq 23 `actor` changed to `jdoe` without rehash | `audit_verify` returns 23 | Tamper evidence; also discuss that the chain alone cannot detect a full rewrite — needs an external anchor |

## 3. Expected numbers

| Item | Expected | Evidence class |
|---|---|---|
| Acceptance (10 nodes) | 5 pass (orion-n38, orion-n39, orion-n40, orion-n10, orion-n23); 5 fail (P1–P5) | SIMULATED |
| Compatibility (41 nodes) | golden 32, deprecated 5 (rack-07 + orion-lab-n01), blocked 2, non_compliant 1, unknown 1 | SIMULATED |
| Replay | 36 journal entries; 1 duplicate; 5 rejected (ev-0023, 0024, 0026, 0027, 0032); 2 noop (ev-0030, 0031); 3 admissions applied (orion-n38, orion-n39, orion-n23) | SIMULATED |
| Final fleet after replay | schedulable 31 (29 initial − orion-n07 + orion-n38 + orion-n39 + orion-n23; orion-n13 drained and returned, net 0); validated 2 (orion-n40, orion-n10); repair 5 (orion-n34..n36, orion-n37, orion-n07); drained 1 (orion-n20); retired 2 (orion-n33, orion-lab-n01). Journal outcomes: 28 applied, 5 rejected, 2 noop, 1 duplicate | SIMULATED |
| Rollout | 28 eligible (21 training + 7 inference; orion-n30 excluded as a pending drain). Headroom per wave: training 21 − 16 = 5, inference 7 − 6 = 1; overall cap ⌊0.25 × 28⌋ = 7. Minimum 7 waves (inference-bound: canary + 6). Reference plan sizes 2, 6, 6, 6, 6, 1, 1 with canary orion-n25 + orion-n01 and the deprecated rack-07 nodes in waves 0–3. Other plans with 7 waves that respect every limit are equally valid | MODELED |
| Rollout cost | 28 × 4 h × 8 GPU = 896 GPU-h planned unavailability | MODELED |
| Canary | S1 promote; S2 abort (orion-n01 −8.4 %); S3 extend; S4 abort (orion-n25 Xid). The planner's canary (orion-n25 + orion-n01) is exactly the pair in `canary_metrics.csv`: one training canary judged on step time, one inference canary judged on serving TPOT p95, each against baselines from its own partition | SIMULATED |
| Remediation | 7 actions: orion-n30 drain(1)+reimage(2); orion-n20 reimage(1); orion-n25..n28 schedule_upgrade | SIMULATED |
| Audit | first broken record seq 23 | SIMULATED |

Arithmetic for P14: training baseline mean = (452.4 + 453.3) / 2 = 452.85 GB/s; orion-n01
regression = (452.85 − 415.0) / 452.85 = 8.36 %; inference baseline mean = (457.1 + 453.8) / 2 =
455.45 GB/s; orion-n25 = (455.45 − 452.0) / 455.45 = 0.76 %. Naive gate: mean of canaries
(415.0 + 452.0) / 2 = 433.5 vs mean of all four baselines 454.15 → 4.55 % < 5 % threshold, so it
would promote.

Note on the final count: the replay final-state count is shown so you can sanity-check a student's
summary; a student who includes `orion-n30` as "schedulable" is correct about the *state* but
should flag it as non-compliant capacity (P9).

## 4. Rubric interpretation (100 points; see ../../RUBRIC.md)

| Dimension | Weight | 9–10 (excellent) | 7–8 (good) | 5–6 (weak) | < 5 |
|---|---|---|---|---|---|
| Problem framing and assumptions | 10 | Assumptions register with ≥ 10 testable entries incl. ORION variation, capacity floor, evidence freshness, queue semantics | Assumptions present but some untestable | Assumptions implicit | Missing |
| Architecture and technical correctness | 20 | Guard table + invariants + proof (graph argument) that INV-1/INV-2 hold; noop vs reject justified; P8–P10 explained in compatibility design | State machine correct, guards partly justified | Missing guards or allows repair → schedulable | Unsafe transitions |
| Implementation / reproducibility | 15 | 17/17; pure functions; extra tests (e.g. randomized event streams, property tests); one-command reproduction | 17/17 with little beyond | 12–16/17 | < 12 |
| Measurement and analysis | 20 | Every threshold derived from a physical ceiling with arithmetic; canary worst-case reasoning; rollout GPU-hour cost; results table fully labelled; correctable-ECC trend proposal | Thresholds justified qualitatively | Thresholds copied without rationale | Labels missing / modeled presented as measured |
| Reliability, security and operations | 15 | Abort + rollback rehearsed (L3) or tabletop with timings; audit anchoring; BMC/OOB, firmware signing, least privilege, two-person override; usable runbook | Most covered, runbook thin | Security generic | Absent |
| Troubleshooting and engineering judgment | 10 | Links P3/P9/P5 to downstream symptoms (collective slowdown, GDR fallback, unproven admission); names what the checker cannot catch | Explains faults, few downstream links | Lists faults only | — |
| Communication and portfolio quality | 10 | CAB-ready plan, captioned diagrams, numbered runbook with expected outputs | Clear but long | Hard to follow | — |

Pass ≥ 70 with ≥ 10/20 in both *Architecture and technical correctness* and *Measurement and
analysis*. Distinction ≥ 90 with reproducible evidence (one-command reproduction at minimum).

## 5. Common failure patterns (and how to mark them)

1. **Gating on correctable ECC (P6).** Rejects a healthy node. −2 in Measurement unless the student
   argues it explicitly with a rate-based threshold and a trend window.
2. **Counting GPUs from `gpu_count` only.** Passes T2 here (both fields agree on P1) but misses the
   general case; reward students who cross-check device lists against the topology inventory.
3. **Ignoring evidence freshness (P5).** The single most important design point; a submission that
   passes T2 only because it copied the check name without explaining *why* deserves probing in
   the oral review.
4. **Treating `admit` on an already-schedulable node as an error.** Breaks idempotency; retries
   then page on-call. Mark under Architecture.
5. **Averaging canaries (P14).** Fails T6; if a student "fixes" it by lowering the threshold to 4 %
   rather than gating per node, mark down under Measurement.
6. **Remediation that reimages a schedulable node without draining.** Fails T7; in production this
   kills jobs. Severity equivalent to an unsafe change: cap Reliability at 6.
7. **Audit chain "verified" by recomputing hashes but not prev_hash links.** Misses deletions; the
   checker's deletion test catches it.
8. **No external anchor.** The chain proves internal consistency only; an admin can rewrite the
   whole file. Expect the threat-model table to say so.
9. **A single fleet-wide capacity floor.** Counting inference nodes (or a node about to be drained)
   toward the training floor overstates headroom; floors must be per partition and exclude pending
   drains. The checker enforces this and the minimum wave count.
10. **Thresholds without arithmetic.** "370 Gb/s seems reasonable" is not a derivation.

## 6. Oral review questions (pick three)

1. A node passes acceptance, is admitted, and two days later NCCL all-reduce on its job is 30 %
   slower. Which acceptance test should have caught it, and which runtime signal will now?
2. Why is `drain` on a drained node a no-op but `fault_confirmed` on a schedulable node a
   rejection? What would break in each case if you swapped the behaviours?
3. Your controller crashes after writing the audit record for `admit` but before calling
   `scontrol update ... State=RESUME`. What state is the node in, and how does the controller
   converge on restart?
4. Security says the audit log is tamper-evident. A platform admin with root on the controller
   host disagrees. Who is right, and what do you change?
5. The vendor ships 40 more nodes with BIOS 2.0.1 next month. Walk through validating a new bundle
   instead of downgrading 40 BIOSes.
6. How long should burn-in be? Defend 12 h against a manager who wants 2 h, using GPU-hours and the
   cost of a failed 256-GPU job (Chapter 14 checkpoint interval, Chapter 21 economics).
