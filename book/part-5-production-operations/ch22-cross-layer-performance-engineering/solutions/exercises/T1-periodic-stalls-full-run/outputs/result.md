# T1 — scores and timeout arithmetic `[ILLUSTRATIVE]`

| Rank | Test | Score |
|---|---|---|
| 1 | correlate long steps with local_ack_timeout_err and FEC uncorrectable (existing telemetry) | 1.600 |
| 2 | module DOM diagnostics on both ends (ethtool -m, switch transceiver) | 1.200 |
| 3 | ib_write_bw on drained orion-n15 and a peer, rail 3 | 0.117 |

ACK timeout per retry: 4.29 s (NCCL 2.23+, value 20), 1.07 s (≤ 2.22, value 18).
One or two timeouts on the critical path: 4.3–8.6 s, bracketing the observed 6–9 s stalls.
FEC corrected codewords on Ethernet28 are 475–1,900× the other ports.
