# Marking scheme: 3.5 Corrected versus uncorrected

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** A table with five rows, event, consequence, rule type, suggested first action.

| Criterion | Points |
|---|---|
| AER corrected, link-level retry, rate-based rule per BDF, correlate with LnkSta | 1 |
| AER uncorrected non-fatal, transaction failed, presence rule, drain at next checkpoint | 1 |
| AER uncorrected fatal, link unreliable, presence rule, drain immediately and RMA path | 1 |
| EDAC CE, corrected DRAM error predicting a UE, rate per DIMM, trend and plan replacement | 1 |
| EDAC UE, data loss or crash, presence rule, drain and replace the DIMM | 1 |
