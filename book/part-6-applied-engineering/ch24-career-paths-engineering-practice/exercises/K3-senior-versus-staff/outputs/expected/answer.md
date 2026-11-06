# K3 — Senior versus staff: model answer

Source: Table 24.6 (Section 24.3) and the rail-3 bus-bandwidth example that follows it.

**Senior.** The senior engineer runs the third incident as incident commander, localizes it with a
discriminating test (per-port FEC/CRC counters and optic Rx power on the affected rail, Section 24.12),
drains the link through the change process and confirms bandwidth recovers over repeated runs. The
postmortem names the detection gap: "we alert on link down, not on degraded links". *Packet outcomes:*
(1) the incident resolved within its SLO, with the before/after `all_reduce_perf` bus bandwidth recorded;
(2) an alert on FEC-uncorrectable rate shipped for that fabric and shown firing in a test; (3) the
postmortem's action items closed by their due dates.

**Staff.** The staff engineer notices that this is the *third* optics-related degradation in a quarter and
treats it as a class of incident, not an instance. They write the proposal for pre-failure optics
telemetry (Rx power and FEC-corrected-rate trends) and a drain-on-threshold policy, and get Fabric and
Fleet teams to adopt it on both fabrics. *Packet outcomes:* (1) the policy adopted by two teams and running
on both fabrics; (2) optics degradations detected before job impact, measured as fewer job-impacting
optics incidents next quarter (for example 3 → 0 or 1); (3) a standard that other engineers now design to.

**The difference** is scope and influence: senior owns a system and removes the cause of an incident;
staff removes a class of incidents through other people. Staff packets list outcomes others achieved.

**Common mistakes.** Describing staff as "a faster senior"; outcomes phrased as activities ("worked on
optics monitoring") rather than verifiable results.
