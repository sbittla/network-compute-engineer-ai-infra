# Marking scheme: DC Shared versus dedicated inference capacity

Type design-challenge · kind computed · tier L1 · 15 points

**Evidence required:** A one-page recommendation with a criteria x option table, at least one quantified argument, explicit assumptions, and a "would change my mind if..." section.

| Criterion | Points |
|---|---|
| A clear recommendation with a criteria x option table covering SLO risk, utilization and cost, scheduler and failure domain | 5 |
| Quantified argument (pool cost 1,681,920 USD/year; at most 672,768 USD/year reclaimable at 60 % inference load) with assumptions stated | 4 |
| Backend fabric need analysed correctly (TP 8 stays in one node; RDMA needed only for multi-node or disaggregated serving) | 3 |
| Explicit assumptions and a would-change-my-mind section with checkable conditions | 3 |
