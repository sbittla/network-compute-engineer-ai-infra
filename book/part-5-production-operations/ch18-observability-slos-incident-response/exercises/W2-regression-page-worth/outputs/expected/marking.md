# Marking scheme: W2 Is a 9 % regression worth a page?

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** Arithmetic for (a)–(b); a justified threshold for (c) with a noise argument.

| Criterion | Points |
|---|---|
| (a) ratio 0.916, lost fraction 0.084 | 2 |
| (b) Case A 2,242 GPU-h ≈ $6,726; Case B 241 GPU-h ≈ $724 | 4 |
| (c) 1.092 < 1.10 so the rule does not fire; proposes a threshold in 1.03–1.07 | 1 |
| (c) Noise argument: 10-min median sd ≈ 1.25 × 1.2 % / √34 ≈ 0.26 %, so 5 % ≈ 19 sd | 2 |
| (c) Evidence plan: ≥ 2 weeks of rolling-median ratios incl. checkpoint/eval boundaries, baseline reset on config change | 1 |
