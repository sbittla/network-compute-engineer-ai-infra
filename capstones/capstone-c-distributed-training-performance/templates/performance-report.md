# W-TRAIN Scaling Performance Report — <fill: author>, <fill: date>

> Master document for Capstone C. Every section is required. Label every number `[MEASURED]`,
> `[MODELED]`, `[SIMULATED]`, `[ILLUSTRATIVE]` or `[VENDOR-SPEC, YYYY-MM]`. Link the other templates.

## 0. Summary (≤ 150 words)

<fill: what was slow, why, what fixed it, by how much (with CI), and what did not help.>

## 1. Problem statement

- Symptom as reported: <fill>
- Question this report answers: <fill>
- Success criteria: <fill: e.g., weak-scaling efficiency ≥ 0.95 at 256 GPUs, shown with ≥ 4 admissible runs per point and a stated CI>

## 2. Architecture and data path

<fill: Mermaid diagram of one DP gradient all-reduce hop on ORION: GPU → (NVLink inside the TP group)
→ PCIe switch → NIC on the same rail → rail leaf → peer NIC → peer GPU. Then the baseline's actual
path: GPU → host memory bounce → frontend NIC (TCP socket) → frontend fabric. Caption both.>

## 3. Assumptions

See [assumptions-register.csv](assumptions-register.csv).

## 4. Implementation and simulation boundary

| Artifact | Evidence class | What it can show | What it cannot show |
|---|---|---|---|
| CPU-proxy harness | `[MEASURED]` on <fill: laptop model> | Harness discipline, ring-algorithm correctness | Anything about GPUs, NVLink, NICs, NCCL |
| Supplied run logs | `[SIMULATED]` | <fill> | <fill> |
| L2/L3 runs (if any) | `[MEASURED]` | <fill> | <fill> |

## 5. Reproducible benchmark harness

See [benchmark-plan.md](benchmark-plan.md) and [environment-manifest.yaml](environment-manifest.yaml).
Include one harness result (JSON) and explain each field.

## 6. Test plan

See [benchmark-plan.md](benchmark-plan.md) §3.

## 7. Results

### 7.1 Admissibility

| run_id | Reason excluded | Evidence | Effect on the conclusion if included |
|---|---|---|---|
| <fill> | | | |

### 7.2 Scaling-efficiency analysis

See [scaling-analysis.md](scaling-analysis.md) and [results-table.csv](results-table.csv).

### 7.3 Profiler evidence

See [profiler-evidence.md](profiler-evidence.md).

## 8. Root-cause narrative

See [root-cause-narrative.md](root-cause-narrative.md).

## 9. Failure analysis

<fill: how this defect could recur (new node pool, new image, new device plugin), how it would be
detected automatically (e.g., a preflight that fails the job when NCCL reports `Using network Socket`
on a backend-attached job), and what else in the stack fails silently into a slow path.>

## 10. Security considerations

<fill: RDMA device exposure to containers (which pods may request RDMA devices; privileged vs device
plugin), profiler captures that contain hostnames and job metadata, benchmark jobs on shared fabrics.>

## 11. Final engineering review

See [final-engineering-review.md](final-engineering-review.md).
