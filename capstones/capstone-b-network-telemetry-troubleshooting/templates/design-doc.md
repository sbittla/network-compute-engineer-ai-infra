# ORION Fabric Telemetry and Troubleshooting System — Design Document

**Author:** <fill> · **Date:** <fill> · **Tier(s):** <fill: L1 / L2 / L3>

> Master document for Capstone B. Every section is required. Link the other templates rather than
> pasting them. Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]`, `[ILLUSTRATIVE]` or
> `[VENDOR-SPEC, YYYY-MM]`.

## 1. Problem statement

- **Who is paged today, and for what?** <fill: e.g., training-job stalls are discovered by ML engineers
  first; fabric alerts are noisy and ignored>
- **What the system must do:** <fill: detect, localize to a root-cause device, suppress planned work,
  carry evidence>
- **Success criteria (testable):** <fill: e.g., recall 1.0 on the injected set, precision ≥ 0.9,
  detection latency ≤ 3 polling intervals, zero pages during change windows>
- **Out of scope:** <fill>

## 2. Architecture

<fill: Mermaid diagram from counter sources (switch CLI poller, gNMI stream, host agent) through
collection, normalization, time-series storage, rule evaluation, alert routing, and the report or
dashboard. Mark trust boundaries. Caption: *Figure B.1 — …*>

| Component | Choice | Why | Failure mode and what happens to alerting |
|---|---|---|---|
| Switch collection | <fill> | <fill> | <fill> |
| Host collection | <fill> | <fill> | <fill> |
| Normalization | <fill: the canonical schema, see telemetry-schema.md> | | |
| Storage | <fill> | | |
| Rule engine | <fill> | | |
| Alert routing | <fill> | | |

## 3. Assumptions

See [assumptions-register.csv](assumptions-register.csv). Name the three assumptions your thresholds
depend on most.

## 4. Implementation and simulation boundary

| Claim | Evidence class | What would make it `[MEASURED]` |
|---|---|---|
| <fill> | `[SIMULATED]` | <fill> |

State what the generator does not model and how each gap could change precision or recall.

## 5. Telemetry schema, parser and rules

- Schema: [telemetry-schema.md](telemetry-schema.md)
- Rules: [alert-rules.md](alert-rules.md)
- Injected-fault scenarios: [injected-fault-scenarios.md](injected-fault-scenarios.md)

## 6. Test plan

See [test-plan.md](test-plan.md).

## 7. Results

See [results-table.csv](results-table.csv) and [false-positive-analysis.md](false-positive-analysis.md).

## 8. Failure analysis (of the monitoring system itself)

| Failure | Effect on detection | Detection of the failure (meta-monitoring) | Mitigation |
|---|---|---|---|
| Collector stops for one leaf | <fill> | <fill: staleness alert> | <fill> |
| Clock skew between sources | <fill> | <fill> | <fill> |
| Counter semantics change after a firmware upgrade | <fill> | <fill> | <fill> |
| <fill: ≥ 2 more> | | | |

## 9. Security considerations

<fill: read-only credentials for collectors; gNMI over TLS with per-device certificates; no shared
switch admin accounts; least privilege for host agents (reading sysfs counters needs no root on most
systems — verify on yours); integrity of the change calendar (who can suppress alerts?); retention and
access to telemetry, which reveals tenant traffic patterns.>

## 10. Operations

Runbook: [runbook.md](runbook.md). Incident report: [incident-report.md](incident-report.md). Report or
dashboard: [dashboard-report-spec.md](dashboard-report-spec.md).

## 11. Final engineering review

See [final-engineering-review.md](final-engineering-review.md).
