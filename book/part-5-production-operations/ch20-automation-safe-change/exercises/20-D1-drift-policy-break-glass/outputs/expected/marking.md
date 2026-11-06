# Marking scheme: 20-D1 Drift policy and break-glass for the ORION fabric

Type design-challenge · kind written · tier L1 · 15 points

**Evidence required:** A policy table (field class x behaviour x rationale), a break-glass procedure, and two scenario walk-throughs.

| Criterion | Points |
|---|---|
| Policy table splits fields by ownership and risk (invariants auto-revert, tunables alert with exemption, admin state via lifecycle) | 5 |
| Break-glass: who, scoped exemption object, expiry <= 24 h, audit record, mandatory follow-up PR; single writer per field and oscillation alert | 5 |
| Two scenario walk-throughs showing the policy's behaviour, including one incident tuning and one harmful hand edit | 5 |
