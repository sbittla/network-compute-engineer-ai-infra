# Lab 23 — Capstone Design-Review Linter

## 1. Goal and the real-world task it mirrors

Before a design review spends an hour of six senior engineers' time, someone should already have
caught the mistakes a script can catch: a GPU count that does not add up, a leaf switch with more
cables than ports, a rack whose nodes draw more than its PDUs can deliver, a "measured" number with
no environment manifest. Mature infrastructure teams automate exactly this pre-review pass: as a CI
job on the design repository, as a linter for capacity plans, or as a form that refuses to submit.

In this lab you implement `design_lint.py`, a linter for a capstone design bundle, and run it on:

- `data/bundle_orion_reference/`: a consistent ORION-256 design. A correct linter reports **zero**
  findings. This bundle is your false-positive control.
- `data/bundle_kestrel_capA/`: a Capstone A submission from the fictional learner team "Kestrel".
  It reads well and most numbers are right, but it contains planted completeness and consistency
  flaws of exactly the kinds that derail real design reviews.

The output is a Markdown lint report with a gate verdict (`PASS` only with zero blocker and zero
major findings) that you attach to your own capstone design review (manuscript Section 23.6).

## 2. Tier and realism boundary

**Tier L1.** Pure Python on supplied YAML/Markdown. The bundles contain `[MODELED]` and
`[ILLUSTRATIVE]` values derived from [REFERENCE_CLUSTER.md](../../../../docs/REFERENCE_CLUSTER.md).
The linter checks *internal consistency and evidence hygiene*; it cannot tell you whether a
consistent design is a *good* design, and it cannot validate any physical number. A bundle that
passes the linter is ready for human review, not approved.

## 3. Setup

```bash
cd book/part-6-applied-engineering/ch23-capstone-production-ai-cluster/lab
python --version                       # 3.10 or newer
pip install -r ../../../../requirements.txt
python check.py                        # progress meter on starter/design_lint.py
```

## 4. Background you need

- Manuscript Section 23.2 (assumptions register) and Section 23.4 (consistency arithmetic).
- Section 23.5 (failure-domain analysis) and Section 23.7 (benchmark evidence and labels).
- The evidence-label vocabulary in [STYLE_GUIDE.md §3](../../../../docs/STYLE_GUIDE.md).

### Bundle format

| File | Content | Key fields |
|---|---|---|
| `design.md` | Narrative design document | Seven `##` sections: Problem statement, Assumptions, Architecture, Failure domains, Benchmark evidence, Failure exercise, Next-step backlog |
| `assumptions.yaml` | Assumptions register + workload | `assumptions[]`: id, statement, value, unit, label, owner, validation; `workload`: total_gpus, parallelism {tp, pp, dp} |
| `bom.yaml` | Bill of materials | `gpu_nodes` {count, gpus_per_node, spares}, `total_gpus`, `node_power_kw` {max, sustained}, `racks` {budget_kw, gpu_racks{rack: nodes}}, `switches`, `cables.backend_400g` |
| `topology.yaml` | Backend/frontend fabric | `backend.rail_leaf` {count, radix, downlinks, uplinks, uplinks_per_spine}, `backend.spine` {count, radix}, `backend.claimed_oversubscription` |
| `failure_domains.yaml` | Failure-domain analysis | `domains[]`: id, class, scope, redundancy, mitigation, detection |
| `slos.yaml` | Service-level objectives | `slos[]`: id, name, sli, target, unit, window, source |
| `benchmarks.md` | Evidence table | columns id, metric, value, unit, label, tier, manifest |
| `manifests/*.yaml` | Environment manifests cited by MEASURED rows | the linter checks that a cited manifest exists (EVID-003); the reviewer reads its content. The reference bundle's L3 manifest is an ILLUSTRATIVE format template (ORION is fictional, so B-02 is labelled ILLUSTRATIVE); its L1 manifest records a real timing run (B-06) |

### Rule catalogue

| Rule | Severity | Fires when | Location format |
|---|---|---|---|
| COMP-001 | blocker | a bundle file is missing, or `design.md` lacks a required section | `<file>` or `design.md:<Section>` |
| COMP-002 | major | a required field is absent or empty | `<file>:<id>.<field>` |
| GPU-001 | blocker | (nodes − spares) × GPUs/node ≠ total GPUs | `bom.yaml:gpu_nodes` |
| GPU-002 | blocker | TP × PP × DP ≠ workload GPUs | `assumptions.yaml:workload.parallelism` |
| GPU-003 | major | nodes placed in racks ≠ BOM node count | `bom.yaml:racks.gpu_racks` |
| PORT-001 | blocker | leaf downlinks + uplinks > leaf radix | `topology.yaml:rail_leaf` |
| PORT-002 | major | claimed oversubscription ≠ downlinks : uplinks (tolerance 0.01) | `topology.yaml:claimed_oversubscription` |
| PORT-003 | blocker | leaves × uplinks per spine > spine radix | `topology.yaml:spine` |
| PORT-004 | major | rail-leaf downlinks ≠ GPU node count | `topology.yaml:rail_leaf` |
| CABLE-001 | major | BOM backend links ≠ leaves × (downlinks + uplinks) | `bom.yaml:cables.backend_400g` |
| POWER-001 | blocker | rack nodes × node **max** power > rack budget | `bom.yaml:racks.<rack>` |
| EVID-001 | major | benchmark row has no label | `benchmarks.md:<id>` |
| EVID-002 | major | label outside MEASURED / MODELED / SIMULATED / ILLUSTRATIVE / VENDOR-SPEC, YYYY-MM | `benchmarks.md:<id>` |
| EVID-003 | major | MEASURED without a manifest, or citing a manifest that is not in the bundle's `manifests/` | `benchmarks.md:<id>` |
| EVID-004 | major | MEASURED physical-performance unit (Gb/s, GB/s, TB/s, TFLOP/s, µs, ms, kW, W) at tier L1 | `benchmarks.md:<id>` |
| NUM-001 | major | a `design.md` line has a number with a unit but no inline label and no ID reference | `design.md:L<n>` |
| XREF-001 | major | `design.md` cites an A-/B-/FD-/SLO- ID that the bundle does not define | `design.md:<ID>` |
| FD-001 | major | failure domain with redundancy `none` and an empty mitigation | `failure_domains.yaml:<id>` |
| FD-002 | major | one of gpu, node, nic, rail_leaf, spine, rack_power, storage, scheduler is not analyzed | `failure_domains.yaml:<class>` |
| SLO-001 | major | SLO target is not a numeric threshold (`>= 0.99`, `<= 800`) | `slos.yaml:<id>.target` |

**Known limitation of EVID-004.** The rule is a heuristic over two declared fields: it fires only when
the label is MEASURED, the tier is `L1`, and the unit is in a fixed list of physical units. It
therefore misses a fabricated physical result expressed in a derived unit (%, ratio, "x faster") and
one whose tier is falsely declared `L2`/`L3` (EVID-003 still demands a manifest path, but the linter
cannot check the manifest's contents, or even that the cited file exists). Treat a clean EVID-004 as "no obvious laptop measurement", not
as proof that the evidence is physical; the reviewer still opens the manifest.

## 5. Tasks

All work is in `starter/design_lint.py`. The loaders, rule table, regular expressions and
`make_finding()` are provided; implement the functions marked TODO.

1. **Completeness (`check_completeness`).** Report missing files, missing `design.md` sections and
   missing required fields. *Acceptance:* the reference bundle is clean; the checker's
   `check_completeness` line passes.
2. **Capacity arithmetic (`check_capacity`).** GPU-001/002/003. *Acceptance:* you can state, for the
   Kestrel bundle, the node count, GPU count and parallelism product that disagree.
3. **Fabric arithmetic (`check_fabric`).** PORT-001..004 and CABLE-001. *Acceptance:* a correctly
   specified 3:1 leaf (48 down, 16 up) produces no findings; Kestrel's rail leaf does.
4. **Rack power (`check_power`).** POWER-001 using node *max* power. *Acceptance:* a rack exactly at
   budget passes; any rack over budget is reported once.
5. **Evidence hygiene (`check_evidence`, `check_unlabeled_numbers`, `check_cross_refs`).**
   EVID-001..004, NUM-001, XREF-001. *Acceptance:* every unlabeled performance number and every
   dangling reference in `design.md` is reported with its line or ID.
6. **Failure domains and SLOs (`check_failure_domains`, `check_slos`).** FD-001/002, SLO-001.
7. **Gate and report (`run_lint`, `render_report`).** Sort blockers first; compute the gate;
   render Markdown. Then run the CLI:
   ```bash
   cd starter
   python design_lint.py ../data/bundle_kestrel_capA --out kestrel_lint.md
   python design_lint.py ../data/bundle_orion_reference
   ```
8. **Triage memo (written).** For each finding in the Kestrel report, write one line: is it a real
   design defect, a documentation defect, or a linter false positive? What is the minimal fix? Which
   finding would you raise first in the review meeting and why?

## 6. Running the checker

```bash
python check.py                    # your starter implementation
python check.py --impl solution    # instructors: reference implementation, must exit 0
```

Each line is `PASS`, `FAIL` or `TODO`. A `FAIL` line counts how many planted findings you found,
lists the missing and unexpected ones, and adds a hint for the commonest mistakes (for example,
sizing racks with sustained power, or flagging a declared-spares design as GPU-001). In the
instructor copy, a first `check_data_regenerates` line confirms the bundles match the generator; it
reports `SKIP` in the student release. The checker requires
the *exact* set of planted findings on the Kestrel bundle and *zero* findings on the reference
bundle: precision matters as much as recall, because a noisy linter is one teams switch off.

## Troubleshooting

- **`FAIL import  could not import starter implementation: ...`.** The error inside names the cause:
  `ModuleNotFoundError: No module named 'yaml'` means `python -m pip install -r
  ../../../../requirements.txt`; a `SyntaxError` means `python -m py_compile starter/design_lint.py`
  will show the line. Use Python 3.10 or newer.
- **`python starter/design_lint.py <bundle>` prints a `NotImplementedError` traceback.** The CLI calls
  `run_lint` and `render_report`, so it works only once every TODO function is implemented. Use
  `python check.py` until then.
- **A `FAIL` line lists "unexpected" findings.** That is a false positive: the reference bundle must
  give zero findings and Kestrel exactly the planted set. Read the `| hint:` text. The usual causes are
  ignoring declared spares (GPU-001), comparing rail-leaf downlinks with 32 instead of the BOM node
  count (PORT-004), flagging a no-redundancy domain that has a real mitigation (FD-001), not skipping
  headings and labelled or ID-referenced lines (NUM-001), and rejecting `VENDOR-SPEC, YYYY-MM` (EVID-002).
  "Missing" findings with a POWER-001 hint mean you sized racks with sustained instead of max power.
- **Your own capstone bundle gets COMP-001 on every section.** The headings must be exactly
  `## Problem statement` and so on. Numbered headings such as `## 1. Problem statement` do not match
  (see "Mapping your capstone to a lint bundle" in §7).
- **EVID-003 on a row that does cite a manifest.** The `manifest` cell must be the path inside the
  bundle, `manifests/<file>.yaml`, and that file must exist in the bundle's own `manifests/` folder.
- **`check_data_regenerates` FAILs** (instructor copy only). A file under `data/` was edited. Restore
  it with `git checkout -- data/`.

## 7. Deliverable and grading rubric

Submit `starter/design_lint.py`, `kestrel_lint.md`, and the triage memo (Task 8), plus the lint
report for **your own** capstone bundle.

| Task | Points |
|---|---|
| 1 Completeness | 10 |
| 2 Capacity arithmetic | 10 |
| 3 Fabric arithmetic | 15 |
| 4 Rack power | 10 |
| 5 Evidence hygiene | 20 |
| 6 Failure domains and SLOs | 10 |
| 7 Gate and report | 10 |
| 8 Triage memo (correct classification, minimal fixes, justified ordering) | 15 |
| **Total** | **100** |

### Mapping your capstone to a lint bundle

No capstone starter kit writes the linter's YAML bundle for you: the capstones produce CSV and Markdown
artifacts (registers, results tables, design documents), and only capstone A has a BOM and a topology.
To lint your own capstone (here and in exercise M1), assemble a bundle directory, for example
`exercises/M1-complete-capstone-track/outputs/bundle/`, and run your **completed**
`starter/design_lint.py` on it (the unmodified starter raises `NotImplementedError`).

**The linter has no waiver or "not applicable" mechanism.** Every rule runs on every bundle, and a
missing file is a COMP-001 *blocker*, so the gate fails. All seven files must exist:

| Bundle file | Rules that read it | Map from your capstone |
|---|---|---|
| `design.md` | COMP-001 (sections), NUM-001, XREF-001 | Your design document (A `design-pack.md`; B and D `design-doc.md`; E–H `design-document.md`; C `performance-report.md`). The headings must read exactly `## Problem statement`, `## Assumptions`, `## Architecture`, `## Failure domains`, `## Benchmark evidence`, `## Failure exercise`, `## Next-step backlog`. A numbered heading such as `## 1. Problem statement` does not match. Every line with a number and a unit needs an inline label (`[MODELED]`) or an ID reference (`A-03`, `B-02`, `FD-04`, `SLO-01`). |
| `assumptions.yaml` | COMP-002, GPU-002, XREF-001 | The assumptions register (A–D `assumptions-register.csv`; E–H the assumptions section of `design-document.md`): `id`, assumption → `statement`, `value`, `unit`, `evidence_label` → `label`, `owner`, `how_to_validate` → `validation`. IDs must be `A-` plus two digits. The optional `workload` block (`total_gpus`, `parallelism` {tp, pp, dp}) is checked by GPU-002 only when `parallelism` is present. |
| `benchmarks.md` | EVID-001..004, XREF-001 | Your results table, rewritten as one pipe table with columns `id \| metric \| value \| unit \| label \| tier \| manifest` and IDs `B-01`, `B-02`, … A `MEASURED` row must cite a file under the bundle's own `manifests/` folder (copy your filled `starter-kit/manifest.yaml` there); `SIMULATED` and `MODELED` rows need no manifest. |
| `failure_domains.yaml` | COMP-002, FD-001, FD-002, XREF-001 | Your failure analysis (A `failure-analysis.md`, G `failure-classification.md`, H `failure-scenarios.md`, or the failure-analysis section of your design document). FD-002 requires a domain for each of the eight classes `gpu`, `node`, `nic`, `rail_leaf`, `spine`, `rack_power`, `storage` and `scheduler`, whatever your track. |
| `slos.yaml` | COMP-002, SLO-001, XREF-001 | Your SLOs (D `slo-sli-spec.md`, H `phase-slos.md`; for other tracks, the acceptance targets in the brief written as SLOs). Each `target` must be a numeric threshold such as `'>= 0.99'`. |
| `bom.yaml` | GPU-001, GPU-003, POWER-001, PORT-004, CABLE-001 | Capstone A: `templates/bom.csv` and the power budget. Other tracks: the cluster your track runs on (below). |
| `topology.yaml` | PORT-001..004, CABLE-001 | Capstone A: `templates/topology-worksheet.md`. Other tracks: the cluster your track runs on (below). |

**Tracks without a BOM or topology (B–H).** You do not design hardware in these tracks, but your
results still run on a cluster. Describe that cluster in `bom.yaml` and `topology.yaml`. If it is
ORION-256 unchanged, copy both files from `data/bundle_orion_reference/`, which lint clean, and say in
`## Architecture` that they are inherited from the reference cluster. If your brief declares a different
cluster (for example capstone E's 40-node variation or capstone G's ORION-XL), write its counts and keep
the arithmetic consistent: rail-leaf downlinks equal `gpu_nodes.count`, and `cables.backend_400g` equals
leaves × (downlinks + uplinks). Leave out `racks.gpu_racks` or `cables` only if your brief gives no
values; GPU-003, POWER-001 and CABLE-001 then have nothing to check. Do not hand in empty `bom.yaml` or
`topology.yaml` files. They also lint clean, because the arithmetic compares zeros with zeros, so a PASS
on them proves nothing and a reviewer treats them as missing.

**Waivers are written by you, not by the linter.** If a finding remains that you judge does not apply
(for example FD-002 for a class your track's scope excludes), the generated report still says
`Gate: FAIL`. Add a `## Waivers` table after the generated report in your lint report, with one row per
remaining finding: rule, location, reason, and the artifact that covers the risk instead. M1 accepts
either `Gate: PASS` or a FAIL whose every finding has a waiver row.

## 8. Extensions (L2/L3): replace modeled rows with measured ones

The linter only checks that evidence is *labelled*; the extension makes some of it *real*. Work on
dedicated lab hardware only: never on a shared production fabric (**Safety:** see Section 23.8).

**L2 (one GPU host).** Validate node-level assumptions in your own bundle:

```bash
nvidia-smi --query-gpu=index,name,memory.total,power.limit --format=csv   # A-01/A-02/A-03 class
nvidia-smi topo -m                                                        # GPU-NIC affinity
lscpu | grep -i numa ; numactl --hardware                                 # NUMA layout
ibv_devinfo | grep -E "hca_id|fw_ver|active_mtu|state"                    # NIC firmware, MTU (A-10)
sudo ipmitool dcmi power reading                                          # node power under load
```

Run the node power reading during a sustained GPU load (for example the burn-in from Chapter 16) and
record the peak over at least 10 minutes. Replace the `[VENDOR-SPEC, YYYY-MM]` node power in your BOM with the
measured value *and* keep the vendor maximum for rack budgeting; note both in the assumptions register.

**L3 (2+ nodes with RDMA).** Produce a real `B-02`-style row:

```bash
# nccl-tests must be built with MPI support for multi-process runs: make MPI=1 MPI_HOME=/path/to/mpi
# One rank per GPU, 16 ranks over 2 nodes; warm-up iterations discarded by -w
mpirun -np 16 -H nodeA:8,nodeB:8 -x NCCL_DEBUG=INFO \
  ./build/all_reduce_perf -b 1M -e 8G -f 2 -g 1 -w 5 -n 20
# Under Slurm instead of mpirun (requires Slurm built with PMIx support):
srun --mpi=pmix -N2 --ntasks-per-node=8 --gpus-per-node=8 \
  ./build/all_reduce_perf -b 1M -e 8G -f 2 -g 1 -w 5 -n 20
```

Repeat at least 5 times and report the median and min/max of the 8 GiB bus bandwidth. On ORION-class
nodes (8 × 400G) expect ≈ 350+ GB/s node busbw; the per-rail figure is busbw ÷ 8, compared with the
50 GB/s line rate `[VENDOR-SPEC, 2026-10]`. Save the `NCCL_DEBUG=INFO` log to prove the transport: the
channel lines must end in `/GDRDMA` (for example `via NET/IB/0/GDRDMA`); also record
`lsmod | grep nvidia_peermem`, remembering that DMA-BUF can provide GPUDirect RDMA without that module.
Copy `manifest.yaml`, fill every `record:` field of the L3 extension, commit it under
`manifests/`, and reference that path in the `manifest` column. Rerun the linter: the row must
pass EVID-003/EVID-004.

### Running the L2 experiment (course harness)

From the repository root:

```bash
python scripts/hw_labs.py build ch23
python scripts/hw_labs.py run ch23 --device gpu   # measure on the GPU -> lab/l2/results/gpu-<model>/
python scripts/hw_labs.py run ch23 --device cpu   # CPU fallback        -> lab/l2/results/cpu-fallback/
python scripts/hw_labs.py test ch23               # quick run now + committed-evidence checks
```

The experiment is `lab/l2/experiment.py`. With `--device auto` (the default) it uses the GPU when one is
visible; without a GPU the CPU fallback runs automatically and its report says which invariants were
skipped. Add `--quick` for a smoke test (never committed as evidence).

It validates the reference bundle's node-level assumptions against this host. A-01 is an FP16/BF16 GEMM
sweep against this GPU's peak, and that fraction is the ceiling for A-04 MFU. A-02 is GPU memory, A-03 is
GPU board power under load (node power is not measurable here), and A-08 is a checkpoint write and
verified restore. A-10, GPU-NIC affinity and NUMA are probed. It then appends the measured rows to a copy
of `benchmarks.md` as `MEASURED`, tier `L2`, with the run's manifest, and runs the lab's own
`check_evidence`. The new rows must pass, and two negative controls must fire EVID-003 and EVID-004.

Not runnable on the harness: node power from a BMC/PDU, `ibv_devinfo` MTU/firmware (no RDMA NIC), and the
L3 B-02 all-reduce row.

The CPU fallback uses an FP32 CPU GEMM for A-01 and host memory for A-02, writes host tensors for the
checkpoint test and measures no power. The lint step is identical.

**Observed on the reference run.** `lab/l2/results/` holds the committed evidence bundles
(`environment.json`, `results.json`, `report.md`) from the course's reference host: a laptop GeForce RTX
4060 (Ada, 8 GB, PCIe Gen4 x8) under WSL2, not an H100-class server. `gpu-<model>/` is the GPU run and
`cpu-fallback/` the CPU run; each `report.md` lists what was measured, what was not runnable and why, and
the invariants it passed. The assumption register shows how an acceptance check flags a node that does
not match the bundle. Rerun on your own hardware and compare like with like.

## 9. Intentionally flawed inputs

The Kestrel bundle contains planted flaws and also several *traps*: things that look wrong but are
consistent. The list, with the reasoning for each, is in `solutions/exercises-key.md` (instructors
only). Learners: the checker tells you how many findings each rule family must produce, not which.
