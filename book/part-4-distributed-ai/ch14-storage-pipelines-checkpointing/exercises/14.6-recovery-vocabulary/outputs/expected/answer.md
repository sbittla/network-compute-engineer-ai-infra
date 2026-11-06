# 14.6 — Recovery vocabulary: worked solution

| Term | Definition | Category |
|---|---|---|
| Checkpoint overhead | Training time lost per checkpoint (blocking + interference) ÷ interval: δ/τ | Model output when planned; a measurement when taken from step-time logs |
| Completion latency | Snapshot start → commit marker durable (checkpoint restorable) | Measurement |
| RPO (recovery point objective) | Maximum acceptable lost training progress. The achieved worst case is τ + L (k·τ + L for a k-level PFS copy) | **Objective** |
| RTO (recovery time objective) | Maximum acceptable time from failure to training progressing again | **Objective** |
| Time-to-resume | Measured time from failure to the first completed step after restart: detect + relaunch (+ replace) + validate + load + warm-up | Measurement |
| Lost accelerator-hours | GPUs × (checkpoint overhead + recomputed work + time-to-resume) over a period, e.g. GPU-h/day | Model output (or measured per incident) |

**How they relate (Section 14.11).** Objectives are what the business commits to. Measurements are what
the system did. Model outputs are what a planner predicts from inputs such as MTBF and bandwidth. The
design is accepted when *measured* completion latency and time-to-resume, fed into the model, give an
achieved RPO and RTO within the objectives. For W-TRAIN asynchronous PFS saves at M = 48 h:
τ = 643.8 s, RPO max ≈ 662 s, E[time-to-resume] ≈ 904 s, lost ≈ 55.6 GPU-h/day `[MODELED]`.

**Common wrong answers.** Calling RPO "the checkpoint interval". RPO is a target and the interval is
one input to the achieved value. Treating time-to-resume and RTO as synonyms. One is measured, the other
is the limit it is measured against.
