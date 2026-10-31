# 5.11 — Shortest GPU–NIC pairings on `orion-n01` (model answer)

Relies on manuscript Section 5.6.1, Figure R.1 (docs/REFERENCE_CLUSTER.md: two GPUs and two backend NICs per
PCIe switch, four switches per socket pair of host bridges) and the Lab 5 capture
`lab/data/hosts/orion-n01/nvidia-smi_topo_m.txt` `[SIMULATED]`. `solve.py` parses the matrix and asserts the
table.

**Method.** For each GPU row take the NIC column with the best relation (PIX < PXB < PHB < NODE < SYS) and
translate the column to a device with the NIC legend (`NIC0: mlx5_8`, `NIC1: mlx5_0`, …, `NIC5: mlx5_9`,
`NIC6: mlx5_4`, …).

| GPU | Column | HCA | Relation | Rail |
|---|---|---|---|---|
| GPU0 | NIC1 | `mlx5_0` | PIX | 0 |
| GPU1 | NIC2 | `mlx5_1` | PIX | 1 |
| GPU2 | NIC3 | `mlx5_2` | PIX | 2 |
| GPU3 | NIC4 | `mlx5_3` | PIX | 3 |
| GPU4 | NIC6 | `mlx5_4` | PIX | 4 |
| GPU5 | NIC7 | `mlx5_5` | PIX | 5 |
| GPU6 | NIC8 | `mlx5_6` | PIX | 6 |
| GPU7 | NIC9 | `mlx5_7` | PIX | 7 |

(Rails per the LLDP capture: r0–r7 in order on this host.)

**One example per class** (quoted matrix cells):

- PXB: GPU0 ↔ NIC2 (`mlx5_1`) = `PXB`: the other NIC of the same switch complex, through its top switch.
- PHB: GPU0 ↔ NIC0 (`mlx5_8`, frontend) = `PHB`: same host bridge, through the root port.
- NODE: GPU0 ↔ NIC3 (`mlx5_2`) = `NODE`: another switch on the same socket.
- SYS: GPU0 ↔ NIC6 (`mlx5_4`) = `SYS`: a NIC on socket 1.

Any other correct quoted cells are accepted (e.g. GPU1 ↔ NIC1 PXB, GPU4 ↔ NIC5 PHB, GPU6 ↔ NIC5 NODE).

**Common wrong answers.** Reading `NIC1` as `mlx5_1`; picking the frontend NIC for a GPU because it is PHB "and
on the CPU"; listing columns without the legend translation.
