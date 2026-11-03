# 20-K4 — The five validation layers: worked answer

**Relies on:** manuscript Section 20.5, Table 20.6, and the MTU policy of Section 20.5.1.

## Model answer

The five layers, in order, each catching a defect class the previous one cannot:

1. **Syntax**: does it parse? (a tab in YAML)
2. **Schema**: are fields known, typed and in range? (`ecn_enabled: "yes"`, a string where a boolean is
   required)
3. **Cross-object policy**: do invariants that span objects hold?
4. **Pre-deployment analysis**: what will the network do with this config? (route leak, ACL shadowing,
   a missing BGP neighbour, found by Batfish-class analysis or simulation)
5. **Post-deployment verification**: did the target end up in the intended state and behave correctly?
   (read-back shows RDMA `active_mtu` still 1,024 after the change; an `all_reduce_perf` pair test)

**A defect only layer 3 catches on ORION:** a rail leaf with PFC enabled on priority 4 while RoCE data is
mapped to priority 3 (DSCP 26 → TC 3). The schema is satisfied: `pfc_priorities: [4]` is a list of
integers in 0–7. Only the relationship is wrong: PFC must be enabled on exactly the priority RoCE uses, on
both hosts and leaves. Applied, rail 5 would become lossy under incast while an unused class pauses, a
rail-specific busbw collapse (the planted `orion-be-leaf-r5` override in the lab). Other valid examples:
`host_mtu + 22 > min(leaf port_mtu)` (9,216 + 22 = 9,238 > 9,216 on `orion-n10`), or CNP DSCP 48 mapped to a
PFC-enabled or non-strict class.

## Marking notes (4 points)

2 points for all five layers in order (1 point if one is missing or misordered); 1 point for a valid
layer-3 ORION defect; 1 point for explaining that each value is valid in isolation and only the
relationship across objects is wrong.

**Common wrong answers.** Giving a schema defect (a wrong type, an out-of-range value) as the layer-3
example. Listing "unit tests" or "code review" as layers. Placing pre-deployment analysis after deployment.
