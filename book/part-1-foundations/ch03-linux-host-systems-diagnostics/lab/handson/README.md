# Chapter 3 hands-on lab: host diagnostics on a real Linux machine

## 1. What you will do

You run the chapter's read-only collector (Section 3.10) on your own Linux host, as root and as an
unprivileged user, and triage the snapshot. Then you produce, on purpose, each signal the chapter teaches
you to read: one saturated core hidden in an average, CPU time-sharing under `taskset`, the page cache
turning a disk read into a memory copy, `RLIMIT_MEMLOCK` refusing to lock memory, pinned versus pageable
copies to the GPU, and CPU saturation in pressure stall information (PSI) and `vmstat r`.

## 2. What is real here, and what is not

Real: every command runs against this machine's kernel, and every number comes from it: `mpstat`, `vmstat`,
`taskset`, `mlock(2)`, `mincore(2)`, `posix_fadvise(2)`, `/proc/pressure`, `dmesg`, and a CUDA copy over
the GPU's PCIe link.

What one machine cannot show:

- **No HX8.** The host has one socket, one NUMA node and one GPU, so the NUMA placement of Section 3.4
  (`numastat -p`, remote memory) and IRQ locality cannot be reproduced. The triage against the ORION HX8
  baseline flags the inventory mismatch, which is correct for a laptop.
- **WSL2 hides hardware.** On the reference machine (WSL2), `lspci` lists four Hyper-V paravirtual
  functions instead of the GPU, there is no cpufreq interface and no PCIe link files in sysfs, the guest's
  "SMT siblings" are not the host's hyperthread pairs, and `nvidia-smi` lives in `/usr/lib/wsl/lib`, outside
  the collector's fixed search path. Those are real findings about this platform, recorded as evidence gaps.
  On native Linux more of the collector's sections come back `ok`.
- **Disk numbers are a virtual disk.** The "cold" read in Step 4 goes to a virtual disk file that Windows
  may itself cache. The mechanism (residency 0 % → 100 %, warm faster than cold) carries over; the
  absolute GB/s values do not.
- **No faults.** A healthy laptop shows no AER, EDAC, Xid or MCE lines. The analyzer's fault rules are
  exercised by the Level 1 snapshots, not here.

Absolute numbers from a laptop are not ORION numbers. The ratios (a time-shared CPU halves each worker,
pinned copies release the CPU) and the mechanisms carry over. Section 9's L3 extension of
[`../README.md`](../README.md) (two or more GPU nodes) covers the rest.

## 3. Requirements

| Item | Value |
|---|---|
| GPU | Optional: only Step 5b uses it (an NVIDIA GPU with `nvidia-smi` and CUDA) |
| Docker | No |
| Root | Yes (non-root parts run as `nobody` through `setpriv`) |
| Disk | 1 GiB free in `/var/tmp` during Step 4 |
| RAM | About 2 GiB free |
| Time | Setup 1–2 minutes; run about 3 minutes plus any wait for the shared GPU lock |

## 4. Safety

The lab changes nothing persistent. It runs the read-only collector, short CPU busy loops (each under
`timeout`, the overload ones at `nice 19`), one 1 GiB file in `/var/tmp` that it deletes, and a GPU copy
benchmark. It evicts only its own file from the page cache (`posix_fadvise`), never the whole cache
(`drop_caches`). It does not touch interfaces, routes, sysctls, cpufreq or GPU clocks. Every load
generator carries a `ch03-` tag, and `teardown.sh` kills them and removes the file.

## 5. Setup

```bash
cd book/part-1-foundations/ch03-linux-host-systems-diagnostics/lab/handson
sudo bash setup.sh          # pciutils, sysstat, numactl, hwloc (pinned), plus the shared PyTorch venv
```

The collector and analyzer come from `../../solutions/lab/` (instructor edition) or, if that is absent,
from your completed `../starter/`.

## 6. Steps

Run everything unattended with `sudo bash run.sh my-run` (results in `results/my-run/`), or step by step
as below. Write your answers in `results/<run-id>/answers.md`.

### Step 1: run the collector as root and as `nobody`

Use your completed collector and analyzer from `../starter/` (the instructor edition has them in
`../../solutions/lab/`, which `run.sh` prefers when present). `nobody` cannot read your checkout, so copy
the collector to a world-readable temporary folder first:

```bash
python3 ../starter/host_collector.py --out-dir out/root --note "idle, root"
NR=$(mktemp -d /tmp/ch03-nonroot.XXXXXX); cp ../starter/host_collector.py "$NR/"; sudo chown -R 65534:65534 "$NR"; chmod 755 "$NR"
sudo setpriv --reuid=65534 --regid=65534 --clear-groups python3 "$NR/host_collector.py" --out-dir "$NR/out" --note "idle, nobody"
python3 ../starter/host_analyzer.py out/root/*.json --baseline ../data/orion_hx8_baseline.yaml
```

Look at the evidence-gap table at the top of each Markdown report, the `<access denied>` lines in the
non-root `lspci -vv` section, and the triage verdict.

**Question 1.** Which sections are not `ok`, and for each, is the cause the platform, the privilege, or
the collector's own design? What does the analyzer conclude against the HX8 baseline, and is that a
false positive?

### Step 2: one saturated core in an average

```bash
taskset -c 14 timeout 20 python3 spin.py ch03-spin 15 &
taskset -cp $(pgrep -n -f 'spin.py ch03-spin'); ps -L -o pid,tid,psr,pcpu,comm -p $(pgrep -n -f 'spin.py ch03-spin')
vmstat 1 6
mpstat -P ALL 1 5
```

Compare the pinned CPU's `%idle` with the `all` row, and the first `vmstat` row with the rest.

**Question 2.** What all-CPU busy percentage does one saturated core produce on this host, and how would
that same core look on a 224-CPU HX8? Why must the first `vmstat` row be discarded?

### Step 3: CPU placement and throughput

```bash
python3 cpu_bench.py --cpu 14 --seconds 3 --reps 3
```

Each worker is pinned with `sched_setaffinity` (what `taskset -c` does). Read `per_worker_vs_alone` for
`same_cpu`, `smt_siblings`, `separate_cores` and `unpinned`.

**Question 3.** Two workers pinned to the same CPU each get how much of a lone worker's throughput? What
does the `smt_siblings` result tell you about whether this guest's CPU topology is real?

### Step 4: the page cache

```bash
free -m
python3 pagecache.py /var/tmp/ch03-pagecache.bin 1024
free -m; rm /var/tmp/ch03-pagecache.bin
```

`resident_fraction` comes from `mincore(2)`. The file is evicted with `POSIX_FADV_DONTNEED`, read cold,
read warm, then read with `O_DIRECT`.

**Question 4.** How much faster is the warm read than the cold one, and what does that imply for a
"storage benchmark" run twice on the same file? Why is the `O_DIRECT` number on this platform not a
clean disk number?

### Step 5: locked and pinned memory

```bash
ulimit -l; sudo setpriv --reuid=65534 --regid=65534 --clear-groups bash -c 'ulimit -l'
python3 mlock_probe.py 128                                                   # root
NR=$(mktemp -d /tmp/ch03-nonroot.XXXXXX); cp mlock_probe.py "$NR/"; chmod 755 "$NR"; chmod 644 "$NR/mlock_probe.py"
sudo setpriv --reuid=65534 --regid=65534 --clear-groups python3 "$NR/mlock_probe.py" 16
sudo setpriv --reuid=65534 --regid=65534 --clear-groups python3 "$NR/mlock_probe.py" 128
python pinned_copy.py --mib 256 --reps 10                                    # 5b: needs the GPU
```

**Question 5.** Why does `nobody` fail to lock 128 MiB while root succeeds with the same `ulimit -l`?
In 5b, what is the bandwidth gain from pinned memory, how long does the CPU stay blocked by each kind
of `non_blocking=True` copy, and what does one `pin_memory()` call cost compared with the copy itself?

### Step 6: kernel log and `/proc` signals, idle and saturated

```bash
dmesg -T | less; dmesg --level=emerg,alert,crit,err
grep -E '^(oom_kill|pgmajfault) ' /proc/vmstat
cat /proc/pressure/cpu
for i in $(seq 1 $((2 * $(nproc)))); do timeout 14 nice -n 19 bash -c 'while :; do :; done' ch03-hog & done
sleep 2; vmstat 1 6; cat /proc/pressure/cpu /proc/loadavg
```

**Question 6.** Which kernel-log lines on this host are errors that matter, and which are platform
noise? Under overload, which signal shows saturation most directly: `vmstat r`, PSI `cpu some`, or the
load average, and why does the load average lag?

## 7. Check your results

```bash
python3 check.py results/<run-id>
```

It checks that the bundle is complete and that each mechanism shows, for example that two workers on one
CPU each get about half the throughput, and that a cold read leaves the file resident.

## 8. Reference results

Measured on the reference machine (WSL2 Ubuntu 24.04, Intel i7-13700HX with 24 logical CPUs, RTX 4060
Laptop GPU); the full bundle is in [`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/report.md).

| Step | Result |
|---|---|
| 1 Collector | 13 of 15 sections as root and as non-root. cpufreq has no interface in a VM. `nvidia-smi` is missing because the collector searches only a fixed system PATH (`/usr/sbin:/usr/bin:/sbin:/bin`), and WSL2 installs it in `/usr/lib/wsl/lib`. 4 `lspci` lines `<access denied>` without root. Triage against the HX8 baseline: DRAIN, because this laptop is not an HX8 and the inventory rules fire |
| 2 One busy thread | its CPU 100 % busy, all-CPU average 4.5 %. One core is 4.2 % of this host, so the average hides it |
| 3 Placement (throughput relative to one worker alone) | same CPU 0.49 each (0.98 total); SMT siblings 1.00 and 0.99; separate cores 1.01 and 1.00; unpinned 1.01 each |
| 4 Page cache, 1 GiB file | cold 4.62 GB/s, warm 9.25 GB/s (2.0×), O_DIRECT 3.02 GB/s; residency 0 % → 100 % after one read |
| 5 Locked memory | as `nobody` with a 64 MiB limit (set by `run.sh` with `prlimit`), `mlock` of 16 MiB succeeds and 128 MiB is refused |
| 5 Pinned vs pageable, 256 MiB H2D | 10.99 vs 12.96 GB/s (1.18×). CPU held: 24.1 vs 0.035 ms. Pinning the buffer took 206 ms, about 10 copies' worth |
| 6 Kernel log | AER, EDAC, Xid, MCE, OOM and I/O errors all 0; 62 `dxg` ioctl failures (normal WSL2 noise) |
| 6 CPU pressure, 48 busy loops on 24 CPUs | PSI `cpu some avg10` 0.58 → 39.2 %, run queue up to 48, load 2.3 → 9.3 |

Three results need explaining. The SMT siblings run at full speed, as if they were separate cores. On
a native host, two hardware threads of one core typically reach 0.5–0.7 each. The WSL2 guest's sibling
map need not match the physical cores, so on a VM, measure placement; don't read it from `lscpu`.
`VmLck` and `VmPin` read 0 after `pin_memory()` even though the copy runs at pinned speed. CUDA's pinned
allocation is not counted there on this platform, so on WSL2 these counters cannot confirm that memory is
pinned; use the copy rate and CPU-hold time instead. The limit root inherits also varies (about 1 GB
from WSL's init, 64 MiB from a login shell), which is why `run.sh` sets the unprivileged limit itself.

Your numbers will differ. `check.py` tests physical sense, not equality.

## 9. Clean up

```bash
sudo bash teardown.sh       # kills any ch03- load generator, removes /var/tmp/ch03-pagecache.bin
```

`run.sh` calls it on exit, even after a failure.

## Troubleshooting

- **`ERROR: this step needs root: run with sudo`** → run `setup.sh`, `run.sh` and `teardown.sh` with `sudo bash`.
- **`ERROR: missing command: <tool> (run setup.sh)`** → run `setup.sh` first; it installs or checks every tool the run needs.
- **First `setup.sh` is slow or fails in `pip`** → it builds the shared venv `~/.venvs/ai-infra-handson` and
  downloads PyTorch 2.5.1+cu124, so it needs network access. If `python3 -m venv` fails, install
  `python3-venv` (`sudo apt-get install python3-venv`). After a broken install, delete the venv and re-run.
- **The first `sudo` run downloads PyTorch again** → the venv path is `$HOME/.venvs/ai-infra-handson`,
  and `sudo` on Ubuntu sets `HOME` to `/root`, so root gets its own venv. This is a one-time cost.
- **The run stops with no output before a GPU step** → it is waiting for the shared GPU lock
  `/tmp/handson-gpu.lock`, held by another hands-on run. Let that run finish; `pgrep -fa flock` shows it.
- **Step 5b reports `skipped: no NVIDIA GPU visible`** → expected without a GPU; every other step still runs.
- **`teardown: processes still running`** → a `ch03-` load generator outlived its `timeout`; run `sudo bash teardown.sh` again.

## 10. Connect to the chapter

| Step | Chapter section |
|---|---|
| 1 | Section 3.10 (the collector's six rules), Section 3.9 (USE checklist), Section 3.2 (inventory) |
| 2 | Section 3.3 (averages hide the saturated core; the since-boot row) |
| 3 | Section 3.3 (affinity and isolation) |
| 4 | Section 3.4 (reading `free`), Section 3.5 (storage I/O) |
| 5 | Section 3.4 (pinned memory and the copy to the GPU), Section 3.6 (link rate) |
| 6 | Section 3.8 (kernel log), Section 3.9 (saturation signals) |
