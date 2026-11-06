# Marking scheme: 3.3 Diluted signals

Type knowledge-check · kind computed · tier L1 · 4 points

**Evidence required:** The arithmetic, and the two metrics with the command that shows each.

| Criterion | Points |
|---|---|
| Maximum blocked tasks = 0.045 x 224 = 10.1 (about 10), with the one-task-per-idle-CPU reasoning | 2 |
| First undiluted metric with its command (vmstat 1 5 column b, ignoring the first row) | 1 |
| Second undiluted metric with its command (iostat -x 1 3 r_await/w_await and aqu-sz, or PSI /proc/pressure/io) | 1 |
