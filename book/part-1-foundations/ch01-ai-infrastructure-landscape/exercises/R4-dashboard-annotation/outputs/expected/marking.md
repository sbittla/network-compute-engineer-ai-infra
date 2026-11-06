# Marking scheme: R4 Dashboard annotation for the utilization trap

Type reflection · kind written · tier L1 · 3 points

**Evidence required:** The annotation text you would add to the dashboard.

| Criterion | Points |
|---|---|
| States that GPU utilization counts any running kernel, including NCCL kernels waiting on peers | 1 |
| Points the reader to SM-active and tensor-active panels (or the step-time panel) for compute efficiency | 1 |
| Gives the actionable pattern (tensor activity falls while utilization stays flat, so suspect communication or waiting) in two or three sentences an on-call engineer can use | 1 |
