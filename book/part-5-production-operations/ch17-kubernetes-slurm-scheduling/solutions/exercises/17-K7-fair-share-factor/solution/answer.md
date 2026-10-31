# 17-K7 — Classic fair-share factor

Classic Slurm multifactor fair share: `F = 2^(−U/S)`, U = decayed normalized usage, S = normalized
shares (Section 17.5.4). `[MODELED]`

| Usage | U/S | F |
|---|---|---|
| equal to share | 1 | 2^(−1) = **0.500** |
| half the share | 0.5 | 2^(−0.5) = 1/√2 = **0.707** |
| twice the share | 2 | 2^(−2) = **0.250** |

Interpretation: F ∈ (0, 1]; an account that used nothing gets 1.0, one at exactly its share 0.5.
The factor halves for every additional share's worth of usage, so heavy users are pushed down
smoothly rather than cut off. It is then multiplied by `PriorityWeightFairshare` (10,000 on ORION),
so the gap between 0.707 and 0.25 is ≈ 4,570 priority points, less than the QOS weight (20,000)
and more than the age weight (1,000).

Note that current Slurm defaults to the Fair Tree algorithm; the intuition is the same.
Common mistake: computing 2^(−S/U). `solve.py` asserts the three values.
