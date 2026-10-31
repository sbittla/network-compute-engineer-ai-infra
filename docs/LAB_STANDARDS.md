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

## 6. Containers

Every package (24 chapters and 8 capstones) runs in its own Docker image, built from
[`docker/lab.Dockerfile`](../docker/lab.Dockerfile). The image holds that one package, the pinned
runtime ([`docker/requirements.lock`](../docker/requirements.lock), Python 3.13.1) and the test harness
([`docker/harness/`](../docker/harness/)). No package depends on another one or on the network.

| Image | Contents | Default command |
|---|---|---|
| `ai-infra-lab:<id>` (instructor/CI) | full package | `pytest /opt/harness/test_package.py` (the package test suite) |
| `ai-infra-lab:<id>-learner` | solutions, review, instructor files and generators stripped | the lab checker against `starter/` |

```bash
python scripts/docker_labs.py ci                # build every image first, then run every test suite
python scripts/docker_labs.py build ch09        # one package
python scripts/docker_labs.py test ch09
python scripts/docker_labs.py outputs ch09      # regenerate committed outputs (then build + test again)
docker run --rm -it --network none -v "$PWD/lab/starter:/work/pkg/lab/starter" ai-infra-lab:ch09-learner
```

Tests run with `--network none`, 2 GB memory and 2 CPUs. Results go to `build/test-results/<id>/junit.xml`
and `build/test-results/summary.md`. CI runs the same `ci` command on every push
([`.github/workflows/labs.yml`](../.github/workflows/labs.yml)).

The package test suite checks the following:

- the `check.py` contract: the solution passes; the starter fails without a traceback; the solution still
  passes with `tools/` removed;
- golden lab reports: `solutions/lab/outputs/check_{solution,starter}.txt` (capstones:
  `instructor/outputs/`) must equal a fresh run once timings and temp paths are normalized;
- every exercise folder (Section 7): structure, prompt in sync with `exercises.md`, and outputs that
  regenerate exactly.

## 7. Exercise folders

Every exercise in a chapter's `exercises.md` has one learner folder and one instructor folder with the
same name, `<ID>-<slug>`. Examples: `K1-roles`, `W2-incast-feedback`, `3.4-numa-placement`.

```text
chNN-*/exercises/README.md                 index: ID, title, type, ★, tier, kind, link; "Exercise count: N"
chNN-*/exercises/<ID>-<slug>/README.md     prompt (verbatim between <!-- prompt:start --> / <!-- prompt:end -->;
                                           relative link targets re-based to work from this folder),
                                           what to submit, where the evidence goes
chNN-*/exercises/<ID>-<slug>/outputs/      the learner's outputs (empty, .gitkeep)
chNN-*/solutions/exercises/<ID>-<slug>/    INSTRUCTOR ONLY (stripped from the student release)
    meta.yaml                              id, title, folder, type, difficulty, tier, kind, points,
                                           evidence_required, marking[{criterion, points}], lab_checks[]
    solution/answer.md                     full worked solution: method, numbers with units, evidence labels
    solution/solve.py                      kind: computed only; deterministic, runnable, asserts the key's answer
    outputs/                               GENERATED by `docker_labs.py outputs`; committed; compared in CI
        marking.json                       every exercise: the marking scheme from meta.yaml
        result.json, result.md, ...        kind: computed (written by solve.py --out DIR)
        lab_checks.json                    kind: lab (the named lab checks and their PASS lines)
```

| `kind` | Use it for | Tested by |
|---|---|---|
| `computed` | Any exercise with a numeric or algorithmic answer (worked problems, sizing, arithmetic knowledge checks, models) | `solve.py` re-runs in the container; its assertions encode the answer key; outputs must match the committed files |
| `lab` | Exercises completed by doing the lab (hands-on, many outline exercises) | the listed `lab_checks` must PASS in the solution report |
| `written` | Conceptual, troubleshooting reasoning, design defence, reflection | `answer.md` and the marking scheme exist; points add up |

`solve.py` contract:

- Usage is `python solve.py --out DIR`. It uses only the pinned runtime: stdlib, numpy, pandas and PyYAML.
- It reads inputs only from the prompt's stated parameters (as named constants, with their source) or from
  its own package's `lab/data/`, located as `Path(__file__).resolve().parents[4] / "lab" / "data"`.
- Its output is deterministic: no clock, no randomness without a fixed seed, sorted JSON keys, and
  rounded floats.
- It writes `result.json` (inputs, intermediate steps, answer, units, evidence label) and `result.md`
  (the human-readable working).
- It `assert`s the final answer against the value in `solutions/exercises-key.md`, within a stated
  tolerance. When the key is wrong, fix the key; never fix the assertion to match a wrong key.

Pitfalls found while building the exercise solvers:

- PyYAML parses `70.0e9` (an exponent with no sign) as a **string**; write `70.0e+9`, or wrap the value in
  `float()`. Several lab YAML files rely on `float()` in the readers.
- The pinned runtime has no matplotlib. A solver that "plots" writes the plot data as CSV, and the answer
  describes the expected figure.
- In `lab_checks`, a check name may be given with or without the trailing colon some checkers print
  (`"bom_counts:"` or `bom_counts`). Quote names that end in a colon, or YAML reads them as a mapping.

## 8. L2 extensions on a real GPU (with CPU fallback)

Packages whose L2 extension can be exercised on one GPU host provide `lab/l2/experiment.py`
(capstones: `starter-kit/l2/experiment.py`). It runs in the package's GPU image
([`docker/gpu.Dockerfile`](../docker/gpu.Dockerfile): PyTorch 2.5.1 + CUDA 12.4) through the shared
runtime [`docker/hwlab/`](../docker/hwlab/):

```bash
python scripts/hw_labs.py build ch13
python scripts/hw_labs.py run ch13 --device gpu      # measure on the GPU  -> lab/l2/results/gpu-<model>/
python scripts/hw_labs.py run ch13 --device cpu      # CPU fallback        -> lab/l2/results/cpu-fallback/
python scripts/hw_labs.py test ch13                  # quick run now + committed-evidence checks
python scripts/hw_labs.py evidence                   # full GPU then CPU runs for every package, serially
```

- **Device selection:** `--device auto` uses the GPU when one is visible and falls back to the CPU otherwise.
  The same experiment always runs. Without a GPU it executes its documented `cpu_fallback` (for example,
  a host-memory copy sweep in place of PCIe transfers). Its report says so, and the GPU-only invariants are
  skipped.
- **The evidence bundle** is `environment.json` (the filled-in manifest: GPU, driver, CUDA, PCIe link,
  CPU, OS), `results.json` (raw repetitions, summary statistics, status, invariants) and `report.md`. It
  is `[MEASURED]` on the hardware named in it. Re-run on your own hardware; never compare a laptop GPU's
  numbers with H100-class figures without saying so.
- **Invariants:** `check()` encodes physical facts the measurement must respect. Examples: bandwidth
  stays below the negotiated PCIe link; pinned memory is no slower than pageable; achieved TFLOP/s stays
  below the device peak. A run that breaks an invariant fails.
- **Absent hardware:** an extension that needs something the host lacks (RDMA NIC, BMC, NVLink, a second
  GPU or node) probes for it. When the hardware is missing, it records `status: not-runnable` with what is
  missing, and runs its fallback analysis. It is never faked.
- **Benchmark discipline (section 5):** 3 warm-ups and ≥ 5 timed repetitions; report the median, p95 and
  spread. GPU runs are serial. `--quick` mode (small sizes, 5 repetitions) is for CI and smoke tests, and
  is never committed as evidence.
- **L3 (multi-node RDMA):** these extensions cannot run on a single host. Their status and requirements are
  tracked in [HARDWARE_RUNS.md](HARDWARE_RUNS.md).
