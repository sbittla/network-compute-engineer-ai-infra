# Capstone G L2: real read-only health evidence and a validated checkpoint/resume drill

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:19:17Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

## 1. Read-only evidence on this host

| Command | available | first output |
|---|---|---|
| `nvidia-smi inventory` | True | 0, GPU-fe211e06-dfa3-0d80-fb58-b775a89cc629, 00000000:01:00.0 |
| `nvidia-smi -q -d ECC` | True | ==============NVSMI LOG============== |
| `nvidia-smi -q -d ROW_REMAPPER` | True | ==============NVSMI LOG============== |
| `journalctl -k` | False | journalctl: not installed |
| `dmesg` | False | dmesg: read kernel buffer failed: Operation not permitted |
| `rdma link show` | False | Failed to open NETLINK_RDMA socket |
| `ethtool -S` | False | no stats available |
| `lldpctl` | False | lldpctl: not installed |
| `chronyc tracking` | False | chronyc: not installed |
| `dcgmi discovery -l` | False | dcgmi: not installed |

Events produced by the adapters: 2 (DCGM_FI_DEV_ROW_REMAP_FAILURE, DCGM_FI_DEV_ROW_REMAP_PENDING).
L1 `normalize_events` -> 2 rows (dcgm); `health_scores` -> nothing flagged (`instructor/reference/ftops.py`).
Positive control (synthetic: the same event with ROW_REMAP_PENDING=1): {'gpu:f0533d9d1b4c:0': {'score': 60, 'evidence': ['row remap pending']}}. The healthy verdict comes from a path that can flag.

Format differences against the synthetic bundle (`log_format_differences`):

- nvidia-smi pci.bus_id is '00000000:01:00.0' (8-hex-digit PCI domain); the kernel Xid line prints 'PCI:0000:01:00' (4-digit domain, no function) and the synthetic inventory uses '0000:01:00.0': normalise the domain width and the function suffix in the adapter
- no DCGM here: field values come from nvidia-smi text and are renamed to DCGM_FI_* by the adapter; nvidia-smi reports 'Yes/No' for remap pending/failure, DCGM reports counts
- ECC counters are 'N/A' on this GPU (GeForce, no ECC): the adapter must emit nothing, not 0. A 0 would read as 'checked and clean'
- host_ts here is the container's clock with no chrony offset available; the synthetic data carries per-host offsets from clock_offsets.csv

## 2. Resume validation on a real training run (L1 `validate_resume`)

MLP width 1024, batch 256, 200 pre-fault steps, checkpoint at step 100100. Replay noise (same checkpoint restored twice): loss 0.0e+00, grad_norm 0.0e+00 (relative) -> tolerance **1e-05** (10x the observed maximum, floor 1e-5).

| Resume | first_step_ok | sample_idx_ok | continuity_ok | progressed | max rel dev | ok |
|---|---|---|---|---|---|---|
| validated (model + optimizer + data cursor) | True | True | True | True | 0.0e+00 | **True** |
| data loader not restored | True | False | False | True | 2.3e-01 | **False** |
| optimizer state not restored | True | True | False | True | 3.9e-02 | **False** |

## 3. Checkpoint commit protocol (L1 `select_checkpoint`)

4 shards x 32 MiB per checkpoint; metadata with SHA-256 written last. Step 3000 had `shard_02.bin` corrupted after commit; step 4000 was SIGKILLed after its first shard.

| Step | metadata committed | missing shards | checksum failures |
|---|---|---|---|
| 1000 | True | - | - |
| 2000 | True | - | - |
| 3000 | True | - | [2] |
| 4000 | False | [1, 2, 3] | - |

Selected: **step 2000**; rejected: 4000: metadata not committed, 3 missing shards; 3000: checksum failure on shards [2].

Checkpoint write 0.26 GB/s median of 3 (range 0.19-0.33), restore read 2.22 GB/s on the container's overlay file system `[MEASURED]`.

## Not runnable here

- **dcgmi discovery -l**. Probe: rc=127: dcgmi: not installed. Needs: DCGM on a data-center GPU host.
- **journalctl -k**. Probe: rc=127: journalctl: not installed. Needs: host kernel log (root, not a container).
- **dmesg**. Probe: rc=1: dmesg: read kernel buffer failed: Operation not permitted. Needs: host kernel log (root).
- **rdma link show**. Probe: rc=1: Failed to open NETLINK_RDMA socket. Needs: RDMA NIC + iproute2 rdma.
- **ethtool -S**. Probe: rc=94: no stats available. Needs: a real NIC netdev and ethtool.
- **lldpctl**. Probe: rc=127: lldpctl: not installed. Needs: lldpd on a host cabled to a switch.
- **chronyc tracking**. Probe: rc=127: chronyc: not installed. Needs: chrony on the host.
- **L3 drill: kill a rank, NCCL watchdog timing, link flap, drain + restart on >= 2 RDMA nodes**. Probe: GPUs=1, RDMA devices=none. Needs: >= 2 GPU nodes with RDMA NICs, lab scheduler, shared storage.

## What to conclude

- Measure the replay noise and derive the tolerance from it. Then the resume check is strict enough to catch a data loader that restarted from sample 0, *and* a resume that dropped the optimizer state. Loss alone looks plausible in both.
- A checkpoint is restorable only if its commit record exists and every shard matches its checksum. Reading 'the newest directory' would have restored a half-written or corrupted checkpoint.
- Real tools disagree with the synthetic formats (PCI domain width, N/A versus 0, Yes/No versus counts). The adapter is where these differences are handled. Emitting 0 for N/A would hide a missing signal.
- This is a **laptop Ada GPU in a container**: no DCGM, ECC, kernel log or RDMA. The read-only part shows how much of the L2 command list depends on host access a container does not have.

- Resume drill: one process, three restores of the same in-memory checkpoint into freshly initialised models (different init seed), so a missing restore cannot hide behind identical initial weights.
- Commit protocol: shards first (each fsynced), metadata with SHA-256 per shard last, renamed into place; the rename is the commit point. The kill lands after shard 0 is durable.
- Throughput: write = subprocess wall time for shards + metadata (incl. interpreter start); read = all shards of one checkpoint with the page cache dropped per file.
