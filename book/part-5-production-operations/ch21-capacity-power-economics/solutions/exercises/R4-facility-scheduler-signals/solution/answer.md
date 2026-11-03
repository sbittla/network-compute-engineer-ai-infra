# R4 — Facility to scheduler signals: model answer

Source: manuscript Section 21.8 ("Coordinating workloads with the facility", Table 21.8) and
Figure 21.2 (telemetry at UPS, busway, PDU and node levels).

**Where the signals come from**

| Signal (Section 21.8) | Source system | Typical owner today |
|---|---|---|
| Per-rack / per-row power budget and per-phase current | Rack PDUs and busway meters via the EPMS (electrical power monitoring system) | Facilities / data-center operations |
| Cooling capacity, CDU supply/return temperature, pump redundancy | BMS (building management system), CDU controllers, leak sensors | Facilities (MEP) |
| Maintenance windows (UPS-B, CDU pump service) | Facility change calendar / CMMS work orders | Facilities |
| Demand-response events, utility limits | Utility contract, energy management | Facilities / finance |
| Node power, cap state, clock-event reasons | BMC (Redfish), DCGM | Platform |

In a colocation site the BMS/EPMS belongs to the provider, so the data arrives through a customer
portal or API. That is a contract item.

**The integration.** A **power-budget service** reads EPMS, BMS and calendar data, computes the
remaining budget per rack and row (one side under 2N, minus the transient margin), and publishes it
as a schedulable resource: Slurm licences or GRES per rack, or a Kubernetes extended resource or
admission webhook. The scheduler places jobs against it and triggers Table 21.8's actions (stop
placement at 80 %, uniform job caps at 90 %). In the other direction the scheduler publishes planned
large-job starts and stops (> 500 kW) to Facilities.

**Ownership.** Joint, with a written interface: Facilities owns the *signals* (accuracy, latency,
alarm thresholds), Platform owns the *service and the automated actions*, and Training Infra owns job
ramps. Changes to thresholds go through the Chapter 20 change process with the facility owner as
approver.

**Common weakness:** "the scheduler reads the PDUs directly". That skips the 2N and margin logic and
the facility's ownership of safety-relevant limits.
