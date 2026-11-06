# Marking scheme: 11.15 8k sequences next quarter

Type design-challenge · kind computed · tier L1 · 10 points

**Evidence required:** the config, memory and step-time output from the tool, and a trade-off table.

| Criterion | Points |
|---|---|
| Config edited correctly (seq_len 8,192, global batch 512 sequences) and a layout proposed | 2 |
| Memory shown under 68 GB from the tool for the chosen layout | 2 |
| Step time and MFU from the tool for at least the chosen layout and one alternative | 2 |
| Trade-off table on memory, communication and risk, defending the choice | 3 |
| Notes that attention FLOPs grow with s and are not in 6ND (bonus-level insight) | 1 |
