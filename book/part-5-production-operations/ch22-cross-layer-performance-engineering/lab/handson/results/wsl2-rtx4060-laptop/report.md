# Ch 22 hands-on: find the bottleneck — `wsl2-rtx4060-laptop`

Every number is `[MEASURED]` on the machine in `environment.json` (step named) unless labelled otherwise.

## Calibration

GPU-only step 42.8 ms; decode 86.2 ms per batch on one CPU (9 rounds); netem delay 257 ms `[MEASURED, calibration]` (sizes chosen by rule: decode ≈ 2 × GPU step, delay ≈ 6 × GPU step).

Healthy: 5 runs, mean step **43.6 ms**; data-wait share 0 %; GPU-Util median 99.0 %; ping over the veth 0.067 ms `[MEASURED, healthy]`.

## Diagnoses (rules in diagnose.py, written before the runs)

| Scenario | Injected | Step vs healthy | Data-wait share | Network wait / batch (ms) | Decode run-queue share | Syncs / step | GPU-Util | Verdict | Expected |
|---|---|---|---|---|---|---|---|---|---|
| Dataloader stall | decode moved into the training process (num_workers=0) | 2.35× | 58 % | 0.5 | 0 % | 0.3333333333333333 | 42.0 % | **dataloader** | dataloader |
| CPU contention | 8 ch22-hog busy loops pinned with taskset to the job's CPUs | 1.73× | 44 % | 4.1 | 69 % | 0.3333333333333333 | 54.0 % | **cpu_contention** | cpu_contention |
| Hidden host sync | a per-block activation statistic copied to the host (.cpu() + numpy) and loss.item() every step | 2.19× | 0 % | 0.6 | 0 % | 5.333333333333333 | 49.0 % | **host_sync** | host_sync |
| Network delay on the data fetch | netem delay on the data server's veth (ch22-d0) | 3.61× | 74 % | 515.3 | 1 % | 0.3333333333333333 | 11.0 % | **network** | network |

All `[MEASURED, evidence run of each scenario]`.

## Fixes validated by A/B (interleaved, separate processes; primary statistic = difference in arm means of run step times)

| Scenario | Fix | Before (ms) | After (ms) | Change | 95 % band | Exact p (floor) | Decision | After vs healthy |
|---|---|---|---|---|---|---|---|---|
| Dataloader stall | num_workers=4 | 99.1 | 42.9 | -56.7 % | [-56.9 %, -56.4 %] | 0.0079 (0.0079) | **improvement** | -1.4 % |
| CPU contention | re-pin the job to a disjoint CPU set | 80.6 | 42.7 | -47.0 % | [-49.4 %, -43.4 %] | 0.0079 (0.0079) | **improvement** | -2.0 % |
| Hidden host sync | remove the per-block host statistic; log the loss every 20 steps | 93.4 | 42.7 | -54.3 % | [-54.5 %, -54.1 %] | 0.0079 (0.0079) | **improvement** | -2.0 % |
| Network delay on the data fetch | 4 fetches in flight per worker (prefetch) | 154.5 | 42.3 | -72.6 % | [-72.7 %, -72.5 %] | 0.0079 (0.0079) | **improvement** | -2.9 % |

All `[MEASURED, A/B of each scenario]`; practical threshold 5 %.

Network scenario ping over the delayed veth: 257.431 ms `[MEASURED, scenario 4]`.

