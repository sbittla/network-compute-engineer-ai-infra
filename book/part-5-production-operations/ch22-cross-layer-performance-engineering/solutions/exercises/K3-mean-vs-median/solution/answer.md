# K3 — Mean versus median of per-job means (solution)

**Interpretation.** The job-weighted mean rose 20 % but the median of per-job means rose only 4 %. The
median describes the typical job; it barely moved, so most jobs are near baseline. The mean is pulled up
by a *minority* of jobs that are badly affected. A fleet-wide cause (a driver on every node, a container
rebuild) would move mean and median together. The pattern points to a cause that hits some jobs and not
others: a placement, node or dataset attribute (manuscript Section 22.3.1, Table 22.4).

**What the unchanged p99 adds.** Per-job p99 is unchanged for most jobs, so inside an affected job the
slowdown is steady (every step a little slower), not intermittent stalls. Intermittent causes such as
storage recalls or a flapping link would raise per-job p99 far more than the per-job median.

**First partition.** Split the after-period jobs by an attribute that differs *within* the window and
maps to a mechanism:

- *TP group spans nodes* (from placement records, `scontrol show job -d`). Hypothesis H-placement: TP
  all-reduces left NVLink. Prediction: affected jobs are exactly the split ones, with a gap of seconds
  per step; packed jobs sit at baseline.
- Alternative acceptable partition: *ran on upgraded nodes* (time-aware inventory join), testing
  H-driver.

**Worked illustration.** If 80 % of jobs are at baseline (+0 %) and 20 % are slowed by +X %, the mean
rises by 0.2·X % and the median by ≈ 0 %. A 20 % mean rise with a 4 % median rise is consistent with,
for example, a quarter of the jobs being ≈ 60–80 % slower and a small common shift on the rest
`[ILLUSTRATIVE]`.

**Common wrong answers.** "Noise" (a 16-point gap between mean and median is not noise); proposing a
partition that cannot be built from records ("jobs that felt slow"); partitioning by the change log's
intent rather than by evidence.
