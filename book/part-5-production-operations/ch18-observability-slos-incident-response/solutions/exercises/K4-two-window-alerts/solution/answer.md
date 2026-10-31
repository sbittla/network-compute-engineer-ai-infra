# K4 — Why multiwindow burn-rate alerts need two windows

Policy (Table 18.5): page when the 1 h burn > 14.4 **and** the 5 min burn > 14.4 (or 6 h and 30 min
> 6).

**What the long window prevents: paging on short blips.** A short window alone reacts to any brief
spike. Lab 18 scenario `[SIMULATED]`: deploy DEP-41 at 05:10 produces ≈ 4 % errors for 7 minutes
against a 0.1 % budget. The 5-minute burn reaches 0.04 / 0.001 = **40**, far above 14.4, but the 1 h
window holds only 7 bad minutes: (7 × 0.04 + 53 × 0.0002) / 60 ≈ 0.0048 → burn ≈ 4.8 by hand, **4.65**
in the request-weighted data, below 14.4. No page, which is right: the canary rolled back
automatically and consumed well under 1 % of the monthly budget. The long window proves that the
problem is *significant* (≥ 2 % of the budget spent).

**What the short window prevents: alerts that fire late or keep firing after the fix.** A 1 h window
stays above threshold for up to an hour after a rollback, because it still contains the bad
minutes. Scenario: a total outage started 50 minutes ago and was rolled back 10 minutes ago; the 1 h
window still holds 40 bad minutes, burn = (40 / 60 × 1.0) / 0.001 ≈ 667 ≫ 14.4, so a
long-window-only rule would page *now*, for a problem that is over, and would not resolve for another 50 minutes. The 5-minute window is back to
≈ 0, so the multiwindow rule does not fire and resolves within minutes of mitigation. The short window
proves the problem is *still happening*.

**Common mistake:** paging on the 5-minute window alone (penalized in the lab, planted anomaly 5).
Source: Section 18.8 ("Multiwindow, multi-burn-rate alerts", "Short blips do not page").
