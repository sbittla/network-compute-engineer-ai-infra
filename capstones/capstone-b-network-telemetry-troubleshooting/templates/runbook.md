# Fabric Alert Runbook — ORION Backend

> **Safety:** Every action below is for the ORION production fabric and must follow change control.
> Read-only diagnostics first. Disruptive actions (disabling a port, resetting a NIC, draining a node)
> need the approvals listed.

## Alert: <fill: pfc_storm>

**What it means:** <fill>

**Impact:** <fill: which jobs, how to find them (rank-to-node map, Slurm job on the node)>

**First five minutes (read-only):**

1. <fill: confirm with the leaf port counters and the host NIC counters (e.g., `ethtool -S <netdev> | grep prio3_pause`)>
2. <fill: check whether the host is alive and draining its receive queue (e.g., host load, kernel log, GPU Xid events)>
3. <fill>

**Decision table:**

| Evidence | Likely cause | Safe action | Approval | Owner |
|---|---|---|---|---|
| <fill> | <fill> | <fill: e.g., drain node from scheduler; enable the switch's PFC watchdog per the vendor's documented feature> | <fill> | <fill> |

**Escalation:** <fill>

**Validation that it is fixed:** <fill: which counters return to baseline, for how long>

## Alert: <fill: link_degradation>

<fill: same structure; include optics DDM (`ethtool -m <netdev>` on hosts, vendor transceiver
commands on switches), cleaning/reseat/replace ladder, and when to drain>

## Alert: <fill: ecn_misconfig>

<fill: same structure; config diff against golden QoS template; who may push QoS changes>

## Alert: <fill: ecmp_imbalance>

<fill>

## Alert: <fill: link_down>

<fill>
