# 2.1.8 — Why the optics count matters operationally

Source: manuscript Section 2.4 ("Counting the backend"); ORION's backend needs 1,024 single-port 400G
transceivers (or 640 with twin-port switch optics) `[MODELED]`.

1. **Failure and spares.** Optical transceivers and their fiber connections are among the most
   frequently failing and replaced components in an AI cluster, and on ORION every backend optic sits on
   the path of a synchronous job: one failing optic on a rail stalls or slows the whole job. The count
   sets the expected failure rate, the on-site spares stock, and the repair workload for Fleet and
   Fabric.
2. **Power, heat and reach.** Each 400G module draws several watts and must be cooled inside the switch
   and the NIC. Across 1,024 modules that is a measurable share of network-rack power. The optic type
   (short-reach multimode versus single-mode) also sets the maximum cable length, which constrains where
   GPU racks can sit relative to the network racks.

Also accepted: firmware and compatibility management (module firmware, vendor coding), and cleaning and
inspection workload for every connector during installation and repair.
