# Lab 3 L2: read-only host discovery and triage on a real GPU host, idle and under load

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:37:02Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

## 1. The read-only guard

- 13 commands in the plan, all read-only: **True**.
- 19/19 mutating or unknown forms refused by `argv_is_read_only()`; `run_command()` refused them without executing anything: **True** (0.04 ms for all of them).

| Refused form | Refused |
|---|---|
| `nvidia-smi -pl 100` | True |
| `nvidia-smi --power-limit=100` | True |
| `nvidia-smi -r` | True |
| `nvidia-smi -lgc 1500,1500` | True |
| `nvidia-smi -pm 1` | True |
| `nvidia-smi --query-gpu index --format csv -pl 100` | True |
| `ethtool -s eth0 speed 1000` | True |
| `ethtool -K eth0 gro off` | True |
| `ip link set eth0 mtu 1500` | True |
| `ip link set dev eth0 down` | True |
| `taskset -cp 0-3 1` | True |
| `setpci -s 01:00.0 CAP_EXP+10.w=0` | True |
| `sysctl -w vm.swappiness=1` | True |
| `numactl --membind=0 true` | True |
| `dmesg -C` | True |
| `sh -c lscpu` | True |
| `lscpu ; reboot` | True |
| `journalctl --vacuum-size=1M` | True |
| `nvidia-smi --query-gpu index;reboot --format csv` | True |

## 2. Inventory: collector + parsers vs an independent probe

| Field | Collector (`lscpu`/`free`, parsed by the lab's analyzer) | Independent probe |
|---|---|---|
| cpus | 24 | 24 |
| sockets | 1 | 1 |
| cores_per_socket | 12 | 12 |
| threads_per_core | 2 | 2 |
| numa_nodes | 1 | 1 |
| memory (MiB) | 7938 | 7938 (/proc/meminfo) |
| model | 13th Gen Intel(R) Core(TM) i7-13700HX | 13th Gen Intel(R) Core(TM) i7-13700HX |

Probe source: /proc/cpuinfo (physical id, cpu cores, siblings), /sys/devices/system/node, /proc/meminfo, torch.cuda.device_count() (GPU run) or display-class functions in /sys/bus/pci/devices (CPU run).

## 4. Evidence gaps (loaded snapshot, non-root)

| Section | Status | Why |
|---|---|---|
| cpufreq | missing | no cpufreq interface (VM, container, or cpufreq disabled) |
| kernel_log | missing | dmesg: read kernel buffer failed: Operation not permitted |
| nvidia_smi | missing | nvidia-smi not found in /usr/sbin:/usr/bin:/sbin:/bin |

13/16 sections ok. Each gap is a finding (EVIDENCE_GAP, info), not a crash: that is the collector's contract.

## 5. Triage with a baseline written for this host

| Host | Critical | Warning | Info | Verdict |
|---|---|---|---|---|
| l2host-idle | 0 | 0 | 3 | healthy (check gaps) |
| l2host-loaded | 0 | 0 | 3 | healthy (check gaps) |

## Info (6)

- **l2host-idle** `EVIDENCE_GAP` [cpufreq] — read /sys/devices/system/cpu/cpu*/cpufreq: missing - no cpufreq interface (VM, container, or cpufreq disabled)
- **l2host-idle** `EVIDENCE_GAP` [kernel_log] — journalctl -k -b --no-pager: missing - dmesg: read kernel buffer failed: Operation not permitted | journalctl not found in /usr/sbin:/usr/bin:/sbin:/bin
- **l2host-idle** `EVIDENCE_GAP` [nvidia_smi] — nvidia-smi --query-gpu=index,pci.bus_id,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,utilization.gpu --format=csv: missing - nvidia-smi not found in /usr/sbin:/usr/bin:/sbin:/bin
- **l2host-loaded** `EVIDENCE_GAP` [cpufreq] — read /sys/devices/system/cpu/cpu*/cpufreq: missing - no cpufreq interface (VM, container, or cpufreq disabled)
- **l2host-loaded** `EVIDENCE_GAP` [kernel_log] — journalctl -k -b --no-pager: missing - dmesg: read kernel buffer failed: Operation not permitted | journalctl not found in /usr/sbin:/usr/bin:/sbin:/bin
- **l2host-loaded** `EVIDENCE_GAP` [nvidia_smi] — nvidia-smi --query-gpu=index,pci.bus_id,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,utilization.gpu --format=csv: missing - nvidia-smi not found in /usr/sbin:/usr/bin:/sbin:/bin

## 6. The same snapshots against the ORION HX8 baseline

- **l2host-idle** `INTERFACE_MISSING` [fe0] — fe0 not present in ip link show
- **l2host-idle** `INTERFACE_MISSING` [fe1] — fe1 not present in ip link show
- **l2host-idle** `INTERFACE_MISSING` [rail0] — rail0 not present in ip link show
- **l2host-idle** `INTERFACE_MISSING` [rail1] — rail1 not present in ip link show
- **l2host-idle** `INTERFACE_MISSING` [rail2] — rail2 not present in ip link show
- **l2host-idle** `INTERFACE_MISSING` [rail3] — rail3 not present in ip link show
- **l2host-idle** `INTERFACE_MISSING` [rail4] — rail4 not present in ip link show
- **l2host-idle** `INTERFACE_MISSING` [rail5] — rail5 not present in ip link show
- **l2host-idle** `INTERFACE_MISSING` [rail6] — rail6 not present in ip link show
- **l2host-idle** `INTERFACE_MISSING` [rail7] — rail7 not present in ip link show

A laptop is not an HX8 node: the inventory rules fire at once. Writing the baseline for the platform you actually run is step one of Section 9's L2 instructions (`my_baseline.yaml`; the one used here is in `results.json` under `baseline_yaml`).

## What to conclude

- The collector ran on a real host without root, changed nothing, and told you exactly which evidence it could not collect and why; the guard refused every mutating form before any process was started.
- Parsers that pass on simulated ORION snapshots also agree with an independent probe of a real machine; that cross-check is what makes the triage verdicts credible.
- The ORION-class findings (rails, MTU 9000, eight GPUs on Gen5 x16) need the real platform: see the table below.

_CPU fallback: no GPU was used. nvidia-smi was absent (reported as an evidence gap, as designed); the PCIe link comparison and the GPU-only invariants were skipped._

## Not runnable on this host (probed, not faked)

| Part | Probe | Needs | Used instead |
|---|---|---|---|
| root snapshot (sudo python host_collector.py ...) | euid = 1000 | root in the container (the harness runs as uid 1000 and never escalates) | non-root snapshots; sections that need root are recorded as denied |
| L3: collector on every node during all_reduce_perf; cross-host MTU/link checks | /sys/class/infiniband absent | 2+ RDMA-connected GPU nodes, nccl-tests | the idle and loaded snapshots of this host analysed as a two-member 'fleet' |

- Both snapshots are non-root and read-only; the analyzer treats them as two hosts (l2host-idle, l2host-loaded).
- The machine is shared: 'idle' means this experiment was not loading the GPU, not that nothing else was.
- Snapshot wall time is dominated by vmstat 1 5 (5 s of sampling by design).
- WSL2: sysfs lists 2 Microsoft (vendor 0x1414) GPU-PV display functions (6294:00:00.0, a1c2:00:00.0), the paravirtual adapters through which the hypervisor shares the host's GPUs (likely the NVIDIA GPU and the CPU's integrated GPU), with no link-speed files. Without nvidia-smi the analyzer's sysfs fallback counts these as GPUs; on a native Linux host the same rule sees the real NVIDIA functions (vendor 0x10de) with their link state.
