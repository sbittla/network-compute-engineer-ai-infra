# ORION host diagnostic report

| Host | Critical | Warning | Info | Verdict |
|---|---|---|---|---|
| srini | 16 | 0 | 2 | DRAIN / repair |

## Critical (16)

- **srini** `INTERFACE_MISSING` [fe0] — fe0 not present in ip link show
- **srini** `INTERFACE_MISSING` [fe1] — fe1 not present in ip link show
- **srini** `INTERFACE_MISSING` [rail0] — rail0 not present in ip link show
- **srini** `INTERFACE_MISSING` [rail1] — rail1 not present in ip link show
- **srini** `INTERFACE_MISSING` [rail2] — rail2 not present in ip link show
- **srini** `INTERFACE_MISSING` [rail3] — rail3 not present in ip link show
- **srini** `INTERFACE_MISSING` [rail4] — rail4 not present in ip link show
- **srini** `INTERFACE_MISSING` [rail5] — rail5 not present in ip link show
- **srini** `INTERFACE_MISSING` [rail6] — rail6 not present in ip link show
- **srini** `INTERFACE_MISSING` [rail7] — rail7 not present in ip link show
- **srini** `INVENTORY_MISMATCH` [cores_per_socket] — lscpu cores_per_socket=12, baseline 56
- **srini** `INVENTORY_MISMATCH` [gpu_count] — 2 GPUs visible, baseline 8
- **srini** `INVENTORY_MISMATCH` [memory] — free -m total 7938 MiB < baseline minimum 2000000 MiB
- **srini** `INVENTORY_MISMATCH` [numa0] — numactl node 0 size 7938 MB < 1000000 MB (DIMM mapped out?)
- **srini** `INVENTORY_MISMATCH` [numa_nodes] — lscpu numa_nodes=1, baseline 2
- **srini** `INVENTORY_MISMATCH` [sockets] — lscpu sockets=1, baseline 2

## Info (2)

- **srini** `EVIDENCE_GAP` [cpufreq] — read /sys/devices/system/cpu/cpu*/cpufreq: missing - no cpufreq interface (VM, container, or cpufreq disabled)
- **srini** `EVIDENCE_GAP` [nvidia_smi] — nvidia-smi --query-gpu=index,pci.bus_id,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,utilization.gpu --format=csv: missing - nvidia-smi not found in /usr/sbin:/usr/bin:/sbin:/bin
