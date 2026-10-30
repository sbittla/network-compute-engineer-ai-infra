# Failure Analysis — ORION-256

## 1. Failure domains

| Domain | Contents | Blast radius on W-TRAIN (option A) | Blast radius (option B) |
|---|---|---|---|
| GPU | 1 GPU | <fill: job stops; TP group and its pipeline stalls> | <fill> |
| Node | 8 GPUs, 8 NICs | <fill> | <fill> |
| Rail NIC / optic / cable | 1 link | <fill> | <fill> |
| Leaf switch | <fill> | <fill: option A loses one rail on all 32 nodes> | <fill: option B loses all rails on 4 nodes> |
| Spine switch | <fill> | <fill: bandwidth loss %> | <fill> |
| Rack power feed | <fill> | <fill> | <fill> |
| Cooling unit | <fill> | <fill> | <fill> |
| Storage server / parallel FS | <fill> | <fill> | <fill> |
| Scheduler / control plane | <fill> | <fill> | <fill> |

## 2. Failure-mode table (FMEA style)

| ID | Failure mode | Cause | Detection signal (metric/log) | Effect | Mitigation / containment | Recovery and RTO | Owner |
|---|---|---|---|---|---|---|---|
| F-01 | Optic degrades on one rail link | <fill> | <fill: rising FEC corrected, falling Rx power in `ethtool -m`> | <fill: slow rail → straggler> | <fill> | <fill> | Fabric |
| F-02 | Single feed lost on rack rack-05 | <fill> | <fill> | <fill> | <fill> | <fill> | Facilities |
| <fill: ≥ 8 rows covering compute, network, storage, power, cooling, orchestration> | | | | | | | |

## 3. Worked failure scenario

Pick one scenario and walk the diagnostic loop: symptom → evidence → ranked hypotheses →
discriminating test → root cause → safe change → validation. Label every number. If you simulated
it, say so.

## 4. Spares and repair policy

<fill: spares by part (optics, DAC, NIC, PSU), repair SLAs, who owns RMA. ORION has no spare nodes: if you propose any, declare them as a variation and price them. Otherwise compare (a) waiting for repair, (b) restarting at reduced DP (DP = 7 → 224 GPUs, −12.5 %, needs a divisible global batch or a batch/LR change), with a restart cost of ≈ 900 s ≈ 64 GPU-h.>
