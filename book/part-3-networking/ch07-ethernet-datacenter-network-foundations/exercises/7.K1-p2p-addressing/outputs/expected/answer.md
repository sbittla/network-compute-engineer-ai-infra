# 7.K1 — Point-to-point /31 addressing (worked solution)

All numbers `[MODELED]`. Relies on manuscript Section 7.3 ("Point-to-point links: /31 and /127") and
Table 7.2.

## Standards

- **RFC 3021** (2000) permits a /31 prefix on an IPv4 point-to-point link: both addresses of the
  pair are used as host addresses; there is no network or broadcast address.
- **RFC 6164** (2011) recommends **/127** for IPv6 inter-router links (the IPv6 equivalent).

## Address counts

ORION-256 has 512 point-to-point links: 256 host links (32 nodes × 8 rails) plus 256 leaf-spine
links (8 leaves × 4 spines × 8 parallel links). `solve.py` counts them directly from
`lab/data/links.csv` (256 `host` + 256 `fabric` rows).

| Prefix | Addresses per link | Formula | Total |
|---|---|---|---|
| /31 | 2³²⁻³¹ = 2 | 512 × 2 | **1,024 addresses** |
| /30 | 2³²⁻³⁰ = 4 (network, two hosts, broadcast) | 512 × 4 | **2,048 addresses** |

## An operational reason to prefer /31

Address conservation is irrelevant inside 10.0.0.0/8. The operational benefit is **regularity**:
with /31s, address = base + 2 × link index, so every address can be *computed* from the link's
position (Table 7.2: `idx = 8r + k`, spine `.2·idx`, leaf `.2·idx+1`). That lets the plan be
generated and validated automatically (the lab's `DUP_P2P` rule depends on it), and each address maps
to exactly one interface, so an address in a capture identifies the interface without a lookup.
There is also no network or broadcast address to assign by mistake.

## Common wrong answers

- Counting only the 256 fabric links (gives 512 and 1,024): host links are point-to-point too.
- Giving "saves addresses" as the operational reason: it earns no credit for that point.
- Quoting /126 or /64 for IPv6 links: RFC 6164 recommends /127.
