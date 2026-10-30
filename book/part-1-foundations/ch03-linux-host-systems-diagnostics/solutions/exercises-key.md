# Chapter 3 — Answer Key (INSTRUCTOR ONLY)

All arithmetic was checked twice: once by hand, and once with a Python one-liner whose output is
reproduced in `review/REVIEW.md`. The marks given here are guidance. Award partial credit for correct
reasoning that is not fully finished.

---

## Knowledge checks

### 3.1 — Reading the CPU map
(a) Socket 1 owns physical cores whose first hardware threads are CPUs 56–111. Their SMT siblings are
**168–223**, which matches `NUMA node1 CPU(s): 56-111,168-223`.
(b) GPU 2 is at `3a:00.0`, on PCIe switch SW1 under **socket 0**, because bus 0x3a is below 0x80. CPUs
56–63 are on socket 1. The rank's main thread and its pinned buffers would sit on the wrong socket. Every
host-to-device copy and every kernel launch would then cross the inter-socket link, which raises latency
and lowers effective H2D bandwidth. Bind to socket-0 cores, for example a slice of 0–55, ideally chosen by
the topology mapping of Chapter 5.
*Marking (4):* 2 for the correct CPU lists, 2 for naming the socket mismatch and its consequence.
*Common mistake:* assuming "CPUs 0–111 are socket 0".

### 3.2 — Since-boot samples
The first `vmstat` line and the first `iostat` report average **every interval since boot**. On a node
that has been up for 21 days, mostly idle or running a different job, they dilute the live behaviour
almost completely. *Example:* the live samples show `b` = 15 for the last five seconds, but the
since-boot row shows `b` = 0. Averaging all five `vmstat` rows gives (0 + 4 × 15) / 5 = 12, and
reporting only the first row gives 0. Either way the blocked loaders are under-reported or hidden.
*Marking (3):* 1 for the definition, 2 for a valid numeric example.

### 3.3 — Diluted signals
(a) Each blocked task can idle at most one CPU in iowait. The maximum is therefore
0.045 × 224 = **10.1**, so about 10 blocked tasks. On Linux the load average counts tasks in state `D`,
which is why it can read 12 while the host is mostly idle.
(b) **`vmstat 1 5` column `b`**, ignoring the first row, gives the count of blocked tasks.
**`iostat -x 1 3`** gives `r_await`/`w_await` and `aqu-sz` per device. PSI `cat /proc/pressure/io`
is an acceptable alternative.
*Marking (4):* 2 for the arithmetic, 2 for the two metrics with their commands.

### 3.4 — PCIe status lines
| Line | Verdict | Rule |
|---|---|---|
| (a) GPU x8 of x16 at 95 % utilization | **Fault (critical)** | Width below capability is never benign |
| (b) GPU 2.5 GT/s x16, 0 % utilization | **Probably benign — verify under load** | Idle GPUs lower their link speed for power saving; width is full |
| (c) VGA 5 GT/s x1 of 5 GT/s x1 | **Healthy** | Status equals capability. An x1 link is by design. |
| (d) Rail NIC Gen4 x16 of Gen5 x16 during a benchmark | **Fault (warning)** | Speed below capability under load. Gen4 x16 gives 31.5 GB/s raw (≈ 26 GB/s achievable), below the 50 GB/s line rate of a 400 Gb/s port, so the rail is PCIe-capped. |
*Marking (4):* 1 per line. Line (d) also needs the bandwidth consequence for full credit.
*Common mistake:* flagging (c) because "x1 looks degraded", or flagging (b) as critical.

### 3.5 — Corrected versus uncorrected
| Event | Consequence | Rule type | First action |
|---|---|---|---|
| PCIe AER corrected | Link-level retry; small bandwidth and latency cost | **Rate per BDF** (e.g. ≥ 10 per capture or per hour) | Correlate with `LnkSta`; schedule inspection |
| PCIe AER uncorrected non-fatal | One transaction failed; the driver may recover | **Presence** | Drain at the next checkpoint; collect logs |
| PCIe AER uncorrected fatal | The link is unreliable and needs a reset; the device may be lost | **Presence** | Drain immediately; hardware RMA path |
| EDAC CE | Corrected DRAM error; predicts a future UE when the rate rises on one DIMM | **Rate per DIMM** | Track the trend; plan DIMM replacement |
| EDAC UE | Data loss; process or host crash | **Presence** | Drain and replace the DIMM |
*Marking (5):* 1 per row.

### 3.6 — NUMA and utilization
A thread that misses in cache and waits for remote DRAM is still *running*, because stall cycles count
as busy time. Remote placement therefore lowers **instructions per cycle** and throughput without
lowering utilization. To reveal it, compare IPC against a well-placed peer with
`perf stat -e cycles,instructions -p <pid> -- sleep 10`. Read the placement itself with
`numastat -p <pid>`, cross-checked against `taskset -cp <pid>`. `/proc/<pid>/numa_maps` gives
per-mapping detail.
*Marking (4):* 2 for the mechanism, 2 for both commands.

### 3.7 — Safe collection
Any four, each with an example:
1. **Default-deny allowlist of exact read-only forms** (not a deny-list): refuses `ethtool -s rail0 speed 200000`,
   `ip link set`, `dmesg -c`, `nvidia-smi --power-limit=300`, `nvidia-smi -mig 1`, because none is a listed form.
2. **No shell, argv only**: a hostname or interface name cannot inject `; rm -rf`.
3. **Timeouts**: a hung `lspci` on a wedged device cannot hang the collector.
4. **Never escalates**: no `sudo`; `dmesg` denied → record it and fall back to `journalctl -k`.
5. **Records every outcome**: a missing `iostat` becomes `status: missing`, not a traceback.
6. **`LC_ALL=C`**: parsers do not break on localised decimal separators or dates.
*Marking (4):* 1 per property with a valid example.

---

## Troubleshooting case — 3.8 (model answer)

**1. Abnormal signals in `orion-n12`.**

| Section | Value | Baseline / peer |
|---|---|---|
| `iostat` (live report) | `nvme3n1` r_await **48.60 ms**, aqu-sz **40.34**, %util **99.90**, 830 r/s | siblings `nvme0–2n1`: 0.21 ms, 0.17, 17.4 % |
| `iostat` | `md0` r_await **49.10 ms**, aqu-sz 40.75, %util 100.0, 830 r/s × 512 KiB | healthy md0 < 1 ms, ≈ 5 % util |
| `iostat` avg-cpu | %iowait **6.90**, %idle 88.90 | < 1 % |
| `vmstat` (live rows) | `b` = 14, 14, 16, 17 (mean **15.25**); `wa` 6–8; `bi` ≈ 370–440 MB/s | `b` ≤ 1 |
| `mpstat` | all-CPU busy **11.5 %**; **CPU0 99.5 % busy** (%soft 76.5, %sys 22.4) | no CPU > 90 % |
| `interrupts` | all 8 `mlx5_comp` IRQs of `rail0` (19:00.0) **and** `fe0` (4c:00.0) counted on **CPU0** (100 %) | spread across local cores |
| `numastat_pid`/`taskset_pid` | PID 48211 bound to node-0 CPUs (`0-55,112-167`); **210,855.6 of 213,171.2 MB on node 1 (98.9 %)** | < 25 % remote |
| `nvidia_smi` | GPU utilization **55–60 %**, links Gen5 x16 | peers ≈ 95–99 % |
| Normal | PCIe x16 Gen5 everywhere, MTU 9000, rail and fe speeds nominal, `intel_pstate`/`performance`, no AER/EDAC/Xid | — |

Raw lines to quote, for example:
`nvme3n1  830.00 106240.00 ... 48.60 ... 40.34 99.90`, `4 14 0 ... 7 0` (vmstat), and
`Total  2315.60  210855.60  213171.20` (numastat).

**2–3. Ranked hypotheses with discriminating tests.**

| Rank | Hypothesis | How well it explains ~40 % | Discriminating test (L2, on the live host) | Confirming result |
|---|---|---|---|---|
| 1 | **Slow RAID 0 member `nvme3n1` gates `md0`**, so loader workers block and the GPUs starve | **Fully.** md0 delivers 830 × 512 KiB = 435 MB/s. A loader that needed ≈ 725 MB/s (peers' rate) gets 435 / 725 = 60 %, which is the observed 40 % shortfall. GPU utilization ≈ 58 % agrees. | `nvme smart-log /dev/nvme3` (temperature, `critical_warning`, media errors); kernel log for nvme timeouts or resets; per-member latency with a read-only `fio --readonly` job on the drained node; PSI `io` | nvme3 thermal throttling or media errors; per-member latency ≫ siblings |
| 2 | **IRQ/softirq concentration on CPU0** (rail0 and fe0 queues) | **Partially.** It caps kernel-path traffic (frontend PFS reads, checkpoint uploads, IP on rail0) and slows any thread scheduled on CPU0. W-MM reads come from local NVMe, so it is not the main limiter. | `/proc/softirqs` NET_RX delta per CPU; `cat /proc/irq/<n>/smp_affinity_list`; `systemctl is-active irqbalance`; `sar -n DEV 1` on fe0 during a PFS read | NET_RX grows only on CPU0; fe0 throughput plateaus with CPU0 at 100 % |
| 3 | **NUMA-remote memory for the loader** (98.9 % remote) | **Partially.** It slows decode and copy work and adds cross-socket traffic, but the workers are *blocked*, not busy, so it cannot be primary. | `perf stat -e cycles,instructions` IPC vs a peer's loader; how the job was launched (wrapper, `numactl` args) | IPC clearly lower than the peer's |
| 4 | **PCIe/GPU constraint** | **No.** All links are Gen5 x16 under load, and GPU utilization is low because the GPUs are waiting. | `nvidia-smi` link query under load; GPU timeline shows data-wait gaps | Gaps are before data arrives, not during compute |
| 5 | **CPU frequency** | **No.** The governor is `performance` with `intel_pstate`. | `turbostat` Bzy_MHz | Matches peers |

**4. Root cause and remediation order.** The primary cause is the `nvme3n1` latency (48.6 ms, about
230× its siblings), inherited by every 512 KiB `md0` read. The contributing factors are the IRQ
concentration on CPU0, which looks like the result of a stopped `irqbalance` or a bad affinity
profile, and the loader's remote memory placement. Order: (1) drain the node (this stops new placement only; ORION-256 has no spare). W-MM is a single-node (8-GPU) job, so the ≈ 40 % loss is
node-local: 0.40 × 8 ≈ 3.2 GPU-h per hour. Stopping that job at its next checkpoint costs only
8 × 0.25 h = 2 GPU-h plus 8 × T_repair, so stop it, repair, and restart. If W-MM were instead one
synchronous 256-GPU job, the same slowdown would cost ≈ 0.40 × 256 ≈ 102 GPU-h per hour and would
justify a planned stop of the whole job. Fleet
replaces or reseats `nvme3`, or temporarily rebuilds the cache without it or bypasses it to the PFS.
(2) Platform restores the IRQ affinity profile or `irqbalance` through config management. (3) Training
Infra fixes the launcher so that loader CPUs and memory are on the same node (`--cpunodebind` with a
matching `--membind`, or first-touch from bound threads). Each change is made on the drained node
through the change process.

**5. Validation.** Run on the repaired node with a fixed W-MM configuration: 50 warm-up steps, then
300 measured steps, repeated 3 times. Report median and p95 samples/s per run, with the min–max spread,
against two peer nodes. The acceptance target is median within 3 % of peers. Secondary signals: md0
`r_await` < 1 ms, `vmstat b` ≤ 2, GPU utilization ≥ 90 %, CPU0 `%soft` back to background.

*Marking (10, the same 10 points as lab rubric item D):* signal table 3 (at least 6 correct signals),
hypotheses and ranking 2, discriminating tests 2, root cause and order 1.5, validation plan 1.5.
*Common mistakes:* calling NUMA the primary cause because "98.9 %" looks worst, even though workers
blocked on I/O cannot be CPU-bound; reading `%iowait` 6.9 as "fine"; blaming `md0` without naming the
member; using `%util` as the evidence of saturation; proposing to change IRQ affinity live on the
training node.

---

## Worked problems

### 3.9 — The price of a narrower pipe
(a) With 128b/130b encoding for Gen3 and later, and 8b/10b for Gen1/2:

```text
Gen5 x16: 32  × 16 × 128/130 ÷ 8 = 63.0 GB/s
Gen4 x16: 16  × 16 × 128/130 ÷ 8 = 31.5 GB/s
Gen4 x2 : 16  ×  2 × 128/130 ÷ 8 =  3.94 GB/s
Gen1 x16: 2.5 × 16 × 8/10    ÷ 8 =  4.0 GB/s      (per direction, raw)  [MODELED]
```

(b) S = 70e9 ÷ 32 × 2 B = 4.375 GB, and the ring all-reduce sends 2 × 7/8 × 4.375 = **7.656 GB** per GPU.
Healthy: 7.656 ÷ 45 = 0.170 s. Gen4 x16 achievable is 0.82 × 31.5 = 25.8 GB/s, giving
7.656 ÷ 25.8 = 0.296 s. The extra time is **≤ 0.126 s per step**.
Lost fraction = 0.126 ÷ (17.4 + 0.126) = 0.0072, so 256 × 24 × 0.0072 ≈ **44 GPU-hours/day** `[MODELED]`.
(c) The loss is 44 ÷ 24 ≈ 1.8 GPU-h per hour. Shrinking to DP = 7 costs 32 GPU-h per hour plus
restarts, and a planned stop costs at least 64 GPU-h plus 256 × T_repair. Waiting for the next
unplanned restart costs ≈ 48 h × 1.8 ≈ 88 GPU-h. **Keep running** and repair at the next restart,
watching for escalation (an AER storm or uncorrected errors force a stop). The Gen3 x8 case of §3.11
costs ≈ 339 GPU-h/day (14.1 per hour), about 8× worse. There too shrinking loses (14.1 < 32), but
waiting ≈ 677 GPU-h justifies a planned stop for repairs shorter than ≈ 2.4 h.
*Common mistake:* assuming a spare node exists, or that draining moves the job.
*Marking (10):* (a) 3, (b) 5 (formulas 2, numbers 2, labels 1), (c) 2.
*Common mistakes:* using 8b/10b for Gen4/5; forgetting the 2(n−1)/n factor; mixing Gb/s and GB/s.

### 3.10 — Queues, stripes and packets
(a) Little's law gives aqu-sz = arrival rate × time in system. For `nvme3n1`: 830 /s × 0.0486 s =
**40.3**, matching the reported 40.34. For `md0`: 830 × 0.0491 = **40.8**. The md layer reports its own
queue column, and the value is consistent with ≈ 41 requests outstanding.
(b) 830 r/s × 512 KiB = 830 × 524,288 B = 435.2e6 B/s = **435 MB/s**. Cross-check: four members ×
830 r/s × 128 KiB gives the same 424,960 KiB/s.
(c) Throughput = concurrency ÷ latency × size = 41 ÷ 0.00025 s = 164,000 req/s × 524,288 B ≈ **86 GB/s**.
That is far above what four Gen4 x4 drives can deliver: their links total 4 × 7.88 = 31.5 GB/s raw, and
media limits are lower still. The *loader's demand* is ≈ 0.73 GB/s (peers' rate). With a healthy member
the storage path stops being the bottleneck and the limit moves back to GPU compute.
(d) Mean live `b` = 15.25, and 15.25 ÷ 224 = **6.8 %**. That is consistent with the reported
`%iowait` of 6.9 %.
(e) MTU 9000 needs 200e9 ÷ 8 ÷ 9038 = **2.77 Mpps**. MTU 1500 needs 200e9 ÷ 8 ÷ 1538 = **16.3 Mpps**. The
ratio is 9038 ÷ 1538 = **5.9×** more packets to process per second at MTU 1500.
*Marking (10):* 2 per part.

---

## Hands-on lab — 3.11

`python check.py` should report 21/21. Then grade with the rubric in `lab/README.md` §8. The
reference implementation is in `solutions/lab/`; its fleet report is reproduced under "Reference
output" below.

### Planted anomalies (do not distribute)

| Host | Planted condition | Expected findings (critical/warning) | Teaching point |
|---|---|---|---|
| `orion-n01` | Reference node. **Trap:** 2 historical corrected AER events on NIC 4 (`9b:00.0`), weeks apart. | none (one info `PCIE_AER_CORRECTED`) | Corrected errors matter by rate; do not page on noise |
| `orion-n07` | GPU 3 (`5d:00.0`) trained at **Gen3 x8** under load (97 % utilization); 37 corrected AER RxErr events on that BDF; `DevSta CorrErr+` | `PCIE_WIDTH_DEGRADED` crit; `PCIE_SPEED_DEGRADED` warn; `PCIE_AER_CORRECTED` warn | Width faults and AER storms together; §3.11 cost |
| `orion-n12` | W-MM loader: `nvme3n1` 48.6 ms in RAID 0 `md0`; `vmstat b` ≈ 15; loader PID 98.9 % NUMA-remote; all `rail0` and `fe0` IRQs on CPU0, so CPU0 is 99.5 % busy in softirq; GPUs at ~58 % | `NUMA_REMOTE_MEMORY` crit; `IO_SATURATION` warn (nvme3n1 and md0); `PROC_BLOCKED` warn; `IRQ_CONCENTRATION` warn (×2); `CPU_HOTSPOT` warn (cpu0) | "CPU low, throughput poor"; diluted `%iowait`; the md0 finding is real but the actionable subject is the member drive |
| `orion-n19` | Post-RMA: NUMA node 1 has 774,107 MB instead of ≈ 1,032,000 (≈ 252 GiB missing, consistent with DIMMs mapped out at POST); `rail3` MTU **1500**; `acpi-cpufreq` + `powersave` at 800 MHz | `INVENTORY_MISMATCH` crit (memory, numa1); `MTU_MISMATCH` crit (rail3); `CPUFREQ_POWERSAVE` warn | Baselines catch silent hardware loss; RMA returns need full re-provisioning. On a RoCE rail the 1500 B netdev MTU also caps the RDMA active MTU at 1024 B (docs/VERIFIED_FACTS.md) |
| `orion-n23` | `rail5` negotiated **200 000 Mb/s**; 12 EDAC CE on MC2 (one DIMM); Xid 63 (row remap pending) on GPU 5 (`ab:00.0`) | `LINK_SPEED_DEGRADED` crit; `MEM_ECC_CORRECTED` warn; `GPU_XID` warn | A link that is up can still be wrong; CE trends; Xid classes |
| `orion-n28` | Collected **non-root**, GPUs **idle**, sysstat **not installed**: `lspci` capabilities `<access denied>`, `dmesg`/`journalctl` denied, `iostat`/`mpstat` missing, GPUs at 2.5 GT/s x16 (idle), `intel_pstate` + `powersave` | none at critical/warning; info: 3 × `EVIDENCE_GAP`, 8 × `PCIE_SPEED_LOW_IDLE`, `CPUFREQ_POWERSAVE` | Graceful degradation; sysfs fallback; idle downshift and `intel_pstate` powersave are not faults; "no findings" with gaps ≠ healthy |

There are 14 distinct (host, check, severity) keys at critical/warning. These are the hashes in
`lab/check.py`.

### Reference output (`solutions/lab/host_analyzer.py`, summary table)

| Host | Critical | Warning | Info | Verdict |
|---|---|---|---|---|
| orion-n01 | 0 | 0 | 1 | healthy (check gaps) |
| orion-n07 | 1 | 2 | 0 | DRAIN / repair |
| orion-n12 | 1 | 6 | 0 | DRAIN / repair |
| orion-n19 | 3 | 1 | 0 | DRAIN / repair |
| orion-n23 | 1 | 2 | 0 | DRAIN / repair |
| orion-n28 | 0 | 0 | 12 | healthy (check gaps) |

### Model fleet triage memo (lab Part D.3)

| Host | Verdict | Evidence | Owner |
|---|---|---|---|
| orion-n07 | Drain at next checkpoint; reseat or replace GPU 3 path | `LnkSta 8GT/s x8` under load; 37 AER RxErr | Fleet |
| orion-n12 | Drain; replace nvme3; fix IRQ profile; fix loader binding | 48.6 ms member latency; CPU0 100 % softirq; 98.9 % remote | Fleet, Platform, Training Infra |
| orion-n19 | Drain; DIMM investigation; full re-provision (BIOS, image); MTU via config management | node1 774,107 MB; rail3 MTU 1500; 800 MHz | Fleet, Fabric (MTU verification) |
| orion-n23 | Drain; rail5 optic/cable/port check; monitor DIMM CE trend; GPU reset to apply row remap | 200 Gb/s; 12 CE on MC2; Xid 63 | Fabric, Fleet |
| orion-n28 | **Not cleared.** Re-collect as root, with sysstat, under load, before declaring healthy | 3 evidence gaps | Fleet / on-call |
| orion-n01 | Healthy reference | — | — |

### Common lab mistakes

- Counting all four AER lines per event, which gives 148 "events" on orion-n07 and turns orion-n01's noise into a warning.
- Including the since-boot `vmstat` row, which drops orion-n12's mean `b` to 12.2: still a warning, but the parser check fails.
- Using the first `iostat` report, which hides `nvme3n1` entirely.
- Stopping at `md0`. Its `IO_SATURATION` finding is correct, but an array's `%util` comes from md
  accounting (0 on older kernels or with statistics off), and the actionable subject is the member
  drive `nvme3n1`.
- Raising a warning for GPU speed downshift on idle orion-n28, or for `intel_pstate` `powersave` there.
- Treating `lspci` `<access denied>` as "no PCIe devices" instead of falling back to sysfs.
- Computing IRQ concentration per IRQ (each queue *should* be on one CPU) instead of per device.

---

## Exercise 3.12 — Host inventory (reference for the L1 path)

From `orion-n01.json`: Intel Xeon Platinum 8480+, 2 sockets × 56 cores × 2 threads = 224 CPUs
(`lscpu`); NUMA 0 = CPUs 0–55 and 112–167 with 1,031,868 MB, NUMA 1 = CPUs 56–111 and 168–223 with
1,032,151 MB (`numactl_hardware`); `free -m` total 2,064,019 MiB. 8 GPUs (`18,2a,3a,5d` on node 0;
`9a,ab,ba,db` on node 1), each 32 GT/s x16 (`lspci`). 8 ConnectX-7-class rail NICs at 32 GT/s x16 and 2
ConnectX-6 Dx-class frontend NICs at 16 GT/s x16. 8 NVMe drives at 16 GT/s x4. `rail0–7` and `fe0–1`
at MTU 9000, 400 000 / 200 000 Mb/s (`ip_link`, `ethtool:*`). Kernel 5.15.0-122-generic (`uname`); GPU
driver 550.127.05 and mlx5 firmware 28.39.1002 (`kernel_log`). Governor `performance` with
`intel_pstate` (`cpufreq`).
*Marking (10):* 1 per category correct with provenance (CPU, NUMA, memory, GPUs, NICs, NVMe,
interfaces, kernel/driver, cpufreq, layout). For the L2 path, award the same 10 for a correct table of
the learner's host, plus up to 5 for the root/non-root gap analysis. That analysis should note that
`lspci` link data is hidden without root and recovered from sysfs, that `dmesg` may be denied and
recovered via `journalctl -k` with group membership, and that `nvme` and `turbostat` need root.

---

## Design challenge — 3.13 (marking guide)

A strong answer contains the following.
(a) Continuous: node exporter and DCGM exporter at 10–30 s intervals for utilization, temperature,
ECC, Xid and NIC counters (Chapter 18). On demand: the collector, triggered by straggler detection,
any critical finding, node acceptance and RMA return.
(b) Unprivileged collection on live nodes, using sysfs and journal group membership. Root collection
only on drained nodes or through an audited privileged agent, with every run logged.
(c) Auto-drain at the next checkpoint only for unambiguous, high-cost findings: `PCIE_WIDTH_DEGRADED`,
`PCIE_AER_UNCORRECTED`, `MEM_ECC_UNCORRECTED`, critical Xids, `LINK_SPEED_DEGRADED` and
`INVENTORY_MISMATCH`. Page a human for rate-based or contextual findings (CE trends,
`IRQ_CONCENTRATION`, NUMA placement). The rationale should be stated in GPU-hours: a false drain costs
one node, about 8 GPUs × time to return, whereas a missed straggler costs a share of the whole job.
(d) Snapshot volume: the supplied snapshots are ≈ 74–154 KB of JSON each, ≈ 140 KB typical, so one sweep
is 512 × 140 KB ≈ **72 MB**. Daily sweeps come to ≈ 26 GB/year before compression, and text compresses
roughly 5–10×. Retention is tied to incident review (for example 90 days hot, 1 year compressed).
(e) The baseline lives in Git, changes by pull request with review from Fleet and SRE, and is rolled
out in canary fashion (analyze a sample of nodes with the new thresholds in shadow mode before
enforcing), as in Chapter 20.
Rejected alternatives might include "run everything as root continuously" (blast radius, audit) and
"alert on every corrected error" (alert fatigue).
*Marking (15):* decision table 5, arithmetic 2, auto-drain rationale 4, rejected alternatives 2, change
control 2.

---

## Reflection — 3.14 to 3.17

**3.14** Examples: (1) tool output formats differ (pciutils without the `(ok)` annotations, sysstat
adding columns, 12-hour timestamps in `mpstat` without `LC_ALL=C`). Validate by running the parsers on
real captures from each OS image. (2) Real faults are intermittent: AER storms come in bursts and the
snapshot window may miss them. Validate by collecting repeatedly and correlating with continuous
metrics. (3) Thresholds were chosen by judgment; real fleets have different noise floors. Validate by
computing fleet distributions before enforcing them. (4) Interface naming and topology differ from
`rail*/fe*`. Validate by generating the baseline from a known-good node.
*Marking (3):* 1 per item with a validation step.

**3.15** Can be concluded: inventory as seen through unprivileged sources (CPU, NUMA, memory, GPU and
NIC presence and link width via sysfs, MTU and speeds), and idle GPU link speed, which is benign.
Cannot be concluded: kernel-log health (AER, EDAC, Xid, MCE); storage latency and per-CPU behaviour
(sysstat missing); PCIe speed under load; process NUMA placement (no PID). Next steps: install
sysstat or use a container image that has it; collect as root or as a member of `adm`/`systemd-journal`
to get kernel logs; collect again under load with `--pid`.
*Marking (3).*

**3.16** Upper-bound assumptions: (1) no overlap of the DP all-reduce with backward compute; (2) NCCL
does not route around the slow link (for example via PXN); (3) 45 GB/s healthy rail and 82 % PCIe
efficiency are illustrative; (4) only the DP all-reduce traffic is affected (pipeline sends ignored).
Measurement (L3): with the degraded node in a dedicated test allocation, run
`all_reduce_perf -b 1G -e 8G -f 2 -g 1` across the 8 nodes' local-rank-3 GPUs, and the same on a
healthy rail, each with ≥ 5 runs after warm-up, reporting median busbw and p95. Then run 200 training
steps with and without the node, reporting median and p95 step time and the difference with its spread.
*Marking (4).*

**3.17** Example: `aer_corrected_warn_per_bdf: 10`. Tighter (for example 3) catches deteriorating links
earlier, before uncorrected errors. Looser (for example 50) avoids paging on benign retry bursts during
link training or hot-plug. Evidence needed: the per-BDF corrected-error rate distribution across the
fleet over weeks, correlated with later uncorrected errors or RMA outcomes, to pick a threshold with an
acceptable false-positive rate.
*Marking (3).*

---

## Collector guard: required safety cases (lab A2)

The reference `argv_is_read_only()` is default-deny over exact forms (`ALLOWED_FORMS`), with
`--opt=value` split before matching. `check.py` requires these to be **refused**:
`ethtool -s rail0 speed 200000`, `ethtool --set-priv-flags rail0 x on`, `ethtool -sfoo`,
`sudo lspci -vv`, `ip link set rail0 mtu 1500`, `dmesg -c`, `rm -rf /tmp/x`,
`nvidia-smi --power-limit=300`, `nvidia-smi -pl 300`, `nvidia-smi -mig 1`, `nvidia-smi -lmc 1593`,
`nvidia-smi -r`, `taskset -cp 0-3 1234` (sets affinity), `lspci -vv -s '5d:00.0;reboot'`, and
`numactl --membind=0 python3`. It also requires a spec with a mutating fallback to be unsafe. These
must be **allowed**: `ip -s link show`, `ethtool -i rail0`, `lspci -s 5d:00.0 -vv`,
`nvidia-smi --query-gpu=index,pci.bus_id --format=csv`, and `numastat -p 1`.
*Common mistake:* a deny-list of "dangerous" tokens. Deny-lists miss new setters (`-mig`, `-lmc`,
`--set-priv-flags`) and refuse harmless forms (`ip -s link`). Award no A2 credit for a deny-list
design even if it passes the listed cases.

## Generator (instructor material)

`lab/tools/generate_snapshots.py` (seed 3) encodes the planted faults above and is stripped from the
student release. Regenerate with `python lab/tools/generate_snapshots.py` and verify with `--check`,
which should print "byte-identical".
