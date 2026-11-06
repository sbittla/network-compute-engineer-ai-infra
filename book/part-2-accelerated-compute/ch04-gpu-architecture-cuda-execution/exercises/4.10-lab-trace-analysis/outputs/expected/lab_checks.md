# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `merge_intervals` | PASS merge_intervals — overlapping, touching and empty intervals handled |
| `busy_ns` | PASS busy_ns — union length correct (no double counting across streams) |
| `step_windows` | PASS step_windows — 2 step windows |
| `utilization` | PASS utilization — train_step_41: busy(any) 88.8%, busy(kernel) 78.6% |
| `copy_compute_overlap` | PASS copy_compute_overlap — train_step_41: 13.4% of copy time overlapped with compute |
| `find_gaps` | PASS find_gaps — causes over 2 steps: {'host_sync': 30, 'launch_bound': 1200, 'dependency': 2} |
| `copy_table` | PASS copy_table — pageable ≈ 10.7 GB/s vs pinned ≈ 48.1 GB/s |
| `theoretical_occupancy` | PASS theoretical_occupancy — 7 launch configurations match hand calculation |
| `kernel_summary` | PASS kernel_summary — layernorm_bwd at 22% of HBM roof; GEMM at 62% of BF16 roof |
| `analyze_findings` | PASS analyze_findings — 5 planted problems found; tensor-core kernels correctly not flagged |
| `render_report` | PASS render_report — report renders with all findings |
