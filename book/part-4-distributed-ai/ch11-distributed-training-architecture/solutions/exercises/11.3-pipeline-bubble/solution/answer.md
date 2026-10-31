# 11.3 — 1F1B bubble fraction

**Formula** (Section 11.5, Figure 11.4). With m micro-batches and p stages the pipeline takes
(m + p − 1) slots per stage, of which m are busy, so the idle fraction of total time is

```text
bubble fraction = (p − 1) / (m + p − 1)
```

**Values** `[MODELED]`:

| p | m | Substitution | Bubble (of total time) |
|---|---|---|---|
| 4 | 8 | 3 / 11 | **27.3 %** |
| 4 | 32 | 3 / 35 | **8.6 %** |
| 4 | 128 | 3 / 131 | **2.3 %** (the W-TRAIN baseline) |
| 8 | 32 | 7 / 39 | **17.9 %** |

**Reading the numbers.** The bubble shrinks only as m grows relative to p: quadrupling m from 8 to 32
cuts it by 3×, and doubling p at fixed m roughly doubles it. Because m = global batch / (DP ×
micro-batch), scaling DP at fixed global batch shrinks m and grows the bubble — pipeline parallelism
and strong scaling work against each other (Section 11.9). Interleaved schedules divide the bubble by
the number of virtual stages v at the cost of v× more point-to-point messages.

**The other convention.** Relative to ideal compute time the bubble is (p − 1)/m: 37.5 %, 9.4 %,
2.3 % and 21.9 %. Accept these only if the learner names the form; the question asks for the fraction
of total time.

**Common wrong answers.** Using (p − 1)/m without saying so; using m/(m + p − 1) (the busy fraction);
forgetting that the bubble is the same for GPipe and 1F1B (1F1B changes memory, not idle time).
