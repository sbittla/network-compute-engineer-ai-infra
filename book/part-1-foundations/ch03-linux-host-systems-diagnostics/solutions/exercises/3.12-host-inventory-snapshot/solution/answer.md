# 3.12 — Host inventory of `orion-n01` (L1 path)

Method: manuscript Section 3.2 (the HX8 as Linux sees it) and Section 3.10 (snapshot sections). Source:
`lab/data/snapshots/orion-n01.json` `[SIMULATED]`. `solve.py` extracts every value below from the
snapshot and asserts it, so the table is reproducible.

| Category | Value | Section |
|---|---|---|
| CPU | Intel Xeon Platinum 8480+; 2 sockets × 56 cores × 2 threads = 224 CPUs | `lscpu` |
| NUMA | node 0 = CPUs 0–55, 112–167, 1,031,868 MB; node 1 = CPUs 56–111, 168–223, 1,032,151 MB; distance 10/21 | `numactl_hardware` |
| Memory | `free -m` total 2,064,019 MiB (2 TiB = 2,097,152 MiB installed; the rest is firmware/kernel reserved) | `free` |
| GPUs | 8 × H100-class: `18`, `2a`, `3a`, `5d` (node 0) and `9a`, `ab`, `ba`, `db` (node 1), all 32 GT/s x16 | `nvidia_smi`, `pcie_sysfs`, `lspci` |
| Rail NICs | 8 × ConnectX-7-class (device 0x1021), 32 GT/s x16 | `pcie_sysfs`, `lspci` |
| Frontend NICs | 2 × ConnectX-6 Dx-class (device 0x101d), 16 GT/s x16 | `pcie_sysfs` |
| NVMe | 8 drives, 16 GT/s x4 each | `pcie_sysfs` |
| BMC VGA | 1 device at 5 GT/s x1 (healthy by design) | `pcie_sysfs` |
| Interfaces | `rail0–7` MTU 9000 at 400,000 Mb/s; `fe0–1` MTU 9000 at 200,000 Mb/s | `ip_link`, `ethtool:*` |
| Kernel | 5.15.0-122-generic | `uname` |
| Drivers/firmware | NVIDIA driver 550.127.05; mlx5 firmware 28.39.1002 | `kernel_log` |
| CPU frequency | `intel_pstate` driver, `performance` governor | `cpufreq` |

Layout check against `docs/REFERENCE_CLUSTER.md`: four GPUs and four rail NICs per socket, every GPU and
NIC at its full capability, which makes this node a valid baseline.

**L2 path (grading notes).** Award the same 10 points for a correct table of the learner's own host, plus up
to 5 for the root/non-root gap analysis. That analysis should note that `lspci -vv` hides link
capabilities without root (`<access denied>`) and that sysfs (`current_link_speed`, `max_link_width`)
recovers them; that `dmesg` may be denied and `journalctl -k` recovers it with `adm` or
`systemd-journal` group membership; and that `nvme smart-log` and `turbostat` need root, with no
unprivileged fallback.
