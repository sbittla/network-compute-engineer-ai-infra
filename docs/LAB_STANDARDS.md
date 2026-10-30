# Lab Standards

## 1. Tiers

| Tier | Environment | What it can prove | What it cannot prove |
|---|---|---|---|
| **L1** | Laptop or cloud VM; Python 3.10+, `requirements.txt`; no GPU, no root | Reasoning, modeling, parsing, diagnosis on supplied/synthetic data, automation logic, design | Any physical performance of GPUs, NICs, switches, RDMA, NVLink |
| **L2** | One GPU host (local or cloud), optionally containers/Kubernetes-in-Docker/Slurm-in-container | Single-node GPU behaviour, profiling, intra-node collectives, real host inventory | Multi-node fabric behaviour, RDMA congestion, rail alignment at scale |
| **L3** | ≥ 2 multi-GPU nodes with RDMA (RoCEv2 or InfiniBand) and access to switch counters | Multi-node collectives, GPUDirect RDMA, congestion behaviour, physical-layer counters | Behaviour at hyperscale (thousands of GPUs) unless actually run there |

Every lab is **runnable at L1**. L2/L3 variants are *extensions* with exact commands to run on real
hardware and an explicit list of what to record.

## 2. Determinism and datasets

- Synthetic data is produced by `lab/tools/generate_*.py` with a fixed seed and committed to `lab/data/`.
  Regenerating must produce byte-identical files.
- Datasets include **intentionally planted anomalies** (documented only in `solutions/`) so that labs
  teach diagnosis, not just happy paths.
- Generators encode the planted faults, so they are **instructor material**.
  `scripts/make_student_release.py` strips `lab/tools/` and `starter-kit/tools/`.
  - Any `check.py` check that regenerates data must report `SKIP` (not FAIL) when the generator is absent.
  - Learner-facing READMEs and chapter-card file maps must not tell learners to read or run the
    generator. Mention it only as "instructor copy only".
  - `python scripts/validate_labs.py` enforces this: it also runs `--impl solution` on a copy with
    `tools/` removed (the `no-generator` column), which must pass.
  - Generator comments should not be the only record of the answers. Keep the planted-fault list in `solutions/`.
- Keep each lab's `data/` under 2 MB.

## 3. Environment manifest (`lab/manifest.yaml`)

```yaml
lab: ch07-fabric-design
tier: L1
python: ">=3.10"
dependencies: [numpy, pandas]
hardware_assumptions: "None. Uses synthetic data modeled on ORION-256 (docs/REFERENCE_CLUSTER.md)."
data_generation: {script: tools/generate_data.py, seed: 7}
evidence_class: SIMULATED   # MEASURED | MODELED | SIMULATED
runtime_budget_seconds: 60
extensions:
  - tier: L3
    requires: "2+ nodes with RoCEv2 NICs and switch CLI access"
    record: [nic_firmware, driver_version, switch_os_version, topology, mtu, run_count]
```

Learners running an L2/L3 extension copy this file and fill in the real values for their environment
(software versions, firmware, topology, number of runs, warm-up policy).

## 4. `check.py` contract

See [CHAPTER_TEMPLATE.md](CHAPTER_TEMPLATE.md#1-folder-layout). Summary:

- `--impl solution` → imports `../solutions/lab/`, exit 0.
- `--impl starter` (default) → imports `starter/`, never crashes, exits non-zero while TODOs remain.
- Pure Python, no network access, no hardware, < 60 s, deterministic.
- Starter functions that are unimplemented raise `NotImplementedError`; the checker reports them as
  `TODO` rather than crashing.

## 5. Benchmark discipline (applies to every L2/L3 measurement)

Record: environment manifest; workload definition; warm-up policy; repetitions (≥ 5, more for noisy
metrics); report median and p95/p99 with spread (IQR or min/max); concurrency; input sizes; what changed
between runs (one variable at a time); and whether each value is measured or modeled.
