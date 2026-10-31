# 3.15 — `orion-n28` is "healthy (check gaps)"

Source: lab severity policy (`EVIDENCE_GAP`, sysfs fallback, `PCIE_SPEED_LOW_IDLE`) and the `orion-n28`
snapshot (non-root, GPUs idle, sysstat missing) `[SIMULATED]`.

**What can be concluded.** From unprivileged sources the inventory matches the baseline: CPU topology,
NUMA nodes and memory, GPU and NIC presence, PCIe *width* (recovered from sysfs because `lspci` showed
`<access denied>`), interface MTUs and speeds. The GPUs at 2.5 GT/s x16 are idle (utilization ≤ 5 %), so
the downshift is power management (`PCIE_SPEED_LOW_IDLE`, info). `intel_pstate` with `powersave` is
dynamic, not pinned low.

**What cannot be concluded.** "No findings" is not "healthy" when evidence is missing:

| Missing evidence | Why it is missing | What is needed |
|---|---|---|
| Kernel-log health: AER, EDAC, Xid, MCE, link flaps | `dmesg` and `journalctl -k` denied | Root, or membership of `adm`/`systemd-journal`, then `journalctl -k -b --no-pager` |
| Storage latency, per-device queues | `iostat` missing | Install sysstat (or a collector image that has it); `iostat -x 1 3` |
| Per-CPU hotspots, softirq load | `mpstat` missing | sysstat; `mpstat -P ALL 1 5` |
| PCIe speed under load | GPUs idle | Re-collect while a workload runs (`nvidia-smi` link gen with utilization > 5 %) |
| Process NUMA placement | No PID given | `--pid <training pid>` for `numastat -p` and `taskset -cp` |

**Next step:** keep the node out of the "cleared" state and re-collect as root (or with journal group
access), with sysstat installed, under load, with the training PID. Only then can it be declared
healthy.
