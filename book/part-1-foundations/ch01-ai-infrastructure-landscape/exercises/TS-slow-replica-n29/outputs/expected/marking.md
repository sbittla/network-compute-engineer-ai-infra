# Marking scheme: TS Slow inference replica orion-n29

Type troubleshooting · kind computed · tier L1 · 15 points

**Evidence required:** Ranked hypotheses with for/against evidence; mechanism paragraph; two tests with expected outcomes; remediation with a measurable validation criterion; explicit statement of what is proven versus correlated.

| Criterion | Points |
|---|---|
| At least three hypotheses across compute, network and orchestration, ranked with evidence for and against; GPU 5 NVLink loss ranked first and the replay counter treated as a watch item | 4 |
| Mechanism explains that 160 sequential TP all-reduces per step wait for the slowest GPU and that small, latency-bound messages make decode sensitive (about 44 us extra per all-reduce) | 4 |
| Two safe, read-only discriminating tests with expected results under the top hypothesis | 4 |
| Remediation (drain, hand off, return after acceptance), a measurable validation criterion, and an explicit proven-versus-correlated statement | 3 |
