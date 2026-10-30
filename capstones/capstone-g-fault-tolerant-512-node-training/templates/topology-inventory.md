# Rank-to-Device Topology Inventory

> Template for Capstone G artifact 1. Source of truth: OBSERVED topology (LLDP, `nvidia-smi`,
> `lspci`), not the DCIM plan. Replace every `<fill: …>`.

## 1. Schema

| Column | Source command (tier) | Example |
|---|---|---|
| rank | job launcher rank file | 3013 |
| node | scheduler allocation | orionxl-n377 |
| gpu, gpu_uuid, gpu_bdf | `nvidia-smi --query-gpu=index,uuid,pci.bus_id --format=csv` (L2) | 5, GPU-…, 0000:ab:00.0 |
| numa | `cat /sys/bus/pci/devices/<bdf>/numa_node` (L2) | 1 |
| hca, nic_bdf, rail | `rdma link show`, `ls /sys/class/infiniband/<dev>/device -l` (L2) | mlx5_5, 0000:ac:00.0, 5 |
| leaf, leaf_port | `lldpctl` on the host or the switch LLDP neighbour table (L2/L3) | orionxl-be-leaf-p11-r5, 25 |
| `<fill>` | | |

## 2. Invariants checked
`<fill: e.g. GPU i and HCA i share a PCIe switch; rail = HCA index; one rank per GPU; every job rank maps to exactly one device>`

## 3. Discrepancies against the DCIM cabling plan

| Node | HCA | Planned | Observed (LLDP) | Ticket |
|---|---|---|---|---|
| `<fill>` | | | | |

## 4. Refresh policy
`<fill: when the inventory is rebuilt (boot, repair, every job start?) and how staleness is detected>`
