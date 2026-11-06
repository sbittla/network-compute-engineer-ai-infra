# 17-K1 — Capacity 8, allocatable 7

**Component.** The NVIDIA **device plugin** (deployed by the GPU Operator) registers
`nvidia.com/gpu` with the kubelet and streams the list of devices and their health over the
`ListAndWatch` gRPC stream. The kubelet derives `allocatable` from the *healthy* devices; the
scheduler only ever reads `allocatable`.

**Mechanism.** The plugin watches NVML for critical events on each GPU, for example an uncorrectable
ECC error (Xid 48, or Xid 95 for an uncontained one) or a row-remap failure (Xid 64), and marks that
device `Unhealthy`. It then
reports 7 healthy devices; the kubelet sets `allocatable nvidia.com/gpu: 7` while `capacity` stays
8, and `nvidia-smi -L` still lists 8 GPUs because the device is still enumerated. (A GPU that has
fallen off the bus, Xid 79, is not a good fit for this prompt: it usually disappears from
`nvidia-smi -L` or makes it error.)

**Scheduler outcome.** An 8-GPU pod is never bound to this node: the filter reports
`Insufficient nvidia.com/gpu`, even though the node is `Ready`. Smaller pods can still use the 7
healthy GPUs, which is why the node should be drained rather than left in service.

**Correct follow-up.** Treat it as a hardware event: drain through the Chapter 16 lifecycle
(category `fault`), capture `nvidia-bug-report.sh` and `dmesg` before any reboot, and repair and
re-accept. Restarting the plugin or rebooting only hides a latent fault.

**Common mistakes:** blaming the scheduler, a quota, or a taint; assuming `nvidia-smi` listing
8 GPUs proves all 8 are healthy. Source: Section 17.2.1 (Figure 17.2).
