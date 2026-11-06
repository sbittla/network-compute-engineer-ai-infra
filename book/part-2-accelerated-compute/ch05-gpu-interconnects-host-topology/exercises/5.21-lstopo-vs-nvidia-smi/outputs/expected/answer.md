# 5.21 — When `lstopo` and `nvidia-smi` relations disagree (model answer)

Relies on manuscript Section 5.6.2 (lstopo and hwloc) and Section 5.6.4 (cross-checking sources).

**Why they can disagree.** The lab derives PIX…SYS from a simplified tree rule (count bridges, check for a
shared host bridge or package). Real platforms contain things that rule does not model: extra or
firmware-hidden bridges, retimers, multi-level PCIe switches, switch functions exposed as separate bridges,
NVSwitch or management functions in the tree, GPUs or NICs in a different PCI domain (segment), or hwloc
attaching a device to the wrong package because of incomplete ACPI tables. Separately, the NVIDIA driver may
classify a path with its own rules (e.g. treating a particular switch topology as PXB rather than PIX).

**What to do.** Do not silently pick one. Inspect the actual tree with `lspci -tv` (and `lspci -vvv` for
bridge types), compare it with the vendor's platform block diagram, and use measured P2P bandwidth
(`p2pBandwidthLatencyTest`, `ib_write_bw --use_cuda`) as the tie-breaker. Record the discrepancy and the
resolved relation in the mapping artifact, and update the parser rule if it is a platform feature.

(≈ 150 words.)
