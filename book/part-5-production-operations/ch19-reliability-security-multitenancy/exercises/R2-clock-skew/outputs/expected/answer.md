# R2 — Clock skew on orionxl-n212: guidance and model answer

**Relies on:** Section 19.5 "Proven cause versus correlation" (temporal precedence); Section 19.11 Step 3
(timing arithmetic); Section 19.7 (RPO/RTO); lab `data/events.jsonl` (the `host` and `source` fields).

## What depends on orionxl-n212's clock

In `events.jsonl` only two kinds of events come from orionxl-n212 itself: its kernel `mlx5_core … Link
down/up` lines and its own NET/IB warning. The other evidence comes from other clocks: the NET/IB errors
on n211 and n213, the switch syslog of orionxl-be-leaf-p06-r5, the trainer log on n001, and slurmctld.

## Conclusions that would change with a 15 s skew

1. **Temporal precedence of H1.** The claim is "link down at 03:41:02, first NET/IB error 9 s later at
   03:41:11, which matches the 8.6 s retry budget". If n212's clock is 15 s fast, its true link-down was
   at 03:40:47, so the gap is 24 s and no longer matches the mechanism. If it is 15 s slow, the true
   link-down was 03:41:17, *after* the peers' errors. The cause would then appear to follow the
   symptom, and H1 would fail the precedence test. The 01:12:44 attempt-1 timing changes the same way.
2. **Link-down duration.** It is computed from two n212 timestamps, so it is unaffected by a constant
   skew (14 s either way). The "14 s > 8.6 s" part of the mechanism survives.
3. **RPO and RTO.** These use the failure time. If the failure time is taken from n212's kernel log,
   RPO and RTO shift by ±15 s (≈ ±17 GPU-h on 4,096 GPUs). The conclusions do not change, but the
   numbers do.
4. Conclusions from other clocks (stuck group, checkpoint selection, watchdog order) are unaffected.

## How to re-establish order

Use an **independent clock that saw the same event**: the switch syslog records Ethernet20/1 DOWN at
03:41:02 and UP at 03:41:16 from the leaf's own clock. Cross-check the n211/n213 NET/IB errors against it
and the 8.6 s mechanism. Then measure the skew (chrony/PTP offset logs, `chronyc tracking`) and record it
in the packet. Prevention: alert on NTP/PTP offset > 100 ms and include clock offset in node health.
