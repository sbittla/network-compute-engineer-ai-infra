# Exercise 5.11 — shortest GPU–NIC pairings on `orion-n01`

| GPU | topo -m column | HCA | Relation |
|---|---|---|---|
| GPU0 | NIC1 | `mlx5_0` | PIX |
| GPU1 | NIC2 | `mlx5_1` | PIX |
| GPU2 | NIC3 | `mlx5_2` | PIX |
| GPU3 | NIC4 | `mlx5_3` | PIX |
| GPU4 | NIC6 | `mlx5_4` | PIX |
| GPU5 | NIC7 | `mlx5_5` | PIX |
| GPU6 | NIC8 | `mlx5_6` | PIX |
| GPU7 | NIC9 | `mlx5_7` | PIX |

| Class | Example (matrix cell) |
|---|---|
| PXB | GPU0 ↔ NIC2 (`mlx5_1`) = PXB |
| PHB | GPU0 ↔ NIC0 (`mlx5_8`) = PHB |
| NODE | GPU0 ↔ NIC3 (`mlx5_2`) = NODE |
| SYS | GPU0 ↔ NIC6 (`mlx5_4`) = SYS |
