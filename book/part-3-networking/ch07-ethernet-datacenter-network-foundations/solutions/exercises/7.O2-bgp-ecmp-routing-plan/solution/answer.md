# 7.O2 — BGP/ECMP routing plan and failure behaviour for ORION-256 (model answer)

Capacities `[MODELED]` (from `fabric_capacity`; `solve.py` reproduces them), detection and convergence
times `[ILLUSTRATIVE]` (configured timers). Relies on manuscript Sections 7.3, 7.5, 7.6 ("Resilient
hashing"), 7.9 and Table 7.8.

## Routing plan (one page)

**ASN plan (RFC 7938).** Spines share AS 65100; `orion-be-leaf-r<r>` uses AS 65101 + r (65101–65108).
One eBGP session per fabric link (256 sessions: 32 per leaf, 64 per spine), on the link's /31.

**Origination.**
- Each leaf originates its rail aggregate `10.100.r.0/24` and its loopback `10.255.0.(11 + r)/32`.
- Spines originate only their loopbacks `10.255.0.1–4/32`.
- No host routes, and no default route on the backend.

**Inbound prefix filters.**
- Spines accept from leaf-r*r* only `10.100.r.0/24` and that leaf's /32 loopback; anything else is
  dropped. This is the standing control that would have prevented 7.T.
- Leaves accept from spines only `10.100.0.0/16 le 24` and `10.255.0.0/24 le 32`.

**Multipath.**
- `maximum-paths 64` everywhere.
- **Leaves need ≥ 32**: a remote rail's /24 is reachable via 4 spines × 8 links = 32 equal-cost
  next hops. The lab's `ECMP_MAXPATHS` fault (max 4) caps a leaf at 1.6 Tb/s of egress.
- **Spines need ≥ 8**: each spine has 8 parallel links to each leaf.
- `as-path multipath-relax` is not needed: all 32 paths at a leaf come from the same neighbor AS
  (65100). Leaving it off also keeps a mis-originated prefix from being load-shared.
- Resilient hashing on, so a member failure moves only the failed member's ≈ 1/32 of flows.

**Timers.** BFD 300 ms × 3 (0.9 s detection) on every session; BGP keepalive/hold 3 s / 9 s as the
backstop; advertisement interval 0.

**Drain procedure.**
1. Drain before planned work: AS_PATH prepend on the device's advertisements, or tag them with
   GRACEFUL_SHUTDOWN (RFC 8326) so neighbours lower local preference.
2. Verify that interface counters fall to ≈ 0.
3. Do the work.
4. Undrain and verify the 32/8 path counts and counters again.

## Failure table

| Failure | Detection mechanism and time `[ILLUSTRATIVE]` | Routes withdrawn (by whom, which prefixes) | ECMP width at an unaffected leaf (to a remote rail) | Capacity impact `[MODELED]` | Workload impact |
|---|---|---|---|---|---|
| One `orion-be-leaf-r0`↔`orion-be-spine-1` link | Loss of signal in ≈ 1–50 ms; BFD 0.9 s if it is a gray failure | Only that session's paths: leaf-r0 drops 1 of 32 next hops; spine-1 drops 1 of its 8 paths to leaf-r0. **No prefix is withdrawn**: spine-1 still advertises rail 0 | **32** (unchanged) | leaf-r0 raw uplink **12.4 Tb/s**, ECMP-aware ingress **11.2 Tb/s** (−12.5 %); bisection 50.8 Tb/s | Cross-rail traffic to rail 0 up to 12.5 % slower; flows on the dead link rehash (brief RDMA retransmission); same-rail traffic unaffected |
| `orion-be-spine-2` | BFD 0.9 s (crash) or loss of signal on all its ports | Every leaf removes spine-2's 8 paths for every remote prefix (8 sessions per leaf go down) | **24** | **9.6 Tb/s** per leaf (−25 %); bisection **38.4 Tb/s** | All cross-rail traffic −25 %; same-rail traffic unaffected; the job keeps running |
| `orion-be-leaf-r3` | Loss of signal / BFD on the spines' 32 links to it | Spines withdraw `10.100.3.0/24` and `10.255.0.14/32` from every leaf | **32** for other rails; rail 3 unreachable | Rail 3 capacity **0** (ingress and uplink); bisection **38.4 Tb/s** | Every node loses NIC 3; multi-node NCCL communicators on rail 3 break; the 256-GPU job fails and restarts from checkpoint |

Consistency with the lab: `fabric_capacity` returns 12,400 / 11,200 / 50,800 Gb/s for the link case,
9,600 / 9,600 / 38,400 for the spine case and 0 / 0 / 38,400 for the leaf case, matching T5 and
Table 7.8. Convergence after detection is sub-second, because withdrawals propagate at most two hops
and no valley paths exist (7.K2).

## Common mistakes

- "The spine withdraws rail 0" after a single link failure: it still has 7 paths.
- `maximum-paths` 8 at leaves (should be ≥ 32).
- Quoting raw uplink 12.4 Tb/s as the link-failure capacity without the ECMP-aware 11.2 Tb/s.
