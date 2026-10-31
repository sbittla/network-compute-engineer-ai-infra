# 2.7 — The maintenance-window slowdown: model answer

Method: manuscript Section 2.2 (PSU feed-loss rule), Section 2.6 (power brake and clock-event reasons) and
the diagnostic loop of Section 2.12. Evidence is `[ILLUSTRATIVE]`; arithmetic `[MODELED]`, reproduced by
`solve.py`.

## 1. Slowdown and why 8 nodes slow the job

Step time 22.6 / 17.4 = 1.299, a **+29.9 %** slowdown. On rack-02 and rack-03 the SM clock fell to
1,050 / 1,755 = 0.598 of the peers' clock (−40 %). The job is synchronous, so all 256 GPUs wait every
step for the 64 braking GPUs (8 of 32 nodes). The slowdown is smaller than the clock loss because only
part of the step scales with SM clock: solving 17.4 × [f / 0.598 + (1 − f)] = 22.6 gives f ≈ 0.45, so
roughly 45 % of the step behaves as clock-bound compute. Communication, memory-bound phases and waits do
not scale with clock `[MODELED, single-factor model]`.

## 2. Ranked hypotheses (why only rack-02/03 braked on feed A)

| Rank | Hypothesis | For | Against |
|---|---|---|---|
| H1 (high) | PSU **cording** differs on those nodes, so feed A alone cannot supply them | `HW Power Brake Slowdown` is the platform reacting to insufficient PSU capacity; feed-A load ≈ 24 kW against ≈ 34 kW on peer racks | None yet |
| H2 (medium) | Failed or missing PSUs on those nodes, fewer than three left on feed A | Same brake signature | Two whole racks failing alike is unlikely |
| H3 (medium) | Different BMC/firmware power policy on a delivery batch (a configured feed-loss limit) | Racks 02–03 may share a delivery batch | A policy cap usually shows `SW Power Cap`, not a hardware brake |
| H4 (low) | Rack-PDU fault on feed A limiting current | Rack-specific | No breaker events; other racks fine on the same feed |

Reject thermal: no thermal reasons are active, and power fell rather than rose.

## 3. Evidence plan (read-only)

- PSU presence, health and per-PSU input power on one node per rack:
  `ipmitool -I lanplus -H <bmc> -U <user> -E sdr type "Power Supply"` and Redfish
  `/redfish/v1/Chassis/<id>/PowerSubsystem/PowerSupplies` (the deprecated `/Power` resource on older BMCs).
  H2 is confirmed if PSUs are absent or failed.
- PDU outlet maps and per-outlet power for rack PDUs A and B: which node PSU is on which feed. H1 is
  confirmed if rack-02/03 nodes show 2 outlets on A and 4 on B.
- BMC power-limit settings with `ipmitool dcmi power get_limit`, and firmware via Redfish
  `UpdateService/FirmwareInventory`: H3.
- PDU event log and per-phase current on rack-02/03 feed A: H4.

## 4. Root cause, fix and validation

With 2 PSUs on feed A the node has 2 × 3.0 = **6.0 kW of DC** against a sustained DC need of about
8.5 kW × 0.94 = **7.99 kW**, so the platform asserts the power brake. Peer nodes have 3 × 3.0 = 9.0 kW ≥
7.99 kW, so they do not brake at sustained load (they would still brake at the 9.59 kW DC peak).
Consistency check: braked nodes are held at ≤ 6.0 kW DC = 6.0 / 0.94 = **6.38 kW AC**, so a rack draws
≤ 4 × 6.38 = **25.5 kW**, consistent with the 24.1 kW measured on feed A (the brake undershoots the
limit). Compare DC with DC and AC with AC: PSU ratings are DC output.

**Fix:** drain the 8 nodes at the next checkpoint
(`scontrol update NodeName=orion-n[05-12] State=DRAIN Reason="PSU cording 2A/4B"`). Fleet re-cords them
to 3 A / 3 B under the rack's change procedure, then returns them to service.

**Validate without a maintenance window:** per-outlet PDU readings show each node's load split ≈ 50/50
across A and B (45–55 %); `sdr type "Power Supply"` shows six healthy PSUs; the inventory's outlet map
matches the standard. A true single-feed test belongs in a Facilities-run commissioning window. Never
toggle breakers to test.

## 5. Acceptance-checklist line (Chapter 16)

"PSU cording verified 3 A / 3 B against the PDU outlet map; per-feed load share 45–55 % at idle and under
burn-in; recorded in inventory."

**Common wrong answers:** blaming the UPS maintenance itself (other racks on the same feed were fine);
proposing to toggle breakers to test; comparing 6.0 kW of DC with AC power.
