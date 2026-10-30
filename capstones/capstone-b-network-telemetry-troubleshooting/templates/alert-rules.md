# Alert Rules Specification

One block per rule. Every threshold needs a justification from data (a baseline percentile, a physical
limit, or a peer comparison), not "it passed the checker".

## Rule: <fill: pfc_storm>

| Field | Value |
|---|---|
| Fault class | <fill> |
| Signal(s) | <fill: canonical counters and scope, e.g., pfc_rx_pause_p3 on leaf host-facing ports> |
| Condition per interval | <fill: e.g., rate > 10,000 frames/s> |
| Persistence | <fill: N consecutive valid intervals> |
| Root-cause attribution | <fill: the device that *sends* the pause, found through topology.csv> |
| Suppression | <fill: change windows of the device and of its link peer> |
| Severity and routing | <fill: SEV and team> |
| Expected detection latency | <fill: persistence × poll interval after onset> |
| Threshold justification | <fill: baseline p99.9 of the signal across healthy ports; benign burst peak; margin> |
| Known false-positive sources | <fill> |
| Known false-negative risks | <fill> |
| Runbook link | [runbook.md](runbook.md)#<fill> |

## Rule: <fill: link_degradation>

<fill: same table>

> **Note (docs/VERIFIED_FACTS.md):** 400G PAM4 links with RS(544,514) carry ≈ 78 M codewords/s per port, and a
> healthy link at pre-FEC BER ≈ 1e-6 can correct hundreds of thousands per second. Do **not** page on an
> absolute corrected-codeword rate. Page on FCS and uncorrectable counts; alert on pre-FEC BER (and its trend)
> and on high symbol-error histogram bins approaching the correction limit where the platform exports them;
> treat corrected-codeword growth against the port's own baseline as an early warning.

## Rule: <fill: ecn_misconfig>

<fill: same table; explain the peer comparison (why compare one rail leaf with the median of the
others at the same minute, and when that comparison breaks)>

## Rule: <fill: ecmp_imbalance>

<fill>

## Rule: <fill: link_down>

<fill>

## Meta-rules

| Rule | Condition | Why |
|---|---|---|
| Stale source | <fill: no sample from a device for > 3 poll intervals> | Silence is not health |
| Reset storm | <fill: > N resets on a device in 10 minutes> | Flapping device or misbehaving collector |
