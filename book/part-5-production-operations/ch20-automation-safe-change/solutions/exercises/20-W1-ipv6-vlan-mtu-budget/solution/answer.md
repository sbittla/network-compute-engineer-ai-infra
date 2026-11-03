# 20-W1 — MTU budget for an IPv6, VLAN-tagged variant: worked solution

**Relies on:** manuscript Section 20.5.1 (Figure 20.2 and the three MTU rules) and Section 20.11, Step 1
(Table 20.12, the IPv4 ORION figures). All results are `[MODELED]` from header sizes; the per-vendor MTU
convention must be confirmed on the platform. Reference computation: `solve.py` (asserts every value
below).

## a. Largest host IP MTU the leaves forward

The leaf counts the **full frame**: Ethernet header 14 + 802.1Q tag 4 + FCS 4 around the IP packet.

frame = IP MTU + 14 + 4 + 4 = IP MTU + 22 B ≤ 9,100 B → max IP MTU = 9,100 − 22 = **9,078 B**.

## b. Minimum host IP MTU for a 4,096-byte RDMA payload

The IPv4 budget of 64 B covers IPv4 20 + UDP 8 + BTH 12 + ICRC 4 = 44 B of fixed headers plus 20 B of
extended headers (RETH 16 + immediate data 4, for example). IPv6's header is 40 B, 20 B more than IPv4, so:

budget = 64 + (40 − 20) = **84 B**; min IP MTU = 4,096 + 84 = **4,180 B**.

Check: fixed IPv6 headers = 40 + 8 + 12 + 4 = 64 B, leaving 20 B for extended headers, the same allowance
as the IPv4 policy.

## c. Is the ORION host MTU of 9,000 valid?

- Fabric rule: 9,000 + 22 = 9,022 ≤ 9,100 ✓
- RDMA rule: 4,096 + 84 = 4,180 ≤ 9,000 ✓ (and 4,096 is an InfiniBand-defined MTU)

**Valid.** Note the smaller headroom than ORION: 78 B here against 194 B on ORION's 9,216 B ports.

## d. Wire efficiency and packet rate at 400 Gb/s

Per-packet overhead = 8 + 14 + 4 + 40 + 8 + 12 + 4 + 4 + 12 = **106 B**. Line rate =
400 × 10⁹ / 8 = 50 × 10⁹ B/s.

| RDMA MTU | Wire bytes | Efficiency | Packets/s `[MODELED]` |
|---|---|---|---|
| 1,024 B | 1,130 | 1,024 / 1,130 = **90.6 %** | 50 × 10⁹ / 1,130 ≈ **44.2 M/s** |
| 4,096 B | 4,202 | 4,096 / 4,202 = **97.5 %** | 50 × 10⁹ / 4,202 ≈ **11.9 M/s** |

The ceiling rises by 0.9748 / 0.9062 − 1 ≈ **7.6 %**, more than ORION's 5.9 % (82 B overhead) because the
fixed overhead per packet is larger; the packet rate still falls by ≈ 3.7×.

## e. The two rules, thresholds from policy data

```python
def pol_mtu_fabric(node, leaves, pol):     # POL-MTU-FABRIC
    return node["host_mtu"] + pol["l2_overhead_bytes"] <= min(l["port_mtu"] for l in leaves)

def pol_mtu_rdma(node, pol):               # POL-MTU-RDMA
    return (node["rdma_path_mtu"] in pol["allowed_rdma_path_mtu"]
            and node["rdma_path_mtu"] + pol["roce_header_budget_bytes"] <= node["host_mtu"])

# policy data for this variant
pol = {"l2_overhead_bytes": 22, "roce_header_budget_bytes": 84,
       "allowed_rdma_path_mtu": [256, 512, 1024, 2048, 4096]}
```

The rules use the *minimum* port MTU across all 8 rail leaves because every node reaches every rail.

## Marking (10 points)

a 2 · b 2 · c 1 · d 3 · e 2.

**Common wrong answers.** Using 18 B L2 overhead (forgetting the 802.1Q tag). Keeping the 64-byte IPv4
budget for IPv6, which gives 4,160 B and accepts a host MTU that cannot carry a 4,096-byte payload with
extended headers. Mixing Gb/s and GB/s (400 Gb/s = 50 GB/s). Hard-coding 22 and 84 in the rule bodies
instead of reading them from policy data.
