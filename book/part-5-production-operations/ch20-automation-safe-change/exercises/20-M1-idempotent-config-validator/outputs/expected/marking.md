# Marking scheme: 20-M1 Idempotent node/network configuration validator

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** Source code; two consecutive runs showing drift -> fixed -> in sync (second apply plans zero actions); audit lines; L2 manifest fields.

| Criterion | Points |
|---|---|
| Reads state through machine-readable interfaces (ip -j, ethtool -i, ibv_devinfo, sysfs speed) | 2 |
| Exit codes 0 in sync / 1 drift / 2 cannot determine | 1 |
| Validates without mutating by default (dry run) | 2 |
| --apply touches only the IP MTU of backend NICs and the second run is a no-op | 2 |
| One JSON audit line per check and per action (target, key, before, after, result) | 2 |
| Missing tool or device reported as cannot-determine, never as in sync | 1 |
