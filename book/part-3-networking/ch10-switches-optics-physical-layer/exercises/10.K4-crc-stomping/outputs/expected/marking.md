# Marking scheme: 10.K4 CRC stomping

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** ≤ 150 words plus the name of the localizing counter.

| Criterion | Points |
|---|---|
| Mechanism: a cut-through switch forwards before it has the FCS, so it replaces the FCS with a known-bad value | 2 |
| Why the healthy downstream link reports FCS errors without uncorrectables or post-FEC symbol errors | 1 |
| Localizing counter: FEC-uncorrectable (with elevated pre-FEC symbol errors) on the ingress port of the upstream switch; stomped-CRC counter if exposed | 2 |
