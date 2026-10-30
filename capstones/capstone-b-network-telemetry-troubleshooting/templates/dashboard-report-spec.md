# Fabric Health Report / Dashboard Specification

## 1. Audience and questions

| Audience | Question the view must answer in < 30 s |
|---|---|
| Fabric on-call | <fill: which rail or link is unhealthy right now, and is it a root cause or a symptom?> |
| Training Infra | <fill: is the fabric the reason my job is slow?> |
| Fabric lead (weekly) | <fill: error trends, top-N degrading links, alert precision> |

## 2. Panels

| Panel | Metric (canonical counter → derived) | Aggregation | Visual | Thresholds shown | Drill-down |
|---|---|---|---|---|---|
| Rail overview | <fill: from leaf_health_table> | per leaf, per interval | <fill: table or small multiples> | <fill> | <fill> |
| PFC by rail | pfc_rx_pause_p3 + pfc_tx_pause_p3 rate | <fill> | | | |
| ECN vs PFC by rail | <fill> | | | | |
| Link errors | fcs_errors, fec_corrected, fec_uncorrectable | top-N ports | | | |
| Uplink balance | uplink CV per leaf | | | | |
| Alert log | detect() output | | | | |

## 3. Rendered example

<fill: include at least one chart or table rendered from the capture (PNG from matplotlib, or a
Markdown table), labelled `[SIMULATED]`, with a caption.>

## 4. Data freshness and correctness indicators

<fill: last sample time per source; count of invalid (reset) intervals; collector health.>
