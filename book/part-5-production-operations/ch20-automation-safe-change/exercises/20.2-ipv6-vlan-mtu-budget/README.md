# 20.2 — MTU budget for an IPv6, VLAN-tagged variant (★★, L1)

Type: Worked problem · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
A second cluster reuses ORION's design with three differences: the backend underlay is **IPv6**,
host ports are **802.1Q-tagged**, and the leaves' configured port MTU is **9,100 B**. The vendor
documents that the switch MTU counts the full frame including the Ethernet header, VLAN tag, and
FCS. Assume a 64-byte extended-header budget for IPv4, as in Section 20.5.1. The IPv6 header is 40 B
(IPv4 is 20 B).

a. What is the largest host IP MTU the leaves will forward without drops?
b. What is the minimum host IP MTU that carries a 4,096-byte RDMA payload, using a header budget
   adjusted for IPv6?
c. Is the ORION host MTU of 9,000 valid here? Show both inequalities.
d. Compute wire efficiency and packet rate at 400 Gb/s for RDMA MTU 1,024 and 4,096 on this
   variant. Per-packet wire overhead = preamble+SFD 8 + Ethernet 14 + 802.1Q 4 + IPv6 40 + UDP 8 +
   BTH 12 + ICRC 4 + FCS 4 + IFG 12.
e. Write the two policy rules (in pseudo-code or Python) with the thresholds read from policy data.

**Evidence required:** formula → substituted values → result with units for each part, and the
two rules.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md` (working for a-e)
- `outputs/rules.py` (the two policy rules)
