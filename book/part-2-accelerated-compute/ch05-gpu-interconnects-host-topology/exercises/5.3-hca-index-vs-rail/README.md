# Exercise 5.3 — HCA index is not the rail

★ · Tier L1 · knowledge check · kind: `written`

<!-- prompt:start -->
**5.3** ★ L1 — On `orion-n01`, `NIC1` in `nvidia-smi topo -m` is `mlx5_0` and is the rail-0 NIC. Explain
why the nvidia-smi NIC column index (`NIC1`) is not the rail number, why even the HCA name `mlx5_0` is only
a software label, and which source is authoritative for the rail.
*Evidence required:* column-order explanation; naming-rule explanation; LLDP/cabling database.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
