# Marking scheme: K2 Why one slow GPU slows the whole job

Type knowledge-check · kind computed · tier L1 · 4 points

**Evidence required:** Mechanism plus the throughput-loss arithmetic for a 256-GPU synchronous job.

| Criterion | Points |
|---|---|
| States that every synchronous step waits for the slowest rank in the collective | 2 |
| Computes the loss as about 10 % of the whole job (about 25.6 GPU-equivalents), not 10 %/256 | 1 |
| Notes that the other 255 GPUs idle (spin in the collective) rather than doing useful work | 1 |
