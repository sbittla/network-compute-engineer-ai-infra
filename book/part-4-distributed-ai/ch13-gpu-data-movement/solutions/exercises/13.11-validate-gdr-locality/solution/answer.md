# 13.11 — Validate GPUDirect RDMA and GPU/NIC locality (O3): worked solution

Platform: a drained pair of HX8 nodes (`orion-n05`, `orion-n14`), NIC *i* = `mlx5_i` behind the same
PCIe switch as GPU *i*. Every command, flag and output format is `[VENDOR-SPEC, 2026-10]`; verify
against the installed driver, perftest and NCCL versions. Plan follows Table 13.5 (Section 13.10).

| # | Question | Command | Pass criterion | Record |
|---|---|---|---|---|
| 1 | GPU *i* under the same switch as NIC *i*? | `nvidia-smi topo -m`; `lstopo --of txt` | GPU*i*↔NIC*i* = `PIX` for all *i* | topo matrix, BDFs |
| 2 | Peer-memory mechanism present? | `lsmod \| grep nvidia_peermem`, or `ib_write_bw -d mlx5_2 --use_cuda=2 --use_cuda_dmabuf` | module loaded, or dma-buf run succeeds | module/driver versions |
| 3 | ACS redirecting P2P? | `sudo lspci -vvv -s <switch-port> \| grep -i ACSCtl` | `ReqRedir- CmpltRedir-` on GPU/NIC downstream ports | ACSCtl lines |
| 4 | IOMMU mode | `cat /proc/cmdline`; `dmesg \| grep -i iommu` | matches validated config (e.g. `iommu=pt`) | cmdline |
| 5 | PCIe link healthy? | `sudo lspci -vvv -s <BDF> \| grep -E 'LnkCap\|LnkSta'` | Gen5 x16 in `LnkSta` = `LnkCap` | LnkSta per device |
| 6 | Host-buffer RDMA baseline | `ib_write_bw -d mlx5_2 --report_gbits -s 1048576 -D 10` (server + client) | ≈ 390 Gb/s on 400G | Gb/s, median/spread |
| 7 | GPU-buffer RDMA, aligned | same with `--use_cuda=2` | within ≈ 3 % of row 6 | Gb/s |
| 8 | **Misaligned** GPU/NIC | same with `--use_cuda=6` and `mlx5_2` (SYS) | measurably worse than row 7 (locality matters) | Gb/s, latency (`ib_write_lat`) |
| 9 | Does NCCL use GDR? | `NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=INIT,NET mpirun … all_reduce_perf -b 8 -e 8G -f 2 -g 1` | every inter-node channel line ends `/GDRDMA` | INFO excerpt |
| 10 | **GDR-off control** | same with `NCCL_NET_GDR_LEVEL=LOC` | GDR-on busbw ≥ GDR-off; small/medium latency gap visible | busbw/latency per size |
| 11 | Host traffic avoided? | `dcgmi dmon -e 1009,1010` (PCIe TX/RX) plus host memory bandwidth (`pcm-memory` or equivalent) during row 9 | host DRAM traffic low with GDR on, high with GDR off | GB/s |

**Repetitions.** Each bandwidth or latency test is run ≥ 5 times after one warm-up. Report the median
and the spread (min–max or IQR). A difference counts only if it exceeds the spread.

**Manifest fields.** Hostnames, GPU/NIC BDFs and serials, driver, CUDA, NCCL, MLNX_OFED/`rdma-core`,
firmware, kernel, BIOS, perftest version, environment variables, the date, and evidence labels
(`[MEASURED]`).

**Safety note.** The plan only *reads* configuration. Changing ACS, IOMMU or kernel modules needs a
maintenance window and Fleet change control (Chapter 20). A wrong ACS change can break device
isolation. Run only on drained nodes, never next to a production job.
