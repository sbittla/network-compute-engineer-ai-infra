# Scaling-Efficiency Analysis

## 1. Definitions (with formulas)

- Tokens per step at scale N: <fill: 128 × 4,096 × N/32>
- Per-GPU throughput: <fill>
- Weak-scaling efficiency: E(N) = per-GPU throughput(N) / per-GPU throughput(32)
- Why not strong scaling for this experiment: <fill>

## 2. Weak-scaling table `[SIMULATED]` (valid runs only)

| Variant | GPUs | Runs | Median step (s) | Run-median range (s) | Tokens/s | E(N) |
|---|---|---|---|---|---|---|
| baseline | 32 | <fill> | | | | 1.000 |
| <fill> | | | | | | |

Chart: <fill: E(N) vs N per variant with min/max bars; caption and label>

## 3. Expected behaviour (model)

<fill: predict E(256) for each variant from bytes per GPU (2(n−1)/n × 4.375 GB for DP), bandwidth per
rail and the DP overlap window (exposed = max(0, T_DP − ≈ 70 ms) with PP, docs/VERIFIED_FACTS.md); compare with the observed table; explain the residual (slowest-node
effect grows with node count: E[max of k normal deviations] rises with k).>

## 4. Variant comparisons

| Comparison | GPUs | Speedup | 95 % CI | p raw (exact permutation) | p Holm (8 tests) | Significant? | Interpretation |
|---|---|---|---|---|---|---|
| baseline → ib_gdr | 64 | <fill> | | | | | |
| ib_gdr → ib_gdr_bucket | 64 | <fill> | | | | | |
| <fill> | | | | | | |

What the number of runs can and cannot resolve: <fill: smallest achievable p; detectable effect size given
run-to-run spread>.

## 5. Sensitivity to exclusions

<fill: rerun the tables including each excluded run; does any conclusion change?>
