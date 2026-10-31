# 7.K5 — Hash polarization (worked solution)

All numbers `[MODELED]`. Relies on manuscript Section 7.6 ("Hash polarization").

## Definition

**Hash polarization** happens when switches at successive tiers make *correlated* hash decisions
(same hash function, same fields, same seed). The second-tier switch then receives only the flows
whose hash fell in one slice of the hash space at the first tier, and its own modulo choice maps that
slice onto only a subset of its links. Some links carry everything and others stay idle, even though
each switch is "balancing" correctly by its own logic.

## Modular-arithmetic argument

Leaf numbering (Section 7.6): a flow with hash *h* leaves on uplink *i = h mod 32*, and uplink *i*
goes to `orion-be-spine-(i mod 4 + 1)`.

1. Spine *s* receives the flow only if *(h mod 32) mod 4 = s − 1*. Because 4 divides 32,
   *(h mod 32) mod 4 = h mod 4*, so spine *s* sees only flows with **h mod 4 = s − 1**.
2. The spine picks its downstream link with the same function, *k = h mod 8*. Because 4 divides 8,
   *h mod 4* is determined by *h mod 8*: *h mod 8 ∈ {r, r + 4}* where *r = h mod 4*.
3. With *r = s − 1*: **k ∈ {s − 1, s + 3}**.

## Resulting link set

| Spine | Links used toward each destination leaf | Share |
|---|---|---|
| `orion-be-spine-1` | **k ∈ {0, 4}** | 2 of 8 (25 %) |
| `orion-be-spine-2` | {1, 5} | 25 % |
| `orion-be-spine-3` | {2, 6} | 25 % |
| `orion-be-spine-4` | {3, 7} | 25 % |

`solve.py` confirms this by sweeping 65,536 hash values through both stages. Each spine-to-leaf bundle
runs on 2 of its 8 links, so cross-rail capacity into a leaf is a quarter of what Table 7.8 assumes.

## Remedy and common mistakes

Production ASICs avoid this with per-switch hash seeds or different field sets. Operators should
confirm that the seeds really differ and *measure* the spread of link utilization. Common mistakes:
answering "{0}" (forgetting that *h mod 8* has two residues per *h mod 4* value); or describing the
leaf picking spines as polarization, when the effect is at the second tier.
