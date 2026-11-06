# K6 — Incident commander and communications lead

**Why the IC should not debug hands-on (Table 18.7):**
1. The IC owns the *global view*: severity, roles, priorities, stakeholder needs, the decision log.
   Hands-on debugging produces tunnel vision; nobody is left watching whether the incident is
   widening, whether a team is missing, or whether it is time to mitigate instead of investigate.
2. Decisions such as "roll back CHG-4471 now" or "exclude the node and restart from checkpoint" need
   someone not invested in their own hypothesis. The operations lead runs the investigation and every
   change; the IC decides.

**Communications lead for a SEV2 on ORION (Table 18.8):** publishes status updates every **60
minutes** (SEV1: 30 min) to users and leadership, containing impact, scope, current status, and the
next update time, never speculative cause.

**Example update:**
> 03:20 UTC — INC-2291 (SEV2). Both training jobs (trn-70b, ft-13b) have been ≈ 15–20 % slower since
> ≈ 02:10. Inference is unaffected. Fabric and Training Infra are investigating a recent network
> change; no data loss. Next update 04:20 UTC or sooner if status changes.

**Common mistakes:** IC as the most senior debugger; updates that guess at a root cause ("a bad
switch") and later have to be retracted. Source: Section 18.10.
