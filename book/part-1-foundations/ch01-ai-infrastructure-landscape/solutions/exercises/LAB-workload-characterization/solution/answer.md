# LAB — Workload-characterization lab: reference solution

Reference implementation: `solutions/lab/workload_model.py`; planted flaws: `solutions/lab/README.md`;
rubric: `lab/README.md` Section 7. The ceiling model is manuscript Section 1.6; W01 and W02 are the
Section 1.9 worked example. Evidence class `[MODELED]` over `[ILLUSTRATIVE]` synthetic profiles.

## Expected checker result

`python check.py --impl solution` prints 9/9 PASS (the committed report is
`solutions/lab/outputs/check_solution.txt`). In the student edition `dataset_reproducible` prints SKIP
because the generator in `lab/tools/` is stripped; that does not count against the learner.

## Key results the implementation must reproduce

- Validation: 4 rows rejected (W13 `MISSING`, second W05 `DUPLICATE`, W15 `NEGATIVE`, W18 `BAD_UNIT`),
  14 clean rows.
- Normalization: W11's 80 Gb → 10 GB, so its scale-out bound is 0.2 s (fraction 0.81), *not* 1.6 s.
- Lower bounds: W01 compute 6.95 s and scale-up 2.67 s; the per-node I/O ceiling is
  min(frontend 50 GB/s, PFS aggregate / nodes in the job), for example 80 / 32 = 2.5 GB/s for W06's
  32-node checkpoint write (30.6 GB per node → 12.24 s, the 12.25 s of Section 1.7).
- Flags: `IMPOSSIBLE` = W12 (fraction 1.62); `LATENCY_OR_OVERHEAD` = W16 (fraction 0.21 < 0.25);
  `MISLABELED` = W05 (scale-out 1.20 s vs compute 0.49 s) and W09 (TP across nodes, scale-out 0.76 s vs
  compute 0.26 s).

## Model data-quality note

| Row | Flaw | Probable real-world cause | Owner to ask |
|---|---|---|---|
| W13 | `hbm_gb_per_gpu` blank → reject | Profile exported before the memory profiler ran | Workload team |
| W05 (second) | Duplicate ID → reject, keep first | Rerun pasted into the shared sheet without a new ID | Workload team / sheet owner |
| W15 | `io_read_gb_per_node` = −2 → reject | Counter wraparound or snapshots subtracted in the wrong order | Observability team |
| W18 | `net_unit` = `Gbps` (a rate) → reject | Throughput copied from a NIC dashboard instead of bytes per step | Workload team |
| W11 | 80 Gb → 10 GB, valid | Switch dashboards report bits, host tools bytes | None: converted, noted |
| W12 | 40 GB in 0.49 s ≈ 81 GB/s > 50 GB/s → `IMPOSSIBLE` | Host counter summed TX + RX, or two NICs aggregated | Observability team |
| W16 | Fraction 0.21 → `LATENCY_OR_OVERHEAD` | Batch-1 eager-mode decode, no CUDA graphs; fix in software | Inference team |
| W05 | Declared compute, actually scale-out → `MISLABELED` | Labelled by model type, not by evidence | Workload team |
| W09 | Declared compute, TP spans nodes → `MISLABELED` | TP group placed across nodes (the Section 1.11 failure) | Training Infra / Platform |

## Grading notes

Award the computational part of Tasks 1–3 from the checker. For Task 4, the comparison must name the
dominant bound and ceiling fraction of both workloads and the confirming telemetry (Table 1.7). For Task
5, full marks need every row above with flaw, cause and owner; half marks for W16 if a hardware fix is
proposed. **Common mistakes:** rejecting W11 instead of converting it; "fixing" W12 by halving it without
asking the owner; deleting the first W05 instead of the second; treating a blank as zero.
