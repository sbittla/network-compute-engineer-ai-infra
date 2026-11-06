# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `dataset_reproducible` | PASS dataset_reproducible   generator reproduces committed data byte-for-byte |
| `validation_issues` | PASS validation_issues      4 bad rows rejected with correct codes, 14 clean rows |
| `unit_normalization` | PASS unit_normalization     Gb -> GB conversion correct (80 Gb = 10 GB) |
| `resource_times_core` | PASS resource_times_core    compute/memory/NVLink/NIC ceilings applied correctly (NIC = 400/8 = 50 GB/s) |
| `resource_times_io` | PASS resource_times_io      per-node I/O ceiling = min(frontend NICs, PFS aggregate / nodes in the job) |
| `w01_worked_example` | PASS w01_worked_example     W01 (W-TRAIN) lower bounds match the Section 1.9 worked example |
| `classification` | PASS classification         all 14 clean workloads assigned the correct bound class |
| `flags` | PASS flags                  IMPOSSIBLE=W12, LATENCY_OR_OVERHEAD=W16, MISLABELED=W05,W09 |
| `comparison_markdown` | PASS comparison_markdown    one-page W01 vs W02 comparison has all resources, bounds and evidence |
