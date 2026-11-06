# R3 — How the training throughput SLI can mislead

The SLI (Table 18.4) counts job-minutes with median step time ≤ 1.10 × the job's baseline.

| Way it misleads | Example | Guard |
|---|---|---|
| **Baseline drift** | Re-baselining on a slow day (e.g. during a degraded fabric) makes the slow state "normal"; every later minute looks good | Pin the baseline to a config hash (model, batch, parallelism, bundle); re-baseline only on a config change, from a known-good window; alert on baseline changes |
| **Over-excluding steps** | Labelling slow steps as "checkpoint" or "evaluation" removes them from the SLI (the lab excludes real checkpoint stalls: +9 s every 30 min for trn-70b) | Audit exclusions: excluded minutes as a metric, capped per hour, derived from the job's own checkpoint log, not a threshold |
| **Legitimate step changes** | A batch-size or sequence-length change alters step time; the ratio moves without any infrastructure problem (false page), or a smaller batch hides a regression (false good) | Report tokens per second alongside step time; reset the baseline automatically on config change |
| **Throughput is not goodput** | A job that crashes every 6 h has 100 % throughput SLI and 80 % goodput (K3) | Keep the goodput and recovery SLIs next to throughput |
| **Warm-up and partial minutes** | Counting warm-up or restart minutes as bad (or excluding them silently) | Define warm-up explicitly (N steps after start) and report it |

Any three with a guard each earn full credit. Source: Section 18.7 design notes; `lab/data/job_steps.csv`.
