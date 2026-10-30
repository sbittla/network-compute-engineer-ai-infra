# Chapter 9 — Exercise Key (INSTRUCTOR ONLY)

Conventions: r = 400 Gb/s = 50 GB/s = 50 B/ns = 50 KB/µs; v = 2 × 10⁸ m/s (5 ns/m); port MTU
9,216 B; t_resp = 1 µs; PFC frame 64 B. All numbers below are `[MODELED]` unless marked. Every value
was computed twice (by hand and by a short script).

Headroom formula: **H = 2 × MTU + 2 × r × (L / v) + r × t_resp + 64 B**.

---

## Knowledge check

**K1.** CP = the orion-be-leaf-r3 egress queue on eth1/5 (toward orion-n05); NP = orion-n05's NIC (`mlx5_3`); RP = each
of the 12 sending NICs. NP→RP packet: the Congestion Notification Packet (CNP), DSCP 48, TC 6 (strict
priority). *Marking:* 1 point per role, 1 for CNP + class. *Common mistake:* naming the switch as the
device that sends CNPs (in RoCEv2 DCQCN the receiver NIC does).

**K2.** Quantum = 512 bit / rate.
- 100 Gb/s: 512 / 100 × 10⁹ = 5.12 ns; max = 65,535 × 5.12 ns = 335,539 ns ≈ **335.5 µs**.
- 400 Gb/s: 512 / 400 × 10⁹ = 1.28 ns; max = 65,535 × 1.28 ns = 83,885 ns ≈ **83.9 µs**.
A sustained pause longer than one frame's maximum requires the pausing device to refresh with new
frames before the timer expires, so counters show a steady frame *rate* (≈ 23,800/s at 400 Gb/s with
half-life refresh). *Mistake:* using bytes instead of bits (gives 8× error).

**K3.** Not-ECT `00`, ECT(1) `01`, ECT(0) `10`, CE `11`. Above Kmin the switch marks ECT packets CE
with probability p(q); Not-ECT packets are dropped with the WRED probability. In TC 3 a drop is a loss
in a class promised lossless and triggers go-back-N retransmission; all RoCE data must be ECT and WRED
drop must be disabled for that class. *Mistake:* claiming CE is set by the receiver.

**K4.** (1) Switches queue CNPs in TC 3 behind the very congestion they report; (2) when TC 3 is paused,
CNPs are paused too; (3) the RP receives rate-cut signals late or in bursts, so senders keep sending at
high rate; (4) queues reach Xoff more often → pause rate rises relative to ECN marks; observable as a
falling ECN-marks/pause ratio and `rp_cnp_handled` lagging `np_cnp_sent` in time; in the worst case
CNPs are counted as part of TC 3 traffic on the switch. *Full marks* need the chain to end in a counter.

**K5.** Xoff: the ingress PG occupancy at which the switch *decides* to send pause. Headroom: a separate
per-(port, lossless PG) reservation that absorbs bytes arriving *after* the decision (in-flight frames,
wire bytes in both directions, response time). Symptom: non-zero lossless-class discards on the port
despite active PFC. Longest links first because the 2 × r × L / v term grows with cable length; a profile
sized for short cables is short by exactly that term. *Mistake:* "raise Xoff" — that does not create
headroom; it only delays the pause, so even more bytes are in the buffer when the in-flight bytes arrive.

**K6.** P with high `pfc_tx`: P's *ingress* buffer (for priority 3) is filling; P asks its *peer* to stop
sending. Q with high `pfc_rx`: Q's *peer's* ingress is filling; Q is being asked to stop *transmitting*
priority 3 out of Q.

**K7.** Instantaneous samples every 10 s catch the queue at a random instant; bursts of tens of
microseconds that cause marking are almost never sampled. ECN counters are cumulative and miss nothing.
Plot the queue **watermark** (peak since last read) and the ECN-mark *rate*.

**K8.** On the switch port facing the device — storm vs incast: queue flat at maximum vs deep but
varying; egress ≈ 0 vs ≈ line rate; ECN marks ≈ 0 vs heavy; pause received from device sustained
(thousands/s) vs ≈ 0; device receive throughput ≈ 0 vs ≈ line rate. Any four.

---

## Worked problems

**W1.**
(a) L / v = 150 m × 5 ns/m = 750 ns.
2 × MTU = 2 × 9,216 = 18,432 B; 2 × r × L/v = 2 × 50 B/ns × 750 ns = 75,000 B; r × t_resp = 50 B/ns ×
1,000 ns = 50,000 B; + 64 B.
H = 18,432 + 75,000 + 50,000 + 64 = **143,496 B ≈ 143.5 KB** per port per lossless priority.
(b) 64 ports × 2 priorities × 143,496 B = **18,367,488 B ≈ 18.4 MB**.
(c) At 800 Gb/s, r = 100 B/ns: 18,432 + 2 × 100 × 750 + 100 × 1,000 + 64 = 18,432 + 150,000 + 100,000 + 64 =
**268,496 B ≈ 268.5 KB**, i.e. 268,496 / 143,496 ≈ **1.87×**. The wire and response terms scale linearly
with rate; only the MTU term does not, so headroom nearly doubles with each speed doubling while
buffer per port often grows more slowly.
*Marking:* 4 / 3 / 3 points. *Mistakes:* using 4,096 B (RDMA path MTU) instead of the port MTU; counting
propagation once instead of twice; forgetting the factor of 2 priorities.

**W2.**
(a) Excess = (16 − 1) × 50 KB/µs = **750 KB/µs**.
(b) 1,500 KB / 750 KB/µs = **2.0 µs**.
(c) **No.** Feedback needs at least one RTT (6 µs) plus CNP generation; the threshold is reached in a
third of that. PFC must handle the first burst. (Without PFC, the 6 MB share would fill in
6,000 / 750 = 8 µs and drops would follow.)
(d) Total = 16 × 2 MB = 32 MB; 32 × 10⁶ B / 50 × 10⁹ B/s = **640 µs**.
(e) Need a 16× aggregate cut: log₂ 16 = **4 halvings** (α ≈ 1 initially, so each cut ≈ halves). First
cut ≈ 1 RTT after marking starts (≈ 6 µs); subsequent cuts at most every N = 50 µs per flow: ≈ 6 + 3 × 50 =
**≈ 156 µs**, i.e. 156 / 640 ≈ **24 %** of the minimum completion time, during which PFC carries the
excess. Accept 150–210 µs (some students count 4 × 50 = 200 µs ≈ 31 %) if the reasoning is stated.
(f) BDP = 50 GB/s × 6 µs = **300 KB**. Kmin should be ≤ 1 BDP and comfortably below the 1.5 MB
threshold, e.g. 100–300 KB; justify that marks must begin before PFC engages.
*Marking:* 1 point each for (a)–(d), 3 for (e), 3 for (f).

---

## Hands-on lab (H1) and O1 — reference results and planted anomalies

Reference output: `python solutions/lab/congestion_lab.py --out report.md` from the chapter folder
(or run check.py with `--impl solution`). Expected findings `[SIMULATED / SYNTHETIC data]`:

| Episode (s) | Label | Root / source | Discriminating evidence (medians over the episode) |
|---|---|---|---|
| 100–158 | incast | root `orion-be-leaf-r3:eth1/5` (to orion-n05) | eth1/5: tx ≈ 394 Gb/s, queue ≈ 3,100 KB (above that leaf's 1,500 KB Kmin), ECN ≈ 0.75 M pkts/s, pause rx 0; pause *tx* 2,500–6,000/s on the 12 sender ports only; no fabric-port pauses; orion-n05 `cnp_sent` ≈ 400 k/s |
| 250–318 | pause_propagation | root `orion-be-leaf-r3:eth1/10` (to orion-n10) | eth1/10 at line rate with deep queue and no pause rx; leaf-r3 uplinks send 6–10 k pause/s to spines; spine ports toward leaf-r3 have deep queues (above Kmax, so ≈ 6 M marks/s) *and* receive pause (branches); spines pause leaf-r4 uplinks; leaf-r4 pauses its 8 rail-4 NICs |
| 400–468 | pfc_storm | source `orion-n12:mlx5_3` | leaf-r3 eth1/12: pause rx ≈ 23,750/s, tx ≈ 0 Gb/s, queue ≈ 4,000 KB flat, ECN 0; NIC `pfc_tx_p3` ≈ 23,750/s, rx 0 Gb/s; leaf pauses eth1/3 and eth1/6 (orion-n03, orion-n06: peers of orion-n12) |
| 520–558 | *not an episode* | — | orion-be-leaf-r4 eth1/7 (to orion-n07): 375–392 Gb/s, queue 155–250 KB (just above that leaf's 150 KB Kmin), ECN ≈ 50 k/s, **no pause** — busy and healthy; DCQCN working |

Victims: **P1** (orion-n03 → orion-n07) in the incast (p99 ≈ 21×) and in the storm (≈ 358×): destination eth1/7
uncongested; its *source* NIC orion-n03 is one of the paused senders. **P4** (orion-n04 rail 4 → orion-n13 rail 3,
cross-rail via spines) in the propagation episode (≈ 39×): destination eth1/13 uncongested; it crosses
paused leaf-r4 and spine ports. **Not victims:** P3 (orion-n02 → orion-n05) is inflated in the incast but its
destination is the root — it is part of the incast. P2 is a control and never inflates.

QoS findings: `orion-be-leaf-r3 ECN_KMIN_HIGH` (1,500 KB > same-rail BDP 200 KB = 400 Gb/s × 4 µs; the
template value × 10 — a units/copy error), `orion-be-leaf-r3 PFC_WATCHDOG_DISABLED` (why the storm lasted
70 s), `orion-be-leaf-r4 CNP_CLASS_MISMATCH` (CNPs in TC 3 — feedback stuck behind pauses during
propagation), `orion-be-spine-2 PFC_PRIORITY_MISMATCH` (priority 4 lossless: wasted headroom and
path-dependent behaviour). No false positives on orion-be-spine-1.

**Planted data anomalies (do not reveal to learners).** The machine-readable specification the generator
loads is `solutions/lab/planted_faults.yaml`; the generator (`lab/tools/`) is instructor-only and is
stripped from the student release, as is this folder. ECN marks in the data are consistent with each
switch's Kmin/Kmax: ports whose watermark stays below Kmin show zero marks.
1. **Counter reset** on `orion-be-leaf-r4:eth1/2` at t = 200 s (all cumulative counters restart from the current
   interval's count, as after "clear counters"). Naive differencing produces huge negative rates;
   correct handling yields NaN for that one interval.
2. **Telemetry gap**: `orion-be-spine-2` has no samples for t = 300–310 s (inside the propagation episode). Rates
   at t = 312 must divide by 14 s (from t = 298), not 2 s. Dividing by 2 s inflates spine-2 pause rates 7×
   (does not change labels, but is a marked error in the narrative if quoted).
3. **Benign high utilisation** at orion-be-leaf-r4 eth1/7 (t = 520–558): designed to catch detectors that flag
   "high throughput" or "ECN marks > 0" as congestion.
4. **Victim decoys**: P3's latency inflates during the incast, but it is not a victim.
5. **Configuration faults** (four, above), each linked to an episode's severity: the late ECN profile
   makes leaf-r3 run on pause; the missing watchdog prolongs the storm; misclassified CNPs worsen
   propagation; the extra lossless priority on spine-2 is a latent risk with no episode.
6. **Cross-rail traffic** in the propagation episode (rail-4 NICs of orion-n01–n08 → rail-3 NIC of orion-n10) hints at a rank-to-rail
   mapping error (Chapter 13); strong reports point it out.

Simulation reference `[SIMULATED]`: A completion 960.0 µs, peak 1,660 KB, paused 862.8 µs, 0 CNPs;
B 1,256.8 µs, peak 1,660 KB, paused 113.6 µs, 60 CNPs; C 3,875.2 µs, peak 4,000 KB, 17,840,000 B dropped,
84 CNPs; lower bound 960 µs for all.

**Lab rubric notes:** award the 15 narrative points only if each episode's label is supported by at
least two *discriminating* values (values that would differ under the competing label), and the report
says which conclusions are proven (e.g., the NIC is the storm source: its own counters show it) versus
correlated (e.g., the job's rank mapping caused the cross-rail incast: plausible, not proven from this
data). Deduct 5 if any simulated number is presented without the `[SIMULATED]` label.

**O1** is answered by the table above; full marks require the quoted values to be *rates* computed by
the learner's code (not raw cumulative counters).

---

## O2 — Why not PFC everywhere? (model answer)

Risks (any four, each with mechanism):
1. **HOL blocking** — PFC pauses a (port, priority), so flows to uncongested destinations sharing the
   paused port/NIC stall (victims).
2. **Pause propagation / congestion trees** — paused devices' queues fill and they pause their upstream
   neighbours; a single hot egress can stall senders several hops away.
3. **PFC storms** — a faulty NIC or host emitting continuous pause can freeze every path through its
   leaf; without a watchdog, nothing stops it.
4. **Deadlock** — cyclic buffer dependencies (routing out of up-down order, flooding of lossless
   traffic) leave buffers waiting on each other forever.
5. **Buffer cost** — headroom per port per lossless priority (≈ 6.5 MB per ORION leaf per priority)
   removed from the shared pool, reducing burst absorption for everything else.
6. **Masking** — PFC hides misconfigured or absent ECN/DCQCN: the fabric "works" while running on pause,
   with poor tail latency, until a storm or deadlock exposes it.

Procedure (model):
1. Confirm scope: list ports with pause tx/rx rate > threshold in the window; note any switch↔switch
   ports (propagation) and any lossless discards or watchdog events (incident).
2. Convert counters to rates on both ends of each link; verify the two ends agree (tx on one = rx on the
   other) to rule out counter errors.
3. For each port with a deep TC 3 watermark, check whether it *receives* pause. Receives → branch: follow
   to its peer downstream. Does not receive and is at line rate → root.
4. At the root, classify: line-rate egress with heavy ECN → incast (find the fan-in workload); egress ≈ 0
   with sustained pause rx from the peer → storm/slow receiver (inspect the peer NIC: `ethtool -S`
   pause and storm counters, host `lspci` link state, `dmesg`).
5. Check DCQCN health on the root: ECN-marks/pause ratio, NIC `np_cnp_sent` at the destination and
   `rp_cnp_handled` at senders; CNP class mapping on every hop.
6. Identify HOL victims: for flows/probes with p99 inflation, check their *destination* queue; if
   uncongested, find which of their ingress ports or NICs is being paused.
7. Record evidence (counter snapshots, timestamps) before any change; then choose a safe action (drain
   a node, rely on watchdog) per the runbook.

*Marking:* 4 × 2 points for risks, 7 points for the procedure (deduct for steps without a counter or
decision rule).

## O3 — Controlled experiment (model answer outline)

- Hypothesis: on the lab leaf, Kmin 150 KB (B) reduces total pause duration in a 12:1 incast by ≥ 5×
  versus Kmin 1,500 KB (A) and increases median incast completion by ≤ 20 %.
- Configurations: full snapshots of A and B (trust DSCP, DSCP 26 → TC 3, PFC priority 3, Xoff/headroom
  profile, ECN Kmax 1,500 / 6,000 KB, Pmax 0.2, watchdog on, CNP DSCP 48 → TC 6); only Kmin/Kmax differ.
- Workload: 12 perftest `ib_write_bw` clients, fixed message size and QP count, fixed duration, plus a
  bystander probe (e.g. `ib_write_lat`) from one sender NIC to an idle host.
- Procedure: warm-up discarded; A/B interleaved; ≥ 5 runs each; counters snapshotted before/after each run.
- Metrics: per-client and aggregate bandwidth; incast completion; bystander p50/p99/max latency; pause
  frames and pause duration tx/rx per port; ECN marks; CNPs sent/handled; queue/PG watermarks; TC 3
  discards; watchdog events.
- Analysis: median and p95/p99 with min/max; difference claimed only if ranges do not overlap or a
  pre-registered test passes.
- Manifest: fields from `lab/manifest.yaml` `record:`.
- Safety: isolated lab fabric, rollback snapshot, no shared switches.
- Cannot conclude from the simulation: absolute magnitudes; ASIC shared-buffer and per-PG behaviour;
  multi-hop propagation and ECMP; real DCQCN timers, byte counter, additive/hyper increase; NIC loss
  recovery (go-back-N vs selective); HOL victims, storms, deadlock, watchdog; generalisation beyond
  synchronous equal senders. The experiment establishes behaviour only for that hardware, firmware,
  scale, and workload.
*Marking:* 2 points per element (10 elements), capped at 20.

---

## Troubleshooting case T1

(a) Ranked hypotheses: **H1 undersized headroom on the long uplink** (discards only on the 100 m port
while eth1/33, with the same pause rate, has none; profile sized for 5 m; leaf recently replaced → new
default profile); H2 a slow PFC response on orion-be-spine-4 — cannot be excluded from this data alone
(eth1/33 faces a different spine), so test it by comparing other leaves' 100 m links to spine-4, which
show no discards; H3 lossy traffic mis-mapped into TC 3 (would show drops on all busy
ports); H4 physical-layer errors (Chapter 10) — CRC drops are counted as errors, not TC 3 discards; check
to exclude.
(b) Provided (5 m): L/v = 25 ns → 2 × 50 × 25 = 2,500 B; H = 18,432 + 2,500 + 50,000 + 64 = **70,996 B**.
Needed (100 m): **118,496 B**. Deficit = 118,496 − 70,996 = **47,500 B per pause event** (≈ 40 % short).
(c) eth1/33 (20 m) needs 18,432 + 2 × 50 × 100 + 50,000 + 64 = 78,496 B: a 7,500 B (≈ 10 %) shortfall
against the 70,996 B provided. It has not dropped because the formula is a worst case (two maximum-size
frames in flight, worst-case response time) that is rarely realised, and cell-rounding margins may cover
part of it. **The learner must state that the evidence cannot prove eth1/33 is safe**: zero discards in a
5-minute window is absence of evidence, not a guarantee; under worst-case alignment the port is short
and can drop. Full marks for (c) require this statement; deduct 2 if the answer calls eth1/33 "fine". The 30 m downlinks (need 83,496 B, ≈ 12,500 B
short) are also under-provisioned and must be fixed even though they have not dropped yet — a strong
answer notices this.
(d) Fix: set the per-port cable length (or headroom) to the real values via the change pipeline — canary
on orion-be-leaf-r5 in a maintenance window, rollback plan, Fabric team approval; verify the vendor recomputes
headroom and that the shared pool still meets its minimum. Validate: zero TC 3 discards over ≥ 24 h
including training peaks; headroom watermark (where exposed) below its reservation; no change in pause
behaviour; a post-change audit comparing every leaf's cable-length/headroom settings against the cabling
database. *Marking:* 4 / 4 / 3 / 4.

---

## Design challenge D1 (model answer)

Recommendation: **reject a second lossless priority on the backend; accept checkpoint RDMA in a lossy,
ECN-enabled class (or on the frontend/storage fabric) with conditions.**
- Headroom: 32 × 83,496 + 32 × 118,496 = **6,463,744 B ≈ 6.5 MB** more per rail leaf, and 64 × 118,496 =
  7,583,744 B ≈ 7.6 MB per spine — buffer taken from burst absorption for W-TRAIN's TC 3.
- Risks: a second set of congestion trees and storms; checkpoint bursts (≈ 980 GB per W-TRAIN
  checkpoint) pausing ports that also carry TC 3 collectives (HOL across classes shares ports and NICs);
  doubled deadlock surface; configuration drift (exactly the lab's spine-2 fault).
- "Cannot tolerate loss" conflates transport reliability with network losslessness: RDMA RC is reliable
  over a lossy network; the question is retransmission cost, which checkpoint writes (bulk, latency
  tolerant) can afford.
- Alternatives table (cost, isolation, risk, maturity): (1) lossy TC with ECN/DCQCN + NIC selective
  retransmission; (2) frontend/storage fabric (2 × 200 GbE per node) for checkpoint traffic — ORION's
  design intent; (3) schedule checkpoints with rate limiting; (4) second lossless class (rejected).
- What would change the decision: measured evidence on a lab fabric that loss recovery for the
  checkpoint path is unacceptable *and* a headroom budget showing no impact on TC 3 burst absorption.
*Marking:* arithmetic 4, risks 4, alternatives 4, decision quality 3.

---

## Reflection

**R1.** Trust the **direction and rough size of the pause-exposure reduction** more: it follows from a
robust mechanism (marks begin before Xoff vs never). The **31 % completion penalty** is mostly an
artifact of the model's simplified recovery (fast recovery only, no additive/hyper increase, no byte
counter); real DCQCN recovers faster, so the penalty is likely overstated. Both need L3 measurement.

**R2.** Microbursts of tens of microseconds (revealed by queue/PG **watermarks**); short pause storms or
brief pause trains between samples (revealed by cumulative pause counters plus **pause-duration**
counters, or sub-second streaming telemetry); incast onset order (needs high-rate or event-driven
telemetry, e.g. in-band telemetry or mirror-on-drop).

**R3.** Proof: `LnkSta` shows x8 while `LnkCap` is x16; the ≈ 213 Gb/s ceiling matches what Gen5 x8
achieves (252 Gb/s raw, ≈ 200–220 Gb/s after protocol overhead); pause
originates from that NIC (its own `tx_prio3_pause`); fix (x16) removes pauses and restores step time —
the validation closes the loop. Correlated only: the Tuesday maintenance (temporal), victim senders'
pauses (consequence), the job-level slowdown (could have other contributors until validated).

**R4.** Misidentification cases: the root's receiving NIC is itself a slow receiver (it *does* send
pause, so the true root is the host, and the rule finds no switch root — classify as storm/slow
receiver instead); missing samples at the root port (the rule never sees it); two simultaneous roots;
counters at the root reset. Extra evidence: NIC-side pause and storm counters, host PCIe/memory state,
both-end agreement of pause counters, and topology walk of the flows involved.
