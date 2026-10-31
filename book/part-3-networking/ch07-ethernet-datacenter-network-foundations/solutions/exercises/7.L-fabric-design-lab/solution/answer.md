# 7.L — Progressive Lab 2: fabric design and validation (reference solution)

Everything in this lab is `[MODELED]`: no packets are sent. Reference implementation:
`solutions/lab/fabric_lab.py`. `python lab/check.py --impl solution` reports **19/19 PASS**. In the
student release T0 reports SKIP, because the generator in `lab/tools/` is stripped. The named checks
and their PASS lines are in `outputs/lab_checks.json`. Relies on manuscript Sections 7.3–7.11 and lab
README §5–§7.

## Task 1 — sizing (T1a–T1c)

- ORION-256 backend `size_two_tier(256, 64, 64, 1.0)`: 32 down / 32 up, **8 leaves, 4 spines,
  8 links per pair**, 256 host + 256 fabric = 512 cables, 1,024 transceivers.
- Frontend pair: 48 × 200G down / 16 × 400G up is **3:1 by ports** but 48 × 200 / (16 × 400) =
  **1.5:1 by bandwidth** (`down_gbps=200`).
- ORION-XL (4,096 GPUs) at radix 64: the two-tier maximum is spine ports × downlinks per leaf =
  64 × 32 = 2,048 endpoints < 4,096, so `feasible=False`. A 64-port spine can reach at most 64
  leaves. At radix 128: 128 × 64 = 8,192 ≥ 4,096, so it is feasible (64 leaves, 32 spines, 2 links per
  pair). This is why ORION-XL needs either 128-port switches or a third tier.

## Tasks 2–3 — addressing plan and BGP table (T2a, T2b, T3)

512 unique /31s (256 host links in `10.100.r.0/24`, 256 fabric links in `10.101.s.0/24`,
idx = 8r + k). Spot value: `F-r2-s3-k1` → spine `10.101.3.34/31`, leaf `10.101.3.35/31`, leaf port
`Ethernet50`, spine port `Ethernet18`. The BGP table has 256 sessions: 32 per leaf, 64 per spine;
spines in AS 65100, leaf-r*r* in AS 65101 + *r*. Both are exported as CSV for the deliverable.

## Task 4 — validation findings (reference output)

```text
[blocker] DUP_P2P        10.101.3.72/31   /31 used on 2 links: F-r4-s3-k4, F-r4-s3-k5
[blocker] ASN_COLLISION  65107            ASN shared by orion-be-leaf-r6, orion-be-leaf-r7
[blocker] MTU_MISMATCH   F-r3-s2-k6       orion-be-leaf-r3 9216 vs orion-be-spine-2 1500
[major  ] ECMP_MAXPATHS  orion-be-leaf-r2 max-paths 4 < 32 equal-cost paths
[blocker] BAD_ORIGIN     orion-be-leaf-r1 10.100.6.0/24   prefix owned by orion-be-leaf-r6
[major  ] ASYM_ADVERT    orion-be-leaf-r5 10.100.5.0/24   not advertised to orion-be-spine-4
```

| Finding | Operational consequence on ORION | Severity | Capacity consequence (Task 5) |
|---|---|---|---|
| DUP_P2P | Second interface fails to configure or both links share a subnet; ARP/BGP confusion, one session down or flapping | blocker | ≈ one link down for leaf-r4: uplink 12.4, ingress 4 × 7 × 0.4 = **11.2 Tb/s** |
| ASN_COLLISION | leaf-r6 and leaf-r7 drop each other's routes (AS_PATH loop check); rail 6 ↔ 7 unreachable while all sessions are Established | blocker | Cross-rail capacity rail 6 ↔ rail 7 = **0** |
| MTU_MISMATCH | 4,174-byte RoCE frames dropped on that link; flows hashed onto it hit retry-exceeded; BGP stays up (7.K3) | blocker | Worse than a down link (traffic is sent and lost); once drained, **11.2 Tb/s** ingress for leaf-r3 |
| ECMP_MAXPATHS | leaf-r2 installs 4 of 32 uplinks; cross-rail traffic *from* rail 2 is squeezed; ingress unaffected | major | leaf-r2 egress 4 × 0.4 = **1.6 Tb/s** (12.5 % of 12.8) |
| BAD_ORIGIN | Spines that prefer leaf-r1's path deliver rail-6 traffic to leaf-r1, which drops it (this is the 7.T incident) | blocker | ≈ 50 % of cross-rail flows to rail 6 lost if 2 of 4 spines prefer it |
| ASYM_ADVERT | Traffic *to* rail 5 uses 3 spines, traffic *from* rail 5 uses 4 | major | Ingress to leaf-r5 3 × 8 × 0.4 = **9.6 Tb/s** (−25 %) |

**False-positive traps that must not be reported:** all spines sharing AS 65100 (RFC 7938, 7.K2);
host links at 9216 (switch) / 9000 (host) by design; loopbacks advertised by every leaf to every
spine; spines with `ecmp_max_paths` 64 ≥ 8. Severity differences are acceptable if justified.
Anything that silently drops or misroutes traffic is a blocker; capacity-only degradations are major.

## Task 5 — capacity (T5)

| Scenario | Uplink | ECMP-aware ingress | Bisection |
|---|---|---|---|
| Baseline | 12,800 | 12,800 | 51,200 Gb/s |
| One leaf-r0/spine-1 link down | 12,400 | 11,200 | 50,800 Gb/s |
| Spine-2 down | 9,600 | 9,600 | 38,400 Gb/s |
| leaf-r5 prefix not sent to spine-4 | 12,800 | 9,600 | 51,200 Gb/s |
| leaf-r3 down (rail 3 isolated) | 0 | 0 | 38,400 Gb/s |

## Task 6 — design note (what a full-marks note contains)

A diagram with 8 rail leaves, 4 spines, "× 8" parallel links per pair, ASNs (65100; 65101–65108) and
loopbacks (spines .1–.4, leaves .11–.18). A routing policy with inbound prefix filters per leaf,
`maximum-paths` ≥ 32 at leaves and ≥ 8 at spines, BFD 300 ms × 3, BGP 3 s / 9 s, and a drain procedure
(AS_PATH prepend or GRACEFUL_SHUTDOWN, RFC 8326). A failure-convergence table for link, spine and leaf
failures consistent with Table 7.8 and 7.O2, every number labelled `[MODELED]` and traced to the
tool output.

## Stretch — `QOS_MISMATCH` rule (model answer)

**Intent fields the dataset lacks:** per switch `dscp_to_tc` map, `lossless_priorities`,
`pfc_enabled_priorities`, `ecn_enabled_tcs`; per host-facing port `dscp_trust`.

**Rule:** every backend switch has an identical `dscp_to_tc` map (26 → TC 3, 48 → TC 6) and identical
lossless/PFC priority sets. Every host-facing port trusts DSCP. PFC is enabled on exactly the lossless
priority (3) on every fabric and host port.

| # | Test input | Expected |
|---|---|---|
| 1 | All switches consistent | no finding |
| 2 | One leaf maps DSCP 26 → TC 0 | finding (RoCE goes lossy at that hop) |
| 3 | One spine missing PFC on priority 3 | finding |
| 4 | One host-facing port does not trust DSCP | finding (traffic remarked to TC 0) |
| 5 | PFC enabled on an extra priority | finding, warning: pause-storm exposure (Chapter 9) |

## Common mistakes

Reporting the shared spine ASN or host MTU 9000 as errors. Treating the MTU mismatch as "major"
because BGP is up. Quoting raw uplink instead of ECMP-aware ingress for planted-fault consequences.

## Hardware run (L2 harness)

On the course harness (`python scripts/hw_labs.py run ch07`) the containerlab fabric cannot run: there is
no containerlab, no Docker socket, no CAP_NET_ADMIN and `--network none`. That is recorded with the
probe. The harness instead reproduces Section 7.6: 8 RoCE flows on 8 links, 32 on 32, polarization with a
reused seed, and modulo versus resilient rehash. Every figure is checked against its closed form, which
supports the design note's ECMP discussion with `[SIMULATED]` numbers. Convergence timings still need the
containerlab L2 on a Linux host.
