# Chapter 16 hands-on lab: accept this node

## 1. What you will do

You run a node acceptance suite against the machine in front of you and judge it the way Section 16.5
judges an HX8 node: cheap checks first, then a GPU stress run with numerical checks and telemetry, each
result tied to a reason code from Table 16.4, and a PASS/WARN/FAIL verdict against a versioned policy.
Then you decide whether the node is *validated*, which is a different question from whether nothing
failed.

## 2. What is real here, and what is not

Real: every value in the report is read from this machine (nvidia-smi, `/proc`, `/sys`, `dmesg`,
`ethtool`, fio on the raw disk, PyTorch GEMMs on the GPU, CPU reference GEMMs) and judged by
`evaluate.py` against `acceptance_policy_laptop.json`, whose thresholds are the chapter's.

Not real, or not ORION:

- **A laptop is not an HX8 node.** One RTX 4060 Laptop GPU (GDDR6, no ECC, no NVLink), one virtual NIC,
  one virtual disk. The policy's `expected` block is rewritten for this machine and every change is
  listed in the policy file and the report; the report also shows what the chapter's unadapted HX8
  policy says about the same evidence (it rejects it, correctly).
- **Many checks cannot run here, and say so.** DCGM (`dcgmi diag`) supports data-centre GPUs on
  bare-metal Linux, not a GeForce GPU in WSL2. ECC and row remapping need a GPU with memory ECC. NVLink,
  RDMA pair tests, link BER, GPUDirect RDMA and the 8-GPU NCCL test need hardware a laptop does not have.
  In WSL2 the NVIDIA kernel driver runs in Windows, so Xid events never reach the Linux kernel log. Each
  of these is reported **N/A**, with the probe that showed it.
- **Our GEMM and memory checks stand in for part of DCGM, not all of it.** They compare GPU results
  with a CPU reference and with a golden output while the GPU is hot, and write and verify patterns in
  device and host memory. They are lab-local checks (codes the chapter does not use) and are marked so.
- **The burn-in is 2 minutes, not 24 hours,** and the disk floor (1 GB/s) is an illustrative value, not a
  baseline measured on known-good nodes as Section 16.5 requires.

What carries over is the method: the cheap-first order, judging PCIe width under load, the throttle
reason classes, numerics checked hot, the median of repeated disk runs judged per device, and above all
the rule that N/A is not PASS. The chapter's Level 2/3 extensions in [../README.md](../README.md)
(Section 8) collect the rest on real servers.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | Yes, NVIDIA (peak 6.4 GiB of device memory allocated by PyTorch on the reference run, most of it the memory pattern test; it sizes the test to half the free memory, capped at 1.5 GiB per buffer) |
| Docker | No |
| Root | Yes: `dmesg`, raw block devices for read-only fio, package install |
| Disk | No free space needed (reads only) |
| RAM | 7 GB; the host pattern test uses at most 512 MiB or 20 % of available memory |
| Time | setup 1 min; run about 3-6 min (2 min of GPU stress, plus any wait for the shared GPU lock) |

## 4. Safety

- Read-only on every device: fio runs with `--readonly` against the disks that hold this OS's mounted
  file systems (on WSL2, the root VHDX). Never remove `--readonly`, and never point a write test at a disk
  holding data.
- The GPU stress draws full power for 2 minutes and heats the laptop; run it on a hard surface with the
  vents clear. It takes the shared GPU lock. No clocks or power limits are changed.
- No interfaces, routes, devices or files outside `results/` are created. Teardown only stops this lab's
  processes.

## 5. Setup

```bash
cd book/part-5-production-operations/ch16-bare-metal-fleet-lifecycle/lab/handson
sudo bash setup.sh        # fio 3.36, ethtool; the shared PyTorch venv; prints versions
```

On your own machine, edit `expected` in `acceptance_policy_laptop.json` (GPU product and memory, NIC,
host memory) and change `policy_version`: a policy written for someone else's SKU will fail your node on
`GPU_PRODUCT`, which is the point of versioned per-SKU policies.

## 6. Steps

`sudo bash run.sh <run-id>` runs the stages in the chapter's order and writes `results/<run-id>/`.

### Step 1: inventory and discovery (seconds)

```bash
nvidia-smi --query-gpu=index,uuid,pci.bus_id,name,memory.total,vbios_version,driver_version,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,ecc.mode.current --format=csv
nvidia-smi -q -d ECC,ROW_REMAPPER;  nvidia-smi nvlink --status;  command -v dcgmi
```

Look at the idle PCIe generation against its maximum, `ecc.mode.current`, and what the row-remapper
section reports.

**Question 1.** The driver reports `Remapped Rows: Pending No, Remapping Failure Occurred No`. Why does
the suite still mark `HBM_ROW_REMAP_PENDING` N/A instead of PASS?

### Step 2: kernel log, host memory, NICs (seconds)

```bash
sudo dmesg -T | grep -i xid;  lsmod | grep nvidia;  ls -l /dev/dxg
grep -E 'MemTotal|MemAvailable|HardwareCorrupted' /proc/meminfo;  ls /sys/devices/system/edac
ethtool eth0;  ethtool -i eth0;  ls /sys/class/infiniband
```

`collect_host.py` also writes and verifies 5 patterns over up to 512 MiB of host memory.

**Question 2.** `dmesg | grep -i xid` finds nothing. Under what condition is that evidence of a healthy
GPU, and why is that condition false here?

### Step 3: data disks, read-only fio per device (about 1 minute)

```bash
sudo fio --name=ch16-sdX --filename=/dev/sdX --readonly --rw=read --bs=1M --iodepth=32 \
    --ioengine=libaio --direct=1 --ramp_time=2 --runtime=8 --time_based --output-format=json
```

`/dev/sdX` stands for each disk that holds a mounted file system of this OS (`lsblk -o NAME,MOUNTPOINTS`
shows them; WSL2 names change between boots). One warm-up run, then three timed runs per disk; the median is judged against the per-device floor
and the sum against the total floor, as in Table 16.4.

**Question 3.** Why does the chapter judge every drive separately instead of only the aggregate, and
why the median of repeated runs rather than one run?

### Step 4: GPU memory, numerics, stress and telemetry (about 2.5 minutes, GPU lock)

```bash
. ../../../../../scripts/handson/venv.sh
sudo flock /tmp/handson-gpu.lock "$HANDSON_PY" gpu_stress.py --out results/<run-id> --seconds 120
nvidia-smi --query-gpu=timestamp,temperature.gpu,power.draw,clocks.sm,pcie.link.gen.current,pcie.link.width.current,utilization.gpu,clocks_event_reasons.active --format=csv -lms 500   # what it samples
```

In order: write and verify 5 patterns over up to 1.5 GiB of device memory; compare an FP32 GEMM (TF32
off) with a float64 CPU reference and an FP16 GEMM with a float32 CPU reference of the same inputs
(tolerances fixed in the script before it runs); run FP16 4096³ GEMMs for 120 s, checking every 2 s
that a fixed input still gives a bit-identical output; repeat the CPU comparison while the GPU is hot.
nvidia-smi samples temperature, power, clocks, PCIe link and clock-event reasons every 500 ms, and the
reason counters are read before and after.

**Question 4.** Which clock-event reasons were active under load, and which policy list is each in?
Did the PCIe link run at its maximum generation and width under load? Why does the chapter judge
the link under load but the width at any time?

### Step 5: the verdict

```bash
python3 evaluate.py results/<run-id>
```

**Question 5.** What is the verdict on the checks that ran, and what is the acceptance decision?
Explain the difference, and say which three N/A checks you would most want to turn into real tests
before letting this class of machine run production jobs, and why.

## 7. Check your results

```bash
python check.py results/<run-id>        # or, from the repository root: python scripts/handson.py check ch16 <run-id>
```

The checker does not require the node to pass. It requires that every Table 16.4 reason code has a
status and evidence, that the verdict and decision follow from the statuses (N/A never counted as PASS),
that checks which cannot run on WSL2 are N/A, and that the stress, telemetry, PCIe and disk evidence is
present and plausible. Write your answers in `results/<run-id>/answers.md`.

## 8. Reference results

Measured on the reference machine (WSL2 Ubuntu 24.04, i7-13700HX, 7.8 GiB for WSL, RTX 4060 Laptop GPU,
driver 592.82, VBIOS 95.07.28.00.59, fio 3.36, PyTorch 2.5.1); the full bundle, with the acceptance
record and every raw command output, is in
[`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/report.md). Every value is `[MEASURED]`.

**Verdict on the checks that ran: PASS (17 PASS, 0 WARN, 0 FAIL). Acceptance decision: NOT VALIDATED,
because 12 required checks produced no evidence (N/A).**

| Stage | Check | Measured | Status |
|---|---|---|---|
| discovery | `GPU_COUNT`, `GPU_PRODUCT`, `HBM_CAPACITY` | 1 × RTX 4060 Laptop GPU, 8,188 MiB GDDR6 | PASS |
| pcie | `PCIE_DEGRADED` | Gen4 x8 under load (median of 226 samples), which is this GPU's maximum | PASS |
| gpu-health | `GPU_MEM_PATTERN` (lab-local) | 1.50 GiB × 5 patterns, 0 mismatched words; fill 100 GB/s | PASS |
| gpu-health | `GPU_NUMERICS` (lab-local) | FP32 GEMM error 3.5e-7 (limit 1e-5), FP16 5.1e-5 (limit 2e-3), cold and hot; golden output 0 of 59 mismatched | PASS |
| burn-in | `THERMAL_THROTTLE` | max 76 °C over 120 s; only `SW_POWER_CAP` active (100 % of loaded samples) | PASS |
| burn-in | `STRESS_PERF_DECAY` (lab-local) | FP16 GEMM 27.7 TFLOP/s median (27.0-28.2), no decay from the first third to the last | PASS |
| host | `HOST_MEM_CAPACITY`, `HOST_MEM_PATTERN` (lab-local) | 7.75 GiB; 512 MiB × 5 patterns, 0 bad chunks | PASS |
| nic | `NIC_COUNT`, `NIC_LINK_DOWN`, `NIC_SPEED`, `NIC_MTU` | eth0 (hv_netvsc) up, reports 10,000 Mb/s, MTU 1500 | PASS |
| storage | `NVME_COUNT`, `NVME_DRIVE_SLOW`, `STORAGE_THROUGHPUT_LOW` | 1 virtual disk (sdd); read-only 1 MiB QD 32: 7.15, 8.02, 7.63 GB/s, median 7.63 | PASS |
| everything else | NVLink, ECC, row remap, DCGM, host ECC, RDMA, link BER, GPUDirect, SMART, NCCL, Xid, firmware matrix | no hardware or no driver path to test | N/A |

What the numbers mean:

- **The power limit, not heat, sets the clock.** The GPU drew a median 79.9 W against its 80 W enforced
  limit, and `SW_POWER_CAP` was active in every loaded sample, so the SM clock sat at 2,295 MHz, 74 % of
  the 3,105 MHz maximum. The policy ignores `SW_POWER_CAP` because a GPU at its power limit is working
  as designed. The temperature peaked at 76 °C, 11 °C under the 87 °C limit, and no thermal or
  power-brake reason appeared. Steady 27.7 TFLOP/s with no decay over 120 s is what a healthy,
  power-limited GPU looks like.
- **The driver's clock-event counters are not trustworthy here.** The `sw_power_cap` counter grew by
  0 µs during this run, and by 0.8 s and 3.0 s in two earlier runs, although the reason was active for
  the whole 120 s each time. In WSL2 the counters come from the Windows driver. The suite therefore
  judges the reasons from the 500 ms samples and records the counters only as supporting evidence.
- **Numerics are bit-stable, cold and hot.** The hot GEMM errors equal the cold ones to every digit, and
  59 golden checks during the stress all matched bit for bit. A GPU with a marginal SM or memory cell
  under heat shows up here as a mismatch, not as a slower run.
- **PCIe Gen4 x8 is the maximum for this GPU**, so `PCIE_DEGRADED` passes. Under the chapter's HX8
  policy (Gen5 x16) the same evidence fails, as do eight other codes in the report's HX8 table. The link
  also reported Gen4 at idle (54 °C, SM at 2,550 MHz before the stress, probably still busy from another
  lab's run). A truly idle GPU usually drops its link to Gen1 to save power, which is why the chapter
  judges the generation under load and the width at any time.
- **The disk numbers swing between runs** (4.69-8.68 GB/s per timed run across three runs of this
  lab), because the virtual disk shares the laptop's drive and Windows cache with everything else,
  including other labs running at the same time. The median of three timed runs is well above the
  illustrative 1 GB/s floor every time. A single fast run (8.68 GB/s) next to a slow one (4.69 GB/s)
  is why Table 16.4 judges the median of repeated runs and never one run.
- **PASS on the checks that ran does not make the node validated.** Twelve required checks are N/A.
  Each N/A means no evidence, and a fleet controller must treat missing evidence like a missing test,
  not like a pass.


Results on other hardware will differ; the checker tests physical sense, not equality.

## 9. Clean up

```bash
sudo bash teardown.sh     # run.sh already calls it, even after a failure
```

The suite creates nothing outside `results/`; teardown stops any fio, stress or collector process this
lab started and confirms none is left.

## 10. Connect to the chapter

| Step | Chapter section |
|---|---|
| 1 | 16.5 Discovery and PCIe topology; GPU health: DCGM diagnostics, ECC and row remapping |
| 2 | 16.5 GPU health (Xid table), NICs and RDMA |
| 3 | 16.5 Storage; Chapter 14 Section 14.2 (one slow drive paces a stripe) |
| 4 | 16.5 Thermals and burn-in (clock event reasons, Listing 16.8) |
| 5 | 16.5 Table 16.4 and the policy verdict; 16.1 the lifecycle state machine (`validated` needs PASS or WARN + waiver) |

## Troubleshooting

- **`ERROR: this step needs root: run with sudo`** → run `sudo bash setup.sh` and `sudo bash run.sh <run-id>`.
  Root is needed for `dmesg`, read-only `fio` on the raw disks and the package install.
- **`ERROR: missing command: fio (run setup.sh)`** (or `ethtool`, `lsblk`) → run `sudo bash setup.sh`.
  It uses `apt-get`; on a distribution without it, install fio 3.28 or later, ethtool, iproute2 and
  util-linux with your own package manager.
- **`ERROR: no NVIDIA GPU visible (nvidia-smi failed)`** → this suite needs an NVIDIA GPU and has no CPU
  mode (use the L1 lab in [../README.md](../README.md) instead). Run `nvidia-smi -L` as your own user
  first. On WSL2, `nvidia-smi` lives in `/usr/lib/wsl/lib` and the scripts add that to `PATH` under sudo.
  If it also fails without sudo, update the Windows NVIDIA driver and run `wsl --update`.
- **The run stops at "Stage 4 ... (waits for the shared GPU lock)"** → another hands-on lab holds
  `/tmp/handson-gpu.lock`. `lslocks | grep handson-gpu` shows which process. Let it finish; the stage
  starts by itself when the lock is released.
- **Setup is slow the first time, or later fails inside the venv** → `scripts/handson/venv.sh` builds the
  shared environment at `~/.venvs/ai-infra-handson` on first use and downloads PyTorch 2.5.1 (CUDA 12.4),
  so it needs network access. Under `sudo`, `~` can be root's home, so the manual Step 4 command run as
  your user may build a second venv. If a download was interrupted, delete the venv folder and run
  `sudo bash setup.sh` again.
- **`check.py` reports `missing from the bundle: [...] (did run.sh finish?)`** → `run.sh` stopped before
  the verdict. Read the logs in `results/<run-id>/raw/` (`collect_host.log`, `gpu_stress.log`), fix the
  cause, and rerun with a new run-id. A line such as `fio /dev/sdX rep 1: rc=1` means fio failed on that
  disk; its JSON output is in the same `raw/` folder.
