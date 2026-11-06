# K8 — Reachability vs performance: worked solution

**Relies on:** Section 19.9 (Table 19.8 "Backend RoCE fabric" row and the paragraph after Figure 19.5);
Chapter 9 (PFC, ECN, head-of-line blocking).

## Mechanism

Different VRFs and VNIs give tenants A and B separate routing tables and overlay segments. A cannot
address B's endpoints and vice versa: that is **reachability** isolation. It is not **resource**
isolation. On ORION's shared RoCE fabric, both tenants' packets still cross the same spine links, the
same switch egress queues, and the same shared buffer pool, usually in the same lossless traffic class
(TC 3).

When B runs incast-heavy or very large collectives:

1. B's flows fill the shared egress queues on spines and leaves that A's flows also use.
2. ECN marks those queues. DCQCN on A's senders sees marks too, because the marks are applied per queue
   and not per tenant, so A slows down even though A did not cause the congestion.
3. If the buffers reach the PFC threshold, the switch pauses the whole priority on the upstream port.
   That pause stops A's packets queued behind B's (head-of-line blocking). Pauses can propagate hop by
   hop toward A's senders (congestion spreading).

So B's job raises A's collective latency and lowers A's bus bandwidth, with no reachability breach and
no errors. The only symptoms are higher step time, more CNPs, and more PFC pause counts on shared ports.

## Two mitigations (any two)

- **Placement:** put large tenants on separate leaf groups or spine planes (or dedicated nodes and
  leaves), so they share no links. This is the strongest option.
- **QoS separation:** separate traffic classes per tenant group, each with its own buffer allocation and
  PFC/ECN thresholds, so B's queue cannot pause A's.
- **Tenant-aware rate limits or admission:** cap a tenant's aggregate injection rate.
- **Congestion-control tuning:** working DCQCN with ECN thresholds set below PFC thresholds, so rate
  control acts before pauses spread.

## Common wrong answers

- "Different VNIs mean no interaction": this confuses reachability with performance.
- Proposing ACLs or firewalls: they block traffic and do nothing for shared-queue contention.
- Naming only "more bandwidth" without addressing shared queues and pauses.
