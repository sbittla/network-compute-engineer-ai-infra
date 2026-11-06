# Chapter 5 hands-on lab: host topology from the inside

## 1. What you will do

You read your own machine's GPU topology with the chapter's tools (`nvidia-smi topo -m` and `-q`, `lspci`,
`lstopo`, `numactl`, sysfs), record what they show and what they cannot, and then measure the one path
this host does have: the GPU's PCIe link. You compare its negotiated generation and width with its
capability, measure host-to-device (H2D) and device-to-host (D2H) bandwidth from pinned and pageable
memory against the link's theoretical rate, and see what changes under load.

## 2. What is real here, and what is not

Real: the topology commands, the link state that `nvidia-smi` reports, and every copy, timed with CUDA
events on the GPU.

What this host cannot show, said plainly. On the reference machine (WSL2 on a laptop):

- **No PCIe tree.** WSL2 gives the guest paravirtual functions, not the real PCIe hierarchy. `lspci`
  lists four Hyper-V/virtio functions (two "Basic Render Driver" GPU-PV devices, vendor 1414). The NVIDIA
  GPU (vendor 10de) is not among them. There is no root port, no switch and no `LnkCap`/`LnkSta`, and the
  GPU's bus ID from `nvidia-smi` (`00000000:01:00.0`, the Windows host's view) does not exist in the
  guest's sysfs. So `PIX`, `PXB`, `PHB`, `NODE` and `SYS` cannot be observed here.
- **One GPU.** No GPU-to-GPU path, no NVLink, no peer-to-peer.
- **No NIC-to-GPU locality.** `nvidia-smi topo -m` prints no NIC columns. `eth0` is a Hyper-V synthetic
  NIC (`hv_netvsc`), not a PCIe device, and there is no RDMA HCA. Section 5.6's GPU-to-NIC pairing rule has
  nothing to pair, and GPUDirect RDMA is impossible.
- **No NUMA.** One node holds all 24 CPUs. Step 5 runs the copy with the process bound to the first and
  to the last CPU as a *null control*: on one node it should make no difference. On a two-socket HX8 the
  same commands with `numactl --cpunodebind=1 --membind=1` would cross UPI.

What `nvidia-smi` still reveals, because the driver reports it from the host side: the PCIe generation
and width, current against maximum, the host side's maximum generation, and the PCIe throughput counters
(`dmon -s t`). That is enough to compute the link's rate and to measure how close real copies come to it.

Absolute numbers are a laptop's Gen4 x8 link (15.75 GB/s per direction), not ORION's Gen5 x16 (63 GB/s).
The ratios carry over: the fraction of the link that pinned copies achieve, the penalty for pageable
memory and small transfers, and the comparison of current state against capability. Section 5.11's
L3 extension in [`../README.md`](../README.md) covers multi-GPU, multi-NIC hosts.

## 3. Requirements

| Item | Value |
|---|---|
| GPU | Yes: an NVIDIA GPU with `nvidia-smi` and CUDA (sized for 8 GB; uses under 1.5 GB) |
| Docker | No |
| Root | Yes, for `lspci -vvv` capabilities (the other steps work without it) |
| Disk | Under 10 MB of results |
| RAM | About 2 GiB free (pinned buffers up to 512 MiB) |
| Time | Setup 1–2 minutes; run about 1 minute plus any wait for the shared GPU lock |

## 4. Safety

Read-only toward the host: the lab queries topology and runs copy and GEMM benchmarks under the shared
GPU lock. It changes no interfaces, routes, BIOS or GPU settings (no clocks, no power limits, no
persistence mode). `teardown.sh` stops any benchmark left running.

## 5. Setup

```bash
cd book/part-2-accelerated-compute/ch05-gpu-interconnects-host-topology/lab/handson
sudo bash setup.sh          # pciutils, numactl, hwloc (pinned), plus the shared PyTorch venv
```

## 6. Steps

Run everything unattended with `sudo bash run.sh my-run` (results in `results/my-run/`), or step by step.
Write your answers in `results/<run-id>/answers.md`.

### Step 1: what the host shows

```bash
nvidia-smi -L; nvidia-smi topo -m
nvidia-smi -q | sed -n '/GPU Link Info/,/Link Width/{p}'
lspci -D -nn; lspci -tv; sudo lspci -vvv | grep -E 'LnkCap:|LnkSta:'
lstopo-no-graphics --of console
numactl --hardware
ls /sys/bus/pci/devices/; ls /sys/bus/pci/devices/0000:01:00.0     # the BDF nvidia-smi reported
ls /sys/class/infiniband; for n in /sys/class/net/*; do echo "$n -> $(readlink -f $n/device)"; done
```

Fill in the table "native server versus this host" for: GPU count, GPU in `lspci`, PCIe tree, `LnkCap`
and `LnkSta`, the GPU's BDF in sysfs, NUMA nodes, NIC columns, RDMA devices.

**Question 1.** Which of Section 5.6's three cross-checks (topo matrix, `lstopo`, sysfs) can you perform
on this host, and why does each one that fails, fail? What would you need to see GPU↔NIC locality?

### Step 2: the link `nvidia-smi` reports

```bash
nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.gen.gpucurrent,pcie.link.gen.max,pcie.link.gen.gpumax,pcie.link.gen.hostmax,pcie.link.width.current,pcie.link.width.max --format=csv -lms 250
```

Compute the link's rate per direction: GT/s × lanes × 128/130 ÷ 8 (Table 5.1).

**Question 2.** What generation and width did the link train to, against what the GPU and the host can
do? Which end limits the link, and what per-direction rate does that give? Did the link drop speed at idle?

### Step 3: copy bandwidth against the link

```bash
python bw.py sweep      # H2D and D2H, pinned and pageable, 64 KiB to 512 MiB
python bw.py bidir      # 256 MiB each way at the same time, on two streams
```

**Question 3.** What fraction of the link rate do pinned 256 MiB copies reach, and pageable ones? At what
size does a pinned copy reach about 80 % of its large-transfer rate, and why are 64 KiB copies so slow?
Does running both directions at once double the aggregate here, as a full-duplex link allows?

### Step 4: what changes under load

```bash
nvidia-smi --query-gpu=timestamp,pcie.link.gen.current,pcie.link.width.current --format=csv -lms 250 &
nvidia-smi dmon -s t -d 1 &
python bw.py hold --seconds 8; kill %1 %2
python bw.py contend    # pinned H2D alone, then while a GEMM loop runs on another stream
```

**Question 4.** Did the link generation or width change under sustained copies? Do the `dmon` PCIe
counters agree with the copy loop's own rate? Does a GEMM on another stream slow the copy engine?

### Step 5: does the copying CPU matter on this host?

```bash
numactl --cpunodebind=0 --membind=0 taskset -c 0 python bw.py point
taskset -c $(( $(nproc) - 1 )) python bw.py point
```

**Question 5.** What changes between the two placements, and why is that the expected answer on a
one-node host? What result would you expect on a two-socket server if the process and its pinned buffer
sit on the socket that does not own the GPU (Sections 3.4 and 5.5)?

## 7. Check your results

```bash
python3 check.py results/<run-id>
```

It checks completeness and physical sense: no copy beats the link, large copies beat small ones, pinned
memory is at least as fast as pageable, the link does not fall under load, and the capture is
internally consistent (a GPU absent from `lspci` must also be absent from sysfs).

## 8. Reference results

Measured on the reference machine (WSL2 Ubuntu 24.04, i7-13700HX, RTX 4060 Laptop GPU, driver 592.82);
the full bundle is in [`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/report.md).

| Measurement | Result |
|---|---|
| What WSL2 hides | No NVIDIA function in `lspci`, a flat PCIe tree, no `LnkCap` lines, one NUMA node, no NICs in `topo -m` |
| Link (from `nvidia-smi`) | Gen4 x8, the GPU's maximum, idle and under load; 15.75 GB/s per direction `[MODELED]` |
| Pinned copies, 256 MiB | H2D 12.96 GB/s (82 %), D2H 13.17 GB/s (84 %) |
| Pageable copies, 256 MiB | H2D 10.89 GB/s (69 %), D2H 11.02 GB/s (70 %) |
| Small copies, 64 KiB | 1.6–4.6 GB/s (10–29 %): per-copy overhead dominates |
| Both directions at once | 12.99 GB/s aggregate, 0.99× of one direction alone |
| Pinned H2D while a GEMM runs | 12.84 GB/s, 1.00× of the copy alone |

Pinned copies level off at about 83 % of the link rate. The rest goes to TLP headers, flow control and
DMA setup, the gap Section 5.2 calls achievable against raw. Pageable copies lose another 15 points to
the extra staging copy through a pinned bounce buffer. Running both directions at once gives no more
than one direction alone. On a native host PCIe is full duplex and the aggregate would approach twice
one direction. Under WSL2 the GPU is reached through the GPU paravirtualization layer, and copies in
the two directions appear to share one path. Treat this as a property of this platform, not of PCIe.
A GEMM running on another stream does not slow the copy, because the copy engines are separate from
the SMs.

Your numbers will differ. `check.py` tests physical sense, not equality.

## 9. Clean up

```bash
sudo bash teardown.sh
```

## 10. Connect to the chapter

| Step | Chapter section |
|---|---|
| 1 | Section 5.2 (hierarchy and addressing), Section 5.6 (`topo -m`, `lstopo`, cross-checks), Section 5.5 (NUMA) |
| 2 | Section 5.2 (bandwidth by generation, Table 5.1; capability versus status) |
| 3 | Section 5.2 (achievable versus raw), Section 3.4 (pinned memory) |
| 4 | Section 5.2 and the runbook (read counters under load) |
| 5 | Section 5.5 (NUMA, CPU affinity) |
