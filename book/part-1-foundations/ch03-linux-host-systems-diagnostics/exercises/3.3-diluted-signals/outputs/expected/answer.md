# 3.3 — Diluted signals

Source: manuscript Section 3.5 ("`%iowait` is a diluted signal") and Section 3.3 (load average).
`[MODELED]`; `solve.py` checks the arithmetic.

**(a) Largest number of blocked tasks consistent with `%iowait` = 4.5 %.** `%iowait` is the share of
*CPU time* spent idle while at least one task waits on I/O for that CPU. Each blocked task can make at
most one CPU idle-in-iowait, so

```text
max blocked tasks ≈ %iowait × CPUs = 0.045 × 224 = 10.1  → about 10 tasks
```

That is consistent with a load average of 12 on a 92 %-idle host: on Linux the load average counts tasks
in uninterruptible sleep (state `D`, usually I/O) as well as runnable ones. So ≈ 10 blocked tasks plus
≈ 2 running ones give ≈ 12. On a 224-CPU host, ten stuck data-loader workers look like 4.5 %, a number
most dashboards would call fine.

**(b) Two undiluted metrics to check next.**

1. **Blocked tasks directly:** `vmstat 1 5`, column `b`, ignoring the first (since-boot) row.
2. **Device latency and queue:** `iostat -x 1 3`, reading `r_await`/`w_await` (ms) and `aqu-sz` per
   device from the last report. Pressure stall information, `cat /proc/pressure/io` (`some`/`full`
   avg10), is an acceptable alternative.
