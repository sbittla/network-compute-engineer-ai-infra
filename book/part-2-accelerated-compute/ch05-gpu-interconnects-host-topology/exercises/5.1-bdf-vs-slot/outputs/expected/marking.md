# Marking scheme: 5.1 PCIe BDF versus physical slot

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** definition and two commands/fields.

| Criterion | Points |
|---|---|
| BDF defined as domain:bus:device.function, the enumeration address of a PCIe function | 1 |
| Explains why it is not the slot: bus numbers are assigned at enumeration by firmware/OS and can change (BIOS change, platform differences) | 1 |
| Two slot sources given (lspci -vmm PhySlot / lspci -v Physical Slot, dmidecode -t slot, /sys/bus/pci/slots/*/address) | 1 |
