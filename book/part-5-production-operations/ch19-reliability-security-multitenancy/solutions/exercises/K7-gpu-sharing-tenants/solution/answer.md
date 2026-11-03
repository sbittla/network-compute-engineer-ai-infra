# K7 — Sharing a GPU across tenants: worked solution

**Relies on:** Section 19.9, Table 19.8 and the GPU-sharing paragraph; MIG behaviour `[VENDOR-SPEC, 2026-10]`.

| Mode (two tenants, one H100-class GPU) | Memory isolation | Fault isolation | Performance isolation |
|---|---|---|---|
| **Whole GPU** (only one tenant gets it; the other gets a different GPU) | Full: one tenant per GPU; reset or scrub on release so the next tenant sees no residue | Full: a fault affects only the owning tenant | Full: no co-tenant on the device |
| **MIG** (up to 7 instances on H100) | Hardware-partitioned: each instance has its own HBM slice and L2 cache share | Instance-level: most errors are contained to the instance, but some GPU-wide errors (for example an uncontained ECC or a GPU fall-off-the-bus) still affect every instance | Strong: dedicated SMs, memory bandwidth and cache slices per instance; small residual sharing of some engines and of power/thermal limits |
| **Time-slicing** | Weak: separate virtual address spaces, but no capacity limit, so one client can exhaust GPU memory and make the other fail allocations | None: a fatal fault in one client can take down the others sharing the GPU | None: contexts compete for SM time and memory bandwidth |

## Conclusion

Across tenants, ORION allows only whole GPU or MIG. Time-slicing (and MPS, which can set memory
limits but still shares fault exposure and has no bandwidth isolation) is acceptable only within one
tenant, for example one team's notebooks. The lab's cobalt-inference tenant time-slices GPUs shared with
borealis, which `check_isolation()` flags as a violation (`gpu_cross_tenant_sharing_requires: mig`).

## Common wrong answers

- "MIG gives complete fault isolation": GPU-wide errors still cross instances.
- "Time-slicing has no memory isolation at all": it does keep address spaces separate. What it lacks is
  capacity limits and fault and performance isolation.
- Forgetting residue: even whole-GPU allocation needs a reset or scrub between tenants.
