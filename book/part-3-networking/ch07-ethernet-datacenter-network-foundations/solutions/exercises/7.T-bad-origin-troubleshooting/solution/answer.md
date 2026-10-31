# 7.T — Half the flows to rail 6 fail after a template push (worked solution)

The evidence pack is `[ILLUSTRATIVE]`; the flow-fraction arithmetic is `[MODELED]`. Relies on
manuscript Section 7.12 (diagnostic loop, Table 7.9 checklist), Section 7.5 (eBGP best path,
multipath) and Section 7.6 (per-flow ECMP).

## (a) Evidence checklist (Table 7.9 format)

| Evidence (pack item) | MTU mismatch predicts | Asymmetric routing predicts | Incorrect advertisement predicts | Pack shows |
|---|---|---|---|---|
| Size dependence (1, 3) | Large fails, small works | Size-independent | Size-independent | **Size-independent**: default-size and 8,972-byte pings both fail; 1,400 and 8,948 MSS fail alike |
| Flow dependence (2, 3) | ≈ 1/N of flows (one ECMP member) | Only flows that cross a stateful or strict-uRPF device | A fraction set by how many spines prefer the bogus path | **31/64 ≈ 50 %**, and the outcome varies with the source |
| Prefix dependence (1, 2) | Any destination behind the bad link | Any destination | Only the affected prefix | **Only rail-6 destinations** fail; the same-rail ping (rail 6 → rail 6) succeeds |
| Interface counters (5) | Giants/oversize on one port | Clean | Clean | **All zero; every MTU matches intent** |
| Path trace (6) | Normal path | Forward ≠ reverse through a stateful device | Trace ends at the wrong leaf | **Ends after `10.101.1.17` = orion-be-leaf-r1** |
| BGP view (4, 8) | Normal | Normal | Unexpected origin AS for the prefix | **Origin 65102 (orion-be-leaf-r1) for rail 6's /24**, best on spines 1 and 3 |
| Change history | MTU change, RMA | ACL, uRPF or path-preference change | Config push on the originating device | **Template push to orion-be-leaf-r1 at 14:05**, failures from 14:06 |

## (b) Ranking and root cause

1. **Incorrect advertisement**: every discriminator matches (items 1–6, 8 and the change history).
2. **Asymmetric routing**: the backend has no stateful devices and no strict uRPF, and asymmetry
   would not single out one prefix or end a trace at leaf-r1.
3. **MTU mismatch**: refuted by size independence (items 1, 3) and clean counters with matching MTUs
   (item 5).

**Root cause:** the 14:05 template push made `orion-be-leaf-r1` originate `10.100.6.0/24`, which
belongs to `orion-be-leaf-r6`. Each spine receives two paths with AS_PATH length 1: `65102` and
`65107`. Without `as-path multipath-relax` (item 8) the two paths have different neighbor ASes, so they
cannot be multipath and each spine installs exactly one best path. Every earlier best-path step ties:
local preference, AS_PATH length 1, origin, and MED (not compared across different neighbor ASes).
So the eBGP tie-breakers decide:

- **Spines 2 and 4** (no `compare-routerid`): by default an eBGP speaker keeps the **oldest** of
  otherwise-equal external paths (RFC 5004 behaviour), which is leaf-r6's long-standing route.
  These spines deliver correctly.
- **Spines 1 and 3** carry template drift, `bgp bestpath compare-routerid` (item 8). That skips the
  oldest-path rule and prefers the **lower router ID**: 10.255.0.12 (leaf-r1) < 10.255.0.17 (leaf-r6).
  These spines forward rail-6 traffic to leaf-r1, which has no host behind `10.100.6.x` and drops it.

Item 8 is what explains the exact 2-of-4 split. A uniform router-ID rule would send all four spines to
leaf-r1, and a uniform oldest-path rule would send none. (Sources *on rail 1* fail 100 %, because
leaf-r1 prefers its own locally originated route.)

## (c) Why about half the flows fail, and why rails 2 and 5 failed but rail 3 did not

Each source leaf spreads traffic to `10.100.6.0/24` over its 32 uplinks, 8 to each spine. 16 of 32
uplinks lead to spines 1 or 3, so P(fail) = 16/32 = **50 %** per flow. The sweep's 31/64 fits:
expected 32, binomial σ = √(64 × 0.5 × 0.5) = **4**, so 31 is 0.25 σ from the mean. A ping is a
single flow (ICMP has no ports, so one hash). The rail-2 and rail-5 pings happened to hash to spine 1
or 3, and the rail-3 ping to spine 2 or 4. That is **hash luck, not a property of the rail**: a
64-flow sweep from rail 3 would also show ≈ 50 % failure. The traceroute (item 6) follows one TCP
flow, port 41022, which hashed to spine-1.

## (d) Reply to the colleague (item 7)

Different forward and reverse paths are *normal* in an ECMP fabric: each direction is hashed
independently by different switches. They only cause loss when a stateful device (firewall, NAT) or
strict uRPF sits on the path, and ORION's backend has neither. Asymmetry also cannot explain the three
facts that matter: only rail-6 destinations fail, the failing trace ends at leaf-r1, and the BGP
table shows a second origin AS (65102) for `10.100.6.0/24`.

## (e) Fix, validation, prevention

**Fix (through change control):**
1. Fastest safe mitigation: on all four spines, apply an **inbound prefix filter** on the leaf-r1
   sessions that accepts only `10.100.1.0/24` and `10.255.0.12/32`. That withdraws the bogus path
   everywhere with no session reset.
2. Then revert the template change on leaf-r1 so it stops originating rail 6's prefix.
3. Do not "clear bgp" on production spines without the filter in place.

**Validate (acceptance criteria):**
- Every spine shows a **single origin (65107)** for `10.100.6.0/24`, with 8 ECMP paths.
- Every leaf shows **32 next hops** for `10.100.6.0/24`.
- A **256-flow source-port sweep** from every rail to rail 6 completes with **0 failures**.
- The NCCL cross-rail benchmark is back to baseline bus bandwidth over **≥ 5 runs** (median and spread
  reported).

**Prevent:**
1. Standing per-leaf **inbound prefix filters** on spines, so a leaf can only advertise its own /24 and
   loopback.
2. Run the lab's **`BAD_ORIGIN`** validator in the change pipeline before any push.
3. Template unit tests that render each leaf's config and diff its originated prefixes against the
   ownership table.
4. Remove the `compare-routerid` drift so all spines apply one best-path policy, and add a config
   compliance check for it.

## Common mistakes

Blaming MTU because of the 8,972-byte ping (the default-size ping fails too). Treating the rail-3
success as meaningful. Answering "router ID decides" without explaining the 2-of-4 split (3 of 5).
Proposing to clear BGP sessions without a filter.
