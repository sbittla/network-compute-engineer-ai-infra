# Marking scheme: 8.9 The price of a lost packet

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** every step as formula → values → result; bandwidth-delay product computed; assumptions stated; labelled `[MODELED]`.

| Criterion | Points |
|---|---|
| (a) 256 packets; 21.4 µs at 392 Gb/s | 2 |
| (b) BDP 245,000 B ≈ 60 packets; extra ≈ 5.0 µs ≈ one RTT (23 %) | 2 |
| (c) T_ack = 4.096 µs × 2¹⁸ = 1.074 s extra | 2 |
| (d) 10⁻⁵ × 1.074 s = 10.7 µs per isolated message → ≈ 67 % goodput; back-to-back amortized per burst | 2 |
| (e) (retry_cnt + 1) × T_ack = 8 × 1.074 = 8.59 s | 2 |
