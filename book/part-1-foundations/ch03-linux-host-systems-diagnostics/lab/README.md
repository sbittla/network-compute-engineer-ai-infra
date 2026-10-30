# Lab 3 — Host Discovery and Fleet Health Triage (Progressive Lab 1)

## 1. Goal and the real-world task it mirrors

You are on Halcyon AI's **Fleet** team. Training Infra has flagged several ORION `HX8` nodes as
stragglers, and one node has just come back from a motherboard-tray RMA. Before anyone touches a BIOS
setting or reboots a node, the team wants two artifacts:

1. **A reusable, read-only host collector** (`host_collector.py`) that any on-call engineer can run on a
   Linux host, with or without root, to produce a timestamped inventory and health snapshot in JSON
   (for machines) and Markdown (for humans). It must never change the host, and it must tell you
   honestly what evidence it could *not* collect.
2. **A fleet analyzer** (`host_analyzer.py`) that parses snapshots from many hosts, compares each to
   the HX8 baseline, and produces a triage report: which nodes to drain, which to investigate, and
   which are healthy — each finding backed by the line of evidence that supports it.

This is the first of the book's eight progressive labs ("Lab 1 — Host discovery"). Chapter 5 extends
it with GPU↔NIC topology mapping; Chapter 16 turns it into a node-acceptance gate; Chapter 18 feeds its
output into incident timelines.

## 2. Tier and realism boundary

| Tier | What you do | What it proves |
|---|---|---|
| **L1 (this lab)** | Implement the collector against a fake runner and the analyzer against six supplied ORION snapshots (`data/snapshots/*.json`). | Parsing, diagnosis, severity reasoning, safe-tool design. |
| L2 (extension) | Run your collector on a real Linux GPU host (root and non-root) and analyze it with your own baseline. | Real inventory and real failure signatures on one node. |
| L3 (extension) | Run it across ≥ 2 RDMA-connected GPU nodes, under load and idle, and compare. | Fleet consistency, PCIe/NIC behaviour under real traffic. |

> **Realism boundary:** The six ORION snapshots are `[SIMULATED]`: generated to imitate real tool
> output closely, but they are not captures from
> physical HX8 hardware. Tool output formats vary across distributions and versions (pciutils,
> sysstat, procps, util-linux); expect to adjust a regex or two on your own hosts. Nothing in this lab
> measures performance — it diagnoses configuration and health. The reference collector *has* been
> run on real Linux (a Debian-based container on a WSL2 kernel, root and non-root) to confirm the
> graceful-degradation paths; see `manifest.yaml`.

## 3. Setup

```bash
cd book/part-1-foundations/ch03-linux-host-systems-diagnostics/lab
python --version                    # 3.10 or newer
pip install -r ../../../../requirements.txt     # only pyyaml is needed here
python check.py                     # progress meter: everything is TODO at the start
```

## 4. Background you need

| Topic | Manuscript section |
|---|---|
| HX8 NUMA and PCIe topology as Linux sees it | §3.2 |
| Scheduling, run queue, `r`/`b`, per-CPU hot spots, cpufreq | §3.3 |
| NUMA placement, first touch, `numastat -p` | §3.4 |
| `iostat -x` columns, `%iowait` dilution, NVMe `%util` caveat | §3.5 |
| PCIe `LnkCap` vs `LnkSta`, idle downshift, AER | §3.6 |
| MSI-X queues, `/proc/interrupts`, softirq | §3.7 |
| Kernel log: AER, EDAC, Xid, `dmesg_restrict` | §3.8 |
| Collector design rules | §3.10 |

## 5. Snapshot format (`hostdiag/1`)

Every snapshot — yours or the supplied ones — is one JSON document:

```text
{ "schema": "hostdiag/1", "host": "...", "collected_at": "2026-10-14T09:15:02Z",
  "platform": "linux", "user_is_root": true, "context": {"pid": 48211, "note": "..."},
  "sections": { "<name>": {"argv": [...], "status": "ok|missing|denied|timeout|error|skipped",
                           "returncode": 0, "stdout": "...", "stderr": "...", "elapsed_s": 0.02,
                           "attempts": [[...], [...]]  /* only when a fallback ran */ } } }
```

Section names: `uname`, `lscpu`, `numactl_hardware`, `free`, `vmstat`, `iostat`, `mpstat`, `ip_link`,
`ethtool:<iface>`, `lspci`, `nvidia_smi`, `kernel_log`, `numastat_pid`, `taskset_pid` (commands) and
`pcie_sysfs`, `interrupts`, `cpufreq` (file reads). The six ORION hosts are `orion-n01` (the
reference node), `-07`, `-12`, `-19`, `-23`, and `-28`; read each snapshot's `context.note`.

## 6. Tasks

### Part A — Collector (`starter/host_collector.py`)

| # | Task | Acceptance criterion |
|---|---|---|
| A1 | `classify_outcome()` — map exceptions and return codes to `missing / denied / timeout / error / ok`. | `collector.classify_outcome` passes. |
| A2 | `build_command_plan()` and `argv_is_read_only()` — the ordered command list, and a **default-deny** guard: an argv is allowed only if it exactly matches one of the read-only forms in `ALLOWED_FORMS` (after splitting `--opt=value`). Never use a deny-list: setters such as `nvidia-smi --power-limit=300`, `-mig 1`, `-lmc`, `ethtool --set-priv-flags`, or `taskset -cp <cpus> <pid>` must fail because they are not listed. | 15 read-only commands for 2 interfaces + PID; 15 unsafe forms refused; read-only forms such as `ip -s link show` allowed. |
| A3 | `collect()` — run the plan via an injectable runner; fallback `dmesg -T` → `journalctl -k -b --no-pager`; refuse non-read-only specs; skip everything on non-Linux; never crash on a failing file reader. | Both `collector.collect` checks pass. |
| A4 | `render_markdown()` — human report with an evidence-gap summary first. | `collector.render_markdown` passes. |

### Part B — Parsers (`starter/host_analyzer.py`)

| # | Function | Trap to avoid |
|---|---|---|
| B1 | `parse_lscpu`, `parse_numactl_hardware` | Split on the first `:` only; CPU lists use range syntax. |
| B2 | `parse_lspci_links` | Compare numbers, not the `(ok)`/`(downgraded)` annotation (older pciutils print neither). Non-root output hides capabilities. |
| B3 | `parse_vmstat` | The first row is the **since-boot average** — exclude it. |
| B4 | `parse_iostat` | The first report is **since boot** — keep the last one. |
| B5 | `parse_mpstat` | Prefer the `Average:` block; align columns from the right. |
| B6 | `parse_interrupts` | One column per CPU (224 here); the action name is the last token. |
| B7 | `parse_ip_link`, `parse_ethtool`, `parse_numastat_process` | `Speed: Unknown!` means no link; `numastat -p` totals are in MB. |
| B8 | `scan_kernel_log` | Count one AER event per `error received` line, not per detail line. |

### Part C — Analysis and report

Implement `analyze_host()`, `analyze_fleet()`, and `write_report()` to apply this **severity policy**
exactly (thresholds come from `data/orion_hx8_baseline.yaml`):

| Check ID | Severity | Rule |
|---|---|---|
| `EVIDENCE_GAP` | info | Any section whose status is not `ok`. |
| `INVENTORY_MISMATCH` | critical | Sockets, cores/socket, threads/core, NUMA nodes, GPU count differ from baseline; `free -m` total below `mem_total_mib_min`; any NUMA node smaller than `numa_node_mem_mb_min`. |
| `PCIE_WIDTH_DEGRADED` | critical | Any device with `LnkSta` width < `LnkCap` width. |
| `PCIE_SPEED_DEGRADED` | warning | `LnkSta` speed < `LnkCap` speed, **unless** the device is a GPU and all GPUs are idle (`utilization.gpu` ≤ `gpu_idle_util_pct`) → `PCIE_SPEED_LOW_IDLE` (info). |
| (source rule) | — | Use `lspci -vv` link data; if it is hidden (`<access denied>`), use `pcie_sysfs`. |
| `PCIE_AER_CORRECTED` | warning / info | Corrected AER events for one BDF ≥ `aer_corrected_warn_per_bdf` → warning; 1 to threshold−1 → info. Count from the kernel log; if the kernel log is not `ok`, use the sysfs `aer_cor_total` counter (since boot) from `pcie_sysfs` instead (and `aer_nonfatal_total`/`aer_fatal_total` > 0 → `PCIE_AER_UNCORRECTED`). |
| `PCIE_AER_UNCORRECTED` | critical | Any uncorrected (non-fatal or fatal) AER event. |
| `MEM_ECC_CORRECTED` | warning / info | Sum of EDAC CE counts ≥ `edac_ce_warn` → warning; otherwise info. |
| `MEM_ECC_UNCORRECTED` | critical | Any EDAC UE. |
| `GPU_XID` | critical / warning | Xid in `critical_xids` (48, 74, 79, 94, 95, 119, 120, 140, 154 `[VENDOR-SPEC, 2026-10]`) → critical; any other Xid → warning. |
| `MCE_LOGGED`, `NIC_LINK_FLAP` | warning | Machine-check log line; NIC `Link down` line. |
| `INTERFACE_MISSING`, `MTU_MISMATCH`, `LINK_DOWN`, `LINK_SPEED_DEGRADED` | critical | Per baseline interface group (`rail0–7`, `fe0–1`): absent; MTU ≠ expected; state ≠ UP or `Link detected: no`; ethtool speed below expected. Also flag any interface whose MTU differs from the fleet majority (≥ 3 hosts). |
| `CPUFREQ_POWERSAVE` | warning / info | Governor `powersave` with driver `acpi-cpufreq` → warning (pins low frequency); with `intel_pstate`/`amd-pstate` → info (dynamic). Other non-baseline governor → `CPUFREQ_GOVERNOR` info. |
| `NUMA_REMOTE_MEMORY` | critical / warning | Fraction of the PID's memory on NUMA nodes outside its CPU affinity ≥ `numa_remote_fraction_crit` → critical; ≥ `..._warn` → warning. |
| `IRQ_CONCENTRATION` | warning | A device with ≥ `irq_min_queues` IRQs has ≥ `irq_single_cpu_fraction_warn` of its interrupts on one CPU. |
| `IRQ_REMOTE_NUMA` | warning | < 50 % of a device's interrupts serviced on its own NUMA node. |
| `CPU_HOTSPOT` | warning | One CPU ≥ `cpu_hotspot_busy_pct` busy while the all-CPU busy is < `cpu_hotspot_all_busy_max_pct`. |
| `IO_SATURATION` | warning | A device with `max(r_await, w_await)` ≥ `io_await_ms_warn` **and** `%util` ≥ `io_util_pct_warn`. |
| `PROC_BLOCKED` | warning | Live-sample mean of vmstat `b` ≥ `vmstat_blocked_warn`. |

`analyze_fleet()` de-duplicates on (host, check, severity, subject) and sorts critical → warning →
info. `write_report()` lists every host (even with zero findings) with a verdict.

### Part D — Written diagnosis (graded by your instructor)

1. Run your analyzer: `python starter/host_analyzer.py data/snapshots/*.json --baseline data/orion_hx8_baseline.yaml --out out/fleet_report.md`.
2. Write a one-page **troubleshooting report for `orion-n12`** ("samples/s poor although CPU
   utilisation is low"): rank at least three hypotheses, name the discriminating evidence for each,
   state the most likely primary cause and the order in which you would fix things, and the
   measurement that would validate the fix (Exercise 3.8).
3. Write a **triage memo** (≤ 1 page) for the fleet: per host, drain / investigate / healthy, with the
   evidence and the owner team (Fleet, Fabric, Platform, Facilities).

## 7. Running the checker

```bash
python check.py                    # your starter implementation
python check.py --impl solution    # reference (instructor edition only)
```

Each line is `PASS`, `FAIL` (with the reason), or `TODO`. The recall/precision checks compare your
critical/warning findings against salted hashes of the expected ones, so they tell you *how many*
you found without revealing *which*.

## 8. Deliverable and grading rubric (100 points)

Deliverable (course outline): **a reusable host diagnostic script and a troubleshooting report.**

| Item | Points |
|---|---|
| A1–A2 collector classification, plan, read-only guard | 15 |
| A3–A4 collection with graceful degradation; Markdown report | 20 |
| B1–B8 parsers (2.5 points per check, 10 parser checks) | 25 |
| C analyzer: recall 10, precision 7, graceful degradation 3, sysfs AER fallback 2, report 3 | 25 |
| D troubleshooting report for `orion-n12` (hypotheses ranked, discriminating tests, fix order, validation) | 10 |
| D fleet triage memo (correct verdicts, evidence cited, owners named) | 5 |

## 9. Extensions (L2 / L3)

> **Safety:** Run the collector only on hosts you are authorized to inspect. It is read-only, but
> `vmstat`/`iostat`/`mpstat` add a few seconds of sampling and `lspci -vv` as root reads PCIe
> configuration space. Do **not** add `setpci`, `ethtool -s`, `ip link set`, `nvidia-smi -pl/-r`, or
> anything else that writes; the read-only guard will refuse them, and so should you.

**L2 — one real GPU host.**

```bash
python host_collector.py --out-dir out/ --note "idle baseline"                       # non-root
sudo python host_collector.py --out-dir out/ --note "idle baseline (root)"           # root, if authorized
# while a GPU workload runs (your own, on a dedicated host):
sudo python host_collector.py --out-dir out/ --pid <trainer-pid> --note "under load"
nvidia-smi topo -m > out/topo.txt                       # GPU/NIC/CPU affinity matrix (Chapter 5)
lstopo-no-graphics --of console > out/lstopo.txt        # hwloc view of sockets, NUMA, PCIe
ethtool -i <iface>                                      # driver, version, firmware-version, bus-info
```

Then copy `data/orion_hx8_baseline.yaml` to `my_baseline.yaml`, edit the inventory and interface
groups to match *your* platform, and run the analyzer on your snapshots. Compare the idle and loaded
snapshots: does the GPU PCIe link speed change? (Many GPUs drop link speed when idle.)

**L3 — two or more RDMA-connected GPU nodes.** Run the collector on every node during the same
`all_reduce_perf` run (from `nccl-tests`, Chapter 12) and once idle; analyze the set as a fleet and
check the cross-host MTU and link-speed consistency rules on real data.

**Record in your copy of `manifest.yaml`:** distribution and kernel (`uname -r`), pciutils/sysstat/
procps versions, CPU model, BIOS version (`cat /sys/class/dmi/id/bios_version`), GPU driver version,
NIC driver/firmware (`ethtool -i`), run as root or not, idle vs loaded, number of snapshots per host,
and any regex you had to change for your tool versions.
