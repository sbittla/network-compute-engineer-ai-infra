# 7.R1 — What an intent validator can never catch (model answer)

Relies on manuscript Section 7.11 (lab overview), "Realism boundaries", and Section 7.12. The lab's
validator reads the *intended* configuration (devices, links, advertisements). It proves that the
plan is self-consistent, not that the running fabric matches the plan or behaves correctly. Any three
of the following earn full marks:

| Fault class outside intent | Why intent cannot see it | Evidence source that would |
|---|---|---|
| **Physical-layer faults**: dirty or failing optics, CRC/FEC errors, a unidirectional fiber | The intent says "400G link"; it says nothing about signal quality | Interface error counters (FCS, symbol, FEC corrected/uncorrectable), transceiver DOM (Rx power, temperature), pre-FEC BER trend (Chapter 10) |
| **Running-state drift**: the device's live config differs from intent (a port reverted to MTU 1500 after an RMA, as in Section 7.12; a leftover `compare-routerid`, as in 7.T) | The validator checks the plan, not what the switch is running | Config collection and diff against the rendered intent (golden-config compliance, Chapter 20) |
| **FIB/hardware programming faults**: route in the RIB but missing or wrong in the ASIC | Control-plane state looks correct | ASIC table dumps (`show ip route hardware`-style, `[VENDOR-SPEC, 2026-10]`), data-plane probes that sweep every ECMP member |
| **Congestion behaviour**: PFC storms, ECN misconfiguration, incast | Intent describes topology and routing, not dynamics | Per-queue watermarks, PFC pause and ECN mark counters, NIC CNP counters (Chapter 9) |
| **Host-side misconfiguration**: wrong GID index, NIC MTU, cabling to the wrong leaf port | Hosts are outside the fabric intent dataset | Host inventory and readiness checks (Chapters 3 and 8), LLDP neighbour tables |

**Marking point:** each class must come with an evidence source that would actually reveal it. "Monitor
the network" earns nothing.
