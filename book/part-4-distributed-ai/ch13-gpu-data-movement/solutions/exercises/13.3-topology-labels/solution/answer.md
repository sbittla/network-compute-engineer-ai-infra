# 13.3 — Topology labels PIX, PXB, PHB, SYS: worked solution

**Definitions, as printed by `nvidia-smi topo -m` for a GPU↔NIC pair `[VENDOR-SPEC, 2026-10]`:**

| Label | Path between GPU and NIC | ORION HX8 example |
|---|---|---|
| `PIX` | Through at most one PCIe switch, the pair shares a switch | GPU 6 ↔ NIC 6 under switch SW3 |
| `PXB` | Through multiple PCIe switches, without crossing a host bridge | Two switch levels on some platforms |
| `PHB` | Through a PCIe host bridge (the CPU root complex) on the same socket | GPU 6 ↔ NIC 4 (different switch, same socket) |
| `SYS` | Through the root complex *and* the inter-socket link (UPI/xGMI) | GPU 6 ↔ NIC 2 (other socket) |

The labels are ordered from closest to farthest. Each step outward adds latency, shares a more contended
link, and, for `PHB`/`SYS`, makes the P2P traffic depend on root-complex and socket-interconnect
behaviour.

**NCCL default `[VENDOR-SPEC, 2026-10]`.** `NCCL_NET_GDR_LEVEL` sets the maximum distance at which NCCL
uses GPUDirect RDMA. In typical recent releases the default enables GDR for close paths, `PIX` and
`PXB`, and does not use it across `SYS` (and normally not across `PHB`). For farther pairs NCCL stages
through host memory. This default changes between releases and can be changed by platform tuning, so
**verify** it in the NCCL documentation for the installed version and in the INFO log (channel lines
ending in `/GDRDMA`).

**Why it matters (Section 13.5).** ORION's locality rule is "GPU *i* uses NIC *i*" (`PIX`). A rank that
picks a `SYS` NIC loses GPUDirect RDMA and crosses the inter-socket link twice. On an idle machine this
mostly adds variance, which synchronous training turns into stragglers.

**Common wrong answers.** Defining `PIX` as "same PCIe slot". Saying NCCL uses GDR for all labels.
Omitting the vendor label.
