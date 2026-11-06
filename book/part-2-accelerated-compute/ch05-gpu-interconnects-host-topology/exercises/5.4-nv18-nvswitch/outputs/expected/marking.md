# Marking scheme: 5.4 Why every GPU pair shows NV18

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** NVLink/NVSwitch arithmetic and the "nothing" answer.

| Criterion | Points |
|---|---|
| 18 NVLink4 links × 25 GB/s = 450 GB/s per direction per GPU | 1 |
| Links spread across the NVSwitch chips, so every GPU pair is one switch hop at full bandwidth, hence NV18 in every cell | 1 |
| States that NV18 says nothing about GPU-NIC locality, which is purely a PCIe question | 1 |
