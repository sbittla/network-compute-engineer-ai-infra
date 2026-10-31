# 5.8 — PCIe budget (model answer)

Relies on manuscript Section 5.2 ("Bandwidth by generation", Table 5.1) and Section 5.4 (GPU↔NIC paths).
All values `[MODELED]`; `solve.py` asserts them.

## (a) Per-direction theoretical bandwidth

Bandwidth = transfer rate × 128/130 (encoding) × lanes / 8 bits.

| Link | Arithmetic | Per direction |
|---|---|---|
| Gen4 x16 | 16 × 10⁹ × 128/130 × 16 / 8 | **31.5 GB/s** |
| Gen5 x8 | 32 × 10⁹ × 128/130 × 8 / 8 | **31.5 GB/s** |
| Gen5 x16 | 32 × 10⁹ × 128/130 × 16 / 8 | **63.0 GB/s** |

## (b) Which carries a 400 Gb/s NIC at line rate?

400 Gb/s = **50 GB/s** of payload per direction. Only **Gen5 x16**: achievable after TLP/DLLP overheads is
≈ 50–55 GB/s, so even that is tight. Gen4 x16 and Gen5 x8 achieve ≈ 25–27 GB/s, capping the NIC at
≈ 200–215 Gb/s.

## (c) Uplink load on an HX8 switch (2 GPUs + 2 NICs, one Gen5 x16 uplink)

*With GPUDirect RDMA:* NIC↔GPU DMA turns around inside the switch (PIX). The uplink carries only control
traffic (doorbells, completions, small CPU-side buffers): **essentially 0 of the 2 × 50 GB/s**.

*Host-staged:* every byte crosses the uplink twice (GPU↔host and host↔NIC). Assume both NICs send and receive
at line rate. The upstream direction (toward the CPU) carries GPU D2H copies for sends (2 × 50 GB/s) plus NIC
writes of received data into host memory (2 × 50 GB/s) = **200 GB/s of demand against 63 GB/s**. Shared
four ways, each NIC gets ≈ 63 / 4 ≈ **16 GB/s per direction**, about a third of line rate, consistent with the
model's 18 GB/s host-staged cap (Table 5.4).

**Common wrong answers.** Forgetting the encoding factor (32.0 / 64.0 GB/s); quoting bidirectional numbers;
treating Gen5 x8 as faster than Gen4 x16; assuming host staging costs the uplink only once.
