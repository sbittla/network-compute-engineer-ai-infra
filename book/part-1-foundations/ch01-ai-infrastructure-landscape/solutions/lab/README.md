# Chapter 1 Lab — Reference Solution and Planted Flaws (INSTRUCTOR ONLY)

`workload_model.py` in this folder is the reference implementation; `python ../../lab/check.py
--impl solution` exits 0. Run `python workload_model.py` here to print the full report.

## Planted flaws and why they are there

| Row | Planted flaw | What a naive analysis does | Correct handling | Real-world cause it teaches |
|---|---|---|---|---|
| W13 `vision-train-vit` | `hbm_gb_per_gpu` blank | Treats blank as 0 and calls the job communication- or compute-bound on incomplete data | `MISSING`, reject | Profile exported from a notebook that never ran the memory profiler |
| second `W05` (`moe-a2a-train-step-rerun`) | Duplicate workload ID | Double-counts the workload in capacity totals | `DUPLICATE`, keep first | Rerun pasted into the shared sheet without a new ID |
| W15 `eval-harness` | `io_read_gb_per_node = -2` | Produces a negative time that never dominates; silently ignored | `NEGATIVE`, reject | Counter wraparound or a subtraction of counter snapshots in the wrong order |
| W18 `bert-serving` | `net_unit = Gbps` (a rate, not a volume) | Divides a rate by a rate and gets a dimensionless "time" | `BAD_UNIT`, reject | Number copied from a NIC dashboard showing throughput, not bytes per step |
| W11 `dp-allreduce-bench-16node` | NIC volume given as 80 **Gb** | Reads 80 GB → 1.6 s lower bound > 0.247 s observed → wrongly `IMPOSSIBLE` | Convert: 80 / 8 = 10 GB → 0.2 s, ceiling fraction 0.81, communication-bound | Switch dashboards report bits; host tools report bytes |
| W12 `kv-transfer-disagg` | 40 GB through one 400G NIC in 0.49 s | Accepts it and reports a heavily loaded but valid workload | `IMPOSSIBLE`: implies ≈ 81 GB/s > 50 GB/s line rate | Host counter summed TX + RX, or aggregated two NICs |
| W16 `llm70b-decode-b1-eager` | Valid data; ceiling fraction ≈ 0.21 | Calls it memory-bound and proposes more HBM bandwidth | Memory is the largest bound but `LATENCY_OR_OVERHEAD`: launch overhead and per-all-reduce latency dominate | Batch-1 eager-mode decode (no CUDA graphs); fix is software, not hardware |
| W05 `moe-a2a-train-step` | Declared `compute`; actually scale-out bound (1.20 s vs 0.49 s compute) | Trusts the label | `MISLABELED` | Teams label by model type, not by evidence |
| W09 `tp16-cross-node-train` | Declared `compute`; TP group spans nodes, scale-out 0.76 s vs compute 0.26 s | Trusts the label | `MISLABELED` | Same failure as manuscript Section 1.11: TP placed across nodes |

## Reference output (classification)

```text
| id  | bound         | dominant | lower bound | observed  | fraction | flags               |
| W01 | compute       | compute  | 6.95 s      | 17.30 s   | 0.40     |                     |
| W02 | memory        | memory   | 6.02 ms     | 9.69 ms   | 0.62     |                     |
| W03 | compute       | compute  | 36.30 ms    | 74.59 ms  | 0.49     |                     |
| W04 | compute       | compute  | 2.78 s      | 3.55 s    | 0.78     |                     |
| W05 | communication | scaleout | 1.20 s      | 1.73 s    | 0.69     | MISLABELED          |
| W06 | io            | io_write | 12.24 s     | 13.07 s   | 0.94     |                     |
| W07 | io            | io_read  | 2.00 s      | 2.37 s    | 0.85     |                     |
| W08 | memory        | memory   | 4.81 ms     | 6.31 ms   | 0.76     |                     |
| W09 | communication | scaleout | 760.00 ms   | 1.06 s    | 0.72     | MISLABELED          |
| W10 | compute       | compute  | 121.33 ms   | 162.25 ms | 0.75     |                     |
| W11 | communication | scaleout | 200.00 ms   | 247.20 ms | 0.81     |                     |
| W12 | communication | scaleout | 800.00 ms   | 492.34 ms | 1.62     | IMPOSSIBLE          |
| W16 | memory        | memory   | 5.25 ms     | 25.02 ms  | 0.21     | LATENCY_OR_OVERHEAD |
| W17 | communication | scaleout | 12.00 ms    | 18.22 ms  | 0.66     |                     |
```

Observed times carry seeded ±2 % jitter, so they differ slightly from the manuscript's round numbers
(e.g., W01 17.30 s vs 17.4 s). Note W06: the per-node write ceiling for a 32-node job is min(50, 80 /
32) = 2.5 GB/s, so 30.6 GB per node needs 12.24 s: the same 12.25 s as manuscript Section 1.7.

## Marking notes for Task 5 (data-quality note)

Full marks require every row above with (a) the flaw, (b) a plausible real-world cause, (c) an owner
to ask (workload team, observability team, platform team). Award half marks for W16 if the learner
flags it but proposes a hardware fix. Common mistakes: rejecting W11 instead of converting it;
"fixing" W12 by halving the number without asking the owner; deleting the first W05 instead of the
second.
