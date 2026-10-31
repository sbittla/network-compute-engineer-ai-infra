# 14.16 — When Young does not set the interval: worked solution

Young's τ = √(2δM) minimizes expected lost time for *one job*. It ignores policy, other tenants and
capacity. Two situations where something else sets the interval:

1. **The RPO policy.** If Young's τ + L exceeds the RPO target, the policy sets τ = RPO − L. At
   M = 198 h (14.10), async PFS gives τ = 1,305 s and RPO max ≈ 22 min. A 15-minute policy forces
   τ ≤ 900 − 18.5 = 881.5 s, i.e. 50 steps = 870 s, at a small cost increase because the optimum is flat.
   *Metric:* **age of the newest validated checkpoint** (now − commit time of the newest checkpoint that
   passed validation), alerted when it exceeds the RPO target. This is also the metric that catches
   silently failing checkpoints.

2. **PFS fairness or capacity.** The checkpoint burst can saturate shared PFS write bandwidth (ORION-XL:
   5.67 TB at full rate for about 19 s every 3 min, 14.13). Platform may cap the duty cycle or bandwidth
   share, and the interval must then stretch. A capacity quota can also cap how many checkpoints can be
   retained, and so how often they can be taken with a safe in-flight copy.
   *Metrics:* PFS write utilization during bursts and **other tenants' read p99 during checkpoint
   windows** versus outside them. For capacity: quota usage against the retention requirement.

*Also accepted:* **one-in-flight back-pressure.** When completion latency L approaches τ, a new
checkpoint would start before the previous one commits, so the interval is floored at L (as the lab's
A3 check does). *Metric:* a counter of skipped or back-pressured checkpoints, or L/τ trending to 1.

In each case, record which constraint is binding next to the planner output, so that a later MTBF
change does not silently re-optimize the interval against a policy.
