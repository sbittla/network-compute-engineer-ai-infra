# K4 — CNPs in the wrong class (worked solution)

Relies on manuscript Section 9.6 ("Three roles": CNPs in DSCP 48 / TC 6 strict priority; "How DCQCN
and PFC should interact") and the lab's planted `orion-be-leaf-r4 CNP_CLASS_MISMATCH`.

## Causal chain if a leaf maps CNPs into TC 3

1. **CNPs queue behind the congestion they report.** At that leaf, CNPs share the TC 3 egress queue
   with RoCE data. When TC 3 is congested (the very condition that produced the CNPs), each CNP waits
   behind a deep queue instead of jumping it in strict-priority TC 6.
2. **When TC 3 is paused, CNPs are paused too.** PFC on priority 3 stops every TC 3 frame, CNPs
   included. Feedback freezes exactly when it is most needed.
3. **The reaction points get rate cuts late or in bursts.** Senders keep transmitting at high rate for
   extra RTTs; then several stale CNPs arrive together and over-cut. DCQCN's control loop gains delay
   and oscillates.
4. **Queues reach Xoff more often, and PFC does DCQCN's job.** More pause frames, more pause
   propagation (as in the lab's propagation episode through leaf-r4), more HOL victims.
5. **Observable counter symptom:**
   - the ratio of ECN-marked packets to pause frames on congested ports falls ("running on pause");
   - `rp_cnp_handled` on the senders lags `np_cnp_sent` on the receiver in time, and arrives in bursts;
   - CNP-sized packets are counted in TC 3 on the misconfigured leaf, with zero traffic in TC 6.

The fix is a config-compliance rule: DSCP 48 → TC 6 strict on every hop. The lab's `audit_qos`
detects this as `CNP_CLASS_MISMATCH`.

**Full marks** require the chain to end in a counter. "Congestion control gets worse" alone earns
nothing for the final step.
