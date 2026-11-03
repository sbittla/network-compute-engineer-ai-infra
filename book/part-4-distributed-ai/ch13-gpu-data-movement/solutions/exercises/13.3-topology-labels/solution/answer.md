# 13.3 — Topology labels PIX, PXB, PHB, NODE, SYS: worked solution

**Definitions, as printed by `nvidia-smi topo -m` for a GPU↔NIC pair `[VENDOR-SPEC, 2026-10]`:**

| Label | Path between GPU and NIC | ORION HX8 example |
|---|---|---|
| `PIX` | Through a single PCIe switch: the pair shares a switch | GPU 6 ↔ NIC 6 under switch SW3 |
| `PXB` | Through several PCIe switches, without crossing a host bridge | GPU 0 ↔ NIC 1 when switch complex SW0 is two-level (a top switch above two leaf switches, as on HGX-class boards); `PIX` if SW0 is one switch |
| `PHB` | Through a PCIe host bridge (the CPU) | Two switches under one host bridge on platforms built that way |
| `NODE` | Across host bridges within one NUMA node | GPU 0 ↔ NIC 2 (SW0 and SW1 on different root ports of socket 0); likewise GPU 6 ↔ NIC 4 |
| `SYS` | Across the inter-socket link (UPI/xGMI) | GPU 6 ↔ NIC 2 (other socket) |

The labels are ordered from closest to farthest. Each step outward adds latency, shares a more contended
link, and, from `PHB` outward, makes the traffic depend on root-complex and socket-interconnect
behaviour. Whether a same-socket, different-switch pair reports `NODE` or `PHB` depends on how the
platform exposes its root ports; on HX8 each switch hangs off its own root port, so expect `NODE`.
Accept `PHB` for GPU 0 ↔ NIC 2 if the answer explains that assumption.

**NCCL default `[VENDOR-SPEC, 2026-10]`.** `NCCL_NET_GDR_LEVEL` sets the maximum distance at which NCCL
uses GPUDirect RDMA. Recent releases default to about `PXB`: `PIX` and `PXB` pairs use GDR, while
`PHB`, `NODE` and `SYS` pairs are staged through host memory. The default changes between releases and
can be changed by platform tuning, so **verify** it in the NCCL documentation for the installed version
and in the INFO log (channel lines ending in `/GDRDMA`). PXN is separate: it can still use GDR for a
`NODE`/`SYS` destination NIC by forwarding over NVLink to the GPU that sits `PIX` to that NIC
(Section 13.3).

**Why it matters (Section 13.5).** ORION's locality rule is "GPU *i* uses NIC *i*" (`PIX`). A rank that
picks a `NODE` or `SYS` NIC directly loses GPUDirect RDMA, and a `SYS` choice also crosses the
inter-socket link twice. On an idle machine this mostly adds variance, which synchronous training turns
into stragglers.

**Common wrong answers.** Defining `PIX` as "same PCIe slot". Omitting `NODE`, or calling a
same-socket, different-switch pair `PXB` (it crosses the root complex, so it is not `PXB`). Saying NCCL
uses GDR for all labels. Omitting the vendor label.
