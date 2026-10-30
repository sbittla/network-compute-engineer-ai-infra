# Network and Host Topology Worksheet — ORION-256

## 1. Backend fabric summary `[MODELED]`

| Quantity | Option A | Option B | Formula |
|---|---|---|---|
| Host links | <fill> | <fill> | nodes × NICs per node |
| Leaves / spines | <fill> | <fill> | ceil(host links / downlinks); ceil(leaf × uplinks / spine radix) |
| Uplinks per leaf per spine | <fill> | <fill> | uplinks per leaf / spines |
| Oversubscription (down:up) | <fill> | <fill> | downlinks / uplinks |
| Optical links / DAC links | <fill> | <fill> | from cable plan |
| Transceivers | <fill> | <fill> | 2 × optical links |

## 2. Rail map

| Rail | NIC on every node | Leaf (option A) | Leaf (option B) | Subnet (`10.100.r.0/24`, /31 per node) |
|---|---|---|---|---|
| 0 | NIC0 (GPU0, PCIe SW0, NUMA 0) | <fill> | <fill: ToR of the node's rack> | `10.100.0.0/24` |
| <fill: rails 1–7> | | | | |

## 3. Port map excerpt

Attach the full cable plan CSV produced by `cable_plan()`. Show five representative rows here,
including one rack-08 link and one in-rack DAC.

| end_a | rack_a | end_b | rack_b | path (m) | length (m) | medium |
|---|---|---|---|---|---|---|
| <fill> | | | | | | |

## 4. Routing and QoS intent

- Underlay: <fill: eBGP per RFC 7938 style, ASN plan from REFERENCE_CLUSTER (spines AS 65100, leaves 65101–65108 for option A); what changes for option B>
- ECMP: <fill: hash fields, expected flow count per uplink, polarization risk>
- MTU: <fill: switch 9216, host 9000, RDMA path MTU 4096>
- RoCEv2 QoS: <fill: DSCP 26 → TC3 lossless with PFC + ECN; CNP DSCP 48 → TC6; what you would monitor>

## 5. Host topology and GPU↔NIC locality

| GPU | PCIe switch | NUMA node | Nearest NIC | `nvidia-smi topo -m` relation expected | Rail |
|---|---|---|---|---|---|
| GPU0 | SW0 | 0 | NIC0 | PIX | 0 |
| <fill: GPU1–GPU7> | | | | | |

Explain what breaks if a rank is bound to a GPU whose NIC is across the socket (SYS), and how the
acceptance plan detects mis-cabling that swaps two rails.

## 6. Topology diagram

<fill: Mermaid leaf-spine diagram for your chosen option, with racks and rails visible. Caption:
*Figure A.2 — …*>
