# Chapter 7 — Exercise Key (INSTRUCTOR ONLY)

All numbers are `[MODELED]` unless marked. Every calculation below was checked twice, by hand and
with the reference implementation `solutions/lab/fabric_lab.py`. Marking guidance follows each
answer; "common mistakes" lists what to look for.

---

## Knowledge checks

### 7.K1
- RFC 3021 (2000) permits /31 on point-to-point links; RFC 6164 (2011) recommends /127 for IPv6
  inter-router links.
- /31: 512 links × 2 = **1,024** addresses. /30: 512 × 4 = **2,048** addresses.
- Operational reason (any one): addresses are computable from link index (address = base + 2·idx), so
  plans can be generated and validated automatically; no network/broadcast addresses to mis-assign;
  each address maps unambiguously to one interface.

*Marking (4 pts):* 1 per RFC, 1 for both counts, 1 for an operational reason. Address conservation
alone earns 0 for the last point. *Common mistake:* counting only 256 fabric links.

### 7.K2
Spines share an ASN so BGP loop prevention rejects any path that has already crossed the spine tier:
a route orion-be-leaf-r0 learned from orion-be-spine-1 and re-advertises to orion-be-spine-2 contains 65100 and is dropped. This
removes valley (spine→leaf→spine) paths and prevents path hunting after withdrawals. Leaves need unique
ASNs because a leaf drops any route whose AS_PATH contains its own ASN: if orion-be-leaf-r6 and orion-be-leaf-r7 both use
65107, each discards the other's prefixes (`65100 65107` contains 65107), so each loses reachability
to the other's prefixes — while every session stays Established.

*Marking (4 pts):* 2 per half. Full marks require naming AS_PATH loop detection as the mechanism.

### 7.K3
Each TCP endpoint advertises an MSS derived from its own MTU (9216 side ≈ 9176 B; 1500 side 1460 B)
and never sends segments larger than its peer's advertised MSS. Both ends therefore send BGP segments
≤ 1460 B, which fit; keepalives are tiny. Data traffic fails: frames from the 9216 side larger than
the 1500 side's maximum frame size are dropped at ingress as oversize/giants (silently, no ICMP); in
the other direction, packets routed out of the 1500-MTU interface that exceed it are dropped by the
egress MTU check (with ICMP "fragmentation needed" if DF is set and ICMP generation is not
rate-limited away). Large frames are lost in both directions, by different mechanisms.

*Marking (4 pts):* 2 for MSS reasoning, 2 for directional loss. *Common mistake:* "BGP packets are
small" without the MSS mechanism (1 pt only — BGP UPDATEs can be up to 4,096 B, or larger with
RFC 8654 extended messages).

### 7.K4
Frame = Ethernet 14 + IPv4 20 + UDP 8 + BTH 12 + RETH 16 + payload 4,096 + ICRC 4 + FCS 4 =
**4,174 B** (IP packet 4,156 B). With netdev MTU 1500, the space left for RDMA payload is about
1500 − 20 − 8 − 12 − 4 = 1,456 B (less with RETH), so the largest IB MTU that fits is **1,024**. ORION
uses a 9000 host MTU so that the device can select the 4,096 path MTU (which needs an IP MTU above
roughly 4,200 B) — fewer packets, fewer per-packet costs — and so that TCP traffic on the same NICs
benefits from jumbo frames.

*Marking (4 pts):* 2 for the sum (accept 4,158 B if the student explicitly excludes RETH and states
it), 1 for 1,024, 1 for the reason. *Common mistake:* claiming RoCE frames are 9 KB.

### 7.K5
Polarization: successive tiers make correlated hash decisions, so a downstream switch only sees a
subset of the hash space and uses a subset of its links. Leaf picks uplink *i = h mod 32*, uplink *i*
goes to `orion-be-spine-(i mod 4 + 1)`, so spine *s* receives only flows with *h mod 32 ≡ s − 1
(mod 4)*, i.e. *h mod 4 = s − 1*. Since 4 divides 8, *h mod 8 ∈ {s − 1, s + 3}*. `orion-be-spine-1`
uses links **k ∈ {0, 4}** of its 8 (spine-2: {1, 5}, etc.) — 25 % of its downstream links.

*Marking (4 pts):* 1 definition, 2 arithmetic, 1 correct set.

### 7.K6
Raw uplink: 31 × 400 = 12,400 Gb/s vs 12,800 → −3.1 %. Other leaves still split rail-0 traffic
equally over 4 spines (orion-be-spine-1 still advertises orion-be-leaf-r0's prefix), so orion-be-spine-1's quarter must fit in 7
links: ingress = 4 × 7 × 400 = 11,200 Gb/s → −12.5 %. Unweighted ECMP cannot shift load away from the
weakened spine.

*Marking (3 pts):* 1 per number, 1 mechanism.

### 7.K7
A gray failure is a partial failure where the component looks up (link state up, control plane
responsive) but does not forward correctly — e.g., unidirectional fiber, corrupting optic, wedged
forwarding pipeline. BFD catches it (end-to-end liveness on the forwarding path). Detection: 300 ms ×
3 = **0.9 s**; BGP hold timer with 3 s / 9 s timers: up to **9 s**.

*Marking (3 pts):* 1 each.

### 7.K8
In a rail-optimized design orion-be-leaf-r*r* connects NIC *r* of *every* node. Losing it removes one of eight
NICs from all 32 nodes simultaneously, breaking every NCCL communicator that uses rail *r*; a 256-GPU
job typically fails and restarts. A top-of-rack leaf serves only its rack, so a failure removes those
servers and leaves other nodes intact.

*Marking (3 pts).* *Common mistake:* "only 1/8 of bandwidth is lost" without the job-level effect.

---

## Worked problems

### 7.W1 (outline-mandated)

**(a) Rail-optimized, 1:1, radix 64.**
- NICs per rail = 48 nodes = 48. Downlinks per 1:1 leaf = 64 × 1/(1 + 1) = 32.
- Leaves per rail = ⌈48 / 32⌉ = **2**; total leaves = 8 × 2 = **16** (24 nodes per leaf).
- Used downlinks = 384 of 16 × 32 = 512 ports (**75 %**); 24 used per leaf.
- Uplinks = 16 × 32 = 512; spines = 512 / 64 = **8**; links per pair = 32 / 8 = **4**; spine ports
  16 × 4 = 64 ✓.
- Ratio as configured 32:32 = **1:1**; as used 24:32 = **0.75:1** (under-subscribed).
- Cables: host 384 + fabric 512 = **896**; transceivers 2 × 896 = **1,792** (before spares).

*Acceptable alternative (full marks if justified):* trim uplinks to 24 per leaf to stay exactly 1:1 on
used ports: uplinks 16 × 24 = 384 → 6 spines × 4 links (16 × 4 = 64 ports ✓); fabric cables 384, total
768, transceivers 1,536; cost: less headroom for growth to 64 nodes.

**(b)** `size_two_tier(384, 64, 64, 1.0)` returns 12 leaves, 8 spines, 4 links per pair, 384 fabric
cables, 768 total, 1,536 transceivers (spines: ⌈384/64⌉ = 6, but 32 is not divisible by 6 or 7, so 8).
It is not rail-aware: it packs 384 endpoints densely into ⌈384/32⌉ = 12 leaves, which cannot be split
evenly into 8 rails (48 NICs per rail = 1.5 leaves). A rail-optimized design needs a whole number of
leaves per rail, hence 16.

**(c) 3:1, rail-optimized.** Down 48 / up 16. Leaves per rail = ⌈48/48⌉ = 1 → **8 leaves**. Uplinks
8 × 16 = 128 → spines = max(2, 128/64) = **2**, links per pair 16/2 = **8**. Cables 384 + 128 = 512;
transceivers 1,024. Cross-leaf capacity per leaf = 16 × 400 = **6.4 Tb/s** vs downlink 48 × 400 =
**19.2 Tb/s** (3:1). Because each rail fits on one leaf, *same-rail* traffic is still non-blocking;
only cross-rail traffic sees 3:1.

**(d)** In (a) each rail spans two leaves, so same-rail traffic between nodes on different leaves of
the rail crosses the spines: ECMP and its low-entropy collisions now sit on the main collective path
(as in ORION-XL), whereas on ORION-256 same-rail traffic is single-hop.

*Marking (12 pts):* (a) 6, (b) 2, (c) 3, (d) 1. *Common mistakes:* 12 leaves for a rail-optimized
design; forgetting both ends of each cable for transceivers; claiming (c) blocks same-rail traffic.

### 7.W2

**(a)** 16 leaves × 8 spines × 4 links, 400 Gb/s (one direction):

| Scenario | Raw uplink (affected leaf) | ECMP-aware ingress | Bisection |
|---|---|---|---|
| Baseline | 32 × 0.4 = 12.8 Tb/s | 8 × 4 × 0.4 = 12.8 Tb/s | 8 spines × min(8×4, 8×4) = 256 links × 0.4 = 102.4 Tb/s |
| One link (leaf L ↔ spine S) down | 31 × 0.4 = 12.4 Tb/s | 8 × 3 × 0.4 = **9.6 Tb/s** | (31 + 7 × 32) × 0.4 = 255 × 0.4 = 102.0 Tb/s |
| One spine down | 28 × 0.4 = 11.2 Tb/s | 7 × 4 × 0.4 = 11.2 Tb/s | 7 × 32 × 0.4 = 89.6 Tb/s |

(For the link-down bisection, the worst split puts leaf L in half A: spine S carries min(7 × 4 + 3, 32)
= 31 links across the cut; the other 7 spines carry 32 each.)

**(b)** ORION-256 (8 links per pair): one link costs 12.5 % of ECMP-aware ingress; ORION-384 (4 per
pair): **25 %**, because losing one of 4 links removes a quarter of that spine's bundle while
unweighted ECMP still sends 1/8 of the traffic to it. Conversely a spine failure costs 12.5 % here vs
25 % in ORION-256. More, narrower spine bundles trade a smaller spine fault domain for a larger
per-link penalty (unless weighted ECMP is used).

**(c)** P(no collision) = 4!/4⁴ = 24/256 = **9.4 %**. Expected links used = 4 × (1 − (3/4)⁴) =
4 × (1 − 0.3164) = **2.73**.

*Marking (12 pts):* (a) 6 (2 per row), (b) 3, (c) 3. Accept bisection omitted for the link-down row
only if the student explains why it barely changes.

---

## 7.L Hands-on lab — reference results and planted faults

Reference implementation: `solutions/lab/fabric_lab.py` (19/19 checks). `python fabric_lab.py` prints:

```text
[blocker] DUP_P2P        10.101.3.72/31   /31 used on 2 links: F-r4-s3-k4, F-r4-s3-k5
[blocker] ASN_COLLISION  65107            ASN shared by orion-be-leaf-r6, orion-be-leaf-r7
[blocker] MTU_MISMATCH   F-r3-s2-k6       orion-be-leaf-r3 9216 vs orion-be-spine-2 1500
[major  ] ECMP_MAXPATHS  orion-be-leaf-r2          max-paths 4 < 32 equal-cost paths
[blocker] BAD_ORIGIN     orion-be-leaf-r1 10.100.6.0/24   prefix owned by orion-be-leaf-r6
[major  ] ASYM_ADVERT    orion-be-leaf-r5 10.100.5.0/24   not advertised to orion-be-spine-4
```

### Planted faults (instructor only)

| # | Fault | Where | Why it is realistic | Operational consequence on ORION | Capacity consequence `[MODELED]` |
|---|---|---|---|---|---|
| 1 | Duplicate /31 | F-r4-s3-k5 reuses k4's `10.101.3.72/31` | Copy-paste in a spreadsheet plan | Second interface fails to configure or both links share a subnet: ARP/BGP confusion, one session down or flapping | ≈ one link down for orion-be-leaf-r4: uplink 12.4, ingress 4 × 7 × 0.4 = 11.2 Tb/s |
| 2 | ASN collision | orion-be-leaf-r7 = 65107 (should be 65108) | Off-by-one in a template | orion-be-leaf-r6 and orion-be-leaf-r7 drop each other's routes (AS loop); rail 6 ↔ rail 7 cross-rail unreachable; sessions Established | Cross-rail capacity between rails 6 and 7: 0 |
| 3 | MTU mismatch | F-r3-s2-k6, spine side 1500 | Port reverted to default after RMA | RoCE frames (≤ 4,174 B) dropped on that link: flows hashed to it hit RDMA retry-exceeded; BGP unaffected | Worse than a down link: traffic is still sent and lost. Once drained: as one link down for orion-be-leaf-r3 (11.2 Tb/s ingress) |
| 4 | ECMP max-paths too small | orion-be-leaf-r2 `ecmp_max_paths` 4 | Platform default or old template | Cross-rail traffic *from* rail 2 uses 4 of 32 uplinks; ingress unaffected → asymmetric | orion-be-leaf-r2 egress 4 × 0.4 = 1.6 Tb/s (12.5 % of 12.8) |
| 5 | Bogus origin | orion-be-leaf-r1 advertises 10.100.6.0/24 | Template copy-paste | Spines choosing orion-be-leaf-r1's path deliver rail-6 traffic to orion-be-leaf-r1, which drops it | If 2 of 4 spines prefer it: ≈ 50 % of cross-rail flows to rail 6 lost (tie-break dependent) |
| 6 | Asymmetric advertisement | orion-be-leaf-r5 does not send 10.100.5.0/24 to orion-be-spine-4 | Per-neighbor policy typo | Traffic to rail 5 uses 3 spines, traffic from rail 5 uses 4 | Ingress to orion-be-leaf-r5 3 × 8 × 0.4 = 9.6 Tb/s (−25 %) |

**False-positive traps (must NOT be reported):** all four spines share AS 65100 (correct per RFC 7938);
host links are 9216 (switch) / 9000 (host) by design; loopbacks are advertised by every leaf to every
spine; spines have `ecmp_max_paths` 64 ≥ 8.

**Severity guidance:** accept blocker vs major differences if justified. Reasonable default: anything
that silently drops or misroutes traffic (1, 2, 3, 5) is a blocker; capacity-only degradations (4, 6)
are major.

### Marking notes for Task 6 (design note)
Look for: diagram with 8 rails/leaves, 4 spines, "×8" parallel links, ASNs and loopbacks; routing
policy that includes inbound prefix filters, `maximum-paths` ≥ 32 at leaves and ≥ 8 at spines, BFD
300 ms × 3 (or justified alternative), drain procedure (prepend or GRACEFUL_SHUTDOWN); failure table
consistent with Table 7.8 / 7.O2 below; every number labelled `[MODELED]`.

### Stretch: QOS_MISMATCH rule (model answer)
Needed intent fields per device/port: `dscp_trust` (host-facing ports), `dscp_to_tc` map,
`lossless_priorities`, `pfc_enabled_priorities`, `ecn_enabled_tcs`. Rule: every switch in the backend
has identical `dscp_to_tc` and lossless/PFC priority sets; every host-facing port trusts DSCP; PFC is
enabled exactly on the lossless priority (3) on every fabric and host port. Test table: (1) all
consistent → no finding; (2) one leaf maps DSCP 26 → TC 0 → finding; (3) one spine missing PFC on
priority 3 → finding; (4) host port untrusted → finding; (5) PFC enabled on an extra priority →
finding (warn: pause-storm exposure, Chapter 9).

---

## 7.T Troubleshooting case (outline-mandated)

**(a) Evidence checklist**

| Evidence (item) | MTU mismatch predicts | Asymmetric routing predicts | Incorrect advertisement predicts | Pack shows |
|---|---|---|---|---|
| Size dependence (1, 3) | Large fails, small works | Size-independent | Size-independent | **Size-independent** (1472/default and 8972; 1400 and 8948 MSS fail alike) |
| Flow dependence (2, 3) | 1/N of flows | Flows crossing a stateful/uRPF device | Fraction set by how many spines prefer the bogus path | **31/64 ≈ 50 %**, varies by source |
| Prefix dependence (1, 2) | Any destination behind the bad link | Any | Only the affected prefix | **Only rail-6 destinations** |
| Interface counters (5) | Giants on one port | Clean | Clean | **Clean; MTUs match intent** |
| Path trace (6) | Normal path | Forward ≠ reverse via stateful device | Ends at the wrong leaf | **Ends at orion-be-leaf-r1** (10.101.1.17) |
| BGP view (4) | Normal | Normal | Unexpected origin AS | **Origin 65102 (orion-be-leaf-r1) for rail 6's /24** |
| Change history | MTU/RMA | ACL/uRPF/policy | Config push on originator | **Template push to orion-be-leaf-r1 at 14:05** |

**(b) Ranking:** (1) incorrect advertisement — every discriminator matches; (2) asymmetric routing —
no stateful device or strict uRPF on the backend, and it would not be prefix-specific; (3) MTU
mismatch — refuted by size independence and clean counters. **Root cause:** the template push made
orion-be-leaf-r1 originate 10.100.6.0/24. Spines receive two equal-length AS_PATHs (`65102` and `65107`);
without multipath relax (item 8) they install only the best one. All earlier best-path steps tie
(same local preference, AS_PATH length 1, origin, MED), so the eBGP tie-breakers decide. By default an
eBGP speaker keeps the **oldest** of otherwise-equal external paths (RFC 5004 behaviour), so spines 2
and 4 keep orion-be-leaf-r6's long-standing route. Spines 1 and 3 carry template drift —
`bgp bestpath compare-routerid` (item 8) — which skips the oldest-path rule and prefers the lower router
ID: 10.255.0.12 (orion-be-leaf-r1) < 10.255.0.17 (orion-be-leaf-r6). So exactly those two spines deliver
rail-6 traffic to orion-be-leaf-r1, which drops it. (Without item 8, a student cannot explain the 2/2
split: a uniform router-ID rule would send all four spines to leaf-r1, a uniform oldest-path rule
none.) Rail-1 sources fail 100 % (orion-be-leaf-r1 prefers its own locally originated route).

**(c)** Each source leaf spreads rail-6 traffic over 32 uplinks, 16 of which go to spines 1 and 3:
16/32 = 50 % of flows fail; 31/64 is consistent (binomial σ = √(64 × 0.5 × 0.5) = 4). A ping is one
flow: rail-2 and rail-5 pings happened to hash to spine 1 or 3, the rail-3 ping to spine 2 or 4. It is
hash luck, not a rail property; a multi-flow sweep from rail 3 would also show ≈ 50 %.

**(d)** Forward/reverse path differences are normal in an ECMP fabric and harmless without stateful
devices or strict uRPF, neither of which exists on ORION's backend. Asymmetry cannot explain why only
rail-6 destinations fail, why the trace terminates at orion-be-leaf-r1, or the extra origin AS in the BGP table.

**(e) Fix:** change request; fastest safe mitigation is an inbound prefix filter on the spines for the
orion-be-leaf-r1 sessions (accept only 10.100.1.0/24 and 10.255.0.12/32), then revert the template on orion-be-leaf-r1.
**Validate:** every spine shows a single origin (65107) with 8 paths for 10.100.6.0/24; every leaf shows
32 next hops; a 256-flow sweep from every rail to rail 6 with 0 failures; NCCL cross-rail benchmark
back to baseline over ≥ 5 runs (median and spread). **Prevent:** (1) per-leaf inbound prefix filters on
spines as standing policy; (2) the lab's `BAD_ORIGIN` rule in the change pipeline before any push;
(3) template unit tests that render each leaf and diff its originated prefixes against ownership;
(4) remove the `compare-routerid` drift so all spines apply the same best-path policy.

*Marking (20 pts):* checklist 6, ranking/root cause 5, (c) 3, (d) 2, (e) 4. Full credit for the root cause requires explaining the 2-of-4 spine split from item 8 (router-ID comparison on spines 1 and 3 vs the default oldest-path rule on 2 and 4); "router ID decides" alone earns 3 of 5. *Common mistakes:*
blaming MTU because of the 8972-byte ping (it also fails at default size); treating the rail-3 success
as meaningful; proposing to "clear BGP" on production spines without a filter.

---

## 7.D Design challenge

| Metric (ORION-256, 400G links) | A: 4 spines × 8 links, per-link eBGP | B: 8 spines × 4 links, per-link eBGP | C: 4 spines × LAG of 8, eBGP per LAG |
|---|---|---|---|
| ECMP-aware ingress, one link down | 4 × 7 × 0.4 = **11.2 Tb/s** (−12.5 %) | 8 × 3 × 0.4 = **9.6 Tb/s** (−25 %) | LAG to that spine at 7/8; BGP still splits 4 ways: 4 × 7 × 0.4 = **11.2 Tb/s** (unless link-bandwidth/UCMP) |
| ECMP-aware ingress, one spine down | 3 × 8 × 0.4 = **9.6 Tb/s** (−25 %) | 7 × 4 × 0.4 = **11.2 Tb/s** (−12.5 %) | **9.6 Tb/s** |
| Bisection, one spine down (baseline 51.2) | 3 × 32 × 0.4 = **38.4 Tb/s** | 7 × 16 × 0.4 = **44.8 Tb/s** | **38.4 Tb/s** |
| eBGP sessions | 8 × 32 = 256 | 8 × 8 × 4 = 256 | 8 × 4 = 32 |
| BFD sessions | 256 | 256 | 32 (+ 256 micro-BFD member sessions, RFC 7130) |
| Spines / spine ports used | 4 / 64 each (256) | 8 / 32 each (256; half of each 64-port spine idle) | 4 / 64 each |
| Leaf ECMP width | 32 | 32 | 4 (then LAG member hash: two-stage) |

(Option B bisection with a spine down: worst 4/4 split, each of 7 remaining spines carries
min(4 × 4, 4 × 4) = 16 links → 7 × 16 × 0.4 = 44.8 Tb/s.)

**Model recommendation (optics-failure-dominated risk):** A (or C). Link failures are the frequent
event, and A loses 12.5 % of ingress per affected leaf vs 25 % for B; A also uses spine ports fully.
C matches A's capacity with 8× fewer BGP sessions but adds two-stage hashing and LAG min-links
semantics to reason about. **Assumption that flips it:** if spine drains for OS upgrades or spine
faults dominate (every spine upgrade is a planned "spine down"), B halves the per-event penalty and is
preferable — at the cost of 4 extra spine switches. Weighted ECMP (link-bandwidth) narrows the gap for
all options.

*Marking (15 pts):* table 8 (≥ 6 cells correct per column), recommendation 4, flipping assumption 3.

---

## Reflection

**7.R1** (any three): physical-layer faults — CRC/FEC errors, dirty optics (evidence: interface
error counters, DOM, Chapter 10); running-state drift — device config differs from intent (config
collection and diff, Chapter 20); FIB/hardware programming faults — route in RIB but not in ASIC
(hardware table dumps, data-plane probes); congestion and PFC/ECN behaviour (queue and pause
telemetry, Chapter 9); NIC/host misconfiguration (host inventory, Chapter 3/8).

**7.R2** Better: weighted/UCMP or adaptive routing steers load away from weak bundles; real demand is
not uniform, so a weakened leaf may never need full ingress. Worse: hash collisions and polarization
concentrate low-entropy flows; incast and congestion control dynamics reduce goodput below link
capacity; PFC pauses spread congestion.

**7.R3** Rule: "A single successful probe proves one ECMP path. Before ruling out a path-dependent
fault, sweep ≥ 4N flows varying the source port (N = ECMP width) at full size." Reason: switches hash
each flow to one member; ICMP has no ports, so one ping is one path.

**7.R4** Examples: `[MODELED]` 11.2 Tb/s ECMP-aware ingress (formula; upgrade by measuring per-uplink
throughput under an all-to-rail-0 load on a lab fabric); `[SIMULATED]` 49.9 % / 40.9 % most-loaded-link
distribution (Monte Carlo; upgrade by counting per-link flows with real NIC source-port selection on a
lab fabric); `[ILLUSTRATIVE]` BFD 0.9 s / sub-second convergence or the incident's 55 s checkpoint
baseline (upgrade by timed failover runs ≥ 5 with a manifest).

*Marking (R1–R4, 8 pts):* 2 each.

---

## 7.O2 BGP/ECMP routing plan and failure behaviour (outline-mandated) — model answer

**Plan:** spines AS 65100, leaves 65101–65108; eBGP per fabric link; leaves originate 10.100.r.0/24
and loopback; spines originate loopbacks; spines accept from orion-be-leaf-r*r* only 10.100.r.0/24 and its /32
(inbound filters); leaves accept only 10.100.0.0/16 le 24 and 10.255.0.0/24 le 32 from spines;
`maximum-paths` 64 everywhere (≥ 32 needed at leaves, ≥ 8 at spines); BFD 300 ms × 3; BGP timers
3 s / 9 s; advertisement interval 0; resilient hashing on; drain by AS_PATH prepend or
GRACEFUL_SHUTDOWN (RFC 8326) before planned work.

| Failure | Detection & time `[ILLUSTRATIVE]` | Routes withdrawn | ECMP width at an unaffected leaf (to a remote rail) | Capacity `[MODELED]` | Workload impact |
|---|---|---|---|---|---|
| One orion-be-leaf-r0↔orion-be-spine-1 link | Loss of signal, ms (BFD 0.9 s if gray) | Only that session's paths (orion-be-leaf-r0: 32 → 31; orion-be-spine-1: 8 → 7 to orion-be-leaf-r0) | 32 (unchanged) | orion-be-leaf-r0 raw 12.4, ECMP-aware ingress 11.2 Tb/s | Cross-rail traffic to rail 0 ≤ 12.5 % slower; flows on that link rehash; same-rail unaffected |
| orion-be-spine-2 | BFD 0.9 s (crash) or loss of signal | Every leaf removes orion-be-spine-2's 8 paths per prefix | 24 | 9.6 Tb/s per leaf; bisection 38.4 Tb/s | Cross-rail −25 %; same-rail unaffected |
| orion-be-leaf-r3 | Spines: loss of signal / BFD | Spines withdraw 10.100.3.0/24 and 10.255.0.14/32 | 32 for other rails; rail 3 unreachable | Rail 3 capacity 0; bisection 38.4 Tb/s | Every node loses NIC 3; multi-node jobs fail and restart |

*Marking (10 pts):* plan 4, failure table 6 (2 per row). Deduct for any number inconsistent with the
student's own lab output.

---

## Chapter deliverable — marking

Use lab rubric Task 6 (25 pts): diagram 8, routing policy 8, failure-convergence table 9. Require
`[MODELED]` labels and traceability to tool output.
