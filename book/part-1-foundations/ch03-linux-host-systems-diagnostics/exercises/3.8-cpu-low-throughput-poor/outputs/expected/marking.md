# Marking scheme: 3.8 CPU utilization is low but throughput is poor

Type troubleshooting · kind computed · tier L1 · 10 points

**Evidence required:** A one-page report with a signal table (section, value, baseline), a ranked hypothesis table with tests, the root-cause statement, a remediation order and a validation plan; at least three raw lines quoted from the snapshot.

| Criterion | Points |
|---|---|
| Signal table with at least six correct abnormal signals, each with section and value (nvme3n1 48.6 ms, md0, iowait 6.9 %, vmstat b 15.25, CPU0 99.5 % softirq, IRQs on CPU0, 98.9 % NUMA-remote, GPUs 55-60 %) | 3 |
| At least four hypotheses ranked by how well they explain the 40 % loss, with nvme3n1 gating md0 first | 2 |
| A discriminating L2 test with confirming result for each hypothesis | 2 |
| Root cause with contributing factors and a safe remediation order (drain, change process), plus a validation plan with metric, warm-up, repetitions and statistic (key 1.5 + 1.5) | 3 |
