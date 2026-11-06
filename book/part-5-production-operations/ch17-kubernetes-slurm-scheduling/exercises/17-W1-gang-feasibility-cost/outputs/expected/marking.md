# Marking scheme: 17-W1 Gang feasibility and cost

Type worked-problem · kind computed · tier L1 · 8 points

**Evidence required:** Every step as formula → substitution → result with units.

| Criterion | Points |
|---|---|
| 1. Naive 60 GPUs; eligible 52 after excluding draining p07 | 1 |
| 2. Largest gang 3 whole eligible nodes = 24 GPUs | 1 |
| 3. Fragmentation (52 ≥ 32 eligible free but 3 < 4 whole nodes) | 1 |
| 4. Best fit p05 (0 left) | 1 |
| 5. 32 GPUs stranded; 160 GPU-hours; $480 [MODELED price, Chapter 21 TCO] | 2 |
| 6. 128 × (22.5 + 15) min = 80 GPU-hours per preemption | 2 |
