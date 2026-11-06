# 11.11 (O2) — Step-time sensitivity

Model: step = compute + bubble + exposed TP + exposed DP + exposed PP (Section 11.10); ideal step
6.958 s, so MFU = 6.958 s / step. Baseline: 13.916 + 0.326 + 3.083 + 0.098 + 0.028 = 17.45 s,
MFU 39.9 %. All values `[MODELED]`.

| Case | Arithmetic | Step (s) | MFU |
|---|---|---|---|
| Baseline | 13.916 + 0.326 + 3.083 + 0.098 + 0.028 | 17.45 | 39.9 % |
| (a) efficiency 0.50 → 0.55 | compute 13.916 × 0.50/0.55 = 12.651; bubble 12.651 × 3/128 = 0.297; DP window 12.651/128 × 0.667 = 0.066 → exposed DP 0.170 − 0.066 = 0.104; + 3.083 + 0.028 | **16.16** | **43.1 %** |
| (b) TP overlap 25 % → 60 % | exposed TP 4.111 × 0.40 = 1.644; 13.916 + 0.326 + 1.644 + 0.098 + 0.028 | **16.01** | **43.5 %** |
| (c) one rank 8 % slower | every rank waits at each synchronization: + 0.08 × (13.916 + 0.326) = + 1.139 | **18.59** | **37.4 %** |
| (d) DP time × 3 | DP 0.170 × 3 = 0.511; exposed 0.511 − 0.072 = 0.438 (+ 0.341) | **17.79** | **39.1 %** |
| (e) (b) and (c) | 16.012 + 1.139 | **17.15** | **40.6 %** |

**Ranking of levers** (size of effect on the step):

1. **TP overlap (−1.44 s).** Exposed TP is the largest non-compute term; overlapping it is the
   cheapest big win (Section 11.4).
2. **Kernel efficiency (−1.29 s).** It scales the dominant compute term, but 10 % better kernels are
   hard to buy; note it slightly *increases* exposed DP because the overlap window shrinks.
3. **Eliminating stragglers (+1.14 s avoided).** A *single* slow rank of 256 costs every GPU 8 % of
   its compute, because synchronous training runs at the speed of the slowest rank.
4. **Fabric congestion on DP (+0.34 s).** Smallest here, but larger than the < 1 % DP share suggests:
   the overlap window is fixed at ≈ 72 ms (the last micro-batch's backward), so every extra
   millisecond of DP time beyond it lands on the critical path.

(e) shows the levers combine roughly additively: the TP gain (−1.44 s) and the straggler loss
(+1.14 s) nearly cancel.

**Common wrong answers.** Scaling only compute in (a) and leaving the bubble unchanged; in (c)
adding 8 % of one rank's time divided by 256; tripling *exposed* DP (0.29 s) instead of DP time.
