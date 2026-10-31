# 8.9 — result `[MODELED]`

- (a) 1,048,576 / 4,096 = **256 packets**; 1,048,576 B / 49,000 B/µs = **21.4 µs**
- (b) BDP = 49,000 B/µs × 5.0 µs = 245,000 B ≈ **60 packets**; extra ≈ 60 × 4,096 B / 49,000 B/µs = **5.0 µs** (23 % of (a))
- (c) T_ack = 4.096 µs × 2^18 = **1.074 s** extra
- (d) 10⁻⁵ × 1.074 s = **10.7 µs** per isolated message (+ 0.013 µs mid-message) → goodput **67 %**; back-to-back bursts of k messages: {1: 0.666, 4: 0.888, 16: 0.969, 64: 0.992}
- (e) (7 + 1) × 1.074 s = **8.59 s**
