# 7.K2 — Shared spine ASN, unique leaf ASNs (worked solution)

Relies on manuscript Section 7.5 ("ASN design"). ORION plan: spines AS 65100, leaves 65101–65108.

## Why all spines share one ASN

**Mechanism (one sentence):** eBGP AS_PATH loop detection makes every spine reject any route whose
AS_PATH already contains 65100, so a path that has crossed the spine tier once can never re-enter it.

Example: `orion-be-leaf-r0` learns rail 1's prefix from `orion-be-spine-1` with AS_PATH `65100 65102`.
If it re-advertised that route to `orion-be-spine-2`, spine-2 sees its own ASN in the path and drops
it. This removes every *valley* path (spine → leaf → spine) without any filter configuration. It also
prevents **path hunting** after a withdrawal: with unique spine ASNs, spines would briefly try ever
longer valley paths through leaves before converging, delaying convergence and moving traffic through
leaves that were never meant to transit.

## Why every leaf needs its own ASN

**Mechanism (one sentence):** a leaf drops any route whose AS_PATH contains its own ASN, so two
leaves sharing an ASN each discard the other's prefixes.

Precisely: if `orion-be-leaf-r6` and `orion-be-leaf-r7` both use 65107, `orion-be-leaf-r7`'s prefix
reaches `orion-be-leaf-r6` with AS_PATH `65100 65107`. Leaf-r6 sees 65107 (its own) and rejects it,
and vice versa. Result:

- rail 6 ↔ rail 7 cross-rail traffic has **no route** (each leaf lacks the other's /24 and loopback);
- every BGP session stays **Established** and every other prefix is fine, so session-state monitoring
  shows nothing. The fault is visible only in the RIB (missing prefixes) or in failing traffic.

This is exactly the lab's planted `ASN_COLLISION` (7.L).

## Common wrong answers

- "Duplicate ASNs make the session fail to come up": eBGP between a leaf and a spine still has
  different ASNs on each end, so the sessions come up.
- Explaining the spine half with "so the spines are interchangeable" without naming AS_PATH loop
  detection: the key requires the mechanism for full marks.
- Using `allowas-in` as the fix: it suppresses the loop check and reintroduces valley-path risk.
  The fix is to give each leaf its own ASN.
