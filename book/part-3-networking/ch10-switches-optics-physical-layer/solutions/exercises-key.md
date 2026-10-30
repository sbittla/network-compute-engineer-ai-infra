# Chapter 10 — Answer Key (INSTRUCTOR ONLY)

All numbers below were computed twice (by hand and with Python). Values are `[MODELED]` from the
stated `[ILLUSTRATIVE]` assumptions unless labelled otherwise.

---

## A. Knowledge checks

**10.K1**

| Counter | Stage | Why |
|---|---|---|
| (a) Rx optical power | PMD / module (DOM) | Measured by the module's photodiode monitor |
| (b) FEC-uncorrectable codewords | PCS/FEC | RS decoder found ≥ 16 bad symbols |
| (c) FCS errors | MAC | CRC-32 over the frame fails |
| (d) Output discards | Traffic manager (MMU) | Buffer/queue admission rejected the packet |
| (e) PFC pause frames sent | MMU (generation) / MAC control (transmission) | Ingress buffer for a priority crossed its XOFF threshold |
| (f) Giants / oversize frames | MAC | Frame longer than the port MTU |

Marking: 1 point per correct row; accept "MAC control" for (e) if MMU threshold is mentioned.
Common mistake: placing FCS at the PCS.

**10.K2** PAM4 places four levels in the amplitude of two, so each of the three eyes is one third
the height of an NRZ eye: 20·log10(3) ≈ 9.5 dB SNR penalty. At 53.125 GBd over real channels, the
raw BER is therefore ~10⁻⁸–10⁻⁵, and the standard *requires* RS(544,514) FEC, which corrects those
errors and counts every corrected codeword. 10G NRZ links have enough SNR to run at ~10⁻¹² or better
without mandatory FEC, so error counters stay at zero. Marking: SNR penalty with a number (2), FEC
role (2). Common mistake: "PAM4 links are lower quality" — they are engineered to this BER.

**10.K3** 10-bit symbols; 544 symbols per codeword; 30 parity symbols (544 − 514);
t = 30/2 = **15** correctable symbols; 544 × 10 = **5,440 bits**.

**10.K4** A cut-through switch starts transmitting a frame before it has received the frame's FCS.
If the FCS turns out to be bad, it cannot recall the frame, so it replaces the outgoing FCS with a
known-bad value ("stomps" it) so the next hop drops it. The next hop then counts an FCS error on a
link whose own physical layer is perfect. The localizing counter is **FEC-uncorrectable codewords
(and symbol errors) on the ingress port of the upstream switch** where the corruption entered —
those do not propagate. Some platforms also expose a separate "stomped CRC" counter. Marking:
mechanism (2), why healthy link shows errors (1), localizing counter + device (2).

**10.K5**

| | 400GBASE-DR4 | 400GBASE-FR4 |
|---|---|---|
| Medium | SMF | SMF |
| Connector | MPO-12 | Duplex LC |
| Fibers used | 8 (4 Tx + 4 Rx) | 2 |
| Wavelengths | 1 × 1310 nm per fiber | 4 CWDM (1271/1291/1311/1331 nm) multiplexed |
| Reach | 500 m | 2 km |

They cannot link: different connectors, lane structure (four parallel fibers vs four wavelengths on
one fiber), and optical specifications. (A DR4 *can* break out to four 100GBASE-DR modules; that is
not FR4.) Values `[VENDOR-SPEC, 2026-10]` per IEEE 802.3bs/802.3cu.

**10.K6** Any five: temperature → airflow/fan failure, cage overheating (compare with neighbours and
module threshold); supply voltage → host power issue (vs nominal 3.3 V and thresholds); Tx bias →
laser aging (trend against commissioning baseline); Tx power → failing laser or driver (vs spec and
far end Rx); Rx power → dirty/damaged connector, fiber damage, wrong fiber (vs far-end Tx and design
loss; vs sibling lanes); LOS/LOL flags → disconnected fiber, polarity, wrong optic.

**10.K7** Each backend link's /31 is assigned for a specific pair of ports (Chapter 7). If two
jumpers are swapped, both links come up optically clean, but each leaf port faces a spine port
configured with a different /31; eBGP sessions do not establish, so ECMP loses two members
(2/32 = 6.25 % of the leaf's uplink capacity). There is no corruption, so FEC/FCS counters stay at
zero. **LLDP neighbour vs cabling schedule** validation detects it. Marking: mechanism (2), capacity
(1), detection check (2).

---

## B. Worked problems

**10.W1**

(a)
```text
fiber      = 0.420 km × 0.4 dB/km = 0.168 dB
connectors = 4 × 0.5 dB           = 2.000 dB
splices    = 2 × 0.1 dB           = 0.200 dB
channel    = 2.368 dB ≈ 2.37 dB          (≤ 3.0 dB allowed)
Rx (worst) = −2.9 − 2.368 = −5.268 ≈ −5.27 dBm
margin     = −5.268 − (−5.9) = 0.632 ≈ 0.63 dB
```
(b) Channel loss 3.368 dB > 3.0 dB: **fails the channel budget**; worst-case Rx −6.27 dBm is
0.37 dB below the receiver minimum. A typical module (Tx ≈ +0.5 dBm) would still link
(Rx ≈ −2.87 dBm), which is exactly why such links pass at install and fail as lasers age. Decision:
clean/re-terminate before acceptance; do not accept a link that only works with typical Tx.
(c) 10^(−5.268/10) = 10^(−0.5268) = **0.297 mW**.
(d) Measured loss = 0.6 − (−4.1) = 4.7 dB; excess = 4.7 − 2.37 = **2.33 dB**, equal on all lanes →
an element shared by all fibers: a dirty/damaged MPO end-face at one of the four mated pairs (most
likely), a bad splice, or a macro-bend in the trunk. Look first: drain the link (lab/maintenance),
inspect both module-side jumpers and each patch-panel interface, starting with the most recently
touched; if clean, test the trunk with an optical loss test set/OTDR on the dark fiber.
Marking: 3 + 2 + 1 + 3 points; −1 for any missing unit. Common mistakes: adding dBm values; forgetting
splices; calling (b) "OK because typical Tx works".

**10.W2**

(a) 800 × (257/256) × (544/514) = 800 × 1.0625 = **850 Gb/s** (8 × 106.25 Gb/s); codewords
850 × 10⁹ / 5,440 = **156.25 × 10⁶ codewords/s**.
(b) Margin = log10(2.4 × 10⁻⁴ / 2 × 10⁻⁵) = log10(12) = **1.08 decades**. p ≈ 10 × 2 × 10⁻⁵ = 2 × 10⁻⁴;
544p = 0.1088; P(≥1 bad symbol) = 1 − e^(−0.1088) = **0.103** → about 10 % of codewords are corrected
(≈ 1.6 × 10⁷ per second at 800G). Normal for PAM4; not a fault on its own.
(c) λ = 16,384 × 0.015 × 21/365 = **14.14** expected failures per lead time. Cumulative Poisson:

| k | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|---|
| P(X ≤ k) | 0.875 | 0.918 | 0.948 | 0.968 | 0.982 | 0.990 | 0.994 |

≥ 95 %: **21 spares**; ≥ 99 %: **24 spares** (P(X ≤ 23) = 0.9896 just misses 99 %; accept 23 if the
student rounds and says so explicitly). Normal approximation 14.14 + 2.33 × √14.14 ≈ 22.9 confirms.
(d) 3 % of 16,384 = 491.5 → 492 spares. The rate policy covers build-out (dead-on-arrival, infant
mortality, handling damage, installer breakage) and unknown AFR; the Poisson policy covers steady
state with credible AFR and lead time. Use rate-based during build and first months, then move to
model-based plus a buffer for correlated failures (bad lot, firmware).

---

## C. Hands-on lab — Lab answer key (planted anomalies)

Reference: `python lab/check.py --impl solution` → 13/13. Digest of per-port classification:
`e4c73a2d39db8da50081e0b5a1cd49758f67c20eb8a4bb9aa98ef99dc79e1e40`.

| Port | Planted condition | Expected layer / primary (all findings) | Teaching point |
|---|---|---|---|
| Ethernet2 | **Decoy:** counters cleared 240 s before T1 (all T1 counters < T0) | healthy / HEALTHY | Naïve `t1 − t0` gives huge negative deltas; reset-aware delta needed. Rates for that port are underestimated (only 240 s of data) — say so. |
| Ethernet7 | Dirty MPO end-face: lane 2 Rx −7.8 dBm, others ≈ −1.4 dBm; BER 2.6e-6 stable | physical / RX_POWER_LOW (+LANE_IMBALANCE), critical | −7.8 dBm is below the −5.9 dBm DR4 receiver minimum (policy critical), even though the module's own −9 dBm alarm has not fired; inspect/clean both ends. |
| Ethernet12 | Congestion: 18,342 discards, 16,000 ECN marks/s, 3,500 PFC pause tx/s; FEC/CRC/DOM clean | higher_layer / CONGESTION, refer | Looks terrible, is not physical: hand to Chapter 9 (incast on node n12's downlink). |
| Ethernet18 | **Decoy:** busy port, BER 6.5e-7, ≈ 1.5 × 10⁸ corrected CW in window, ECN 400/s, PFC 60/s | healthy | Corrected codewords and ECN marks are normal; under policy limits. |
| Ethernet21 | Pre-FEC BER rising 4.0e-6 → 1.6e-4 (0.18 decades margin), no uncorrectables yet, Rx ≈ −3.4 dBm (above the −4.0 dBm policy warning) | physical / PRE_FEC_BER_HIGH (+RISING), critical (≥ 1e-4 policy) | Trend matters; Table 10.1 says ≈ 1 uncorrectable per 80 days *now*, but the trend crosses the cliff soon. Compare NIC-side Tx/bias (far-end laser) then drain now (host link: coordinate a node drain through the scheduler), then clean/replace. |
| Ethernet27 | Port MTU left at 1500; 45,210 oversize frames from 9000-byte host frames | higher_layer / OVERSIZE_FRAMES, refer | Configuration (Chapter 7), not optics. |
| Ethernet35, 36 | Jumpers swapped at the patch panel: LLDP shows spine-1 Ethernet28/27 instead of 27/28 | physical / MISCABLED, critical | Link up and error-free; eBGP would fail on /31 mismatch; only LLDP vs schedule detects it. |
| Ethernet40 | Damaged cable to spine-1: 1,180 uncorrectable CW and 1,104 FCS errors in 600 s at an average BER of only 3.4e-5; DOM normal | physical / CRC_ERRORS (+FEC_UNCORRECTABLE, PRE_FEC_BER_HIGH), critical | Bursty errors: uncorrectables at ~0.85 decades of margin are impossible under random errors. Drain (uplink: −3.1 % raw, −12.5 % ECMP-aware ingress, since spine-1 still delivers a quarter of remote rail-3 traffic over 7 links; Chapter 7 Section 7.9), inspect, swap cable then optic. |
| Ethernet45 | Wrong optic: 400G-SR8 installed where schedule says 400G-DR4; link down, Rx −40 dBm (LOS) | physical / OPTIC_MISMATCH (+LINK_DOWN), critical | Do not "clean the fiber": the part is wrong (850 nm MMF optic on SMF facing DR4). |
| Ethernet50 | Flapping: 6 link-down events in 600 s, plus 40 uncorrectable CW / 31 FCS around transitions | physical / LINK_FLAP (+CRC_ERRORS, FEC_UNCORRECTABLE), critical | Errors around flaps are a consequence; primary is the flap. Reseat/inspect, check firmware and far end. |

Totals: 7 physical (7 critical, 0 warning), 2 higher-layer, 55 healthy; commissioning overall FAIL,
57/64 accepted. **Marking of `diagnosis.md` (10 pts):** 1 point per correctly explained non-healthy
port (9) + 1 for explaining at least one decoy. Deduct 2 for recommending cleaning on Ethernet12/27,
2 for recommending replacing Ethernet45's fiber, 2 for any action on an undrained production link.

Hardware evidence students should list as still needed: far-end (NIC/spine) DOM and counters for
each faulty link, FEC histograms, end-face inspection images, LLDP from the host side, and a soak
after repair.

---

## D. Troubleshooting case — 10.T1

(a) Apply Section 10.8.1:
1. *Load-dependent?* Yes — only during the 01:00–01:20 MoE all-to-all window → congestion signature.
2. *One link, one direction?* No — all eight uplinks to one spine, simultaneously → shared bottleneck.
3. *Physical precursor?* None: FEC-uncorrectable 0, FCS 0.
4. *DOM and FEC agree?* Both clean (BER 10⁻⁸–10⁻⁷, DOM normal).
5. *Configuration?* Possibly ECMP hashing or buffer/PFC policy; not optics.
Conclusion: **not physical**; congestion from all-to-all incast through spine-1 (or ECMP
polarization concentrating low-entropy RoCE flows on one spine, Chapter 7) — Chapter 9 / Chapter 12.

(b) Missing evidence and safe collection: spine-1 egress/ingress queue depth, discards, and PFC
sent counters (switch telemetry, read-only); per-uplink throughput showing whether spine-1 carries
more than spines 2–4 (ECMP imbalance, Chapter 7); host NIC PFC/ECN/CNP counters (`ethtool -S`
read-only; RDMA `hw_counters`); the evaluation job's all-to-all pattern, rank map, and whether PXN is enabled (Chapter 12).
All are reads — no changes.

(c) Owner: Fabric (congestion/QoS) with Training Infra for the all-to-all pattern. Ticket:
"Cleaning not required: zero FEC-uncorrectable/FCS, clean DOM and BER; discards and PFC are confined
to the MoE all-to-all window on all spine-1 uplinks, indicating congestion. Re-routed to Fabric
congestion workflow (Chapter 9) with the job's traffic analysis." Marking: 2 + 2 + 1.

---

## E. Design challenge — 10.D1 (model answer; accept any well-defended alternative)

| Link class | Choice | Reason |
|---|---|---|
| Host links (25–40 m) | 400G-DR4 + SMF MPO (or AOC if no structured cabling is wanted) | Beyond DAC/AEC reach; DR4 matches ORION's single spare type; AOC avoids cleaning but needs per-length spares and whole-assembly replacement |
| New leaf ↔ new spine (≈ 3 m) | AEC (or DAC if ≤ 2–3 m with routing slack) | Lowest power and highest reliability; must verify AEC/DAC support on both platforms |
| New spine ↔ old hall (350 m) | 400G-DR4 (≤ 500 m) over SMF; FR4 if fiber count is scarce | 350 m with patch panels and splices fits DR4's 3.0 dB budget only if connectors are low-loss: budget it (W1 method); FR4 uses 2 fibers instead of 8 |
| Switch modules | Single-port (consistent with ORION) unless port count forces twin-port | Twin-port halves module count but doubles failure blast radius |

Power: e.g., 16 nodes × 8 host links × 2 ends = 256 DR4 modules × 12 W ≈ 3.1 kW; AEC ends ≈ 1–6 W each.
Spares: DR4 modules, MPO jumpers per length, AEC per length, cleaning kit. Verify with vendors:
supported cable/optic list per NOS release, AEC power, FEC mode compatibility, twin-port module
availability. Marking: decision table (4), quantitative power (2), sparing (2), verification list (2).

---

## F. Reflection

**10.R1** (i) DFE error propagation — one wrong decision biases the next, producing correlated
bursts → the model *underestimates* uncorrectables. (ii) Reflections/intermittent mechanical
contact produce error bursts → *underestimates*. (Interleaving two codewords partially mitigates.)
Also acceptable: temperature-driven drift (non-stationary BER) → model underestimates during peaks.

**10.R2** Baseline the fleet at commissioning (distribution of pre-FEC BER and per-lane Rx per
optic type and link class); set warn at a percentile well outside the healthy population (e.g., 2–3
orders of magnitude above median BER but ≥ 1 decade below the FEC limit); use vendor module alarm
thresholds as outer bounds; refine with failure history (which pre-failure trends preceded RMAs).
Mark as `[ILLUSTRATIVE]` until validated.

**10.R3** Any four: real SerDes equalization/link training; real FEC histograms and burst
behaviour; DOM accuracy and drift; real end-face contamination effects; temperature-dependent
margin; NOS-specific counter semantics and CRC stomping; flap timing/debounce behaviour; impact on
real RoCE flows and NCCL.

**10.R4** (i) Faults between or outside the two samples (intermittent flaps that recover, bursts
in another window) → continuous streaming telemetry at ≤ 30 s with event logs (link up/down
syslog). (ii) Only one end sampled → direction-specific faults invisible → collect both ends and
join by cable ID. Also acceptable: counter resets/wraps hiding increments; DOM polled too rarely to
catch thermal excursions.

---

## G. Outline-mandated exercises and deliverable

**10.M1 — Commissioning checklist (model answer).** Must include the six required areas; manuscript
Table 10.8 is a complete model. Minimum numeric criteria: Rx ≥ −4.0 dBm per lane (policy; −5.9 dBm is the DR4 receiver minimum, and module-programmed −6/−9 dBm thresholds are not acceptance criteria) and lanes within
3 dB; Tx/bias/temperature inside module thresholds; pre-FEC BER < 10⁻⁶ at acceptance (in service: warn ≥ 10⁻⁵, critical ≥ 10⁻⁴, KP4 limit 2.4 × 10⁻⁴); zero FEC
uncorrectable and zero FCS during a ≥ 30-minute loaded soak; link-down counter unchanged during soak;
LLDP = schedule; module PN on the approved list for the NOS release; labels on both ends. Marking:
6 areas × 1 point + numeric criteria (2) + failure actions (2). Common mistake: no soak, or
acceptance thresholds equal to alert thresholds.

**10.M2 — Counter interpretation.**

| Port | Layer | Cause | First safe action | Further evidence |
|---|---|---|---|---|
| P1 | Higher-layer | Congestion (discards + 1,833 PFC pause/s; FEC/FCS clean; BER stable) | Hand to Chapter 9 congestion workflow | Queue depth, ECN marks, which flows (incast?) |
| P2 | Physical | Bursty corruption: uncorrectables + FCS at moderate BER, DOM normal → reflection / damaged connector / intermittent cable | Drain; inspect/clean both ends; swap cable, then optic | FEC histogram tail; far-end counters |
| P3 | Physical *elsewhere* (not this link) | FCS errors without uncorrectables or symbol errors, clean BER → stomped frames from upstream (cut-through) | Do not touch this link; find upstream port with uncorrectables | Upstream switch ingress FEC-uncorrectable counters; stomped-CRC counter if available |
| P4 | Physical | Flapping link (5 events); the small FEC/FCS counts are side effects of transitions | Drain; reseat/inspect; check firmware and far end; replace optic if it repeats | Link up/down syslog timestamps, far-end logs, DOM history |
| P5 | Physical (critical) | One lane at −6.8 dBm, below the −5.9 dBm receiver minimum and 4.7 dB below siblings, + BER up 45× in 7 days → contamination/damage on one MPO fiber, worsening | Drain now (host link: via scheduler); inspect/clean both ends; replace jumper | Far-end per-lane Tx; FEC histogram |
| P6 | Higher-layer | Giants only → MTU mismatch (port MTU < host frame size) | Compare port vs host MTU (Chapter 7) | Port config, host `ip link` MTU |

Margins: P2 log10(2.4e-4 / 4.0e-5) = log10(6) = **0.78 decades**; P5 log10(2.4e-4 / 9.0e-5) =
log10(2.67) = **0.43 decades**. P5's lane imbalance: −6.8 vs ≈ −2.1 dBm → 4.7 dB. Marking: 1 point
per row, 1 per margin. Common mistakes: calling P1 physical because of "errors"; replacing P3's cable.

**10.M3 — Small fabric estimate (24 nodes).**
```text
down_max            = 64 × 1/(1+1)              = 32  → 24 nodes fit: leaves_per_rail = 1
leaves              = 8 rails × 1               = 8
down/up per leaf    = 24 / 24 (1:1)
host links          = 24 × 8                    = 192
fabric links        = 8 × 24                    = 192
spines              = ceil(192 / 64)            = 3   (24 mod 3 = 0 → 8 uplinks per leaf per spine)
total links         = 384;  optics = 2 × 384 = 768 (400G-DR4);  cables = 384
leaf ports used     = 8 × 48 = 384;  free = 8 × 16 = 128
spine ports used    = 192 of 192;  free = 0
spares: optics ceil(768 × 0.03) = ceil(23.04) = 24; cables ceil(384 × 0.02) = ceil(7.68) = 8;
        switches 1 (leaf and spine share one model)
```
Operational spares beyond optics and cables: one pre-imaged switch, PSUs and fan trays (if
field-replaceable), MPO jumpers in each used length, cleaning supplies, inspection probe tips, labels.
Growth to 32 nodes: each leaf needs 32 uplinks → 256 fabric links → 4 spines, still 8 uplinks per
leaf per spine; the existing 24 uplinks per leaf stay where they are and 8 new uplinks per leaf go to
the new spine-4 — no re-cabling if spine port blocks were reserved, but the leaves then have no free
ports. Marking: quantities (6), spares (2), growth (2).

**10.M4 — Deliverable.** Check: CSV has 256 rows, unique cable IDs and endpoints, 8 links per
leaf–spine pair (same as `check.py`), label text names cable ID and both ends, lengths derived from a
stated layout. Runbook must include the signal/threshold/action/escalation table (the manuscript's
runbook excerpt is the model; pre-FEC BER thresholds must match the lab policy: warn 10⁻⁵, critical 10⁻⁴), drain-before-touch for both link classes (host link = node drain via
scheduler; uplink = routing-policy drain then admin-down), commissioning gates, cleaning procedure
(IEC 61300-3-35), and sparing numbers (small fabric: 512 optics → 16 spares; 256 cables → 6 spares;
1 switch). Marking: schedule (40), runbook (60: table 20, procedures 20, gates/cleaning 10,
sparing 10). Deduct for unlabelled thresholds.
