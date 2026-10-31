# O2 — Why not PFC everywhere? (model answer)

Relies on manuscript Section 9.4 (headroom, Table 9.2), Section 9.5 (HOL blocking, propagation, storms,
watchdog, deadlock), Section 9.6 ("How DCQCN and PFC should interact") and Section 9.8 (counters,
Table 9.4, Figure 9.10).

## Risks of enabling PFC indiscriminately (any four, each with its mechanism)

1. **Head-of-line (HOL) blocking.** PFC pauses a whole (port, priority), not a flow. Flows to
   *uncongested* destinations that share the paused port or NIC stall too and become victim flows with
   inflated p99 latency.
2. **Pause propagation / congestion trees.** A paused device's queues fill, so it crosses Xoff and pauses
   *its* upstream neighbours. One hot egress can stall senders several hops away, across spines.
3. **PFC storms.** A faulty NIC or a stuck host emits continuous pause, and every path through its
   leaf freezes. Without a **PFC watchdog** nothing breaks the loop (the lab's storm lasted ≈ 70 s).
4. **Deadlock.** Cyclic buffer dependencies (routing that is not up-down, transient loops, flooding of
   lossless traffic) leave buffers waiting on each other forever, even after the traffic stops.
5. **Buffer cost.** Every lossless priority reserves headroom per port: ≈ 6.5 MB per ORION rail leaf
   per priority `[MODELED]`. That buffer is taken out of the shared pool that absorbs bursts for every
   other class.
6. **Masking.** PFC hides missing or misconfigured ECN/DCQCN: the fabric "works" while running on
   pause, with poor tail latency, until a storm or deadlock exposes it.

## Procedure: investigating pause propagation and HOL blocking (on-call)

1. **Scope the event.** List every port with pause tx or rx rate > 100 frames/s in the window
   (`pfc_tx_p3`, `pfc_rx_p3` as rates). Flag any **switch↔switch** port (propagation) and any
   `discards_tc3` or watchdog event. *Rule:* discards or watchdog events → incident path (headroom or
   storm) first.
2. **Validate the counters.** Convert to rates on **both ends** of each link (switch `pfc_tx` on one end
   = NIC/switch `pfc_rx` on the other). Divide by the true elapsed time and treat resets as NaN. *Rule:*
   ends disagree → counter or telemetry fault; fix the data before concluding anything.
3. **Walk the tree.** For each port with a deep TC 3 **watermark**, check whether it *receives* pause.
   *Rule:* receives pause → branch, follow it to the peer downstream; does not receive pause and is at
   ≥ 90 % of line rate → **root**.
4. **Classify the root.** Read egress Gb/s, ECN-mark rate and pause rx from the peer. *Rule:* line-rate
   egress with heavy ECN → incast (find the fan-in workload); egress ≈ 0 with sustained pause rx →
   storm or slow receiver. Then inspect the peer NIC: `ethtool -S` pause and storm counters, host
   `lspci -vv` LnkSta, `dmesg`.
5. **Check DCQCN health on the root path.** ECN-marks/pause ratio, `np_cnp_sent` at the destination NIC,
   `rp_cnp_handled` at the senders, and the CNP class (DSCP 48 → TC 6) on every hop. *Rule:* pause rate
   comparable to the mark rate, or CNP counts lagging → DCQCN is not acting (Kmin too high, CNP
   misclassified, RP disabled).
6. **Find HOL victims.** For latency probes or flows with p99 ≥ 10× baseline, check their *destination*
   queue. *Rule:* destination uncongested (< 500 KB) → victim; identify which of its ingress ports or
   source NIC is being paused.
7. **Record, then act.** Snapshot counters with timestamps before any change. Choose the safe action
   from the runbook: drain a node, confirm the watchdog is active, open a change for profile fixes. Never
   disable PFC live on a production fabric.

## Marking notes

Two points per risk with a mechanism. Deduct procedure points for steps that name no counter or decision
rule.
