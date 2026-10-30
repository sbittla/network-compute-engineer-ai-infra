# Chapter 24 — Answer Key (instructor only)

Every number below was computed twice (by hand and by `solutions/lab/career_lab.py` where applicable).
Numbers are `[MODELED]` unless stated. Marking guidance is per exercise; "common mistakes" lists what
to look for when deducting.

---

## A. Knowledge checks

**K1 — Roles by what they are paged for.** Model answer (any well-justified variant earns full marks):

| Role | Typical page / owned investigation | First evidence |
|---|---|---|
| AI Network Engineer | All-reduce bandwidth drop on one rail; PFC storm | Switch port counters (FEC, CRC, PFC pauses per priority, ECN marks); `ethtool -S` on hosts |
| GPU Compute / HPC | NCCL hang or Xid error | `dmesg` / kernel log for Xid; `nvidia-smi -q`; NCCL debug logs (`NCCL_DEBUG=INFO`) |
| Cluster / Platform | Jobs pending with free GPUs | `squeue` reason codes / `scontrol show job`, or `kubectl describe pod` events; node health state |
| AI Performance | Regression investigation (owned, rarely paged) | Baseline vs current step-time distribution with manifests |
| SRE / Operations | Any SLO burn alert first | Dashboard for the SLO, change log for the window, blast radius |
| Network Hardware / Vendor | Customer escalation on buffer drops or optics | Customer's counters + switch OS/firmware versions; reproduction in a lab |

*Marking (8 pts):* 1 pt per row with a plausible incident and real evidence source; 2 pts for evidence
that is specific (a named command or counter class), not "check logs".
*Common mistakes:* inventing command flags; giving the performance engineer an on-call page it would
not normally own without saying so.

**K2 — Evidence caps.** A course shows exposure to vocabulary (level 1: "aware"); it contains no
artifact of the learner doing anything. A Level-1 lab shows the learner can reproduce reasoning on
supplied data with guidance from the lab spec (level 2). Level 3 needs evidence of *independent*
design or diagnosis — an open-ended capstone, a hardware-backed lab with a manifest, or a published
case study — where the learner framed the problem and defended choices. Level 4 needs evidence of
*production ownership* verified by someone else, because only production exposes the learner to real
failure, scale and accountability.
*Marking (6 pts):* 2 per boundary (1→2, 2→3, 3→4) naming the behavioural change.
*Common mistakes:* equating level with years; treating a certification as level 3.

**K3 — Senior vs staff.** Senior: leads the third incident, proves the cause with a discriminating test,
writes the postmortem identifying the detection gap; outcomes — incident resolved within SLO, alert on
FEC-uncorrectable rate shipped for that fabric. Staff: recognises the pattern across incidents, writes
the proposal for pre-failure optics telemetry and a drain-on-threshold policy, gets Fabric and Fleet to
adopt it across both fabrics; outcomes — policy adopted by two teams, optics-related degradations
detected before job impact (measured as a reduction in job-impacting optics incidents next quarter).
*Marking (6 pts):* 3 per level; outcomes must be verifiable.
*Common mistakes:* describing staff as "a faster senior"; outcomes phrased as activities ("worked on").

**K4 — The register.** Fields: employer, exact title, job ID, location, seniority, URL, date checked,
required skills, preferred skills, active/archived status. Example pairs: job ID + employer → prevents
counting cross-listed postings multiple times; date checked → prevents describing a closed market as
current; required vs preferred skills → prevents overstating the hiring bar; URL (canonicalised) →
catches re-posts under new IDs; seniority vocabulary → keeps level breakdowns valid.
*Marking (5 pts):* 2 for the complete list; 1 per correct pair.
*Common mistakes:* omitting `date checked` or `status`; conflating required and preferred skills.

**K5 — TP inside the node.** Per TP all-reduce: activation 4,096 × 8,192 × 2 B = 67.1 MB; ring over 8
GPUs sends 2 × (8 − 1)/8 × 67.1 MB = 117 MB per GPU. Per step per GPU: 117 MB × 4 all-reduces per layer
× 20 layers per stage × 128 micro-batches = 1.20 TB `[MODELED]`. Over NVLink at 360 GB/s: 1.20 TB /
360 GB/s ≈ 3.3 s; over a NIC at 40 GB/s: ≈ 30 s, longer than the 17.4 s step.
*Marking (5 pts):* 2 for the volume with arithmetic; 1 each for both times; 1 for the conclusion.
*Common mistakes:* using 450 GB/s and 50 GB/s without stating they are line rates; forgetting the
128 micro-batches; using 2× rather than 2(n − 1)/n.

**K6 — Where the bytes go.** On ORION-256, each rail has one leaf with 32 host ports, so all 32 nodes'
NIC *r* attach to the same leaf; DP and PP peers are the same local rank on different nodes, so their
traffic is leaf-local. In the 1,024-GPU fabric each rail has 128 NICs across 4 leaves (32-node blocks);
DP groups spanning blocks cross the spine layer.
*Marking (4 pts):* 2 per case, including leaves per rail (1 vs 4).
*Common mistakes:* forgetting that this depends on rail-aligned rank mapping (deduct 1).

**K7 — Discriminating tests.** A discriminating test is one whose outcome is predicted differently by
the competing hypotheses, so that its result eliminates at least one. In Section 24.12, per-port
counters/optic Rx power on the rail-3 links separate the two: FEC/CRC errors and low Rx power isolated
to one port point to physical degradation; PFC pauses and ECN/CNP increases across many rail-3 ports
with clean FEC/CRC would have pointed to congestion. (The `ib_write_bw` per-rail test localises the rail
but does not, by itself, distinguish the two.)
*Marking (4 pts):* 1 definition, 1 test, 2 for both outcomes.
*Common mistakes:* choosing a test that both hypotheses predict the same way (e.g., "re-run
all_reduce_perf").

**K8 — Representative, not current.** Hiring is time-sensitive; naming organisations without the
qualification turns a curriculum synthesis into an implied factual claim about current openings that
the book has not verified. A reader could target an employer believing a role exists, or cite the table
as market evidence.
*Marking (3 pts).*

---

## B. Worked problems

### WP1 — Readiness for AI Infrastructure SRE / Operations (mid)

| Competency | w | d | t (mid) | min(d,t)/t | w × fraction |
|---|---|---|---|---|---|
| observability | 3 | 1 | 3 | 0.333 | 1.000 |
| reliability_security | 3 | 2 | 2 | 1.000 | 3.000 |
| automation | 2 | 3 | 2 | 1.000 | 2.000 |
| scheduling | 2 | 1 | 2 | 0.500 | 1.000 |
| storage_ckpt | 1 | 1 | 2 | 0.500 | 0.500 |
| linux_host | 2 | 2 | 2 | 1.000 | 2.000 |
| communication | 2 | 3 | 2 | 1.000 | 2.000 |
| **Σ** | **15** | | | | **11.500** |

(a) Readiness = 100 × 11.5 / 15 = **76.7 %**.
(b) **near**: ≥ 70 but < 85, and the observability gap is 2 (blocks "ready" regardless of score).
(c) Gap plan by priority = w × gap: observability (3 × 2 = **6**), scheduling (2 × 1 = **2**),
storage_ckpt (1 × 1 = **1**).
(d) Observability → 3 adds 3 × (1 − 0.333) = 2.0 → 13.5 / 15 = **90.0 %**; max gap now 1 →
**ready** (≥ 85 and no gap > 1).
*Marking (10 pts):* table 4, score 2, status with reason 1, ordered plan 2, part (d) 1.
*Common mistakes:* using the senior targets; letting automation's d = 3 exceed its target (must cap
at 1.0); calling 76.7 "ready".

### WP2 — A 512-GPU variant

(a) 64 nodes → 64 NICs per rail → 64 / 32 = **2 leaves per rail**; 8 rails × 2 = **16 leaves**;
uplinks 16 × 32 = 512 → 512 / 64 = **8 spines**; 32 uplinks / 8 spines = **4 links per leaf–spine
pair**; host links 512 + fabric links 512 = **1,024 links** (2,048 ports); 24 switches.

(b) P(a given uplink receives none of F flows) = (31/32)^F.
- F = 32: (31/32)^32 = e^(32 × ln 0.96875) = e^(32 × −0.031749) = e^(−1.01596) = 0.3621 → idle uplinks
  = 32 × 0.3621 = **11.6** (36 % of capacity).
- F = 128 (4 QPs per connection): (31/32)^128 = 0.3621^4 = 0.01719 → idle uplinks = 32 × 0.01719 =
  **0.55**.
More flows spread load far better, though the per-uplink load is still uneven (mean 4 flows of
quarter size; some uplinks get 7–8), so the collective is still paced by the most loaded uplink.

(c) M = 768 node-hours / 32 nodes = 24 h = 86,400 s.
τ = √(2 × 12.25 s × 86,400 s) = √2,116,800 s² = **1,455 s ≈ 24.3 min**.
Checkpoint overhead 12.25 / 1,455 = 0.84 %; expected rework (τ/2)/M = 727.5 / 86,400 = 0.84 %; restart
900 / 86,400 = 1.04 %; total ≈ **2.7 %** (versus ≈ 1.7 % at the canonical 48 h: 0.60 + 0.60 + 0.52 %).
Note τ shrinks only by √2 (2,058 s → 1,455 s) while the restart term doubles.
*Marking (12 pts):* (a) 4, (b) 4, (c) 4. Full arithmetic required for credit.
*Common mistakes:* forgetting that the two-tier non-blocking leaf has 32 uplinks, not 64; computing
idle *flows* instead of idle uplinks; using node MTBF instead of job MTBF in Young's formula.

---

## C. Lab answer key

`python lab/check.py --impl solution` → 11/11 PASS. The reference report (`solutions/lab/career_lab.py`)
prints AI Network Engineer readiness 100.0 / 94.1 / 78.4 / 69.6 (junior → staff) and the register
summary "rows: 61; unique postings: 51; complete: 40; active and fresh: 31".

### Planted flaws — learner evidence (`learner_evidence.yaml`)

| Item | Flaw | Rule triggered | Effect |
|---|---|---|---|
| E02 | Course claimed at level 2 | type cap (course = 1) | 1; irrelevant because E01 = 4 |
| E03 | Level-1 lab claimed at 3 | type cap (lab_l1 = 2) | 2; E04 sets RDMA to 3 |
| E05 | Lab report says results were "measured" though it is an L1 simulation | SIMULATION_CLAIMED_AS_MEASURED | capped at 1 — integrity issue |
| E06 | Case study from 2022 | STALE (> 1,095 days) | 3 → 2; congestion = 2 |
| E07 | Production claim, no verifier, from 2021 | PRODUCTION_UNVERIFIED + STALE | 4 → 3 → 2 |
| E09 | Self-assessment at 3 | type cap (self = 1) | 1 |
| E10 | Case study with no artifact ("not yet published") | NO_ARTIFACT | capped at 1; observability = 1 |
| E04 (second copy, position 12) | Same evidence listed twice | DUPLICATE_EVIDENCE | counted once |
| E14 | Competency `bgp_evpn` is not in the catalog | UNKNOWN_COMPETENCY | ignored (learner should map it to `l3_fabric`) |
| E17 | Production evidence from Feb 2023 | STALE (1,352 days) | 3 → 2; Linux host = 2 |
| E19 | Self-assessment with no date | NO_DATE (treated stale) | 1 → 0; GPU compute = 0 |

Explanation marks (10 pts in the lab rubric): the learner must say *why* each rule exists — e.g., stale
evidence describes a previous technology generation; unverifiable production claims are the most
common inflation in interviews; simulation-as-measurement is an integrity failure.

### Planted flaws — job register (`job_register.csv`, 0-based data-row indices)

| Rows | Planted problem | Detected as |
|---|---|---|
| 2 / 26, 5 / 29, 14 / 40 | Exact duplicate rows | DUPLICATE_OF (lowest index kept; dates tie) |
| 3 / 27 | Employer upper-cased with padding, job ID lower-cased, re-checked one day later | Same key → cluster; row 27 kept (newer date) |
| 28 / 36 | Trailing whitespace in employer/title | Same key → cluster; 28 kept (tie) |
| 54 / 55 | Re-post with new ID `…-R`; URL has `/?utm_source=jobboard` | Canonical URL match; 54 kept |
| 15 / 42 | Re-post with new ID `…-R2`; URL host in mixed case | Canonical URL match; **15 (the re-post) kept** because dates tie and it has the lower index |
| 1 / 31 / 35 | Chain: 31 shares 35's key but has a new URL; 1 shares 31's URL but has a new ID | Transitive cluster; 35 kept (latest date) |
| 37 / 59 | Copy with job ID blank, same URL | URL match; also MISSING_FIELD:job_id |
| 58 | New posting with blank job ID | MISSING_FIELD:job_id (not a duplicate) |
| 6, 16, 51, 17, 34 | Blank date, URL, required skills, seniority, location | MISSING_FIELD:* |
| 50 | `15/09/2026` | BAD_DATE |
| 44 | `2026-11-20` (after as-of 2026-10-15) | FUTURE_DATE |
| 56 | `http://` URL | BAD_URL |
| 9 | Seniority `Sr.` | BAD_SENIORITY |
| 49 | Status `open` | BAD_STATUS |
| 13, 25, 48 | Active but last checked 2026-06-01 (136 days) | STALE_ACTIVE |
| 39 | Archived, checked 2026-05-01 | **Not** flagged — staleness only matters for "active" claims |

Totals: 10 duplicate rows, 51 postings, 11 representatives with blocking issues → 40 complete; of those
6 archived and 3 stale → **31 active and fresh**. Top required skills over those 31: python 27,
kubernetes 12, inference serving 7, nccl 7, traffic generators 7.

Discussion points for the rows 15/42 case: the tie-break keeps the re-post's ID. A production tool
should keep all IDs in the cluster as aliases, prefer the earliest-seen ID as canonical, and keep the
latest `date_checked`. Row 27's upper-case employer shows that the representative's *display* fields
should also be normalised. Learners who notice either earn the full "explanation" marks.

---

## D. Troubleshooting case T1

| Hypothesis | Information value | Cost | Risk | Test |
|---|---|---|---|---|
| H1 Thermal slowdown of GPU 5 on `orion-n22` (airflow problem after the `rack-06` fan-tray work) | High: directly explains late ranks | Low (read-only) | None | GPU temps/clocks across all `rack-06` nodes; BMC fan sensors (Redfish Thermal resource or `ipmitool sdr type Fan`) |
| H2 Fabric congestion on rail 5 (ECN marks 3×), or a consequence of the straggler | Medium (open) | Low | None | PFC pause and drop counters on rail-5 ports; whether ECN increase is concentrated on ports facing `orion-n22`'s peers and coincides with its late arrivals |
| H3 Software change (driver/NCCL/framework) | Low (only one node affected) | Low | None | Package versions on `orion-n22` vs peers; change log |
| H4 Failing GPU (hardware) independent of cooling | Medium | Medium (needs drain + diagnostics) | Low in a drained state | DCGM diagnostics after drain; compare after airflow is restored |

**Discriminating tests.** (1) If other GPUs in `rack-06` show elevated temperatures or fan sensors in the
replaced tray read low/absent, H1 with an airflow cause is strongly supported; if only GPU 5 is hot with
normal fans, H4 (GPU-local, e.g., cold-plate/heatsink contact) rises. (2) If rail-5 PFC pauses and drops
are flat and the ECN increase tracks `orion-n22`'s late arrivals, the *hypothesis* that ECN is a
consequence gains support: when the slow rank releases its pipeline sends, peers' traffic may bunch into
bursts that mark ECN. That mechanism is plausible but unproven — accept answers that keep it open and
name the test (ECN rate per port before and after the node is excluded). If ECN were rising on rail-5
ports unrelated to `orion-n22`, H2 needs its own investigation.

**Magnitude check.** If compute is ≈ 13.5 s of the 17.4 s step (≈ 78 %, as in Chapter 22's budget) and
scales with SM clock (peers boost-locked at 1,980 MHz, as the case states), the slowed node's compute
becomes 13.5 × 1,980 / 1,715 = 13.5 × 1.155 = 15.6 s, i.e. +2.1 s → 19.5 s (+12 %), matching the symptom.
Treat +2.1 s as an upper bound: memory-bound kernels slow less than the clock ratio, so the real
thermal penalty is somewhat smaller and a small residual may remain for other causes. (A GPU at 58 % clock would instead add
13.5 × 0.72 ≈ 9.8 s, +56 % — a learner who finds a mismatch of that kind should say the evidence is
inconsistent.)

**Root cause.** *Proven:* GPU 5 on `orion-n22` is in software thermal slowdown (event reason active, 89 °C,
SM clock 1,715 / 1,980 = 87 % of peers), its TP group waits for it, and its ranks gate the pipeline. *Inferred:* the 02:10 fan-tray
replacement caused the airflow deficit — correlated in time, to be confirmed by Facilities' inspection.

**Safe change.** Agree with the job owner to restart from the latest checkpoint without `orion-n22`
(drain the node in the scheduler — this stops new placement but does not move the running job; then restart from checkpoint at DP = 7 / 224 GPUs with a batch/LR adjustment, or wait for repair, since ORION has no spares). Accept a spare-based answer only when it is framed as the explicit hot-spare design proposal of Section 24.6, a variation from the reference cluster. Facilities inspects the `rack-06` fan tray under their
procedure. Do not raise power limits, override clocks, or touch fabric QoS.

**Validation.** Burn-in on `orion-n22` with GPU 5 temperature within the peer range (64–70 °C here) and no
active clock-event reasons; node acceptance (Chapter 16) before return; job step-time p50 back to ≈ 17.4 s
over ≥ 100 steps and ≥ 5 comparisons; rail-5 ECN rate back to baseline (confirming H2 was a consequence).

*Marking (15 pts):* hypothesis table with ranking rationale 4; discriminating tests with both outcomes 3;
proven vs inferred 2; magnitude check 1; safe change 2; validation with repetitions 2; ECN hypothesis with its test 1.
*Common mistakes:* treating the ECN rise as the root cause; "reset the GPU" on a running job; proposing
to raise fan speeds or power limits in production without Facilities; declaring the fan tray proven.
*Version note:* recent NVIDIA drivers label the section "Clocks Event Reasons"; older drivers used
"Clocks Throttle Reasons". Accept either. The DCGM field for fleet-wide alerting is
`DCGM_FI_DEV_CLOCKS_EVENT_REASONS` (formerly `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS`) `[VENDOR-SPEC, 2026-10]`.
HW slowdown would normally trigger only a few °C above the SW thermal limit, which is why the sample shows
SW thermal slowdown alone.

---

## E. Design challenge D1

No single answer. Award marks for: a current matrix produced by the lab on real evidence (3); a plan
whose arithmetic shows the projected score after each artifact (4) — e.g., for the sample learner at
AI Network/senior, Capstone B raising observability 1 → 3 and congestion 2 → 3 moves the score from
13.333/17 to (13.333 + 1.333 + 1.000)/17 = 15.667/17 = 92.2 % with max gap 1 → **ready**; respecting
the 10 h/week budget with realistic hours (2); a reasoned depth/breadth choice tied to the evidence caps
(3); an honest "not doing" paragraph (3). Deduct for plans whose artifacts cannot reach the claimed
level (e.g., an L1 lab "raising" a competency to 3).

Check of the example: observability contributes 2 × 3/3 = 2.000 instead of 0.667 (+1.333); congestion
3 × 3/3 = 3.000 instead of 2.000 (+1.000); total 13.333 + 2.333 = 15.667; 100 × 15.667 / 17 = 92.2 %.
Remaining gaps: physical layer 1, host topology 1 → max gap 1.

---

## F. Mandated exercises

**M1** — Grade against the lab rubric item "own role-readiness matrix" (15) and "gap plan" (10).
Required: the lab report run on the learner's own evidence file, every level backed by a named
artifact, the target plus two adjacent roles at four levels, top three gaps with dates. Deduct for
unsupported level-3/4 claims.

**M2** — 20 pts: assumptions table with labels (3); complete arithmetic (5); data-path diagram (3);
failure-domain table with detection (3); validation plan (2); two anticipated follow-ups answered (2);
rehearsal within 18–22 min (2). A changed constraint must propagate through the arithmetic (e.g.,
sequence length 8,192 doubles per-micro-batch activations to 134 MB and TP volume per micro-batch;
memory must be re-checked).

**M3** — 15 pts: all Table 24.12 sections (5); impact with units and arithmetic (3); a genuinely
discriminating test (3); remaining uncertainty (2); anonymisation statement (2). Deduct heavily for
unlabelled numbers or confidential detail.

**Deliverable** — role-readiness matrix (M1), portfolio narrative (≤ 1 page: target role, three
strongest artifacts and the problem each solved, what you would do differently, dated gaps), technical
presentation (M2).

---

## G. Reflection

**R1** Good answers: self-report bias (over-claiming levels) corrected by a peer or manager review of
the artifacts; matrix mismatch with the target employer's ladder corrected by mapping onto a published
ladder or asking an engineer at that level; evidence older than the current technology generation.
**R2** Any argument grounded in Table 24.7's problems (e.g., neocloud AI-network roles weighting
automation higher because bring-up speed dominates).
**R3** The line is whether the number came from *your* environment with a manifest and repetitions
(skill in measurement) or from a model or supplied data (skill in reasoning). Both are valuable; only the
first supports a measurement claim.
**R4** A dated, deduplicated register over a defined window; segmentation by role and level; the ratio of
postings to qualified applicants (not observable from postings); interview-loop data. Frequency in
postings is not scarcity.

*Marking:* 4 pts each; deduct for generic statements without named evidence.
