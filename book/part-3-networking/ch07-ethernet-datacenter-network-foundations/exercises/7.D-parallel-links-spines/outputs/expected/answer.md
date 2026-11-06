# 7.D — Parallel links and spine count for the next build (worked solution)

All capacities `[MODELED]` (one direction, uniform demand, unweighted ECMP, 400 Gb/s links, 8 rail
leaves). Relies on manuscript Section 7.9 ("Link failure", "Spine failure"), Table 7.8, Section 7.5
(sessions, multipath) and Section 7.6. `solve.py` derives every capacity with the reference
`fabric_capacity`.

## Comparison table

| Metric | A: 4 spines × 8 links, eBGP per link | B: 8 spines × 4 links, eBGP per link | C: 4 spines × 8-member LAG, eBGP per LAG |
|---|---|---|---|
| ECMP-aware ingress, one link down | 4 × 7 × 0.4 = **11.2 Tb/s** (−12.5 %) | 8 × 3 × 0.4 = **9.6 Tb/s** (−25 %) | LAG at 7/8, but BGP still splits 4 ways: 4 × 7 × 0.4 = **11.2 Tb/s** (−12.5 %) |
| ECMP-aware ingress, one spine down | 3 × 8 × 0.4 = **9.6 Tb/s** (−25 %) | 7 × 4 × 0.4 = **11.2 Tb/s** (−12.5 %) | **9.6 Tb/s** (−25 %) |
| Bisection, one spine down (baseline 51.2) | 3 × 32 × 0.4 = **38.4 Tb/s** | 7 × 16 × 0.4 = **44.8 Tb/s** | **38.4 Tb/s** |
| eBGP sessions | 8 leaves × 32 links = **256** | 8 × 8 × 4 = **256** | 8 × 4 = **32** |
| BFD sessions | **256** | **256** | **32** (+ 256 micro-BFD member sessions, RFC 7130) |
| Spine switches / ports used | **4**, 64 of 64 each (256) | **8**, 32 of 64 each (256; half of every spine idle) | **4**, 64 of 64 each |
| ECMP width at the leaf | **32** | **32** | **4** (then the LAG member hash: two-stage) |

Bisection for B with a spine down: the worst 4/4 split leaves each of the 7 surviving spines with
min(4 × 4, 4 × 4) = 16 links across the cut, so 7 × 16 × 0.4 = 44.8 Tb/s. For A and C each surviving
spine carries min(4 × 8, 4 × 8) = 32.

## Recommendation (≤ 300 words)

**Choose A** (C is an acceptable alternative). The stated dominant risk is optics: several link
failures per month. In A a single failed link costs the affected leaf 12.5 % of ECMP-aware ingress.
In B it costs 25 %, because each spine bundle is only 4 links wide while unweighted ECMP still gives
that spine 1/8 of the traffic. Over many link failures per month, B doubles the common-case penalty.
A also uses every spine port and needs 4 fewer spine switches than B, which runs 8 half-empty spines.

C matches A's capacity with 8× fewer BGP and BFD sessions. A failed LAG member keeps the eBGP session
up, so control-plane churn is lower. But C brings two-stage hashing (BGP picks 1 of 4 spines, then the
LAG picks 1 of 8 members), LAG min-links semantics to tune, and micro-BFD per member to catch gray
failures. A failed member that is not detected leaves a black hole inside a healthy-looking session.
For a team that already automates per-link eBGP and validates it (Lab 7), A is simpler to reason
about. With weighted ECMP (link-bandwidth community), A recovers most of the link-failure penalty
(to ≈ the raw 12.4 Tb/s).

**Assumption that would change the recommendation:** if spine events dominate, for example monthly
spine OS upgrades (each a planned "spine down") or a spine platform with a poor reliability record,
then B halves the per-event penalty (−12.5 % instead of −25 % ingress, 44.8 instead of 38.4 Tb/s
bisection). That justifies B's 4 extra spine switches.

## Common mistakes

- Giving C a lower link-failure penalty: BGP does not see the LAG's reduced bandwidth unless
  link-bandwidth/UCMP is configured.
- Counting B's spine ports as 64 each: each spine has only 8 leaves × 4 = 32 ports in use.
- Forgetting the micro-BFD member sessions in C.
