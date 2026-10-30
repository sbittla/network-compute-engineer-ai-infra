# Telemetry and Alert Rules

> Template for Capstone F artifact 3.

## 1. Signal inventory

| Signal (simulator series) | Real-world source | Cause or symptom? | Failure modes of the signal itself |
|---|---|---|---|
| `sim_node_up` | `<fill>` | cause | `<fill: e.g. exporter down is not the same as node down>` |
| `<fill>` | | | |

## 2. Rules

| Name | Expression (`metric op threshold`) | `for` | Severity | Detects | Rationale for threshold and `for` (with numbers) |
|---|---|---|---|---|---|
| `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` |

PromQL equivalents for a real deployment (verify against your exporters):

```text
<fill: e.g. absent(up{job="slurm-exporter"} == 1) held for 1m>
```

## 3. False-positive analysis

`<fill: what fired on a fault-free run with the default rules, why (mechanism), and how your rules avoid it without losing detection>`

## 4. Detection results (canonical scenarios)

| Fault kind | Target (s) | Detected after (s) `[SIMULATED]` | Rule |
|---|---|---|---|
| node_loss | 120 | `<fill>` | `<fill>` |
| link_down | 120 | `<fill>` | `<fill>` |
| scheduler_outage | 120 | `<fill>` | `<fill>` |
| storage_slow | 300 | `<fill>` | `<fill>` |

## 5. Routing and paging

`<fill: which severities page whom; what is a ticket; how alerts for the same incident are grouped>`
