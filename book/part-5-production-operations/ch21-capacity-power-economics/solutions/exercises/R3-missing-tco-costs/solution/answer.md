# R3 — Missing TCO costs: model answer

Sources: manuscript Section 21.4 (Table 21.1a, "Build versus rent") and `lab/data/assumptions.yaml`
(the `prices` block).

The lab's TCO has five lines: capex amortization, energy, colocation space, support, and staff.
Missing costs:

| Missing cost | Could it change a decision? |
|---|---|
| **Financing / cost of capital** (straight-line amortization ignores interest) | **Yes.** Capex is 55 % of TCO. At an 8 % cost of capital over 4 years the annuity factor is 0.302 instead of 0.25, so annualized capex rises by ≈ 21 %, which favours lower-capex designs (A) and renting over owning, and shifts the "own if allocation > 59 %" threshold upward |
| **Electricity demand charges and power-factor penalties** | **Yes.** Synchronized swings and peaks (Section 21.7) are billed on peak kW in many tariffs, which favours capping and penalizes A's higher facility power |
| **Residual / resale value** at end of life | **Yes.** It reduces effective capex. It differs by generation and favours the newer Design B |
| Taxes, depreciation schedule, insurance | Sometimes. Tax rules can change the effective amortization period |
| Software licences (scheduler, observability, enterprise drivers) | Rarely, unless priced per GPU, which then favours fewer, faster GPUs (B) |
| Data egress and storage growth | For build versus rent, yes. It is part of the rent-side price |
| Decommissioning, e-waste, data sanitization | Rarely |
| Onboarding labour and burn-in time (2–3 weeks to schedulable, Section 21.3) | It shifts in-service dates rather than annual cost |
| Spare-pool capex (Chapter 19 variation) | Yes, for reliability-driven designs: it sits outside the production partition |

**The ones that change decisions** are those that scale differently between options: financing
(capex-heavy versus opex-heavy), demand charges (peak-power-heavy designs), and resale (generation
differences). Costs that scale with node count in both options mostly cancel in a per-useful-unit
comparison.

**Common weakness:** listing costs without saying which could flip a choice, or claiming electricity
price is decisive. It is ≈ 4 % of TCO, and M2's sensitivity shows that even $0.20/kWh leaves the
ranking unchanged.
