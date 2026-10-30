# Injected-Fault Scenarios

> **Safety:** These scenarios run in the simulator (L1) or on a dedicated lab fabric (L3) only.

## 1. Scenario catalogue

For each scenario you found in the supplied capture, and for the one you add, fill one row.

| ID | Scenario | Onset (UTC) | Root-cause device / interface | Expected signature (counters, direction, scope) | Rule that should fire | Detected? Latency | Symptoms that must *not* page separately |
|---|---|---|---|---|---|---|---|
| S-01 | <fill> | <fill> | <fill> | <fill> | <fill> | <fill> | <fill> |

## 2. Benign events in the capture

| ID | Event | Why it looks like a fault | Why it is not | Mechanism that keeps it quiet |
|---|---|---|---|---|
| N-01 | <fill> | <fill> | <fill> | <fill: persistence / suppression / wrap handling> |

## 3. Your additional scenario

Add one seeded scenario of your own to a copy of `tools/generate_data.py`, for example an MTU mismatch
that shows up as discards on one host port, a flapping link, or a slow-drain receiver that causes
moderate rather than storm-level pause. Document:

- Mechanism and expected counter signature: <fill>
- Generator change (diff summary) and seed: <fill>
- Which existing rule catches it, or the new rule you wrote: <fill>
- Precision/recall on the extended capture: <fill>

## 4. L3 scenario (optional)

<fill: incast with ECN disabled on the lab switch's lossless queue. Procedure, safety controls,
rollback, results with repetitions.>
