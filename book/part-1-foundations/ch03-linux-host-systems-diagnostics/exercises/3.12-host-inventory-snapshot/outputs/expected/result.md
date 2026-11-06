# 3.12 — orion-n01 inventory `[SIMULATED]`

| Category | Value | Section |
|---|---|---|
| cpu | {"cores_per_socket": 56, "cpus": 224, "model": "Intel(R) Xeon(R) Platinum 8480+", "sockets": 2, "threads_per_core": 2} | lscpu |
| numa | {"node0": {"cpus": "0-55,112-167", "mb": 1031868}, "node1": {"cpus": "56-111,168-223", "mb": 1032151}} | numactl_hardware, lscpu |
| memory | {"free_total_mib": 2064019} | free |
| gpus | [{"bdf": "18:00.0", "link": "32.0 GT/s x16", "numa": 0}, {"bdf": "2a:00.0", "link": "32.0 GT/s x16", "numa": 0}, {"bdf": "3a:00.0", "link": "32.0 GT/s x16", "numa": 0}, {"bdf": "5d:00.0", "link": "32.0 GT/s x16", "numa": 0}, {"bdf": "9a:00.0", "link": "32.0 GT/s x16", "numa": 1}, {"bdf": "ab:00.0", "link": "32.0 GT/s x16", "numa": 1}, {"bdf": "ba:00.0", "link": "32.0 GT/s x16", "numa": 1}, {"bdf": "db:00.0", "link": "32.0 GT/s x16", "numa": 1}] | nvidia_smi, pcie_sysfs |
| rail_nic | {"all_at_capability": true, "count": 8, "links": ["32.0 GT/s x16"]} | pcie_sysfs |
| fe_nic | {"all_at_capability": true, "count": 2, "links": ["16.0 GT/s x16"]} | pcie_sysfs |
| nvme | {"all_at_capability": true, "count": 8, "links": ["16.0 GT/s x4"]} | pcie_sysfs |
| vga | {"all_at_capability": true, "count": 1, "links": ["5.0 GT/s x1"]} | pcie_sysfs |
| interfaces | {"fe0": {"mtu": 9000, "speed_mbps": 200000}, "fe1": {"mtu": 9000, "speed_mbps": 200000}, "rail0": {"mtu": 9000, "speed_mbps": 400000}, "rail1": {"mtu": 9000, "speed_mbps": 400000}, "rail2": {"mtu": 9000, "speed_mbps": 400000}, "rail3": {"mtu": 9000, "speed_mbps": 400000}, "rail4": {"mtu": 9000, "speed_mbps": 400000}, "rail5": {"mtu": 9000, "speed_mbps": 400000}, "rail6": {"mtu": 9000, "speed_mbps": 400000}, "rail7": {"mtu": 9000, "speed_mbps": 400000}} | ip_link, ethtool:* |
| kernel | "5.15.0-122-generic" | uname |
| drivers | {"mlx5_fw": "28.39.1002", "nvidia": "550.127.05"} | kernel_log |
| cpufreq | {"driver": "intel_pstate", "governor": "performance"} | cpufreq |
