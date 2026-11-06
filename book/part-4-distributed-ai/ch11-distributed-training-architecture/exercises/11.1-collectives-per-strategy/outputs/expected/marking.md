# Marking scheme: 11.1 Collectives per strategy

Type knowledge-check · kind written · tier L1 · 6 points

**Evidence required:** a six-row table with collective names and frequencies.

| Criterion | Points |
|---|---|
| DDP and ZeRO-1 rows correct (all-reduce; reduce-scatter + all-gather, once per step) | 2 |
| ZeRO-3/FSDP row correct (all-gather fwd and bwd, reduce-scatter, per layer/unit per micro-batch) | 1 |
| TP + SP row correct (all-gather + reduce-scatter, per layer per micro-batch) | 1 |
| PP row correct (point-to-point send/recv per micro-batch per stage boundary) | 1 |
| EP row correct (all-to-all dispatch + combine per MoE layer per micro-batch) | 1 |
