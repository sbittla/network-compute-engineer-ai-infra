# 12.10 (O1) — Collectives by hand

Inputs: R0 = [2, 4, 6], R1 = [1, 3, 5], R2 = [10, 20, 30]; 4-byte elements, S = 12 B per rank.
Method Section 12.2 (Table 12.2) and Figure 12.1. Results `[MODELED]`.

**Six results**

- **All-reduce (sum):** every rank **[13, 27, 41]**
- **Reduce (sum, root R0):** R0 **[13, 27, 41]**; R1 and R2 unchanged
- **Reduce-scatter (sum, rank r keeps element r):** R0 **[13]**, R1 **[27]**, R2 **[41]**
- **All-gather (of each rank's first element):** every rank **[2, 1, 10]**
- **Broadcast (root R1):** every rank **[1, 3, 5]**
- **All-to-all** (rank i sends element j to rank j): R0 **[2, 1, 10]**, R1 **[4, 3, 20]**, R2 **[6, 5, 30]**

**Ring all-reduce trace** (ring R0 → R1 → R2 → R0; in reduce-scatter step k rank r sends chunk
(r − k + 1) mod 3 to rank r + 1, which adds it; in all-gather the completed chunks are forwarded and
overwrite):

| Step | R0 → R1 | R1 → R2 | R2 → R0 | Buffers after the step |
|---|---|---|---|---|
| RS 1 | c0 = 2 | c1 = 3 | c2 = 30 | R0 [2, 4, 36] · R1 [3, 3, 5] · R2 [10, 23, 30] |
| RS 2 | c2 = 36 | c0 = 3 | c1 = 23 | R0 [2, 27, 36] · R1 [3, 3, 41] · R2 [13, 23, 30] |
| AG 1 | c1 = 27 | c2 = 41 | c0 = 13 | R0 [13, 27, 36] · R1 [3, 27, 41] · R2 [13, 23, 41] |
| AG 2 | c0 = 13 | c1 = 27 | c2 = 41 | all [13, 27, 41] |

After RS 2 each rank owns one fully reduced chunk (R0 c1 = 27, R1 c2 = 41, R2 c0 = 13); all-gather
circulates them.

**Bytes per rank.** 4 steps × one 4-byte element = **16 B**; formula 2(n − 1)/n × S = 4/3 × 12 B =
**16 B** ✓. This is the all-reduce busbw factor of 12.3 in miniature.

**Common mistakes.** All-gather of first elements giving [2, 2, 2]; all-to-all transposed the wrong
way; counting 2(n − 1) × S bytes (sending whole buffers each step).
