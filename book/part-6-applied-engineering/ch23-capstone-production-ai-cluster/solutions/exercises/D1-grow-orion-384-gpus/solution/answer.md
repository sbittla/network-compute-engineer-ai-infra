# D1 — Growing ORION to 48 HX8 nodes (384 GPUs)

**Source:** manuscript Section 23.3 (ADR template, Table 23.4), Section 23.4 (invariants, "What a spine
is for in a rail-optimized fabric"), Section 23.5; docs/REFERENCE_CLUSTER.md; key Section E. All values
`[MODELED]`; switch port configurations `[VENDOR-SPEC, 2026-10]` to be confirmed per SKU.

## Arithmetic per option (8 rails, 48 nodes → 48 NIC ports per rail)

| Option | Leaves | Leaf ports used | Oversub | Spines (64-port) | Spine ports | Backend cables | Spine-crossing traffic |
|---|---|---|---|---|---|---|---|
| A: 1 radix-64 leaf/rail, 48 down / 16 up | 8 | 64 / 64 | 48:16 = **3:1** | 4 (4 per leaf each) | 8 × 4 = 32 / 64 | 8 × 64 = **512** | Cross-rail only |
| B: 2 radix-64 leaves/rail, 24 / 24 | 16 | 48 / 64 | **1:1** | 6 (4 per leaf each) | 16 × 4 = 64 / 64 | 16 × 48 = **768** | Cross-rail **and** same-rail between the two leaves |
| C: 1 × 128-port leaf/rail, 48 / 48 | 8 | 96 / 128 | **1:1** | 6 (8 per leaf each) | 8 × 8 = 64 / 64 | 8 × 96 = **768** | Cross-rail only |

- A: 128 uplinks in total; keeping ORION's 4 spines gives 16 / 4 = 4 per spine per leaf (2 spines would be
  the minimum, at the cost of spine redundancy). Cables 384 host–leaf + 128 leaf–spine.
- B: uplinks 16 × 24 = 384 → 384 / 64 = 6 spines; 24 / 6 = 4 per spine per leaf. Cables 384 + 384.
- C: uplinks 8 × 48 = 384 → 6 spines; 48 / 6 = 8 per spine per leaf. A 51.2 Tb/s ASIC at 400 Gb/s gives
  51,200 / 400 = 128 ports, so C is feasible in principle; verify the SKU and NIC interoperability.
- Racks: 48 / 4 = **12** (4 × 10.2 = 40.8 kW ≤ 45 kW each). GPU-node power 48 × 10.2 = **489.6 kW** maximum.

## ADR-012 (example): backend fabric for ORION-384

- **Context.** W-TRAIN on 384 GPUs is rail-aligned (TP = 8 inside the node; DP/PP peers share local rank),
  so its traffic stays inside a rail leaf when the rail has one leaf. Next year disaggregated serving adds
  cross-rail KV cache transfer on the same backend. Row constraint 45 kW per rack.
- **Options.** A, B, C above.
- **Decision.** **C** if a qualified 128 × 400G leaf is available; otherwise **A** now.
- **Evidence.** C keeps every rail single-hop for W-TRAIN and gives cross-rail KV transfer 1:1 with 768
  cables; A costs 512 cables and has no effect on rail-aligned DP/PP traffic, but cross-rail traffic sees
  3:1; B pushes same-rail W-TRAIN traffic onto the spines and costs the most switches (16 leaves + 6 spines).
- **Consequences.** C: new SKU qualification, larger failure domain per leaf (48 nodes' rail *r*). A: KV
  transfer contends at 3:1 and a later upgrade means recabling.
- **Revisit trigger.** Cross-rail bytes exceed 10 % of backend bytes over a week, or KV-transfer p99 exceeds
  its budget, or a qualified 128-port leaf SKU becomes available.

**Not recommended: B**, because it breaks the rail-locality property that makes W-TRAIN spine-free.

**Common wrong answers.** Counting 800G cages as 128 ports in A; forgetting that two leaves per rail sends
same-rail traffic across spines; omitting racks/power; a revisit trigger that is a date.
