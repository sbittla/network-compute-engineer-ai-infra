# Capstone E — Abridged Exemplar of a Distinction-Level Submission (INSTRUCTOR ONLY)

> This is an *abridged* model answer showing the shape, depth and evidence discipline of a 90+
> submission. It is written in the learner's voice. All results are from the L1 starter kit and are
> `[SIMULATED]` unless labelled otherwise; thresholds are `[ILLUSTRATIVE]` because no calibration
> hardware was available. Score it against the rubric as ≈ 93/100 (see the closing note).

---

## 1. Problem statement

Halcyon's Fleet team needs a lifecycle controller for ORION that admits a node to production only
on fresh, policy-versioned evidence and a golden software bundle; stages bundle changes as canary
plus capacity-bounded waves with an automatic abort; and writes every decision to a tamper-evident
log. Success means: zero admissions that bypass validation; every planted fault caught with a
machine-readable reason; no wave below the per-partition floors (training ≥ 16, inference ≥ 6); canary gated on the worst node;
the tampered audit record located. Scope is L1: this is a design plus a verified decision core,
not a deployed service.

## 2. Architecture (summary)

Producers (provisioner, acceptance runner, health controller, humans via tickets) publish events
to an at-least-once queue. A single lifecycle controller consumes them, evaluates guards against
the acceptance verdict and the compatibility matrix, **appends to the audit log first**, and only
then calls the scheduler (`scontrol update … State=DRAIN|RESUME`, `kubectl cordon|uncordon`). On
restart, the controller reconciles scheduler state against the last audited state (audit log is
the source of truth for intent; the scheduler is the actuator). Figure 1 in my repository is the
brief's Figure E.1 with one addition: a read-only "drift detector" cron that runs
`check_compatibility()` over the live inventory every 15 min and emits `drain` for blocked/unknown
stacks on schedulable nodes.

## 3. State machine and guards (excerpt)

| From | Event | To | Guard | Side effects |
|---|---|---|---|---|
| imaged | acceptance_complete | validated / repair | verdict exists and `started_utc > image_completed_utc`; branch on pass | store evidence SHA-256 in audit record |
| validated | admit | schedulable | acceptance passed **and** compat = golden | audit → `scontrol update State=RESUME` / `kubectl uncordon` |
| drained | undrain | schedulable | compat ∈ {golden, deprecated}; no open incident | audit → resume |
| drained | image_complete | imaged | — | revokes previous acceptance |
| schedulable | drain | drained | — | audit → drain; waits for job checkpoint boundary |

Safety argument (INV-1): removing `validated` from the transition graph leaves `schedulable`
unreachable from `discovered`, `imaged` and `repair` — verified by breadth-first search in
`check.py` and by my own property test that replays 10,000 random event streams (seeded) and
asserts that every `schedulable` entry in the journal is preceded, for that node, by an applied
`acceptance_complete → validated` after its most recent `image_complete`. INV-2 holds because
`schedulable` has a single outgoing event, `drain`.

Idempotency choice: an event whose only target equals the current state is a **noop**, not an
error. With at-least-once delivery, rejecting a re-delivered `drain` would page on-call for a
correct system; but `fault_confirmed` on a schedulable node is **rejected**, because accepting it
would move a node with running jobs to `repair` — the one transition that kills work.

## 4. Acceptance plan (excerpt with derivations)

| Test | Threshold | Derivation |
|---|---|---|
| RDMA write per rail (`ib_write_bw --report_gbits`) | ≥ 370 Gb/s | 400 Gb/s line rate × 0.925. Wire efficiency at a 4096 B RDMA path MTU is ≈ 98 % [MODELED: 4096 / (4096 + 58 B Ethernet/IPv4/UDP/BTH/ICRC headers + 4 B FCS + 20 B preamble and inter-frame gap) = 4096 / 4178 ≈ 0.980 → ≈ 392 Gb/s payload ceiling], so 370 Gb/s leaves ≈ 22 Gb/s (≈ 5.5 points) for host and NIC effects — calibrate on golden nodes |
| H2D copy per GPU | ≥ 45 GB/s | PCIe Gen5 x16 ≈ 63 GB/s per direction theoretical; achievable ≈ 50–55 GB/s [ILLUSTRATIVE, REFERENCE_CLUSTER]; 45 GB/s flags an x8 or Gen4 link (≈ 31 GB/s theoretical) with margin |
| NVLink device-to-device | ≥ 340 GB/s | 450 GB/s per direction × ≈ 0.76 |
| Burn-in | ≥ 12 h, 0 Xid, ≤ 85 °C | Cost 96 GPU-h per node; justified by the 256-GPU blast radius of one infant-mortality failure: a W-TRAIN restart loses on average half a checkpoint interval × 256 GPUs (30 min interval → 0.25 h × 256 = 64 GPU-h) plus restart time, *per failure*, and early-life failures cluster in the first hours of load |
| Correctable ECC | not gating | Trend rule proposed: alert if a GPU's correctable count rises by > 1,000 in 24 h or any row remap is pending; orion-n38 (1,423 on GPU 3) admitted with a watch ticket |

## 5. Results

| # | Result | Value | Class |
|---|---|---|---|
| 1 | Checker | 17/17 PASS | SIMULATED |
| 2 | Acceptance | 5 pass, 5 fail: orion-n33 (gpu_count, xid 79, dcgm_diag), orion-n34 (NIC3 x8), orion-n35 (rail 5 at 200G), orion-n36 (89 °C), orion-n37 (stale evidence) | SIMULATED |
| 3 | Compatibility | 32 golden, 5 deprecated, 2 blocked (orion-n20, orion-n30), 1 non-compliant (orion-n10 mixed VBIOS), 1 unknown (orion-n40 BIOS 2.0.1) | SIMULATED |
| 4 | Replay | 3 admitted; 5 rejected; 2 noop; 1 duplicate; orion-n13 back to schedulable | SIMULATED |
| 5 | Rollout | 28 eligible; headroom 5 training / 1 inference per wave (orion-n30 counted as drained); 7 waves, the minimum; rack-07 expiring bundle first | MODELED |
| 6 | Rollout cost | 28 × 4 h × 8 = 896 GPU-h | MODELED |
| 7 | Canary | Canary = orion-n01 (training, judged on step time) + orion-n25 (inference, judged on serving TPOT p95), each against same-partition baselines. S1 promote; S2 abort (orion-n01 busbw −8.4 % vs 452.85 GB/s; a gate on the mean of all canaries would have promoted at −4.5 %); S3 extend (10 h < 24 h); S4 abort (Xid on orion-n25) | SIMULATED |
| 8 | Audit | first broken record seq 23 (`actor` edited to `jdoe`; recomputed hash ≠ stored) | SIMULATED |

## 6. Failure analysis (excerpt)

- **orion-n30 (blocked stack, schedulable on the inference rack).** Explains last week's orion-n20
  investigation: driver 570 on the golden image without the matching RDMA stack prevents GPUDirect
  RDMA registration, so NCCL stages through host memory. On orion-n30 the symptom would be higher
  KV-transfer and TP all-reduce latency under load — invisible in health checks, visible as TPOT
  creep. Remediation: drain (inference keeps 7 of 8 nodes, above its floor of 6), reimage to
  B-2026.07, short-form acceptance, admit.
- **orion-n37 (stale evidence).** Without the freshness guard this node would have been admitted on a
  factory run that predates our image; any defect introduced in transit (unseated GPU, damaged
  optic) would be first detected by a production job.
- **Controller failure modes.** (a) Crash between audit append and scheduler call → on restart the
  controller replays the audit tail and re-issues idempotent scheduler calls. (b) Two controllers
  (split brain) → leader election with a lease; audit `seq` uniqueness rejects the second writer.
  (c) Clock skew between producers → events carry producer timestamps, but ordering uses the
  queue's offset when timestamps tie within 2 s; skew > 2 s alerts.

## 7. Security considerations (excerpt)

BMC/Redfish on the isolated OOB network (172.16.0.0/16) with per-node credentials from the secret
store and a read-only account for inventory; firmware images accepted only with vendor signatures
and recorded SHA-256 in the bundle row; the controller's service identity may drain/resume nodes
but cannot edit the matrix; moving a bundle to `golden` or overriding `blocked` requires two
approvers; audit head hash published hourly to a write-once bucket owned by Security, so a root
user on the controller cannot rewrite history undetected.

## 8. Final engineering review

Ship: state machine, acceptance gate, compatibility checks, audit chain with anchoring. Do not
ship yet: automatic rollback of BMC firmware (untested downgrade path). Residual risks: (1)
thresholds are ILLUSTRATIVE until calibrated on ≥ 2 golden nodes × 5 runs — owner Fleet; (2) no
runtime detector for a link that flaps *after* admission — owner Fabric (Chapter 10 counters);
(3) the per-partition floors are negotiated values that must be revisited when the expansion nodes join training — owner Platform. Backlog: calibrate thresholds; add
correctable-ECC trend alert; L3 Ironic integration; per-rail NCCL test in short-form acceptance.

---

**Instructor note.** This exemplar earns distinction because every threshold has arithmetic, the
noop/reject decision is argued from queue semantics, the canary analysis contrasts worst-case and
mean gating with numbers, and security includes an external anchor. It loses points for having no
L2/L3 evidence (Measurement capped near 18/20) and for an assumptions register that is not shown
here in full.
