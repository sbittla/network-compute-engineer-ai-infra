# Chapter 2 — Instructor Answer Key

INSTRUCTOR ONLY. All figures are `[MODELED]` from the stated `[ILLUSTRATIVE]` assumptions unless
marked otherwise. Every number below was computed twice (by hand and with Python). Accept answers
within ±1 % of rounding unless a marking note says otherwise.

---

## Exercise 2.1 — Knowledge check

1. **Power-limited rack.** Four HX8 nodes use 32U of a 48U rack but draw 4 × 10.2 + 0.2 = 41.0 kW.
   48U − 32U − 3U (switch and cassettes) leaves 13U, so a fifth 8U node fits physically, but it
   would take the rack to 5 × 10.2 + 0.2 = 51.2 kW, needing 56.3 kW per side with margin — beyond
   ORION's per-rack coolant, CDU, and floor design even though 65.55 kW per side is available. *Marking:* full credit needs both a space and a power number.
2. **Three networks.** Backend: distributed jobs hang or fail (collectives cannot complete);
   frontend/storage: jobs stall on dataset reads and checkpoints, inference is unreachable; OOB:
   running work continues, but remote power control, console, and BMC telemetry are lost.
3. **2N capacity.** Per circuit √3 × 415 × 60 = 43.13 kVA; × 0.80 × 0.95 = 32.78 kW; two circuits =
   65.55 kW per side. With 2N, either side must carry the whole rack alone when the other is lost or
   in maintenance, so usable capacity is 65.55 kW, not 131 kW. *Common mistake:* adding both sides.
4. **TDP vs peak.** TDP is the sustained power the cooling is designed for and the default power
   limit; instantaneous draw can exceed it for microseconds to milliseconds. Board capacitors,
   voltage regulators, and PSU hold-up absorb microsecond excursions; PSUs, PDUs, breakers, and the
   UPS see step-boundary swings (tens of ms to seconds).
5. **FWS/TCS/approach.** FWS: the facility's primary water loop; TCS: the clean, filtered secondary
   loop through the cold plates; approach: TCS supply minus FWS supply at the CDU heat exchanger. On a
   hot afternoon the FWS supply warms, the TCS supply follows (approach roughly constant), cold plates
   run warmer, and a GPU with little thermal margin enters thermal slowdown.
6. **SW Power Cap active.** Not a fault: under dense GEMM a GPU commonly runs at its power limit. It is
   a fault if the limit is lower than intended (check `Current Power Limit` vs `Default Power Limit`
   in `nvidia-smi -q -d POWER`) or if only some GPUs in a job are capped.
7. **Allocation, MFU, goodput.** Allocation = fraction of GPU-hours given to jobs; MFU = useful model
   FLOP/s ÷ peak FLOP/s while running; goodput = fraction of allocated time that becomes durable
   progress. They multiply because each applies to what remains after the previous one: unallocated
   hours produce nothing, allocated hours run at MFU, and lost work removes a fraction of that.
8. **Optics.** (a) Optics are among the most frequently failing and replaced components, so the
   count drives spares stock and repair workload; (b) each optic draws power and must be cooled, and
   optic type determines reach, which constrains rack placement. Also accept: firmware/compatibility
   management, cleaning and inspection workload.

---

## Exercise 2.2 — ORION-128 small-cluster BOM

**1. Nodes per rack.** Usable per circuit: √3 × 415 × 32 = 23,002 VA; × 0.80 × 0.95 = 17.48 kW. Two
circuits per side: **34.96 kW**. Requirement for *n* nodes: (10.2 *n* + 0.2) × 1.10.
- *n* = 3: 30.8 × 1.10 = 33.88 kW ≤ 34.96 ✓ (headroom 1.08 kW).
- *n* = 4: 41.0 × 1.10 = 45.1 kW ✗.

So **3 nodes per rack**; 16 nodes → ⌈16 ÷ 3⌉ = **6 GPU racks** (better balanced as 4 racks × 3 + 2
racks × 2, which also leaves electrical headroom in two racks). A full rack holds 3 × 8U = **24U** of
nodes.

**2. Switches and links.** Rail-optimized with 8 rails → **8 rail leaves**, each with 16 downlinks
(one per node). For 1:1, 16 uplinks per leaf; leaf-to-spine links = 8 × 16 = **128**. Spine ports
needed = 128; with 64-port spines → **2 spines**, each leaf sending 8 uplinks to each spine (8 leaves ×
8 = 64 ports per spine ✓). Host-to-leaf links = 16 × 8 = **128**; total backend links **256**. Ports
used: leaves 8 × 32 = 256 (of 512 → **256 unused leaf ports**), spines 2 × 64 = 128; total **384**.

**3. Transceivers.** 2 × 256 = **512** single-port 400G modules (128 at NICs, 384 at switches).

**4. Bisection.** 128 GPUs × 400 Gb/s = 51.2 Tb/s injection; at 1:1, **25.6 Tb/s per direction**.

**5. Frontend and OOB.** Frontend: 16 × 2 = **32** ports at 200 Gb/s. OOB: 16 BMCs + 10 backend
switches + 2 frontend leaves + 4 storage servers + 6 racks × 4 PDUs (24) = **56** ports.

**6. Assumption to verify.** Best answers: the 10.2 kW node maximum and transient margin at 32 A
(the rack has only 1.08 kW of headroom — a 4 % error in node power breaks the design); or that the
older hall's floor and cooling can take 31 kW racks.

*Marking (20 pts):* nodes/rack with arithmetic 5; racks and RU 2; switches and links 5; transceivers
2; bisection 2; frontend/OOB 2; assumption 2. *Common mistakes:* using 4 nodes per rack (sizing on
sustained power or forgetting the transient margin); computing 4 spines by copying ORION; forgetting
the unused leaf ports (a good answer notes that 32-port-class leaves, or 4 rails per leaf where the
platform supports it, would save cost — but rail-optimized wiring needs one leaf per rail).

---

## Exercise 2.3 — ORION-128 capacity model

| Line | Formula | Result |
|---|---|---|
| Accelerators | 16 × 8 | 128 GPUs |
| Total HBM | 128 × 80 GB | 10,240 GB |
| Usable HBM | 128 × 80 × 0.90 | 9,216 GB (72 GB per GPU) |
| Training state per GPU | 13e9 × 16 B ÷ (TP 8 × PP 1) | 26.0 GB — fits in 72 GB, leaving 46 GB for activations |
| Storage read / write | 4 × 20; 4 × 10 | 80 GB/s; 40 GB/s |
| Read per GPU | 80 ÷ 128 | 0.625 GB/s |
| Checkpoint size | 13e9 × 14 B | 182 GB |
| Checkpoint lower bound | 182 ÷ 40 | 4.55 s |
| Bisection per direction | From 2.2 | 25.6 Tb/s |
| IT maximum | 5 × 30.8 + 1 × 10.4 + 10.0 + 4.5 + 3.0 (using 3,3,3,3,3,1 layout) | 181.9 kW |
| Facility power | 181.9 × 1.30 | 236.5 kW |
| Allocated GPU-hours/yr | 128 × 8,760 × 0.80 | 897,024 |
| Durable fraction of peak | 0.80 × 0.38 × 0.92 | 0.280 (28 %) |

With the balanced 4 × 3 + 2 × 2 layout the GPU racks total 4 × 30.8 + 2 × 20.6 = 164.4 kW — the same
as 5 × 30.8 + 10.4 = 164.4 kW, because rack power depends only on the node count plus 0.2 kW per
rack; IT maximum is 181.9 kW either way.

**6. First binding resource if the model doubles (26 B params).** Per-GPU state doubles to 52 GB at
TP 8, PP 1 — still under 72 GB but leaving 20 GB for activations, so **GPU memory** binds first
(forcing PP > 1 or sharded optimizer state); the checkpoint doubles to 364 GB = 9.1 s, still small.
Accept "memory" with this reasoning; accept "storage write" only if the student argues from frequent
checkpointing with numbers.

*Marking (20 pts):* each of items 1–5 3 pts; interpretation 5 pts. *Common mistakes:* using GiB for
HBM; forgetting the 10 % reserve; dividing training state by DP (DP replicates state without
sharded optimizers).

---

## Exercise 2.4 — Lab 2 answer key

### Planted flaws in `lab/data/` (seed 2) and why each was chosen

| Code | Item | What is wrong | Why it is planted / consequence |
|---|---|---|---|
| `DUPLICATE_RACK` | rack-05 | Row duplicated in `rack_plan.csv` | Spreadsheet copy-paste is the most common BOM error; the sheet totals 36 nodes, so procurement would order 4 extra servers and Facilities would plan a ninth GPU rack's power. |
| `POWER_BASIS` | rack-03 | Planned at sustained power, 34.2 kW | Planning at sustained power under-sizes circuits by (41.0 − 34.2) ÷ 41.0 = 16.6 %; breakers trip during burn-in or synchronised peaks. |
| `CIRCUIT_OVERLOAD` | rack-07 | One circuit per side | 41.0 × 1.10 = 45.1 kW needed vs 32.78 kW per side: the rack cannot survive loss of either feed at load. |
| `FLOOR_LOAD` | rack-08 | 1,000 kg estimate | 1,000 ÷ 0.72 = 1,389 kg/m² > 1,200; real cause is often an extra component (in-rack CDU, ballast) added late. |
| `PORT_OVERCOMMIT` | orion-be-spine-2 | 72 downlinks on a 64-port switch | Mis-summed port plan; the cable plan cannot be built. |
| `OVERSUBSCRIBED_LEAF` | orion-be-leaf-r5 | 24 uplinks instead of 32 | 32 : 24 = 1.33 : 1 on rail 5; collectives run at the slowest rail's pace. |
| `UPLINK_MISMATCH` | fabric | Σ leaf uplinks 248 vs Σ spine downlinks 264 | The two previous flaws make the sheet internally inconsistent; this check catches mistakes even when the individual switch rows look plausible. |
| `UNIT_MISMATCH` | storage.aggregate_read | "160 Gb/s" where 8 × 20 GB/s = 160 GB/s | Bits-for-bytes is the classic factor-of-8 error; taken literally, 20 GB/s would make the storage look 8× too small (or, the other way round, a vendor quoting Gb/s looks 8× better). |
| `PSU_FEED_LOSS` | HX8 | 3 × 3.0 kW = 9.0 kW per feed < node maximum | Node cannot ride through a feed loss at full power; needs a feed-loss power policy (Section 2.10 Step 5). |

There are exactly **9** findings and no others. Non-findings learners sometimes report: the 13U of
empty space (by design); storage racks on 32 A circuits (17.48 kW usable vs 9.0 × 1.1 = 9.9 kW
needed ✓); network racks on one 60 A circuit per side (32.78 vs 16.0 × 1.1 = 17.6 kW ✓);
`aggregate_write` 80 GB/s (= 8 × 10 ✓). The `PSU_FEED_LOSS` rule compares per-feed PSU DC output
(3 × 3.0 = 9.0 kW) with the node's DC peak (`node_dc_peak_kw` = 9.59 kW), not with the 10.2 kW AC
input: PSU ratings are DC. Deduct marks for an AC-vs-DC comparison even though the verdict matches.

### Expected computed values

BOM: 32 nodes, 256 GPUs, 8 GPU racks, 256U of nodes (32U per rack), 8 leaves + 4 spines = 12 backend
switches, 256 host links + 256 leaf–spine links = 512, 768 switch ports, 1,024 single-port
transceivers or 384 twin-port switch modules, 64 frontend ports, 2 frontend leaves, 32 GPU-rack PDUs,
86 OOB ports, 13 racks.

Power/cooling: rack 41.0 kW max, 45.1 kW design, 43.13 kVA per circuit, 65.55 kW usable per side,
20.45 kW headroom; liquid 30.75 kW, air 10.25 kW; 0.7885 kg/s = 46.38 L/min; 1,199 CFM residual,
4,798 CFM all-air; CDU 246 kW = 82 %; cluster 382.0 kW IT max, 477.5 kW facility; sustained 327.6 kW;
3,587.2 MWh/yr; $286,978/yr.

Capacity: 20,480 GB HBM; 1.12 TB training state, 35.0 GB per GPU; 102.4 Tb/s injection; 51.2 Tb/s
bisection per direction; leaf ratio 1.0; storage 160 GB/s read, 80 GB/s write, 0.625 GB/s read per
GPU; checkpoint 980 GB, ≥ 12.25 s; 1,906,176 allocated GPU-hours.

### SPOFs (15) and model answers

| SPOF | Services lost | Mitigation | Fix/accept |
|---|---|---|---|
| `cdu-1` | training, inference | Second CDU (N+1) on a shared row manifold, or split the row across two CDUs | Fix |
| `pdu-net-A` | training, inference | Re-cord both frontend leaves across `pdu-net-A` and `pdu-net-B` | Fix (cheapest high-impact fix) |
| `busway-A`, `ups-A` | training, inference | Same root cause as `pdu-net-A`: the frontend leaves' only power path runs through feed A. Fixing the cording removes all three. | Fix |
| `mds-1` | training | Active/standby metadata servers per the file system's HA design | Fix |
| `slurmctld-1` | training | Configure a backup controller (Slurm supports a backup `SlurmctldHost`); running jobs usually continue during a controller outage | Fix |
| `oob-sw-1` | management | Second independent OOB aggregation path; serial console fallback | Accept short-term with a spare on site; fix at next expansion |
| `orion-be-leaf-r0` … `orion-be-leaf-r7` | training | Inherent to rail-optimized design; on-site spare, pre-staged config, replacement runbook; job restarts after replacement | Accept, documented |

The key teaching point is that **`ups-A` and `busway-A` are SPOFs in a 2N electrical design** solely
because two dual-homed switches are both single-corded to the same feed. Learners who list only the
"singleton" groups (CDU, MDS, scheduler, OOB) have not run the propagation correctly. Non-SPOFs worth
discussing: any single spine (3 of 4 suffice in the model, at reduced bisection), any single chiller
(2 of 3), any GPU-rack PDU (2N), any single node (28 of 32 retained), `busway-B`/`ups-B` (everything
on B also has A, except nothing that depends *only* on B).

*Marking (100, per lab/README.md):* Task 1 30 (2 pts per finding detected = 18 via `check.py`, 12 for
consequence sentences); Task 2 15 (9 checker, 6 table and optics assumptions); Task 3 20 (12 checker, 8
assumptions register); Task 4 15 (9 checker, 6 interpretation); Task 5 20 (12 checker, 8 diagram and
decisions).

---

## Exercise 2.5 — VEGA SPOFs

| SPOF | Impact | Mitigation | Fix/accept, reason |
|---|---|---|---|
| Network rack single PDU on feed A | Feed-A loss or PDU fault takes down both frontend leaves, border router, hypervisor → whole service | Second PDU on feed B; dual-cord every device | Fix: cheap, high impact |
| Single border router | All ingress/egress lost | Second router with ECMP/BGP to upstream | Fix |
| Single hardware load balancer | Inference unreachable | Active/standby pair or software LB on multiple nodes | Fix |
| Single NFS server for weights | New pods cannot start; restarts during an outage fail | Replicate weights to object storage plus local NVMe cache on nodes | Fix |
| Kubernetes control plane: 3 VMs on one host | Host failure loses quorum → no scheduling, no self-healing | Spread control-plane nodes across failure domains (different racks/power) | Fix — the classic *placement* SPOF |
| DNS/NTP VM on the same host | Name resolution and time lost; TLS and logs degrade | At least two resolvers and time sources on separate hosts | Fix |
| Single OOB switch | Remote management lost | Second switch or console server fallback | Accept with on-site spare |
| One sidecar L2A CDU per GPU rack | Rack-level outage (4 nodes, 50 % of capacity) | N+1 pump/fan modules inside the CDU if available; spare capacity in the other rack | Accept if inference SLO tolerates 50 % capacity for repair time; otherwise fix |

**Task 4 (placement SPOF):** the Kubernetes control plane — three replicas is the right *count*, but
co-locating them on one hypervisor (in one rack, on one PDU) makes their count irrelevant. Also accept
the network rack's single-feed PDU.

*Marking (15 pts):* ≥ 5 correct SPOFs with impact 6; diagram 3; mitigations with reasons 4; task 4 2.
*Common mistakes:* listing the MLAG leaf pair as a SPOF (it is redundant — but its shared PDU is not);
proposing mitigations without saying what they cost.

---

## Exercise 2.6 — DLC node power and rack density

1. DC load 9,590 − 1,000 = 8,590 W; AC = 8,590 ÷ 0.94 = **9,138 W ≈ 9.14 kW**. A 4-node rack:
   4 × 9.138 + 0.2 = **36.75 kW** vs 41.0 kW, saving **4.25 kW (10.4 %)** per rack.
2. 5 nodes: 5 × 9.138 + 0.2 = 45.89 kW; × 1.10 = **50.48 kW** ≤ 65.55 kW ✓ (15.07 kW headroom).
3. Liquid 0.80 × 45.89 = **36.71 kW**; ṁ = 36.71 ÷ (3.90 × 10) = 0.9413 kg/s; ÷ 1.02 × 60 =
   **55.4 L/min**. Air 9.18 kW: 9.18 ÷ (1.006 × 1.20 × 15) = 0.507 m³/s = **1,074 CFM**. CDU: 8 ×
   36.71 = **293.7 kW = 97.9 %** of 300 kW ✗ (no operating margin, no redundancy).
4. Mass 5 × 135 + 280 = 955 kg; 955 ÷ 0.72 = **1,326 kg/m²** > 1,200 ✗.
5. Feed loss: 3 × 3.0 = 9.0 kW ≥ 8.59 kW DC peak ✓ — the fan savings remove the feed-loss problem
   (4.8 % margin before PSU derating).
6. **Stay at 4 nodes per rack**: the floor (and the CDU) bind before electrical capacity. The DLC
   variant's real benefits at 4 nodes are lower power (−10.4 %), feed-loss ride-through, and CDU load
   falling to 8 × 0.80 × 36.75 = 235.2 kW (78.4 %).

| Check (5 nodes) | Value | Limit | Verdict |
|---|---|---|---|
| Electrical per side | 50.48 kW | 65.55 kW | ✓ |
| Coolant per rack | 55.4 L/min | Manifold design (ask) | Confirm |
| CDU | 293.7 kW | 300 kW | ✗ |
| Floor | 1,326 kg/m² | 1,200 | ✗ |
| Feed loss | 8.59 kW DC | 9.0 kW | ✓ |

*Marking (15 pts):* 2 pts per item 1–5, 5 pts for verdict with binding constraint. *Common mistake:*
applying the 94 % efficiency to the 1,000 W saving twice or applying the capture fraction to DC load.

---

## Exercise 2.7 — The maintenance-window slowdown

1. Slowdown 22.6 ÷ 17.4 = 1.299 → **+29.9 %**. Clocks on rack-02/03 fell to 1,050 ÷ 1,755 = 0.598 of
   normal (−40 %). The job is synchronous, so all 256 GPUs wait for the 64 braking GPUs every step;
   the slowdown is smaller than the clock loss because communication and other non-compute time do not
   scale with SM clock.
2. Ranked hypotheses: **H1 (high)** — PSU cording or PSU population differs on rack-02/03 nodes so that
   feed A alone cannot supply them (the per-rack feed-A power of ≈ 24 kW vs ≈ 34 kW elsewhere and the
   *power brake* reason point here); **H2 (medium)** — failed or missing PSUs on those nodes, so fewer
   than three remain on feed A; **H3 (medium)** — different BMC/firmware power policy on a delivery
   batch (e.g., a configured feed-loss limit) on those nodes; **H4 (low)** — PDU fault on rack-02/03
   feed A limiting current (no breaker events and other racks fine on the same feed make it unlikely).
   Reject "thermal": no thermal reasons active and power fell.
3. Evidence plan (read-only):
   - `ipmitool -I lanplus -H <bmc> -U <user> -E sdr type "Power Supply"` and Redfish
     `/redfish/v1/Chassis/<id>/PowerSubsystem/PowerSupplies` (or the deprecated `/Power` resource on older
     BMCs) on one node per rack → PSU presence, health,
     and per-PSU input power. H2 confirmed if PSUs are absent/failed.
   - PDU outlet map and per-outlet power from the rack PDUs (A and B) → which node PSUs are on which
     feed. H1 confirmed if rack-02/03 nodes show 2 outlets on A and 4 on B.
   - BMC power-limit settings: `ipmitool dcmi power get_limit`; firmware inventory via Redfish
     `UpdateService/FirmwareInventory` → H3.
   - PDU event log and per-phase current for rack-02/03 feed A → H4.
4. With 2 PSUs on feed A: 2 × 3.0 = **6.0 kW** available vs a sustained DC need of about
   8.5 kW × 0.94 = **7.99 kW** → the platform asserts power brake. Other racks: 3 × 3.0 = 9.0 kW ≥
   7.99 kW → no brake at sustained load (they would still brake at the 9.59 kW peak). Consistency
   check: braked nodes are held at or below the 6.0 kW of DC the two feed-A PSUs deliver (8 GPUs ×
   330 W ≈ 2.6 kW plus non-GPU load). At the AC input that is ≤ 6.0 ÷ 0.94 ≈ 6.4 kW per node, or
   ≤ 25.5 kW per rack, consistent with the 24.1 kW measured on feed A (the brake undershoots the PSU
   limit). Compare DC with DC and AC with AC; PSU ratings are DC output. **Fix:** drain the 8 nodes (`scontrol update NodeName=orion-n[05-12] State=DRAIN
   Reason="PSU cording 2A/4B"`), have Fleet re-cord to 3/3 under the rack's change procedure, return
   to service. **Validate without a maintenance window:** PDU per-outlet readings show each node's load
   split ≈ 50/50 across A and B; `sdr type "Power Supply"` shows six healthy PSUs; the outlet map in
   the inventory matches the standard. A true single-feed test only in a Facilities-run commissioning
   window.
5. Acceptance-checklist line: "PSU cording verified 3 A / 3 B against PDU outlet map; per-feed load
   share 45–55 % at idle and under burn-in; recorded in inventory."

*Marking (20 pts):* arithmetic 3; hypotheses ranked with reasons 5; evidence plan with real commands 5;
root cause arithmetic 4; fix/validation/checklist 3. *Common mistakes:* blaming the UPS maintenance
itself (other racks on the same feed were fine); proposing to toggle breakers to test.

---

## Exercise 2.8 — Power-cap sweep (L2)

No single numeric answer; grade method. Expected shape: throughput per watt rises as the limit falls
from maximum, peaks somewhere in the middle of the range for compute-bound GEMM (often with a
throughput loss far smaller than the power saving), then falls as clocks drop steeply. Memory-bound
workloads show a flatter throughput curve because HBM bandwidth, not SM clock, limits them, so caps
cost them little. For question 3, a good answer picks the highest limit that satisfies the feed-loss
budget (570 W for ORION per Section 2.10), reads the measured throughput at that limit, and converts
it into a **modeled** W-TRAIN step-time impact, labelled `[MODELED from MEASURED single-GPU data]`, and
notes that collectives and non-compute time dilute the effect.

*Marking (20 pts):* manifest and benchmark discipline (warm-up, ≥ 5 reps, median and spread) 8; plots
4; interpretation of compute- vs memory-bound 4; correctly labelled extrapolation 4. Deduct heavily if
default limits were not restored or the server was shared.

---

## Exercise 2.9 — Rack-X power and heat-removal budget (model answer)

1. **One-line concept:** utility (MV) + generators → transfer switchgear → transformers A/B → UPS A /
   UPS B (2N, or distributed redundant at hall level) → busway A/B with tap-offs → rack power-shelf
   inputs A/B → power shelves (N+N or N+1 PSUs within the shelf) → DC busbar → compute trays. Redundancy
   labelled at each stage.
2. **Electrical:** per-side design load 120 × 1.15 = **138 kW**. 125 A circuit: √3 × 415 × 125 =
   89.85 kVA; × 0.80 × 0.95 = **68.29 kW**; two circuits = 136.6 kW ✗ (1.4 kW short — a trap);
   **three circuits = 204.9 kW** ✓ (66.9 kW headroom). 160 A: 115.0 kVA × 0.76 = **87.41 kW**; two
   circuits = **174.8 kW** ✓ (36.8 kW headroom, 21 %). Either valid choice is accepted with
   arithmetic; prefer fewer, larger circuits if the power shelves accept them.
3. **Transients:** 8 racks × 120 kW × 0.30 = **288 kW** step within 50 ms. Confirm against tap-off and
   busway breaker trip curves, UPS step-load and mode-transfer behaviour, generator step acceptance,
   and any utility ramp-rate obligation; consider rack batteries or power smoothing in the platform.
4. **Thermal block diagram:** FWS (towers/dry coolers/chillers) → CDU heat exchanger (redundant pumps,
   filters, sensors) → TCS supply manifold → rack manifolds with dripless QDs → cold plates → TCS
   return; residual heat to room air/RDHx; leak sensors and isolation valves marked.
5. **Heat removal:** liquid 0.85 × 120 = **102 kW**, air **18 kW** per rack. ṁ = 102 ÷ (3.90 × 8) =
   3.269 kg/s; ÷ 1.02 = 3.205 L/s = **192.3 L/min** per rack; row 8 × 192.3 = **1,538 L/min**
   (816 kW). Air 18 ÷ (1.006 × 1.20 × 15) = 0.994 m³/s = **2,106 CFM** per rack. CDUs: 816 kW needs one
   1 MW unit; N+1 → **2 CDUs**, each at 40.8 % normally and **81.6 %** with one failed.
6. **Floor:** 1,400 ÷ 0.72 = **1,944 kg/m²** > 1,200 ✗. Ask the structural engineer for: the slab or
   raised-floor rating basis (footprint vs. distributed), concentrated and rolling loads on the
   transport path, whether spreader plates or slab-on-grade placement are required, and seismic
   anchoring.
7. **Safe operating envelope (example):**

   | Parameter | Limit | Action when exceeded |
   |---|---|---|
   | Per-side load | ≤ 80 % of usable (e.g., 139.8 kW with 160 A × 2) sustained | Stop new placement; review caps |
   | TCS supply | ≤ 30 °C design; alarm at +3 K | Facilities; consider workload power cap |
   | Flow per rack | ≥ 85 % of 192.3 = 163.5 L/min | Inspect strainer/QDs; drain if rising temps |
   | Rack ΔT at load | ≤ 10 K (design 8 K) | As low flow |
   | CDU utilization | ≤ 85 % with N+1 lost | Defer load additions |
   | Inlet air | Within ASHRAE recommended envelope for the equipment class | Facilities |
   | Leak alarm | Any | Isolation procedure; drain affected trays |

8. **Assumptions register:** each of the 14 given values (IT load, margin, feeds, voltage, derate, PF,
   capture fraction, coolant cp/ρ, ΔT, supply temp, air ΔT, CDU size, rack mass, floor rating) with
   source ("exercise assumption — confirm with vendor reference design dated YYYY-MM / MEP engineer /
   coolant datasheet / structural engineer") and consequence if wrong (e.g., capture fraction 0.80
   instead of 0.85 adds 6 kW per rack to air, 48 kW to the room).
9. **Handoff checklist (≥ 12 lines with owner):** per-side max kW and transient profile (IT → MEP);
   circuit count, rating, voltage, phase plan (MEP → IT); power-shelf input connector type (IT); PDU or
   shelf telemetry protocol and OOB addressing (IT/MEP); heat to liquid and air per rack (IT); TCS
   supply temperature, flow, pressure available per rack (MEP); coolant type, chemistry spec, filtration
   mesh (MEP, per cold-plate vendor); QD type and manifold connection (both); leak-detection zones,
   alarm routing, automatic isolation behaviour (MEP → IT monitoring); floor rating, transport path,
   anchoring (MEP/structural); commissioning plan including workload burn-in (both); emergency
   power-down and leak response ownership (both, signed); maintenance windows and feed-loss power policy
   (both).

*Marking (25 pts):* 2 pts each for artefacts 1–9 (18), arithmetic correctness 5, labelling and
assumption discipline 2. *Common mistakes:* using 2 × 125 A circuits (136.6 < 138); using sum of both
feeds; omitting the transient check; presenting 120 kW as a standard rack power.

---

## Exercise 2.10 — ORION to 512 GPUs (model answer outline)

Constraints: 32 extra nodes, ≤ 6 extra racks, ≤ 800 kW IT, one extra 300 kW CDU, no structural work.

- **Air-cooled HX8 at 4 per rack** needs 8 more GPU racks ✗ (rack limit). **DLC at 5 per rack** fails
  the floor (Exercise 2.6) ✗. **DLC at 4 per rack** still needs 8 racks ✗. So the space limit forces
  either reclaiming support-rack positions (e.g., consolidating storage/management) or negotiating more
  rack positions — a strong answer says so explicitly rather than forcing a design that violates the
  floor rating.
- A defensible option: 64 DLC nodes in 16 GPU racks of 4 (36.75 kW each = 588 kW), reclaiming 2 rack
  positions by moving management into the network racks and consolidating storage into one rack
  (16 GPU + 2 network + 1 storage = 19 racks = 13 + 6); CDU: liquid 16 × 0.80 × 36.75 = 470.4 kW
  across two 300 kW CDUs (78.4 % each, **no N+1**) — state that N+1 needs a third CDU and is the next
  request to Facilities. Total IT ≈ 588 + network/storage/management (grows with the fabric) — show it
  stays under 800 kW.
- **Fabric:** 64 nodes × 8 rails = 512 host links; rail leaves of 64 ports at 1:1 serve 32 nodes each,
  so 16 leaves (2 per rail) with 32 uplinks each = 512 leaf uplinks; 8 spines of 64 ports (each leaf 4
  uplinks to each spine) — 24 backend switches, 1,024 backend links, 2,048 link ends. Accept a
  different but consistent Clos.
- SPOF removal: re-cord frontend leaves (A/B), second metadata server, backup Slurm controller, N+1
  CDU request, second OOB path.

*Marking (15 pts):* options and criteria 4; arithmetic 5; fabric consistency 3; honesty about
constraints that cannot be met 3.

---

## Exercise 2.11 — Reflection (marking guidance)

1. Good answers name the 10 % transient margin, the 75 % liquid capture fraction, or the 10.2 kW
   node maximum, and propose an L2 measurement (BMC/DCMI and `nvidia-smi` sampling under burn-in) or
   L3 rack/CDU measurement.
2. Either position is acceptable if it quantifies restart cost against the cost of a design without
   a rail SPOF. Reference pricing: a rail-leaf failure stops the job (ORION-256 has no spare rail and
   no spare nodes). The restart costs 256 × 0.25 h = 64 GPU-hours, plus the replacement time at
   256 GPU-hours per hour (e.g. 2 h to swap a leaf = 512 GPU-hours `[ILLUSTRATIVE]`), plus lost work
   since the last checkpoint.
3. Thermal transients, CDU control dynamics, PSU behaviour, breaker trip curves, real coolant
   performance, and workload power profiles.
4. PUE says nothing about IT efficiency (useful work per IT watt), transient behaviour, or how much of
   the facility's capacity is stranded by redundancy and margin.
5. Any cell with a concrete fix (named owner, runbook link, rehearsal date).

Award full marks for specific, evidence-oriented answers; partial for generic ones.
