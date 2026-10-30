# Lab 22 — Attribute a Cross-Layer Training Regression

## 1. Goal and the real-world task it mirrors

Monday morning, the Training Infra dashboard for Halcyon AI's W-TRAIN ablation sweep on ORION-256
shows mean step time up about 23 % since the weekend change window CW-2026-10-12. Four teams changed
something in that window (a driver upgrade on half the nodes, a scheduler placement policy, a dataset
storage-tier move, and a container rebuild), and an ECC alert started firing on `orion-n13` the same
morning. Every team believes its own change is innocent. (The sweep uses all 32 nodes, including
`orion-n25`..`n32`, because the 8 inference nodes were lent to training for the sweep, as
REFERENCE_CLUSTER.md allows.)

Your job is the job of the performance engineer on point: clean the evidence, build the hypothesis
tree, compute per-factor evidence from the natural experiment the sweep provides, attribute the
regression in seconds per step, rank the next discriminating tests by information value, cost, and
risk, and write the before/after report that separates **measured facts**, **inferred causes**, and
**remaining uncertainty** (manuscript Section 22.9).

## 2. Tier and realism boundary

**Tier L1.** Pure Python on a laptop, < 10 s. The bundle is **[SIMULATED]**, produced by
a seeded generator (seed 2214; instructor copy only, not shipped to learners). It mimics what a training-loop logger, Slurm placement records,
a node inventory, DCGM/host exporters, and an alert manager would give you. It cannot show real NCCL,
RDMA, PCIe, or storage behaviour; effect sizes are teaching values, not product claims. The L2/L3
extensions (Section 8) show how to confirm the inferred causes on real hardware.

## 3. Setup

```bash
cd book/part-5-production-operations/ch22-cross-layer-performance-engineering/lab
python -m pip install -r ../../../../requirements.txt     # numpy, pandas, pyyaml
python check.py                                           # progress meter on starter/regression_lab.py
```

Python 3.10+. Edit only `starter/regression_lab.py`.

## 4. Background you need

- Step-time anatomy and per-layer evidence: manuscript Sections 22.1–22.2.
- Hypothesis trees and test ranking: Section 22.3.
- Natural experiments, confounding, and attribution: Section 22.4.
- Benchmark noise and minimum detectable effect: Section 22.6.
- Anti-patterns (survivorship bias, warm-up contamination, mean vs median): Section 22.8.
- Before/after report format: Section 22.9.

### The bundle (`data/`)

| File | What it is | Grain |
|---|---|---|
| `jobs.csv` | Slurm accounting extract: period, start, final status, steps logged, dataset tier, node list | 48 jobs |
| `step_log.csv` | Training-loop logger: `step_time_s`, `data_wait_s` (time the loop blocked on the dataloader) | job × step |
| `placement.csv` | Rank → node, local GPU, `tp_group`, `pp_stage`, `dp_replica` | job × rank |
| `node_inventory.csv` | **Current** node state: rack, block, driver branch, peer-memory module loaded | node |
| `node_metrics.csv` | Per job-node summaries: SM active, backend tx GB/s, CPU iowait, host bounce-copy GB/s, ECC SBE count, GPU temperature | job × node |
| `alerts.csv` | Alerts around the window | alert |
| `change_log.yaml` | The changes made in CW-2026-10-12 | change |
| `hypotheses.yaml` | Candidate discriminating tests: info value, cost, risk, environment | test |
| `nccl_init_sample.log` | Illustrative NCCL INFO init excerpts from two jobs | lines |

Data-hygiene rules for this lab (they are the rules your team's benchmark policy states; apply them
before computing anything):

1. A step is identified by `(job_id, step)`; the analysis uses at most one row per step (keep the
   first occurrence).
2. Steps `0–9` are warm-up and are excluded (`WARMUP_STEPS = 10`).
3. Every job listed in `jobs.csv` is part of the population, whatever its final status.
4. Statistics are **job-weighted**: compute each job's post-warm-up mean, then average across jobs.

## 5. Tasks

| # | Function | Acceptance criterion (checked by `check.py`) |
|---|---|---|
| 1 | `clean_steps` | Unique per `(job_id, step)`, no step < 10; the row count matches the reference |
| 2 | `tp_split_jobs` | Exactly the set of jobs whose tensor-parallel (TP) groups span more than one node |
| 3 | `job_factor_table` | 48 rows; five 0/1 factors (`after`, `tp_split`, `driver_new`, `storage_new`, `alert_node`) plus `tp_x_storage = tp_split × storage_new`, with correct exposure counts; every job present with its usable step count |
| 4 | `regression_summary` | Job-weighted mean and median change, before → after |
| 5 | `estimate_effects` | OLS effects (s/step) for the six model terms (`TERMS`: five factors + the interaction predicted by the dataloader-slack model, manuscript Section 22.10.4) with standard errors and R² |
| 6 | `attribute` | Per-term contribution (s) and share (%), interaction as its own row; contributions sum to the observed delta; share SEs from classical and HC3-robust coefficient SEs |
| 6b | `bootstrap_shares` | Job-level bootstrap (resample jobs within each period; drop rank-deficient designs): 95 % interval of each share; the common-shift share's interval contains its point estimate |
| 7 | `storage_crosscheck` | Directly measured data-wait delta (after period, TP-packed jobs, capacity minus hot) agrees with the inferred storage effect |
| 8 | `rank_tests` | Tests ranked by `info_value / (cost_hours × risk_multiplier)` (low 1, medium 2, high 5); high-risk production tests rejected, not ranked; ties broken by test ID |
| 9 | `render_report` | Markdown report with `## Measured facts`, `## Inferred causes`, `## Remaining uncertainty`, in that order, naming the headline percentage and the alerted node's verdict |

Hints: build the factor flags from the *evidence*, not from the change log's intent. Ask of every join
"was this attribute true when the job ran?" A factor that looks harmless in a simple before/after
difference can be confounded by another factor (Section 22.4) — that is why you fit all factors
together.

## 6. Running the checker

```bash
python check.py                    # starter: TODO/FAIL per check, exit 1
python check.py --impl solution    # instructor reference: all PASS, exit 0
python ../../../../scripts/validate_labs.py ch22   # from anywhere inside the repo
```

The checker prints one `PASS`/`FAIL`/`TODO` line per check with the value it got and what it expected.

## 7. Deliverable and grading rubric

Submit `starter/regression_lab.py`, the generated `report.md`
(`python starter/regression_lab.py --report report.md`), and a one-page hypothesis tree (Mermaid or
drawn) with your test ranking annotated.

| Task | Points |
|---|---|
| Data hygiene (tasks 1, 3 incl. population rule) — and a note of what each rule removed or kept | 15 |
| Factor derivation from evidence (tasks 2, 3) incl. time-aware joins | 15 |
| Regression summary and mean-vs-median interpretation (task 4) | 10 |
| Effect estimation with uncertainty (task 5) and an interaction check (Exercise O1-c) | 15 |
| Attribution table (task 6) and storage cross-check (task 7) | 15 |
| Hypothesis tree + test ranking with safety rejection (task 8) | 10 |
| Before/after report: facts vs inferences vs uncertainty, correct verdict on the alert (task 9) | 20 |
| **Total** | **100** |

## 8. Extensions (L2/L3, hardware-backed)

Only on nodes you are authorised to drain or reserve. **Safety:** never roll back drivers, change
placement policy, or restart jobs on shared production capacity to "test a hypothesis"; tests T5 and
T9 in `hypotheses.yaml` are rejected for exactly that reason.

**L2 — GPUDirect RDMA state on one upgraded node** (confirms the driver mechanism):

```bash
nvidia-smi --query-gpu=driver_version --format=csv,noheader
lsmod | grep -E 'nvidia_peermem|nv_peer_mem'      # peer-memory module present?
nvidia-smi topo -m                                # GPU<->NIC affinity (expect PIX for GPUi/NICi on HX8)
uname -r; ofed_info -s 2>/dev/null                 # kernel and RDMA stack: needed to judge DMA-BUF support
```

A single node exercises NVLink, not the NIC path, so it cannot show GDR in use. What L2 establishes is
the *precondition*: the peer-memory module is absent, and (from your vendor's compatibility matrix) the
kernel/driver/RDMA-stack combination does or does not support DMA-BUF. DMA-BUF can provide GPUDirect
RDMA without `nvidia_peermem`, so "module absent" means "no GDR" only where DMA-BUF is unavailable
`[VENDOR-SPEC, 2026-10]`. Record the manifest fields under `extensions[0].record`.

**L3 — controlled A/B for placement and GDR** (tests T6 and T7). `srun` launches of `all_reduce_perf`
need nccl-tests built with MPI support (`make MPI=1 MPI_HOME=<path>`) and a Slurm MPI plugin matching your
MPI (commonly `--mpi=pmix`); without it each task runs as an independent single-rank job.

```bash
# TP-packed reference: one 8-rank communicator inside one node's NVLink domain
srun --mpi=pmix -N1 --ntasks-per-node=8 --gpus-per-node=8 ./build/all_reduce_perf -b 64M -e 1G -f 2 -g 1 -w 20 -n 100
# TP-split analogue: the same 8 ranks placed 4 + 4 on two nodes, so the ring crosses the backend fabric
srun --mpi=pmix -N2 --ntasks-per-node=4 --gpus-per-node=4 ./build/all_reduce_perf -b 64M -e 1G -f 2 -g 1 -w 20 -n 100
# GDR effect: one R550 + one R570 node, compare busbw and the 'via NET/IB/x/GDRDMA' lines
NCCL_DEBUG=INFO srun --mpi=pmix -N2 --ntasks-per-node=8 ./build/all_reduce_perf -b 8 -e 4G -f 2 -g 1 -w 20 -n 100 \
  2>&1 | grep -E 'via NET/IB/[0-9]+(/GDRDMA)?'      # '/GDRDMA' suffix = GDR in use
```

Repeat each configuration ≥ 5 times on an otherwise idle fabric segment, report median and min/max of
`busbw` at 64 MiB (the TP all-reduce size in Section 22.10) and at 1 GiB, and record the manifest
fields under `extensions[1].record`. A laptop result never substitutes for these measurements.

## 9. Intentionally flawed inputs

The bundle contains planted flaws that teach diagnosis. They are documented for instructors in
`../solutions/exercises-key.md` (Lab key). Do not look before you finish.
