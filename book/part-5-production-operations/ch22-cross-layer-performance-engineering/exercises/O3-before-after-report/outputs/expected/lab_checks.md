# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `render_report: facts / causes / uncertainty` | PASS render_report: facts / causes / uncertainty - report has hygiene counts (44 duplicates, 480 warm-up rows, 0 jobs dropped) and ordered sections |
| `attribute: contributions and shares` | PASS attribute: contributions and shares - contributions sum 4.04 s vs delta 4.04 s; share issues none; share SE ok=True, HC3 ok=True |
| `bootstrap_shares: job-level 95 % interval` | PASS bootstrap_shares: job-level 95 % interval - common-shift share 8.3 %, bootstrap 95 % [4.2, 14.2] (exp ~[4, 14]), 1884 resamples used |
