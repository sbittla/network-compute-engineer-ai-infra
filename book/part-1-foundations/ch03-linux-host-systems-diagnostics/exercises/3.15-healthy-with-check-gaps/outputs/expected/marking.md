# Marking scheme: 3.15 What "healthy (check gaps)" means

Type reflection · kind written · tier L1 · 3 points

**Evidence required:** A list of the missing evidence, with the command or privilege needed for each.

| Criterion | Points |
|---|---|
| States what can be concluded from unprivileged sources (inventory, PCIe width via sysfs, MTU and speeds; idle GPU downshift is benign) | 1 |
| States what cannot be concluded (kernel-log health AER/EDAC/Xid/MCE, storage latency and per-CPU behaviour, PCIe speed under load, process NUMA placement) | 1 |
| Next collection steps with the command or privilege for each (sysstat, root or adm/systemd-journal group, collect under load with --pid) | 1 |
