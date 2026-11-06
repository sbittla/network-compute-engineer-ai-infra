# Host diagnostic snapshot — srini

- Collected at: 2026-11-05T04:11:59Z
- Platform: linux; running as root: no
- Schema: hostdiag/1; collector 1.0
- Context: note=ch03 hands-on: idle host, non-root (nobody)

Evidence gaps: 2 of 15 sections not ok (nvidia_smi, cpufreq)

| Section | Command | Status | Elapsed (s) |
|---|---|---|---|
| uname | `uname -a` | ok | 0.00 |
| lscpu | `lscpu` | ok | 0.00 |
| numactl_hardware | `numactl --hardware` | ok | 0.00 |
| free | `free -m` | ok | 0.00 |
| vmstat | `vmstat 1 5` | ok | 4.01 |
| iostat | `iostat -x 1 2` | ok | 1.00 |
| mpstat | `mpstat -P ALL 1 1` | ok | 1.00 |
| ip_link | `ip link show` | ok | 0.00 |
| ethtool:eth0 | `ethtool eth0` | ok | 0.00 |
| lspci | `lspci -vv` | ok | 0.01 |
| nvidia_smi | `nvidia-smi --query-gpu=index,pci.bus_id,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,utilization.gpu --format=csv` | missing | 0.00 |
| kernel_log | `dmesg -T` | ok | 0.00 |
| pcie_sysfs | `read /sys/bus/pci/devices/*/{class,numa_node,*_link_*,aer_dev_*}` | ok | 0.00 |
| interrupts | `read /proc/interrupts` | ok | 0.00 |
| cpufreq | `read /sys/devices/system/cpu/cpu*/cpufreq` | missing | 0.00 |

## uname

Status: **ok** (rc=0)

```text
Linux srini 6.18.54.1-rxe+ #1 SMP PREEMPT_DYNAMIC Wed Nov  4 17:29:39 PST 2026 x86_64 x86_64 x86_64 GNU/Linux
```

## lscpu

Status: **ok** (rc=0)

```text
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           39 bits physical, 48 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  24
On-line CPU(s) list:                     0-23
Vendor ID:                               GenuineIntel
Model name:                              13th Gen Intel(R) Core(TM) i7-13700HX
CPU family:                              6
Model:                                   191
Thread(s) per core:                      2
Core(s) per socket:                      12
Socket(s):                               1
Stepping:                                2
BogoMIPS:                                4608.00
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology tsc_reliable nonstop_tsc cpuid tsc_known_freq pni pclmulqdq vmx ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch ssbd ibrs ibpb stibp ibrs_enhanced tpr_shadow ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 xsaves avx_vnni vnmi umip waitpkg gfni vaes vpclmulqdq rdpid movdiri movdir64b fsrm md_clear serialize ibt flush_l1d arch_capabilities
Virtualization:                          VT-x
Hypervisor vendor:                       Microsoft
Virtualization type:                     full
L1d cache:                               576 KiB (12 instances)
L1i cache:                               384 KiB (12 instances)
L2 cache:                                15 MiB (12 instances)
L3 cache:                                30 MiB (1 instance)
NUMA node(s):                            1
NUMA node0 CPU(s):                       0-23
Vulnerability Gather data sampling:      Not affected
Vulnerability Ghostwrite:                Not affected
Vulnerability Indirect target selection: Not affected
Vulnerability Itlb multihit:             Not affected
Vulnerability L1tf:                      Not affected
Vulnerability Mds:                       Not affected
Vulnerability Meltdown:                  Not affected
Vulnerability Mmio stale data:           Not affected
Vulnerability Old microcode:             Not affected
Vulnerability Reg file data sampling:    Mitigation; Clear Register File
Vulnerability Retbleed:                  Mitigation; Enhanced IBRS
Vulnerability Spec rstack overflow:      Not affected
Vulnerability Spec store bypass:         Mitigation; Speculative Store Bypass disabled via prctl
Vulnerability Spectre v1:                Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:                Mitigation; Enhanced / Automatic IBRS; IBPB conditional; PBRSB-eIBRS SW sequence; BHI BHI_DIS_S
... (4 more lines)
```

## numactl_hardware

Status: **ok** (rc=0)

```text
available: 1 nodes (0)
node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
node 0 size: 7938 MB
node 0 free: 6525 MB
node distances:
node   0 
  0:  10 
```

## free

Status: **ok** (rc=0)

```text
               total        used        free      shared  buff/cache   available
Mem:            7938         687        6525           4         880        7250
Swap:           8192           0        8192
```

## vmstat

Status: **ok** (rc=0)

```text
procs -----------memory---------- ---swap-- -----io---- -system-- -------cpu-------
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st gu
 0  0      0 6682216  50680 851076    0    0 18467  3586 1805    0  5  0 95  0  0  0
 0  0      0 6685932  50680 851316    0    0     0     0  301  179  0  0 100  0  0  0
 0  0      0 6686980  50680 851316    0    0     0     0  293  198  0  0 100  0  0  0
 0  0      0 6693204  50692 851320    0    0     0   100  243  194  0  0 100  0  0  0
 0  0      0 6701012  50692 851320    0    0     0     0  258  198  0  0 100  0  0  0
```

## iostat

Status: **ok** (rc=0)

```text
Linux 6.18.54.1-rxe+ (srini) 	11/04/26 	_x86_64_	(24 CPU)

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           1.50    3.20    0.40    0.10    0.00   94.79

Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz     d/s     dkB/s   drqm/s  %drqm d_await dareq-sz     f/s f_await  aqu-sz  %util
sda              2.34    509.58     1.39  37.29    0.30   218.03    0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    0.00   0.06
sdb              0.32      7.56     0.00   0.00    0.05    23.84    0.01      0.01     0.00   0.00    1.00     2.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    1.00    0.00   0.00
sdc              1.85     40.12     0.00   0.00    0.18    21.72    0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    0.00   0.02
sdd             69.10  17637.22    58.19  45.71    0.83   255.23    7.84   3540.55     7.22  47.95   11.94   451.74    2.12   4682.14     0.08   3.49    0.27  2205.76    1.41    0.71    0.15   2.12


avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           0.00    0.00    0.00    0.00    0.00  100.00

Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz     d/s     dkB/s   drqm/s  %drqm d_await dareq-sz     f/s f_await  aqu-sz  %util
sda              0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    0.00   0.00
sdb              0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    0.00   0.00
sdc              0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    0.00   0.00
sdd              0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    0.00   0.00


```

## mpstat

Status: **ok** (rc=0)

```text
Linux 6.18.54.1-rxe+ (srini) 	11/04/26 	_x86_64_	(24 CPU)

20:12:04     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
20:12:05     all    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       0    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       1    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       2    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       3    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       4    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       5    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       6    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       7    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       8    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05       9    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      10    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      11    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      12    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      13    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      14    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      15    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      16    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      17    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      18    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      19    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      20    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      21    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      22    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
20:12:05      23    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00

Average:     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
Average:     all    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
Average:       0    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
Average:       1    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
Average:       2    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
Average:       3    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
Average:       4    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
Average:       5    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
Average:       6    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
Average:       7    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
Average:       8    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
... (15 more lines)
```

## ip_link

Status: **ok** (rc=0)

```text
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
    link/ether 00:15:5d:b8:90:12 brd ff:ff:ff:ff:ff:ff
```

## ethtool:eth0

Status: **ok** (rc=0)

```text
Settings for eth0:
	Supported ports: [  ]
	Supported link modes:   Not reported
	Supported pause frame use: No
	Supports auto-negotiation: No
	Supported FEC modes: Not reported
	Advertised link modes:  Not reported
	Advertised pause frame use: No
	Advertised auto-negotiation: No
	Advertised FEC modes: Not reported
	Speed: 10000Mb/s
	Duplex: Full
	Auto-negotiation: off
	Port: Other
	PHYAD: 0
	Transceiver: internal
        Current message level: 0x000000f7 (247)
                               drv probe link ifdown ifup rx_err tx_err
	Link detected: yes
```

## lspci

Status: **ok** (rc=0)

```text
4140:00:00.0 3D controller: Microsoft Corporation Basic Render Driver
	Physical Slot: 279844141
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
	Latency: 0
	NUMA node: 0
	Capabilities: <access denied>
	Kernel driver in use: dxgkrnl

5582:00:00.0 SCSI storage controller: Red Hat, Inc. Virtio 1.0 console (rev 01)
	Subsystem: Red Hat, Inc. Virtio 1.0 console
	Physical Slot: 3300344309
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
	Latency: 64
	NUMA node: 0
	Region 0: Memory at 9ffe00000 (64-bit, non-prefetchable) [size=4K]
	Region 2: Memory at 9ffe01000 (64-bit, non-prefetchable) [size=4K]
	Region 4: Memory at 9ffe02000 (64-bit, non-prefetchable) [size=4K]
	Capabilities: <access denied>
	Kernel driver in use: virtio-pci

953e:00:00.0 3D controller: Microsoft Corporation Basic Render Driver
	Physical Slot: 2712386113
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
	Latency: 0
	NUMA node: 0
	Capabilities: <access denied>
	Kernel driver in use: dxgkrnl

ecb7:00:00.0 System peripheral: Red Hat, Inc. Virtio file system (rev 01)
	Subsystem: Microsoft Corporation Virtio file system
	Physical Slot: 4111083826
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
	Latency: 0
	NUMA node: 0
	Region 0: Memory at e00000000 (64-bit, prefetchable) [size=4K]
	Region 2: Memory at e00001000 (64-bit, prefetchable) [size=4K]
... (4 more lines)
```

## nvidia_smi

Status: **missing** (rc=None)

stderr: nvidia-smi not found in /usr/sbin:/usr/bin:/sbin:/bin

## kernel_log

Status: **ok** (rc=0)

```text
[Wed Nov  4 20:06:51 2026] Linux version 6.18.54.1-rxe+ (root@srini) (gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, GNU ld (GNU Binutils for Ubuntu) 2.42) #1 SMP PREEMPT_DYNAMIC Wed Nov  4 17:29:39 PST 2026
[Wed Nov  4 20:06:51 2026] Command line: initrd=\initrd.img WSL_ROOT_INIT=1 panic=-1 nr_cpus=24 hv_utils.timesync_implicit=1 printk.devkmsg=on page_reporting.page_reporting_order=5 hv_storvsc.storvsc_max_hw_queues=4 console=hvc0 debug pty.legacy_count=0 WSL_ENABLE_CRASH_DUMP=1
[Wed Nov  4 20:06:51 2026] KERNEL supported cpus:
[Wed Nov  4 20:06:51 2026]   Intel GenuineIntel
[Wed Nov  4 20:06:51 2026]   AMD AuthenticAMD
[Wed Nov  4 20:06:51 2026] BIOS-provided physical RAM map:
[Wed Nov  4 20:06:51 2026] BIOS-e820: [mem 0x0000000000000000-0x000000000009ffff] usable
[Wed Nov  4 20:06:51 2026] BIOS-e820: [mem 0x00000000000e0000-0x00000000000e0fff] reserved
[Wed Nov  4 20:06:51 2026] BIOS-e820: [mem 0x0000000000100000-0x00000000001fffff] ACPI data
[Wed Nov  4 20:06:51 2026] BIOS-e820: [mem 0x0000000000200000-0x00000000f7ffffff] usable
[Wed Nov  4 20:06:51 2026] BIOS-e820: [mem 0x0000000100000000-0x0000000207ffffff] usable
[Wed Nov  4 20:06:51 2026] NX (Execute Disable) protection: active
[Wed Nov  4 20:06:51 2026] APIC: Static calls initialized
[Wed Nov  4 20:06:51 2026] DMI not present or invalid.
[Wed Nov  4 20:06:51 2026] Hypervisor detected: Microsoft Hyper-V
[Wed Nov  4 20:06:51 2026] Hyper-V: privilege flags low 0xae7f, high 0x3b8030, ext 0x42, hints 0x9a4e24, misc 0xe0bed7b2
[Wed Nov  4 20:06:51 2026] Hyper-V: Nested features: 0x3e0101
[Wed Nov  4 20:06:51 2026] Hyper-V: LAPIC Timer Frequency: 0xc3500
[Wed Nov  4 20:06:51 2026] Hyper-V: Using hypercall for remote TLB flush
[Wed Nov  4 20:06:51 2026] clocksource: hyperv_clocksource_tsc_page: mask: 0xffffffffffffffff max_cycles: 0x24e6a1710, max_idle_ns: 440795202120 ns
[Wed Nov  4 20:06:51 2026] clocksource: hyperv_clocksource_msr: mask: 0xffffffffffffffff max_cycles: 0x24e6a1710, max_idle_ns: 440795202120 ns
[Wed Nov  4 20:06:51 2026] tsc: Detected 2304.000 MHz processor
[Wed Nov  4 20:06:51 2026] e820: update [mem 0x00000000-0x00000fff] usable ==> reserved
[Wed Nov  4 20:06:51 2026] e820: remove [mem 0x000a0000-0x000fffff] usable
[Wed Nov  4 20:06:51 2026] last_pfn = 0x208000 max_arch_pfn = 0x400000000
[Wed Nov  4 20:06:51 2026] x86/PAT: PAT support disabled because CONFIG_X86_PAT is disabled in the kernel.
[Wed Nov  4 20:06:51 2026] x86/PAT: Configuration [0-7]: WB  WT  UC- UC  WB  WT  UC- UC  
[Wed Nov  4 20:06:51 2026] last_pfn = 0xf8000 max_arch_pfn = 0x400000000
[Wed Nov  4 20:06:51 2026] Using GB pages for direct mapping
[Wed Nov  4 20:06:51 2026] RAMDISK: [mem 0x03c9d000-0x03fedfff]
[Wed Nov  4 20:06:51 2026] ACPI: Early table checksum verification disabled
[Wed Nov  4 20:06:51 2026] ACPI: RSDP 0x00000000000E0000 000024 (v02 VRTUAL)
[Wed Nov  4 20:06:51 2026] ACPI: XSDT 0x0000000000100000 000044 (v01 VRTUAL MICROSFT 00000001 MSFT 00000001)
[Wed Nov  4 20:06:51 2026] ACPI: FACP 0x0000000000101000 000114 (v06 VRTUAL MICROSFT 00000001 MSFT 00000001)
[Wed Nov  4 20:06:51 2026] ACPI: DSDT 0x00000000001011B8 01E11C (v02 MSFTVM DSDT01   00000001 INTL 20230628)
[Wed Nov  4 20:06:51 2026] ACPI: FACS 0x0000000000101114 000040
[Wed Nov  4 20:06:51 2026] ACPI: OEM0 0x0000000000101154 000064 (v01 VRTUAL MICROSFT 00000001 MSFT 00000001)
[Wed Nov  4 20:06:51 2026] ACPI: SRAT 0x000000000011F2D4 000430 (v02 VRTUAL MICROSFT 00000001 MSFT 00000001)
[Wed Nov  4 20:06:51 2026] ACPI: APIC 0x000000000011F704 000108 (v04 VRTUAL MICROSFT 00000001 MSFT 00000001)
[Wed Nov  4 20:06:51 2026] ACPI: Reserving FACP table memory at [mem 0x101000-0x101113]
... (480 more lines)
```

## pcie_sysfs

Status: **ok** (rc=0)

```text
4140:00:00.0;class=0x030200;vendor=0x1414;device=0x008e;numa_node=0;current_link_speed=unknown;current_link_width=unknown;max_link_speed=unknown;max_link_width=unknown;aer_cor_total=unknown;aer_nonfatal_total=unknown;aer_fatal_total=unknown
953e:00:00.0;class=0x030200;vendor=0x1414;device=0x008e;numa_node=0;current_link_speed=unknown;current_link_width=unknown;max_link_speed=unknown;max_link_width=unknown;aer_cor_total=unknown;aer_nonfatal_total=unknown;aer_fatal_total=unknown
```

## interrupts

Status: **ok** (rc=0)

```text
CPU0       CPU1       CPU2       CPU3       CPU4       CPU5       CPU6       CPU7       CPU8       CPU9       CPU10      CPU11      CPU12      CPU13      CPU14      CPU15      CPU16      CPU17      CPU18      CPU19      CPU20      CPU21      CPU22      CPU23      
  8:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0  IO-APIC   8-edge      rtc0
  9:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0  IO-APIC   9-fasteoi   acpi
 24:          0          1          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0 HV-PCI-MSIX-5582:00:00.0   0-edge      virtio0-config
 25:          0          0       3973          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0 HV-PCI-MSIX-5582:00:00.0   1-edge      virtio0-virtqueues
 26:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0 HV-PCI-MSIX-ecb7:00:00.0   0-edge      virtio1-config
 27:          0          0          0          0          0          6          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0 HV-PCI-MSIX-ecb7:00:00.0   1-edge      virtio1-hiprio
 28:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0         65 HV-PCI-MSIX-ecb7:00:00.0   2-edge      virtio1-requests.0
NMI:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Non-maskable interrupts
LOC:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Local timer interrupts
SPU:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Spurious interrupts
PMI:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Performance monitoring interrupts
IWI:          1          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   IRQ work interrupts
RTR:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   APIC ICR read retries
RES:        587        133        398        348        395        255        561        250        436        201        482        249        463        162        445        267        487        273        505        280        580        203        449        253   Rescheduling interrupts
CAL:      19118       5977       9578       6158       6541       5034      10010       5979       9815       7208       9777       6380       9598       9708       9641       5800       8397       9247       9388       6096       9642       4424      10623       4069   Function call interrupts
TLB:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   TLB shootdowns
TRM:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Thermal event interrupts
THR:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Threshold APIC interrupts
DFR:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Deferred Error APIC interrupts
MCE:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Machine check exceptions
MCP:          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1          1   Machine check polls
HYP:      44301       6480       2898       3339       4746       2502         37          0          5          5          3          0          1          1          0          1          2          9          5          0          2          1          0          0   Hypervisor callback interrupts
HRE:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Hyper-V reenlightenment interrupts
HVS:      13478      11901      10788       8792      10597      11362      13643      10727      13296       9656      13818       8288      12354       9415      32355      10804      10267       9191      10445       8464      13822       7659      11700      10476   Hyper-V stimer0 interrupts
ERR:          0
MIS:          0
PIN:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Posted-interrupt notification event
NPI:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Nested posted-interrupt event
PIW:          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0          0   Posted-interrupt wakeup event
```

## cpufreq

Status: **missing** (rc=None)

stderr: no cpufreq interface (VM, container, or cpufreq disabled)
