# 2.11.2 — Should ORION accept the rail-leaf SPOF?

Model answer: **accept, documented**. A rail-leaf failure stops a full-scale training job, because
ORION-256 has no spare rail and no spare nodes. The cost per event is the restart (256 GPUs × 0.25 h =
**64 GPU-hours**), the replacement time at 256 GPU-hours per hour (a 2 h leaf swap = **512 GPU-hours**
`[ILLUSTRATIVE]`), and the work lost since the last checkpoint (on average half the ≈ 34 min interval,
≈ 73 GPU-hours). That is ≈ 650 GPU-hours, or ≈ $1,950 at $3.00/GPU-hour (Chapter 21's owned-cluster TCO rate
`[MODELED]`), per leaf failure. Switch
failures are rare compared with the 48 h job-level MTBF already driven by nodes, so the leaves add little
to the expected loss. Removing the SPOF would need a second leaf per rail with dual-ported NICs or a
non-rail design, roughly doubling leaf count and optics and giving up the rail-optimized locality that
keeps DP traffic off the spines. The cheaper mitigation is an on-site spare leaf with pre-staged
configuration and a rehearsed replacement runbook that brings the swap well under 2 h. A reasoned
"reject" earns equal credit if it quantifies a case where restarts are costlier: much larger jobs,
long checkpoint intervals, or a tenant SLA.
