# 2.11.5 — The ownership cell most likely to be nobody's job

Graded on specificity: any Table 2.7 cell earns full credit when the fix names an owner, a runbook and a
rehearsal date. Model answer: the **feed-loss power policy**, the decision of what the GPUs do when one
power feed is lost (Section 2.10 Step 5). Facilities owns the feeds and the maintenance window, Fleet owns
the PSUs and BMC configuration, and Training Infra owns the job that slows down, so each team assumes
another has set it. Exercise 2.7 is what happens when nobody does: a planned UPS window becomes a 30 %
slowdown. Fix: make Fleet the single owner of the policy (the 570 W feed-loss cap or a PSU configuration
that rides through), with Facilities required to notify Fleet before every maintenance window. Write the
runbook (verify cording 3A/3B, apply the cap, confirm with `nvidia-smi -q -d POWER`, remove it after),
link it from the maintenance-window template, and rehearse it in the next commissioning or planned
window with a date on the calendar.
