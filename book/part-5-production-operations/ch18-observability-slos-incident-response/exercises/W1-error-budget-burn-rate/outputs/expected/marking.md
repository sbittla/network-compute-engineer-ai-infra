# Marking scheme: W1 Error budget and burn rate for chat-70b

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** Every formula, substitution, and result; a yes/no with the window values for each alert condition.

| Criterion | Points |
|---|---|
| (a) 129,600 failed requests ≡ 43.2 min of total outage | 2 |
| (b) burn 6, 1.25 % budget; no condition fires (1 h = 6; 30 m = 6 not > 6; 6 h = 1.5; 3 d = 0.125) | 4 |
| (c) burn 20; 1 h/5 m page true from 43.2 min, fires ≈ 45 min with for: 2m; 6 h pair needs 108 min; 4.17 % consumed | 3 |
| (d) 30 d / 6 = 5 days (120 h) | 1 |
