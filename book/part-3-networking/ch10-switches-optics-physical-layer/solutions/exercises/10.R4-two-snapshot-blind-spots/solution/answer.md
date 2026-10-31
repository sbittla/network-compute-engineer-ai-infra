# 10.R4 — How a two-snapshot method misses a real fault

A two-snapshot analyzer computes deltas between T0 and T1 (600 s apart) on one end of each link.
Two ways a real fault passes as "healthy":

1. **The fault happens outside the window, or recovers inside it.** An intermittent flap that comes
   back up before T1, or a burst of uncorrectables at 03:00 when the snapshots were taken at 10:00,
   leaves counters that look normal (or only a small delta) and DOM that reads normal at the sampled
   instant. Cumulative link-down counters catch some of this, but instantaneous DOM never does.
   **Change:** continuous streaming telemetry at ≤ 30 s for counters and DOM, plus event logs (link
   up/down syslog with timestamps), so excursions between samples are recorded.
2. **Only one end of the link is sampled.** Many physical faults are one-directional (Section
   10.8.1, question 2): a dirty end-face on the switch-to-host fiber shows up as low Rx power and
   errors on the *host* side only. Sampling only the leaf misses it entirely. **Change:** collect both
   ends (switch telemetry and host `ethtool -S` / `ethtool -m`) and join them by cable ID from the
   cabling schedule, so every link is judged on both directions.

Also acceptable: counter resets or 32-bit wraps that hide increments (use reset-aware deltas and
64-bit counters, and record clear events); DOM polled too rarely to catch thermal excursions (poll
faster and alert on rate of change); thresholds tuned on the snapshot average rather than the
FEC-histogram tail.
