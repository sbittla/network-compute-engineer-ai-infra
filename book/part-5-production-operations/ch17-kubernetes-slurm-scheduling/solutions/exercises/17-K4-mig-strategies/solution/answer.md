# 17-K4 — MIG mixed versus single strategy

`all-1g.10gb` on eight H100s gives 8 × 7 = **56** instances of ≈ 10 GB each (Table 17.2).

| Strategy | Advertised resources | Pod requesting `nvidia.com/gpu: 1` |
|---|---|---|
| `mixed` | `nvidia.com/mig-1g.10gb: 56`, **`nvidia.com/gpu: 0`** | Stays **Pending** with `Insufficient nvidia.com/gpu`; it would need to request `nvidia.com/mig-1g.10gb: 1` (lab case P07, code `MIG_PROFILE_MISMATCH`) |
| `single` | `nvidia.com/gpu: 56` (the slices are advertised under the generic name) | **Schedules** and receives one `1g.10gb` instance: 1/7 of the SMs and ≈ 10 GB of HBM. A workload that expected a full 80 GB GPU will likely fail with out-of-memory |

**Why it matters.** Under `mixed` the failure is loud (Pending) and easy to diagnose from node
`allocatable`; under `single` it is silent until the application runs out of memory. On ORION the
MIG node (orion-n28) is ineligible for whole-GPU jobs, and the diagnoser must report
`MIG_PROFILE_MISMATCH`, not quota (P07's quota 47 + 1 = 48 is *not* exceeded).

**Common mistake:** saying `single` exposes 8 GPUs. Changing MIG geometry is a lifecycle event
(drain first), not a live tweak. Source: Section 17.3.1.
