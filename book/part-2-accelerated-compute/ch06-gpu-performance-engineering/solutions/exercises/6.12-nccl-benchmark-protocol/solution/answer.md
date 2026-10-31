# 6.12 — Protocol: comparing two NCCL versions on two ORION nodes (model answer, 10 points)

Relies on manuscript Section 6.6 (protocol, Table 6.5), Section 6.7 (decision rule), Section 6.8 (manifest) and
Chapter 5 (topology validation).

**Question.** Does NCCL version Y change two-node all-reduce busbw relative to version X by more than the
practical threshold, at any message size that matters to W-TRAIN?

**Setup and concurrency control.** Two dedicated HX8 nodes, drained of other work, same pair for both
versions; mapping CSV golden on both (Chapter 5), all eight rails clean, `/GDRDMA` on every channel; no other
jobs on the leaves for the session (or at least no co-scheduled jobs on these nodes, and switch counters
recorded). Both NCCL builds made from source in the same container image; only `LD_LIBRARY_PATH` differs.

**Fixed environment.** Identical `NCCL_*` variables (record them), `CUDA_DEVICE_ORDER=PCI_BUS_ID`, NUMA
binding per rank, persistence mode, production clocks with `clocks_event_reasons` recorded.

**Workload and sizes.** `all_reduce_perf -b 8 -e 8G -f 2 -g 1`, one rank per GPU (16 ranks); `-w 20` warm-up and
`-n 100` measured iterations per size (stated, identical).

**Repetitions and interleaving.** ≥ 6 separate launches per version, interleaved X, Y, X, Y, … in one session
(so drift hits both arms); one A/A session (X vs X, same schedule) to measure the noise floor.

**Statistic and decision rule (pre-registered).** Per launch and size: the median busbw across the measured
iterations (out-of-place). Per size: the change of the median of launch medians, a bootstrap 95 % band over
launches, and an exact permutation test on launch medians. Decide at 1 GiB and 8 GiB (primary) and report the
small-message latency range (secondary): Y is better/worse if p < 0.05 and |change| ≥ max(A/A floor, 2 %);
otherwise "no material difference". Exclusion rules written in advance (version or env mismatch, NIC errors,
throttling > 5 % of iterations) and applied to both arms.

**Manifest per launch.** NCCL version and build hash, driver, CUDA, NIC firmware, OFED/DOCA version, container
digest, node names and mapping CSV hash, all `NCCL_*` env vars, sizes, `-w`/`-n`, start time, clocks/limiter
summary, NIC counter deltas.

**Common gaps.** One launch per version; no A/A floor; deciding on the best size after seeing the data.
