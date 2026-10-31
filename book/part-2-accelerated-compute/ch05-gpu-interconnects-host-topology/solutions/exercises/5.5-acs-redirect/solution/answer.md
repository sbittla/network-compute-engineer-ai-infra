# 5.5 — ACS Request Redirect and GPUDirect RDMA (model answer)

Relies on manuscript Section 5.2 ("Peer-to-peer and Access Control Services") and Section 5.7.

**Mechanism.** Access Control Services are per-port controls on PCIe switch downstream ports. With **Request
Redirect** (and Completion Redirect) enabled, a peer-to-peer request that would normally turn around inside
the switch (GPU → NIC on two ports of the same switch) is instead forwarded *upstream* to the root complex.
There the IOMMU validates the address, and only then is the transaction routed back down to the peer.

**Why virtualized hosts want it.** When devices are passed through to different VMs, a device must not be able
to DMA directly into another guest's device by bypassing the IOMMU. Redirecting all peer traffic through the
root complex makes the IOMMU see and police every transaction; it is also what makes IOMMU groups small
enough to assign devices to separate guests.

**Why it hurts bare-metal training nodes.** On a dedicated training host there is no guest isolation to
enforce, but every GPU↔NIC GDR transfer now becomes a root-complex round trip: the switch uplink carries the
data twice, latency rises, bandwidth falls and variance grows (on some platforms P2P is refused entirely).
The model treats it as ×0.70 bandwidth and +0.06 CV `[ILLUSTRATIVE]` (Table 5.4).

**Evidence.** `lspci -vvv` on the switch ports: `ACSCtl: ... ReqRedir+ CmpltRedir+` (Lab 5 `orion-n02`, after a
motherboard swap, on all 16 downstream ports `[SIMULATED]`). Topology can look golden while GDR is degraded.

**Common wrong answer.** "ACS improves performance by routing through the CPU."
