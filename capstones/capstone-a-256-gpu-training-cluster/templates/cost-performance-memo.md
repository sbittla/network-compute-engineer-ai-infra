# Cost/Performance Trade-off Memo — ORION-256 Backend Fabric

**To:** <fill: Halcyon AI infrastructure leadership> · **From:** <fill> · **Date:** <fill>
**Decision requested:** <fill: one sentence>

## 1. Recommendation (3 sentences maximum)

<fill>

## 2. Options compared

| Criterion | Option A: rail-optimized 1:1 | Option B: ToR 2:1 | Evidence label |
|---|---|---|---|
| Capex (USD) | <fill> | <fill> | `[MODELED]` from `[ILLUSTRATIVE]` prices |
| Backend fabric share of capex | <fill> | <fill> | `[MODELED]` |
| Optics count | <fill> | <fill> | `[MODELED]` |
| IT power, sustained (kW) | <fill> | <fill> | `[MODELED]` |
| Step time, baseline_3d, launcher order | <fill> | <fill> | `[MODELED]` |
| Step time, fsdp_dp32, launcher order | <fill> | <fill> | `[MODELED]` |
| $/M training tokens (best and worst layout) | <fill> | <fill> | `[MODELED]` |
| Sensitivity to rank order / scheduler fragmentation | <fill> | <fill> | `[MODELED]` |
| Leaf failure blast radius | <fill> | <fill> | qualitative |
| Operational complexity (cabling, spares, troubleshooting) | <fill> | <fill> | qualitative |
| Future workloads (MoE all-to-all, larger DP) | <fill> | <fill> | qualitative |

## 3. Why this recommendation

<fill: the reasoning chain. Use the break-even analysis. State what would change your mind.>

## 4. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| <fill> | | | | |

## 5. What we still need to measure

<fill: the L2/L3 measurements that would convert the key `[MODELED]` numbers to `[MEASURED]`, and when.>
