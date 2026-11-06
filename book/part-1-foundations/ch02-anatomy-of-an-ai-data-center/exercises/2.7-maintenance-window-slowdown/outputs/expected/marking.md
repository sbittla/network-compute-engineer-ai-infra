# Marking scheme: 2.7 The maintenance-window slowdown

Type troubleshooting · kind computed · tier L1 · 20 points

**Evidence required:** Slowdown arithmetic; ranked hypothesis table; evidence plan with commands; root-cause arithmetic; fix and validation plan; one acceptance-checklist line.

| Criterion | Points |
|---|---|
| Slowdown 29.9 % computed, clock ratio 0.574, and the synchronous-job explanation of why it is smaller than the clock loss | 3 |
| At least three hypotheses ranked with reasons (PSU cording first, failed PSUs, BMC power policy, PDU fault), thermal rejected | 5 |
| Evidence plan with real read-only commands or data sources (ipmitool sdr, Redfish PowerSupplies, PDU outlet map, dcmi power limit) | 5 |
| Root-cause arithmetic (2 x 3.0 = 6.0 kW against about 7.99 kW DC sustained; braked rack at most about 25.5 kW, consistent with 24.1 kW) | 4 |
| Safe fix (drain, re-cord 3A/3B under change control), validation without a maintenance window, and the acceptance-checklist line | 3 |
