# 5.20 — Key the mapping by GPU UUID and NIC BDF (model answer)

Relies on manuscript Section 5.6.3 (from raw outputs to a mapping artifact) and Section 5.2 (addressing).

GPU index and HCA name are **software labels**: the GPU index changes with `CUDA_VISIBLE_DEVICES`,
`CUDA_DEVICE_ORDER` (fastest-first vs PCI bus order) and container device mapping; the `mlx5_*` name comes from
probe order or udev naming rules and is reassigned when a card is replaced or a rule changes. A **GPU UUID**
identifies the physical GPU for its lifetime, and a **NIC BDF** identifies where the function enumerated in the
PCIe tree, which is what locality depends on.

**A failure the index-keyed version hides** (Lab 5, `orion-n17` `[SIMULATED]`): the replacement rail-3 NIC is
installed in slot 11 on a socket-1 root port. The site udev rule still names it `mlx5_3`, so a CSV keyed
"GPU3 → `mlx5_3`" diffs clean against golden. Keyed by BDF, the row shows the NIC moved from `43:00.0` to
`86:00.0` (NUMA 1, SYS from GPU3), exposing the fault at once.

(≈ 150 words.)
