# Lab 24 — Role-Readiness Self-Assessment and Job-Posting Register Validator

## 1. Goal and the real-world task it mirrors

Two small tools that engineers and hiring managers in AI infrastructure actually build and use:

1. **Role-readiness self-assessment.** Score an evidence portfolio against a role competency matrix
   and produce a prioritised gap plan. This is the same exercise a staff engineer does when writing a
   promotion packet or a hiring manager does when calibrating a level, reduced to explicit rules:
   evidence is capped by its *type* (a course is not production ownership), discounted when it is
   stale or unverifiable, and rejected when it overstates what was measured.
2. **Job-posting register validator.** Clean a hand-collected register of job postings: enforce
   required fields, normalise and deduplicate, flag stale "active" rows, and compute skill frequencies
   only over postings that survive. This is the evidence discipline Section 13 of the course outline
   requires before anyone claims "we analysed N job postings" (see manuscript Section 24.4).

The register in `data/` is **synthetic**: every employer, job ID, and URL is fictional, and URLs use
the reserved `example.com` domain. Nothing in it is a statement about any real company's hiring.

## 2. Tier and realism boundary

**L1** (laptop). Evidence class: **MODELED** — scores follow from stated rules, not measurement. The
lab cannot tell you whether you would pass a particular employer's interview loop; it shows whether
your evidence supports the level you claim under a transparent rubric, and where to invest next.

## 3. Setup

```bash
cd book/part-6-applied-engineering/ch24-career-paths-engineering-practice/lab
python -m pip install -r ../../../../requirements.txt     # Python >= 3.10; this lab needs only pyyaml
python check.py                                           # progress meter for starter/career_lab.py
```

## 4. Background

- Manuscript Sections 24.2–24.3 (competency maps, the 0–4 proficiency scale, and levels).
- Manuscript Section 24.4 (employer landscape and the dated, deduplicated register).
- Manuscript Section 24.9 (building a portfolio from the capstones; evidence strength).
- `data/competency_matrices.yaml` → `evidence_rules` holds every cap, threshold and penalty.

## 5. Tasks

Implement the functions in `starter/career_lab.py` that raise `NotImplementedError`. Each docstring
is the specification.

| # | Function(s) | Acceptance criterion |
|---|---|---|
| 1 | `effective_level` | 14 rule cases pass: type caps, missing artifact, simulation-claimed-as-measured, unverified production, stale and undated evidence, unknown competency |
| 2 | `demonstrated_levels` | The learner's 15 checked competency levels and 9 evidence flags match |
| 3 | `readiness` | AI Network Engineer scores 100.0 / 94.1 / 78.4 / 69.6 for junior / mid / senior / staff; a score above threshold with a gap of 2 is *not* "ready" |
| 4 | `gap_plan` | Senior AI-network plan is observability (priority 4), congestion (3), host_topology (2), physical_layer (2) |
| 5 | `normalize_url`, `posting_key` | Tracking queries, trailing slashes, host case and scheme do not create new postings |
| 6 | `row_issues` | Field rules: missing, bad date, future date, non-HTTPS URL, invalid seniority/status, stale active (> 30 days) |
| 7 | `duplicate_clusters`, `representative` | 61 rows → 51 postings; a key-then-URL chain of three rows merges into one |
| 8 | `validate_register`, `skill_frequency` | 51 unique / 40 complete / 31 active-and-fresh; top skills match |

Then produce the report:

```bash
python starter/career_lab.py --role ai_network --seniority senior --out readiness_report.md
```

Expected (abridged) once complete:

```text
| AI Network Engineer | 100.0 (ready) | 94.1 (ready) | 78.4 (near) | 69.6 (not_ready) |
...
- rows: 61; unique postings: 51; complete: 40; active and fresh: 31
```

Finally, replace `data/learner_evidence.yaml` with **your own** evidence (keep a copy of the original
so `check.py` still passes — e.g. `python starter/career_lab.py --data my_data/`) and write the
role-readiness matrix and gap plan that are this chapter's deliverable.

## 6. Running the checker

```bash
python check.py                    # your starter implementation
python check.py --impl solution    # instructor reference (requires ../solutions)
```

One line per check (`PASS`/`FAIL`/`TODO`); exit code 0 only when every check passes.

## 7. Deliverable and grading rubric (100 points)

| Item | Points |
|---|---|
| Tasks 1–4 (Part A) pass `check.py` | 30 |
| Tasks 5–8 (Part B) pass `check.py` | 30 |
| Written explanation (≤ 1 page) of every evidence flag raised for the sample learner and *why the rule exists* | 10 |
| Your own role-readiness matrix (one target role, two adjacent roles) with each level backed by a named artifact | 15 |
| Your gap plan: top three gaps, the artifact you will produce for each (capstone, lab, case study), and a date | 10 |
| Statement of limitations: what this score can and cannot say about hiring readiness | 5 |

## 8. Extensions (L1+, L2, L3)

**L1+ — your own dated register.** Collect 20–40 public postings for your target role over a fixed
window. Record every field in `register_meta.yaml`'s `required_fields` *at the time you read the page*,
and run the validator. Record in your copy of `manifest.yaml`: collection window, sources, the dedupe
rule version, rows collected, unique postings, active-and-fresh count. Respect each site's terms of
use; do not scrape where it is prohibited. Keep the register private if it contains anything beyond
public posting text.

**L2 — convert a `lab_l1` evidence item into `lab_hw` evidence.** On one GPU host, for example:

```bash
nvidia-smi -q | head -40                 # driver, CUDA version, GPU model for the manifest
nvidia-smi topo -m                       # GPU/NIC/NUMA relationships (Chapter 5)
lstopo --of txt                          # hwloc view of sockets, NUMA nodes, PCIe (Chapter 5)
./build/all_reduce_perf -b 8 -e 4G -f 2 -g <ngpus>   # nccl-tests, intra-node (Chapter 12)
```

Record GPU model, driver, CUDA, NCCL version, kernel, commands, run count (≥ 5), warm-up policy, and
raw output paths. Then update the evidence item: `type: lab_hw`, `measured_on_hardware: true`, and an
`artifact` pointing at the raw results.

**L3 — multi-node fabric evidence** (dedicated, non-production lab only):

```bash
ibstat                                   # InfiniBand port state and rate
rdma link show                           # RDMA link state (iproute2 rdma tool)
ib_write_bw -d <dev> --report_gbits      # perftest: server side; add <server-ip> on the client
mpirun -np <N> -H <hostA>:8,<hostB>:8 ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1
```

Record NIC model and firmware, RDMA stack version, switch OS version, topology, MTU, PFC/ECN
configuration, run count, and raw output paths. Flags and tool names must be checked against the
versions installed on your systems.

> **Safety:** never run fabric benchmarks on a shared or production fabric to produce portfolio
> evidence. Saturating all-reduce traffic is indistinguishable from an incident to the people on call.

## 9. Intentionally flawed inputs

Both datasets contain planted problems (portfolio-hygiene problems in the evidence file; data-quality
problems in the register). They are documented for instructors in
`../solutions/exercises-key.md` (section "Lab answer key"). Part of the exercise is to explain each one.
