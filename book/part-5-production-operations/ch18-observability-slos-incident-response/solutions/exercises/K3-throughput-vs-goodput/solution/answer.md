# K3 — Throughput SLI versus goodput SLI

**Definitions (Table 18.4):**
- *Training throughput SLI* = job-minutes whose median step time ≤ 1.10 × the job's baseline / all
  running job-minutes after warm-up.
- *Training goodput SLI* = accelerator time producing *retained* progress / allocated accelerator
  time, where lost time = slow steps + work since the last checkpoint at each failure + restart time.

The difference: throughput only judges minutes while the job runs; goodput also charges failures for
lost work and restarts.

**A week with throughput 100 % and goodput 80 %** `[MODELED]`. A job is allocated 168 h. Whenever it
runs it runs at full speed (every running minute is good → throughput SLI 100 %), but it crashes every
6 h: 168 / 6 = 28 crashes. Checkpoints are hourly, so each crash loses on average 0.5 h of work, plus a
0.7 h restart and reload (a deliberate variation; the canonical ORION restart is 0.25 h):
loss per crash = 0.5 + 0.7 = 1.2 h; total = 28 × 1.2 = 33.6 h;
goodput = (168 − 33.6) / 168 = **0.80**.
With the canonical 0.25 h restart: 28 × 0.75 = 21 h lost → goodput 0.875.

Lesson: a job can look perfect on the throughput SLI while a fifth of its GPUs' time is wasted, so
both SLIs belong in the spec (and attribution decides whether the crashes are infrastructure's).
Source: Section 18.7. Any example reaching 80 % with correct arithmetic earns full credit.
