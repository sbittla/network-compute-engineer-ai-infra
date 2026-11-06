# 14.10 — Interval and lost accelerator-hours at a measured failure rate: worked solution

**Inputs.** `lab/data/orion_ckpt_inputs.yaml` with `job_mtbf_h: 198` (the rate derived from the
Llama 3 report, Section 14.11). M = 198 × 3,600 = 712,800 s; failures/day = 86,400 / 712,800 = 0.1212.
Planner model: Section 14.12 and the lab's Part A. All values are `[MODELED]`.

| Strategy | τ (steps) | Overhead | RPO max | Lost GPU-h/day (ckpt + fail) |
|---|---|---|---|---|
| async PFS | 1,305.0 s (75) | 0.09 % | 1,323 s | 5.59 + 13.58 = **19.2** |
| async two-level | 1,061.4 s (61) | 0.07 % | 5,328 s | 4.54 + 19.74 = **24.3** |
| sync local + drain | 2,105.4 s (121) | 0.15 % | 2,126 s | 9.00 + 16.91 = **25.9** |
| sync PFS | 5,046.0 s (290) | 0.35 % | 5,064 s | 21.71 + 29.69 = **51.4** |

**Hand check, async PFS.**

```text
S = 70e9 × 14 = 980 GB; PFS write = 980 / (80 × 0.75) = 16.33 s; persist = 16.33 + 1.5 = 17.83 s
snapshot = 980/256 GB / 25 GB/s + 0.5 = 0.153 + 0.5 = 0.653 s
δ = 0.653 + 0.03 × 17.83 = 1.188 s;   L = 0.653 + 17.83 = 18.5 s
Young = √(2 × 1.188 × 712,800) = √1,693,786 = 1,301.5 s → 74.8 steps → 75 → 1,305.0 s
ckpt cost = 86,400/1,305 = 66.2 × 1.188 s = 78.7 s × 256 / 3,600 = 5.59 GPU-h/day
E[lost] = 652.5 + 18.5 = 671.0 s;  E[resume] = 0.6 × 808.2 + 0.4 × 1,048.2 = 904.2 s
fail cost = 0.1212 × (671.0 + 904.2) × 256 / 3,600 = 13.58 GPU-h/day   → total 19.2
```

**What changed and why.**

- *Ranking unchanged:* async PFS < two-level < sync local + drain < sync PFS.
- *Magnitudes fall about 2.9×* (async: 55.6 → 19.2 GPU-h/day) because failures are about 4× rarer and
  the checkpoint cost per day also falls with the longer interval.
- *Intervals stretch by √(198/48) ≈ 2.0×* (Young τ ∝ √M): 643.8 → 1,305 s.
- *RPO max grows* to 22 min (async) and 84 min (sync PFS). If Halcyon's RPO policy is, say, 15 min,
  the **policy, not Young, sets the interval** (see 14.16). At M = 198 h, Young's optimum is flat:
  checkpointing at 15 min costs only a little more per day.

**Common wrong answer.** Not rounding up to whole 17.4 s steps, or keeping the M = 48 h intervals.
