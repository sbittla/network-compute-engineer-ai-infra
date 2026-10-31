# G4 verification — ch23-capstones

Scope: `book/part-6-applied-engineering/ch23-capstone-production-ai-cluster/` (manuscript, exercises, lab, solutions, review) and the whole `capstones/` tree (README, RUBRIC, capstone-a..h with templates, starter-kit, instructor, review).
Checked 2026-10-30. Claims that repeat docs/VERIFIED_FACTS.md (GDR log lines, `/GDRDMA` evidence, DMA-BUF caveat, `NCCL_IB_TIMEOUT` defaults, `NCCL_IB_QPS_PER_CONNECTION`, NVLS/ring busbw, multi-node busbw, Xid 94/95, RoCE path MTU, DR4 Rx power, PCIe Gen5, ITL vs TPOT, 51.2T port configuration) were compared with that file. They all agree, so they were not researched again.

Verdict counts: **OK 38 · WRONG 1 · STALE/VERSION-DEPENDENT 1 · UNVERIFIABLE 0**.

| file:line | claim (short) | verdict | source URL | version/date checked | change made |
|---|---|---|---|---|---|
| ch23 lab/tools/generate_bundles.py:40, bundles assumptions.yaml A-01; capstones A assumptions-register.csv:3; D hardware.yaml/manifest.yaml:7; H serving_sim.py:42, hardware.csv | H100 SXM dense BF16 989 TFLOP/s, dense FP8 1,979 | OK (datasheet gives 1,979 / 3,958 *with sparsity*; dense is half) | https://www.nvidia.com/en-us/data-center/h100/ | H100 SXM page, 2026-10 | none |
| ch23 generate_bundles.py:42, A-02; D hardware.yaml; H serving_sim.py:43 | 80 GB HBM, 3.35 TB/s | OK | https://www.nvidia.com/en-us/data-center/h100/ | 2026-10 | none |
| ch23 generate_bundles.py:44,205,255; bundles design.md:19; manuscript.md:305,319,764 | Node max power 10.2 kW (DGX H100-class) | OK | https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html | DGX H100/H200 user guide, 2026-10 | none |
| ch23 manuscript.md:239-240 | NVLink 450 GB/s per direction per GPU (900 GB/s total) | OK | https://www.nvidia.com/en-us/data-center/h100/ | 2026-10 | none |
| ch23 manuscript.md:238 | Megatron TP: two all-reduces per layer per forward pass | OK | Narayanan et al., SC'21 / Shoeybi et al. 2019 (Megatron-LM) | paper | none |
| ch23 manuscript.md:519, lab/README.md:179 | per-rail busbw = node busbw ÷ 8 vs 50 GB/s | OK (VERIFIED_FACTS) | docs/VERIFIED_FACTS.md | — | none |
| ch23 manuscript.md:860-880, lab/README.md:179-181; capstone-c data/nccl_debug_*.log | `/GDRDMA` channel lines, `lsmod \| grep nvidia_peermem`, DMA-BUF caveat, `NET/IB : Using [0]mlx5_0:1/RoCE … ; OOB`, `Using network IB/Socket`, `NET/IB : No device found.` | OK (VERIFIED_FACTS; log shapes labelled ILLUSTRATIVE) | docs/VERIFIED_FACTS.md | NCCL 2.18–2.28 | none |
| ch23 manuscript.md:861-866 | `ibv_devinfo` fields `fw_ver`, `state: PORT_ACTIVE (4)`, `active_mtu: 4096 (5)`; `lspci LnkSta: Speed 32GT/s, Width x16` | OK | rdma-core `ibv_devinfo` output; pciutils | 2026-10 | none |
| ch23 lab/README.md:166-172; capstone-c starter-kit/README.md:104-105; capstone-e starter-kit/README.md:150 | nccl-tests `-b -e -f -g -w -n`, `make MPI=1 MPI_HOME=…` | OK (note: `-w` default is 1; text always passes `-w 5` explicitly) | https://github.com/NVIDIA/nccl-tests/blob/master/README.md | nccl-tests master, 2026-10 | none |
| ch23 lab/README.md:170 | `srun --mpi=pmix` needs Slurm built with PMIx | OK | https://slurm.schedmd.com/mpi_guide.html | Slurm docs, 2026-10 | none |
| ch23 lab/README.md:158 | `ipmitool dcmi power reading` | OK | ipmitool man page | 1.8.19 | none |
| ch23 solutions/exercises-key.md:153 | `nvidia-smi --query-gpu=clocks.sm,temperature.gpu --format=csv -l 1` | OK | `nvidia-smi --help-query-gpu` | driver R570+ | none |
| ch23 exercises.md:103, exercises-key.md:171 | 51.2 Tb/s ASIC = 64 × 800G or 128 × 400G | OK (VERIFIED_FACTS) | docs/VERIFIED_FACTS.md | — | none |
| ch23 manuscript.md further reading | RFC 7938 (2016), IEC 60812:2018, Young 1974/Daly 2006, Megatron SC'21, Llama 3 (2024) | OK | https://www.rfc-editor.org/rfc/rfc7938 | — | none |
| capstone-a templates/runbook.md:16 | `NCCL_IB_HCA=^mlx5_<R>` excludes the failed HCA | **WRONG** (imprecise): without `=`, names are prefixes, so `^mlx5_1` also excludes `mlx5_10`–`mlx5_19` | https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html | NCCL 2.32.3 docs | Changed to `NCCL_IB_HCA=^=mlx5_<R>` with a prefix-match note; tag kept |
| capstone-a instructor/EXEMPLAR.md:73 | `NCCL_IB_QPS_PER_CONNECTION` default 1 | OK | same env.html | NCCL 2.32.3 | none |
| capstone-a templates/acceptance-plan.csv:2; EXEMPLAR.md:84 | DR4 Rx warn ≈ −4 dBm, critical ≈ −5.9 dBm | OK (VERIFIED_FACTS) | docs/VERIFIED_FACTS.md | — | none |
| capstone-a templates/acceptance-plan.csv:9 | multi-node busbw ≈ 350+ GB/s | OK (VERIFIED_FACTS) | — | — | none |
| capstone-b starter-kit/README.md:62-83; data/nic/*.txt.gz | mlx5 `ethtool -S`: `rx/tx_vport_rdma_unicast_bytes`, `rx/tx_prio3_pause` (`rx_prio[p]_pause`), `rx_crc_errors_phy`, `rx_discards_phy` | OK | https://docs.kernel.org/networking/device_drivers/ethernet/mellanox/mlx5/counters.html | Linux master, 2026-10 | none |
| capstone-b same; templates/telemetry-schema.md:29-33 | RDMA hw_counters `np_cnp_sent`, `np_ecn_marked_roce_packets`, `rp_cnp_handled`, `out_of_sequence`, `local_ack_timeout_err`; path `/sys/class/infiniband/<dev>/ports/1/hw_counters` | OK | https://github.com/torvalds/linux/blob/master/drivers/infiniband/hw/mlx5/counters.c | Linux master, 2026-10 | none |
| capstone-b spine_stream.jsonl | OpenConfig `/interfaces/interface[name=…]/state/counters` with `in-octets`, `out-discards`, `in-fcs-errors`; PFC under a vendor extension | OK (declared vendor-neutral or "OpenConfig-style") | https://openconfig.net/projects/models/ (openconfig-interfaces) | 2026-10 | none |
| capstone-c starter-kit/README.md:103 | `NCCL_DEBUG_SUBSYS=INIT,NET` valid | OK | NCCL env.html | NCCL 2.32.3 | none |
| capstone-c starter-kit/README.md:119 | `NCCL_IB_HCA` restricts HCAs; `NCCL_NET_GDR_LEVEL` gates GDR | OK | NCCL env.html | NCCL 2.32.3 | none |
| capstone-c starter-kit/README.md:108-111 | `torchrun --rdzv_backend c10d --rdzv_endpoint`; `nsys profile -t cuda,nvtx,osrt --capture-range=cudaProfilerApi` | OK | https://docs.pytorch.org/docs/stable/elastic/run.html ; Nsight Systems user guide | PyTorch 2.9 / nsys 2025.x | none |
| capstone-c starter-kit/README.md:62 | DDP `bucket_cap_mb` default 25 | OK | https://docs.pytorch.org/docs/stable/generated/torch.nn.parallel.DistributedDataParallel.html | PyTorch 2.9 | none |
| capstone-c data/manifests.csv | PyTorch 2.5.1 / CUDA 12.6 / driver 570.86.15 / NCCL 2.23.4 combination | OK as ILLUSTRATIVE (driver ≥ 560.28.03 satisfies CUDA 12.6; NCCL 2.23.4 exists) | https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html | CUDA 13.x notes | none |
| capstone-d starter-kit/README.md:55-57,111-112 | vLLM args `--tensor-parallel-size`, `--max-num-seqs`, `--max-num-batched-tokens`, `--enable-chunked-prefill`, `--gpu-memory-utilization`, `--max-model-len` | OK (all present; text already says defaults change; current `--gpu-memory-utilization` default is 0.92, text sets 0.90 explicitly and claims no default) | https://docs.vllm.ai/en/latest/configuration/engine_args.html | vLLM latest dev docs, 2026-10 | none |
| capstone-e data/compat_matrix.csv | driver 535→CUDA 12.2, 550→12.4, 570→12.8 max | OK | CUDA toolkit release notes (min driver 535.54.03 / 550.54.14 / 570.26) | 2026-10 | none |
| capstone-e starter-kit/README.md:130-138 | `nvidia-smi --query-gpu=…ecc.errors.uncorrected.volatile.total,…pcie.link.gen.current…`, `nvidia-smi -q -d ROW_REMAPPER` | OK | `nvidia-smi --help-query-gpu`, nvidia-smi man page | driver R570+ | none |
| capstone-e starter-kit/README.md:148-149 | `dcgmi diag -r 3`; nvbandwidth | OK | https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/dcgm-diagnostics.html | DCGM 4.x | none |
| capstone-e/h starter-kit README | `ib_write_bw --report_gbits`, `--use_cuda=<id>` | OK | https://github.com/linux-rdma/perftest/blob/master/src/perftest_parameters.c | perftest master | none |
| capstone-e starter-kit/README.md:167-181 | Redfish `/redfish/v1/Systems`, `/UpdateService/FirmwareInventory`; `scontrol update … State=DRAIN/RESUME`; `kubectl drain --ignore-daemonsets --delete-emptydir-data` | OK | DMTF DSP0266; https://slurm.schedmd.com/scontrol.html ; https://kubernetes.io/docs/reference/kubectl/generated/kubectl_drain/ | 2026-10 | none |
| capstone-e README.md:233-237 | busbw > ≈ 400 GB/s implies NVLS | OK (VERIFIED_FACTS) | — | — | none |
| capstone-f starter-kit/README.md:112-116; README.md:186-193 | `ip link`, `ipmitool -I lanplus … chassis power off`, `tc qdisc … netem delay 20ms rate 1gbit`, `scontrol ping`, `node_network_up`, PromQL `absent()` | OK | iproute2 tc-netem(8); https://prometheus.io/docs/prometheus/latest/querying/functions/#absent | 2026-10 | none |
| capstone-g README.md:201; data events.jsonl | Xid 94 contained / 95 uncontained; Xid 63 "Row Remapper: New row marked for remapping, reset gpu to activate." | OK (VERIFIED_FACTS for 94/95) | https://docs.nvidia.com/deploy/xid-errors/index.html | 2026-10 | none |
| capstone-g README.md:202 | Pending row remap takes effect after GPU reset; remap failure ⇒ GPU should not return to service | OK (row-remapping page: reset required; RMA-policy page: failure flag ⇒ RMA criteria with field diag) | https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/row-remapping.html ; …/rma-policy-thresholds-for-row-remapping.html | 2026-10 | none |
| capstone-g README.md:204, starter-kit/README.md:108 | `NCCL_IB_TIMEOUT` 18 ≤ 2.22, 20 from 2.23 | OK (VERIFIED_FACTS) | — | — | none |
| capstone-g starter-kit/README.md:98 | `TORCH_NCCL_DESYNC_DEBUG`, `TORCH_NCCL_TRACE_BUFFER_SIZE` (flight recorder) | OK | https://docs.pytorch.org/docs/2.9/torch_nccl_environment_variables.html | PyTorch 2.9 | none |
| capstone-g data events.jsonl, README further reading | DCGM fields `DCGM_FI_DEV_ECC_SBE_VOL_TOTAL` (310), `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL` (311), `DCGM_FI_DEV_ROW_REMAP_PENDING` (396); mlx5 `link_down_events_phy`, `rx_crc_errors_phy` | OK | https://github.com/NVIDIA/DCGM/blob/master/dcgmlib/dcgm_fields.h ; mlx5 counters.rst | DCGM master | none |
| capstone-h serve.py:17-18 | PCIe Gen5 x16 ≈ 63 GB/s per direction theoretical | OK (32 GT/s × 16 × 128/130 ÷ 8; consistent with VERIFIED_FACTS 504 Gb/s) | PCI-SIG Base Spec 5.0 | — | none |
| capstone-h README.md:159-163 | RoCE path MTU, GDR evidence, ITL vs TPOT | OK (VERIFIED_FACTS) | — | — | none |
| capstone-h README.md:267 | Mooncake citation "2024" | **STALE** | https://arxiv.org/abs/2407.00079 ; https://www.usenix.org/conference/fast25/presentation/qin | 2026-10 | Added arXiv id and FAST 2025 venue/title |
| capstone-h README.md further reading (others); capstone-e/f/g further reading | DistServe OSDI'24, Splitwise ISCA'24, PagedAttention SOSP'23, Sarathi-Serve OSDI'24, Leviathan ICML'23, DCQCN SIGCOMM'15, NIST SP 800-193 (2018), SP 800-92 (2006), Crosby & Wallach USENIX Sec'09, Redfish DSP0266/DSP2046, Llama 3 54-day run | OK | publisher pages | — | none |

## Proposed VERIFIED_FACTS additions

| Topic | Proposed statement |
|---|---|
| H100 SXM peak numbers | Dense BF16 ≈ 989 TFLOP/s, dense FP8 ≈ 1,979 TFLOP/s (the datasheet's 1,979 / 3,958 are *with sparsity*); 80 GB HBM3 at 3.35 TB/s; NVLink4 900 GB/s total = 450 GB/s per direction; TDP up to 700 W `[VENDOR-SPEC, 2026-10]`. Source: nvidia.com/en-us/data-center/h100. Used in ch23, capstones A/D/H and earlier chapters. |
| DGX/HGX H100-class node power | 10.2 kW maximum system power (DGX H100/H200 user guide). Size rack budgets on this maximum and label sustained draw separately. |
| `NCCL_IB_HCA` matching | Tokens are prefixes unless the list starts with `=`; `^` makes it an exclude list; `^=mlx5_1` excludes exactly `mlx5_1`. Plain `mlx5_1` also matches `mlx5_10`–`mlx5_19` (NCCL 2.32.3 env docs). |
| mlx5 counter names | `ethtool -S`: `rx_prio<p>_pause`, `tx_prio<p>_pause`, `rx_vport_rdma_unicast_bytes`, `rx_crc_errors_phy`, `rx_discards_phy`, `link_down_events_phy`. RDMA hw_counters (`/sys/class/infiniband/<dev>/ports/<p>/hw_counters`): `np_cnp_sent`, `np_ecn_marked_roce_packets`, `rp_cnp_handled`, `out_of_sequence`, `local_ack_timeout_err`. Sources: kernel counters.rst and drivers/infiniband/hw/mlx5/counters.c. |
| DCGM ECC/row-remap fields | `DCGM_FI_DEV_ECC_SBE_VOL_TOTAL` (310), `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL` (311), `DCGM_FI_DEV_ROW_REMAP_PENDING` (396), `DCGM_FI_DEV_ROW_REMAP_FAILURE` (395). A pending remap takes effect only after a GPU reset. |
| PyTorch NCCL debug env vars | `TORCH_NCCL_DESYNC_DEBUG` and `TORCH_NCCL_TRACE_BUFFER_SIZE` (flight recorder; 0 disables), PyTorch 2.9 docs. |
| nccl-tests `-w` default | `-w` (warm-up iterations) defaults to 1 and `-n` defaults to 20. Pass `-w` explicitly when you claim a warm-up policy. |
| vLLM `--gpu-memory-utilization` | The default is 0.92 in current vLLM (latest docs, 2026-10); older releases used 0.90. State it explicitly in configs. |

## Cross-scope issues

None found during this pass. The scoped files reference chapters 08, 09, 12, 14 and 16 and VERIFIED_FACTS consistently. I did not audit files outside this scope.

Housekeeping observation, outside every agent's scope: the repository root holds two stray directories, `ch14-storage-pipelines-checkpointing/` and the untracked `network-compute-engineer-ai-infra/`. They look like misplaced copies. The first holds only `lab/`, `review/` and `solutions/`; the second holds only a `.git/` directory. The coordinator should check them. I did not touch them.

## validate_labs

`PYTHONIOENCODING=utf-8 python scripts/validate_labs.py` reported **32/32 labs valid** after the edits. A scoped run (`capstone ch23`) gave 9/9. One earlier full run reported 30/32 while other agents were editing at the same time. In that run capstone-h failed its no-generator check, and the second failure was outside this scope. The capstone-h failure did not come back on re-run, so it was transient. No lab data or answers changed: both edits are prose in a template and a reading list.
