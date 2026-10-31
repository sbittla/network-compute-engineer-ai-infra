# 5.1 — PCIe BDF versus physical slot (model answer)

Relies on manuscript Section 5.2 ("Hierarchy and addressing") and Section 5.6.3.

**Definition.** A BDF (written `domain:bus:device.function`, e.g. `0000:19:00.0`) is the enumeration address
of one PCIe *function*: the PCI domain (segment), the bus number assigned during enumeration, the device
number on that bus and the function number within a multi-function device.

**Why it is not the slot.** Bus numbers are assigned by firmware and the OS when they walk the PCIe tree at
boot; they describe *where the device enumerated*, not the labelled connector on the motherboard. The same
physical slot can get a different bus number after a BIOS update, a change in bifurcation settings or an
added device upstream, and two platform models can map slots to buses differently. A technician replacing a
card needs the slot; software comparing topologies needs the BDF; the mapping CSV records both.

**Two ways to get the slot** (any two):

- `lspci -vmm -s <BDF>` → the `PhySlot:` field (or `lspci -v`, "Physical Slot");
- `dmidecode -t slot` → SMBIOS slot designations with their bus addresses;
- `/sys/bus/pci/slots/*/address` → slot number to bus/device mapping.

Lab 5 example `[SIMULATED]`: on `orion-n17` the replacement rail-3 NIC enumerates at `86:00.0` with
`PhySlot: 11` and `NUMANode: 1` instead of slot 4 under GPU3's switch.

**Common wrong answer.** "The bus number is the slot number." It only looks that way on some platforms.
