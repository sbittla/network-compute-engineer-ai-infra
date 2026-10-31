# 3.2 — Why the first `vmstat` line and the first `iostat` report are discarded

Source: manuscript Section 3.3 ("What the scheduler is telling you") and Section 3.5 ("Reading
`iostat -x`"); lab parser traps B3 and B4.

**What the first sample measures.** Both tools compute rates from kernel counters (`/proc/stat`,
`/proc/vmstat`, `/proc/diskstats`). On the first sample there is no previous reading, so they divide the
counters by the *time since boot*. The first `vmstat` line and the first `iostat -x` report are
therefore the average of every interval since the host booted, not the current behaviour. Only the
later samples are live deltas over the requested interval.

**Numeric example.** A node has been up for 21 days, mostly idle or running another job. For the last
five seconds its data loaders are blocked on a slow drive:

```text
vmstat 1 5 → b column: 0 (since boot), 15, 15, 15, 15
mean of all five rows          = (0 + 4 × 15) / 5 = 12
first row only                 = 0     → the problem disappears
live rows only (correct)       = 15
```

The `iostat` case is worse. A member drive with 48.6 ms `r_await` over the last second can show
≈ 0.2 ms in the since-boot report because 21 days of healthy averages swamp one bad second. That is
exactly how `nvme3n1` hides on `orion-n12` if the parser keeps the first report. Always use
`vmstat 1 N` without its first row, and the last report of `iostat -x 1 2` (or later).
