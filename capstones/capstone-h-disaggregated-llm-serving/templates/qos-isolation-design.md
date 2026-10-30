# Network QoS and Isolation Design for KV Traffic

> Template for Capstone H artifact 4.

## 1. Findings on the proposed mapping
| Finding code | Why it matters (mechanism) | Fix |
|---|---|---|
| `<fill>` | `<fill>` | `<fill>` |

## 2. Corrected mapping
| Class | DSCP | TC | PFC | ECN | Scheduling / share | Notes |
|---|---|---|---|---|---|---|
| training-roce | 26 | 3 | yes | yes | `<fill>` | unchanged |
| cnp | 48 | 6 | — | — | strict priority | |
| kv-transfer | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | |
| best-effort | 0 | 0 | no | yes | | |

## 3. Isolation and encryption
`<fill: tenancy boundary, VRF/VLAN or separate rails, encryption choice and its cost>`

## 4. Validation plan (lab)
`<fill: how you would prove KV bursts do not pause training traffic — counters to read, test to run>`
