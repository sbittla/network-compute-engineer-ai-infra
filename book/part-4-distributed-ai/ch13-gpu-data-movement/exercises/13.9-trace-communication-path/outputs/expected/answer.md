# 13.9 — Trace a communication path (O1): worked solution

Endpoints: GPU 6 on `orion-n05` → GPU 6 on `orion-n14`, a DP gradient chunk. On HX8, GPU 6 and NIC 6
share PCIe switch SW3 on socket 1 (`PIX`), and NIC 6 connects to rail leaf `orion-be-leaf-r6`
(`docs/REFERENCE_CLUSTER.md`). Latencies are `[ILLUSTRATIVE]` orders of magnitude from Section 13.4.
Bandwidths are theoretical per direction `[VENDOR-SPEC, 2026-10]`.

**Diagram 1, GPUDirect RDMA, same rail.**

```text
orion-n05                                                    orion-n14
GPU6 HBM ──(HBM 3.35 TB/s, ≈ ns)──> NCCL send buf (HBM)
  └─PCIe Gen5 x16 via SW3 (≈ 63 GB/s, ≈ 0.5 µs)──> NIC6 (400 Gb/s, ≈ 0.4 µs)
       └─> orion-be-leaf-r6 (cut-through, ≈ 0.6–1 µs; 30 m fibre ≈ 0.15 µs)
            └─> NIC6 (≈ 0.4 µs) ─PCIe via SW3 (≈ 0.5 µs)─> NCCL recv buf ─> GPU6 HBM (reduce)
```

*Caption: rail-local GDR path. 0 host-DRAM copies, 2 PCIe transfers, 1 switch hop. About 2 µs one way
in hardware, plus 2–5 µs of NCCL software per hop.*

**Diagram 2, host-staged (no GDR).**

```text
GPU6 HBM → NCCL buf ─(NCCL kernel stores over PCIe, SW3 uplink)→ pinned host buf, socket-1 DRAM
  ─(NIC6 DMA read, PCIe)→ NIC6 → orion-be-leaf-r6 → NIC6 ─(DMA write)→ pinned host buf, socket-1 DRAM
  ─(NCCL kernel loads over PCIe)→ NCCL recv buf → GPU6 HBM
```

*Caption: host-staged path. 2 host copies (one per side), 4 PCIe transfers, each crossing the SW3 uplink
(≈ 55 GB/s achievable), 1 switch hop. Adds several µs per message and consumes DRAM bandwidth (≈ 300 GB/s
per socket, shared with the data loader).*

**Diagram 3, cross-rail: destination GPU 2 on `orion-n14`.** GPU 2 is behind NIC 2 on rail 2.
- **Without PXN:** NIC6 → `orion-be-leaf-r6` → a backend spine (`orion-be-spine-S`, S = 1–4, e.g. `orion-be-spine-2`) → `orion-be-leaf-r2` → NIC2 →
  GPU 2: 0 copies with GDR, 2 PCIe transfers, **3 switch hops** (≈ +2 µs and shared spine capacity).
- **With NCCL PXN:** on `orion-n05`, GPU 6 → GPU 2 over NVLink/NVSwitch (450 GB/s per direction), then
  NIC 2 → `orion-be-leaf-r2` → NIC 2 → GPU 2: one NVLink hop plus **1 switch hop**, keeping traffic
  rail-local.

| Variant | Host copies | PCIe transfers | Switch hops |
|---|---|---|---|
| GDR, same rail | 0 | 2 | 1 |
| Host-staged, same rail | 2 | 4 | 1 |
| GDR, cross-rail via spine | 0 | 2 | 3 |
| GDR, cross-rail with PXN | 0 | 2 (+1 NVLink hop) | 1 |

**Common wrong answers.** Non-canonical names ("leaf-6", "spine1"). Omitting the NCCL buffer. Drawing
the host-staged copy as done by the CPU (the NCCL kernel does it over PCIe).
