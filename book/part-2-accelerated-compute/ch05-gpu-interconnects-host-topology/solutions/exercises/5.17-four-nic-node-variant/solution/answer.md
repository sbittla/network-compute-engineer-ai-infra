# 5.17 — Four-NIC node variant (model answer)

Relies on manuscript Section 5.8 (rail design), Section 5.9 (model, Table 5.4) and docs/REFERENCE_CLUSTER.md.
Busbw `[MODELED]`, parameters `[ILLUSTRATIVE]`; `solve.py` asserts the arithmetic.

## Rail architecture and mapping: 4 rails

```text
 socket 0                                   socket 1
 ├─ switch 0: GPU0, GPU1, NIC0 → rail 0     ├─ switch 2: GPU4, GPU5, NIC2 → rail 2
 └─ switch 1: GPU2, GPU3, NIC1 → rail 1     └─ switch 3: GPU6, GPU7, NIC3 → rail 3
 (each GPU and the NIC on its own downstream port: both GPUs PIX to the NIC)
```

GPU pair (2*k*, 2*k* + 1) → NIC *k* → rail *k*. Four rails, one leaf group per rail. Eight rails would need eight
NICs (or dual-port NICs split across rails) for no extra PCIe bandwidth.

**Rank placement and settings.** Local rank *i* → GPU*i* (`CUDA_DEVICE_ORDER=PCI_BUS_ID`), CPU/memory bound to
the GPU's NUMA node; NCCL's topology detection pairs GPUs 2*k* and 2*k* + 1 with NIC *k*; optionally
`NCCL_IB_HCA` listing the four backend NICs only; keep the default GDR level (PIX is within it).

## Modeled busbw, 1 GiB, 32 nodes (*n* = 256), α = 0.2 ms, no variance

Assumptions: NCCL still builds eight rings, two per NIC; a NIC shared by two GPUs divides by 2 (Table 5.4);
fabric non-blocking.

- Per-ring rate = 48 / 2 = **24 GB/s**.
- *t* = 1.99219 × 134,217,728 B / 24 × 10⁹ B/s + 0.2 ms = 11.141 + 0.2 = **11.34 ms**.
- busbw = 1.99219 × 1,073,741,824 / 11.34 ms ≈ **188.6 GB/s**, vs **370.7 GB/s** for HX8 (Exercise 5.9 (a)): 51 %.
- Equivalently four rings carrying *S*/4 at 48 GB/s: same 11.141 ms. Per node, 4 × 50 = 200 GB/s of NIC
  bandwidth vs 400 GB/s on HX8.

## Workload recommendation

Schedule on the variant: inference, fine-tuning, and jobs whose heavy traffic stays inside the node (TP-only,
small DP degree, pipeline stages with light activations). Keep large data-parallel and FSDP pretraining,
whose step time includes large cross-node collectives, on HX8. Mixed jobs must not span both node types (the
slowest node sets every ring).

**Rejected alternative:** 8 rails using dual-port NICs with one port per rail. It keeps the 8-rail fabric
uniform, but doubles leaf ports and optics, and each NIC is still behind one PCIe Gen5 x16 link (≈ 50 GB/s), so
per-node bandwidth does not rise. Cost without benefit.
