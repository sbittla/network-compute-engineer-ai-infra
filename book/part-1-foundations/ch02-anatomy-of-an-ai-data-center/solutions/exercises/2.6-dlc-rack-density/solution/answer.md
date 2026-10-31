# 2.6 — What liquid cooling does to node power and rack density

Method: manuscript Section 2.2 (Table 2.2 power breakdown, PSU feed-loss rule), Section 2.7 (coolant and
air arithmetic) and Section 2.10 (ORION's facility envelope: 2 × 60 A per side, 300 kW CDU, PG25 at
ΔT 10 K, 1,200 kg/m², 0.72 m² footprint). Results `[MODELED]` from `[ILLUSTRATIVE]` assumptions;
`solve.py` reads the envelope from `lab/data/facility_envelope.yaml`.

**1. DLC node AC maximum.** DC load = 9,590 − (1,350 − 350) = 8,590 W; AC = 8,590 / 0.94 = **9,138 W
≈ 9.14 kW**. A 4-node rack: 4 × 9.138 + 0.2 = **36.75 kW** against 41.0 kW, saving **4.25 kW (10.4 %)**.

**2. A fifth node.** 5 × 9.138 + 0.2 = 45.89 kW; × 1.10 = **50.48 kW per side** ≤ 65.55 kW ✓ (15.07 kW
headroom).

**3. Cooling a 5-node rack.**

```text
liquid  = 0.80 × 45.89          = 36.71 kW
ṁ       = 36.71 / (3.90 × 10)   = 0.9413 kg/s → / 1.02 kg/L × 60 = 55.4 L/min
air     = 45.89 − 36.71         = 9.18 kW → 9.18 / (1.006 × 1.20 × 15) = 0.507 m³/s = 1,074 CFM
CDU     = 8 racks × 36.71       = 293.7 kW = 97.9 % of 300 kW  ✗ (no margin, no redundancy)
```

**4. Floor.** (5 × 135 + 280) kg / 0.72 m² = 955 / 0.72 = **1,326 kg/m²** > 1,200 ✗.

**5. Feed loss.** Three PSUs on one feed give 3 × 3.0 = 9.0 kW of DC against an 8.59 kW DC peak ✓, a 4.8 %
margin. The fan savings remove the feed-loss problem of Section 2.2. One caution: Section 2.10 targets
≤ 95 % PSU loading (8.55 kW), and 8.59 kW sits 40 W above it. Strictly, a token feed-loss cap of about
695 W per GPU (40 W / 8 = 5 W below 700 W) or a check of PSU derating at worst-case inlet temperature is
still prudent. Compare DC with DC: PSU ratings are DC output.

**6. Verdict: stay at 4 nodes per rack.** The floor rating binds first (and the CDU right after). The
electrical capacity would allow 5.

| Check (5 nodes per rack) | Value | Limit | Verdict |
|---|---|---|---|
| Electrical per side | 50.48 kW | 65.55 kW | ✓ |
| Coolant per rack | 55.4 L/min | manifold design flow (ask vendor) | confirm |
| CDU | 293.7 kW (97.9 %) | 300 kW | ✗ |
| Floor | 1,326 kg/m² | 1,200 kg/m² | ✗ |
| Feed loss | 8.59 kW DC | 9.0 kW per feed | ✓ |

At 4 nodes the DLC variant's real benefits are lower power (−10.4 %), feed-loss ride-through and a CDU
load of 8 × 0.80 × 36.75 = **235.2 kW (78.4 %)**.

**Common wrong answers:** applying the 94 % efficiency to the 1,000 W saving twice; applying the capture
fraction to the DC load instead of the AC load; comparing PSU DC capacity with AC input.
