# Marking scheme: K7 GPU utilization does not show saturation

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** what the utilization counter measures, and two alternative signals with the reason each is better

| Criterion | Points |
|---|---|
| utilization.gpu = fraction of sample period with at least one kernel running; says nothing about SMs, tensor use or HBM bandwidth | 2 |
| Signal 1: DCGM DRAM active (bandwidth saturation) plus tensor/SM active, with reason | 1 |
| Signal 2: engine signals (running vs cap, KV usage, waiting queue, step time vs batch), with reason | 1 |
