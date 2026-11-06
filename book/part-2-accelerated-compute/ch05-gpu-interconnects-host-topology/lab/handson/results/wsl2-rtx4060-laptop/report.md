# Chapter 5 hands-on: host topology from the inside on `NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, 592.82`

Run captured 2026-11-05T02:35:29+00:00, kernel `6.18.54.1-rxe+`. Numbers are `[MEASURED]` by the step named, except the link rate, which is `[MODELED]` from the PCIe encoding. Raw outputs are in the step directories.

## Step 1: what this host shows and hides

| Question | Native multi-GPU server | This host |
|---|---|---|
| GPUs | 8 on ORION HX8 | 1 `[MEASURED]` |
| GPU in `lspci` (vendor 10de) | yes, with its BDF | 0 NVIDIA functions; 4 functions in all, vendors 1414, 1af4 `[MEASURED]` |
| PCIe tree (`lspci -tv`) | root ports, switches, endpoints | flat: no bridges or switches `[MEASURED]` |
| `LnkCap`/`LnkSta` (`lspci -vvv`) | per device | 0 LnkCap lines `[MEASURED]` |
| GPU's BDF `00000000:01:00.0` in sysfs | yes | no `[MEASURED]` |
| NUMA nodes | 2 | 1 `[MEASURED]` |
| NIC columns in `nvidia-smi topo -m` | NIC0..NIC9 | 0 `[MEASURED]` |
| RDMA devices | mlx5_0..9 on PCIe | none `[MEASURED]` |

## Step 2: the link nvidia-smi reports

- GPU link capability Gen4 x8, host side up to Gen5 `[MEASURED]`; per-direction rate 15.75 GB/s `[MODELED]` (GT/s × lanes × 128/130 ÷ 8).
- At idle: generation 4, width x8 over 11 samples `[MEASURED]`.

## Step 3: copy bandwidth against the link

| Size | H2D pageable | H2D pinned | D2H pageable | D2H pinned |
|---|---|---|---|---|
| 64 KiB | 4.60 GB/s (29 %) | 2.43 GB/s (16 %) | 1.58 GB/s (10 %) | 2.46 GB/s (16 %) |
| 256 KiB | 7.00 GB/s (44 %) | 7.59 GB/s (48 %) | 2.49 GB/s (16 %) | 7.85 GB/s (50 %) |
| 1 MiB | 6.86 GB/s (44 %) | 11.02 GB/s (70 %) | 4.46 GB/s (28 %) | 10.98 GB/s (70 %) |
| 4 MiB | 9.44 GB/s (60 %) | 12.34 GB/s (78 %) | 8.10 GB/s (52 %) | 12.83 GB/s (82 %) |
| 16 MiB | 11.84 GB/s (75 %) | 12.71 GB/s (81 %) | 10.11 GB/s (64 %) | 13.05 GB/s (83 %) |
| 64 MiB | 10.91 GB/s (69 %) | 12.84 GB/s (82 %) | 11.08 GB/s (70 %) | 13.16 GB/s (84 %) |
| 256 MiB | 10.89 GB/s (69 %) | 12.96 GB/s (82 %) | 11.02 GB/s (70 %) | 13.17 GB/s (84 %) |
| 512 MiB | 10.90 GB/s (69 %) | 12.87 GB/s (82 %) | 10.96 GB/s (70 %) | 13.15 GB/s (84 %) |

All cells `[MEASURED]`; percentages are of the 15.75 GB/s per-direction link rate.

- Both directions at once (256 MiB each, pinned): 12.989 GB/s aggregate versus 12.841 (H2D) and 13.167 (D2H) alone: 0.986× `[MEASURED]`.

## Step 4: under load

- Link during sustained copies: generation 4, width x8 `[MEASURED]`; `nvidia-smi dmon -s t` peak rxpci 7207.0 MB/s, txpci 7966.0 MB/s `[MEASURED]`; the copy loop moved 6.46 GB/s each way `[MEASURED]`.
- Pinned H2D alone 12.818 GB/s; while a GEMM loop runs on another stream 12.838 GB/s (ratio 1.002) `[MEASURED]`.

## Step 5: CPU placement of the copying process

- CPUs [0] (node 0): pinned 12.835, pageable 8.657 GB/s; CPUs [23]: pinned 12.835, pageable 9.757 GB/s `[MEASURED]`.

