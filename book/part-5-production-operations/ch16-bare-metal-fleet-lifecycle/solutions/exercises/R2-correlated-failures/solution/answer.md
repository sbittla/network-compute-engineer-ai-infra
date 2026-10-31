# R2 — Correlated failures and canary design

Section 16.6 treated failures as independent; the Poisson canary model of Section 16.8 does too. Real
failures cluster:

| Mechanism | Why failures correlate | Design change |
|---|---|---|
| **Bad manufacturing lot** of optics, GPUs, or DIMMs | Parts from one lot share a defect; nodes delivered together share lots | Record lot/batch in the inventory (Table 16.1 fields); choose canary nodes to *cover every lot*, and cap each wave per lot as well as per rack |
| **Rack-level power or cooling** (PDU, CDU loop, containment, a new fan curve) | One rack's environment affects all its nodes at once | Keep the per-rack cap (≤ 1 node per rack per wave); include the hottest rack in the canary; watch inlet and throttle reasons during the bake |
| **Workload-triggered firmware bugs** | A bug appears only under one job's traffic pattern (all-to-all, NVLS) | Bake canaries on representative workloads (W-TRAIN and W-INFER), not idle |
| **Shared upstream** (leaf switch, PDU feed) | Nodes behind one device fail together | Spread canary and wave members across leaves/feeds; treat the shared device as its own change |

**Effect on the numbers.** Correlation lowers the *effective* number of independent samples: four
canary nodes from one lot and one rack behave like ≈ 1 sample for lot or rack effects, so the
1 − e^(−λNT) detection probability is optimistic. Diversity of canary placement matters as much as
its size.

Source: Sections 16.6, 16.8; realism boundaries of Chapter 16.
