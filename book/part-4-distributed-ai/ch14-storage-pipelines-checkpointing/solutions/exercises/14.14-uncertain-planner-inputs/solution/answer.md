# 14.14 — Most uncertain planner inputs: worked solution

The three inputs whose uncertainty moves the answer most for ORION, each with the measurement that
replaces it (a fourth is listed as an alternative):

1. **PFS efficiency for a 256-writer burst** (`pfs_efficiency: 0.75`). It sets the persist time and
   therefore L, δ for synchronous strategies, and the tenant burst. *Measurement:* a full-cluster
   checkpoint write of real shards from all 256 ranks, timed from first open to durable commit
   (bytes ÷ wall time). Repeat ≥ 5 times across a working day so that other tenants' load is sampled.
   Report median and spread `[MEASURED]`.
2. **Job MTBF and hard-failure fraction** (`job_mtbf_h: 48`, `hard_failure_frac: 0.4`). Young's interval
   scales with √M and the failure term dominates lost GPU-h. *Measurement:* incident records over at
   least one quarter, every job interruption classified soft (process, NCCL timeout) or hard (node lost
   with its NVMe). Report M with a confidence interval, because failures are few.
3. **Restart components** (`detect_s`, `relaunch_s`, `validate_s`, `warmup_s`, `replace_s`). These are
   E[time-to-resume], which at high failure rates outweighs checkpoint overhead. *Measurement:*
   timestamps for failure → detection → relaunch → load → first completed step from ≥ 5 real or drilled
   restarts (kill a rank on purpose in a maintenance window), soft and hard separately.

*Alternative fourth:* **interference** (`interference_frac: 0.03`). Measure step time during versus
outside persist windows over ≥ 50 checkpoints and compare the distributions.

Each measurement goes into the lab manifest with versions, dates and `[MEASURED]` labels before the
planner output is used for a production decision.
