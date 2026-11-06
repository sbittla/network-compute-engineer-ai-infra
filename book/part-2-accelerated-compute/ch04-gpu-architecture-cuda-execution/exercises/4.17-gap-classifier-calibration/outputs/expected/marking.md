# Marking scheme: 4.17 Calibrating the gap classifier

Type reflection · kind written · tier L1 · 3 points

**Evidence required:** short written answers (≤ 150 words each) that cite specific numbers or mechanisms.

| Criterion | Points |
|---|---|
| 10 µs launch-latency allowance: how it misclassifies dependency vs launch-bound gaps on hosts with faster or slower launch paths | 1 |
| 2 µs gap threshold: drops real launch gaps or counts normal inter-kernel spacing | 1 |
| Calibration: histogram inter-kernel gaps in a GPU-bound region and measure submit-to-start latency on an idle stream | 1 |
