# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `T4 root-cause correlation` | PASS T4 root-cause correlation: trigger=CHG-4471 (expect CHG-4471), rejected=['CHG-4468', 'FAC-0912']; leaf PFC TX x91, ECN x0.03 |
| `T5 incident timeline` | PASS T5 incident timeline: TTD=48.0 min, TTM=118.2 min, TTR=140.0 min (expect ~48 / ~118 / ~140) |
| `T5 postmortem rendering` | PASS T5 postmortem rendering: all placeholders filled=True; missing fact raises KeyError=True |
