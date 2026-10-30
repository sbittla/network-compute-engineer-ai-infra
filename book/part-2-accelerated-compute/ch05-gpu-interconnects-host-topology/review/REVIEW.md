# Editorial Review — Chapter 5

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.10 | Fail |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | Pass (internal; external review pending) |

**Independent score history:** 8.85 (iteration 1) → 9.33 (iteration 2, Fail) → 9.50 (iteration 3, Pass). Author fixes for
iteration 2 findings are recorded at the end of this file; N3-01 wording fix (mlx5_3 is PHB/NODE/SYS, never ≤ PXB) applied after iteration 3.

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| I-1 | 2026-10-30 | Independent reviewer | 8.85 | Fail |
| I-2 | 2026-10-30 | Independent reviewer | 9.33 | Fail (one major open) |

## Scores by dimension (latest — iteration 2)

| # | Dimension | Weight | Score | Justification |
|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 9.5 | PCIe arithmetic, topo -m legend text, NVLink4/NVSwitch figures, ACS/IOMMU semantics and GDR evidence aligned with docs/VERIFIED_FACTS.md (no "NET/IB : GPU Direct RDMA Enabled for HCA" line; distance-check lines described correctly; DMA-BUF alternative stated). Version-sensitive items labelled. |
| D2 | Depth and production realism | 15 % | 9.5 | Three fault classes, silent failure mechanisms, NCCL nearest-NIC behaviour, x8 link scenario, acceptance gate with severities. |
| D3 | Pedagogy and clarity | 15 % | 9.5 | Raw output → mapping → findings → model → decision; Figures 5.1–5.6 include both required data-path diagrams (GPU↔GPU, GPU↔NIC). |
| D4 | Hands-on lab quality | 15 % | 9.5 | Realistic multi-source parsing, cross-check derivation, clean control host, four fault kinds, deterministic data, closed-form model check, L2/L3 commands. |
| D5 | Exercises and assessment | 10 % | 9.5 | Standard set plus outline exercises 5.11–5.15 and both deliverable lists; complete key with arithmetic and marking. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.5 | Model formula, parameters and omissions stated; deterministic vs stochastic results separated; L3 protocol with repetitions and manifest. |
| D7 | Cross-layer integration | 5 % | 9.5 | Canonical ORION names (`orion-nNN`, `rack-NN`, `orion-be-leaf-rR`, `mlx5_i` ↔ rail i); links to Chapters 3, 4, 8, 10–13, 16, 17, 19, Capstones A/G. |
| D8 | Operational realism and safety | 5 % | 9.5 | Safety callouts on ACS/IOMMU changes and deliberate misalignment runs; drain-at-checkpoint actions. |
| D9 | Editorial polish | 5 % | 9.5 | Acronyms defined, captions on all figures/tables, units stated (GB/s per direction, Gb/s line). |

Weighted = 9.50; lowest dimension 9.5.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Major | lab/check.py | Legend parsing in the classify check matched the "NIC Legend:" header (KeyError ''). | Regex `^\s*(NIC\d+):`. (It 1) |
| F2 | Major | lab data | `nvidia-smi topo -m` rows had an extra empty column before "GPU NUMA ID". | Generator fixed; regeneration byte-identical. (It 1) |
| F3 | Major | whole package | Host, leaf and HCA names diverged from the new canonical names in REFERENCE_CLUSTER.md (`hx8-nNN`, `orion-railR-leaf`, probe-order `mlx5_N`). | Regenerated data with `orion-nNN`, `orion-be-leaf-rR`, `mlx5_i` ↔ rail i (frontend `mlx5_8/9`); the "NICk ≠ mlx5_k" lesson kept via bus-ordered topo columns; text, checker, key updated. (It 2) |
| F4 | Major | manuscript §5.7, key 5.6 | GDR evidence needed alignment with VERIFIED_FACTS (distance-check lines vs `/GDRDMA`; DMA-BUF). | Added explicit paragraph and marking note; removed any reliance on distance lines. (It 2) |
| F5 | Major | model | Healthy 32-node busbw (327.6 GB/s) below the ≈ 350+ GB/s expected for 8 × 400G per node (VERIFIED_FACTS). | PIX μ 47 → 48 GB/s, α 0.5 → 0.2 ms; S1 now 350.4 GB/s; all tables/arithmetic recomputed. (It 2) |
| F6 | Minor | manuscript §5.12 | Illustrative GPU5 topo row did not match the golden layout. | Corrected. (It 1) |
| F7 | Minor | manuscript §5.10 | n02 deterministic busbw rounding. | Recomputed 262.2 GB/s. (It 2) |

## Iteration history

**Author self-review, iteration 1 (9.10; D1 9.0, D4 9.0, D7 9.0).** Ran both checker modes and the
validator; recomputed every Table 5.1/5.5 value; found F1, F2, F6.

**Author self-review, iteration 2 (9.50).** Applied coordinator updates (canonical names, VERIFIED_FACTS);
re-derived deterministic results (370.7, 262.2, 177.0, 219.4, 142.1 GB/s) and stochastic table; checker
11/11 on solution, starter 0/11 with TODO lines; `python scripts/validate_labs.py ch05` OK; word count
≈ 8,200.

## Release-gate items outstanding

- L2/L3 validation of parsers against real captures (real HGX outputs contain more bridges and fields).
- Calibration of `path_model.yaml` against measured nccl-tests on ORION-class hardware.
- External review by a practising GPU-cluster network engineer; re-verify NCCL log formats for the release used.

## Independent review iteration 1 + author fixes (2026-10-30)

Independent reviewer weighted score: **8.85** (gate fail). All four validator columns passed and data was
deterministic; findings below were all addressed by the author.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R-01 | Major | PCIe tree physically wrong (GPU and NIC under one bridge). | Each switch = upstream port + one downstream port per device; two-level switch complex per GPU/NIC pair; PIX = deepest common ancestor is one switch, PXB = more than one switch. Generator, lstopo data, classify_path (solution + starter docstring), §5.2, Fig 5.4, Table 5.2, Ex/Key 5.17 updated. |
| R-02 | Major | ACS location. | n02 ACSCtl now on the 16 downstream ports above each GPU and NIC; check asserts 16. |
| R-03 | Major | GDR distance gate missing; S4 conclusion wrong. | `gdr_max_relation: PXB` in the model; beyond-gate paths host-staged. S4 = 139 GB/s < S3 177 GB/s; S4@SYS (186 GB/s) added; Tables 5.4–5.6 and checks updated. |
| R-04 | Major | PXN not taught. | ~300-word PXN section (NCCL_PXN_DISABLE, NCCL_P2P_PXN_LEVEL, NCCL_CROSS_NIC) and a `pxn` rank-map policy (S5); n17 shown PHB-gated. |
| R-05 | Major | L3 misaligned recipe changed two variables. | Per-rank wrapper `NCCL_IB_HCA="=mlx5_$(((LR+4)%8)):1"`, all 8 NICs, NCCL_PXN_DISABLE=1, record NCCL_NET_GDR_LEVEL, /GDRDMA evidence. |
| R-06 | Major | 33-node arithmetic; no plan after drain. | Job is 16 nodes in the 24-node training partition; n23 fails acceptance first; checkpoint → requeue with --exclude; drain does not move a job; reduced-DP vs wait discussed; restart ≈ 900 s. |
| R-07 | Major | x8 NIC throughput. | ≈ 27 GB/s (≈ 215 Gb/s); Ex/Key 5.9(b) = 211.7 GB/s; Key 5.8(b) fixed; pitfall updated. |
| R-08 | Minor | S1 variance explanation. | Slowest of 128 paths ≈ 2.6σ (16-node job). |
| R-09 | Minor | CV vs variance ratio; n17-only fix. | CV ratio 12× ≈ variance ratio 150; fixing n17 alone leaves n02 at ≈ 262 GB/s. |
| R-10 | Minor | Fig 5.6 caption contradicted key 5.13. | Caption cites rotated per-rank HCA table, stale NCCL_TOPO_FILE, container device remap. |
| R-11 | Minor | "spare". | "idle node from the same partition". |
| R-12 | Minor | memlock limit. | Row 5a (ulimit -l / Slurm / container) in Table 5.3. |
| R-13 | Minor | SYS μ vs UPI capacity. | Stated as an explicit omission (4 × 50 GB/s crossing the link). |
| R-14 | Minor | Simplified files unlabelled; no capture script. | Labelled as simplified/reformatted; `lab/capture/capture_topology.sh` emits the same sections. |
| R-15 | Minor | Two-node run without launcher. | `mpirun -np 16 -N 8` / `srun` shown. |

**Author re-score after fixes:** weighted **9.50** (all ≥ 9.5; lowest D1/D4 9.5). Verified after fixes: `python lab/check.py
--impl solution` passes all checks, `--impl starter` reports TODO and exits 1, `python
scripts/validate_labs.py ch04 ch05 ch06` OK on all four columns, regenerated data byte-identical,
manuscript under 11,000 words. Outstanding: an independent re-review.

## Independent re-review (iteration 2) — 9.33, Fail (one major open)

Recorded separately from the author's self-review. The reviewer confirmed all four validator columns
and determinism and re-checked the arithmetic. Findings and the author's fixes:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| N-01 | Major | PXN modeled as engaging at PHB; eligibility rule missing. | `make_rank_map(policy="pxn")` now requires a peer GPU at ≤ PXB from the rail NIC, else falls back to the nearest NIC; S5 = S3 on n17 ("PXN not eligible"); §5.8, S5 bullet, Tables 5.5/5.6, key rewritten; "gate at PHB → 40 GB/s" aside removed; NCCL_P2P_PXN_LEVEL stated as p2p/all-to-all only, env vars marked [VENDOR-SPEC, verify]; checker asserts the rule (n17 GPU3 → mlx5_2 shared; healthy PXN = aligned; S5 = S3). |
| N-02 | Minor | S2 52 ms rests on the independent-CV assumption. | Deterministic 15.0 ms / ≈ 142 GB/s shown first, sensitivity sentence (c = 0.10 → ≈ 20 ms), S3/S4 crossover at a 22.5 GB/s host-staged rate stated (text and key). |
| N-03 | Minor | Requeue/--exclude wording. | Requeue keeps the spec; drained nodes are not reallocated; `scontrol update jobid=<id> ExcNodeList=…` while pending; §5.12 "drain now, then checkpoint and requeue". |
| N-04 | Minor | 32-node assumptions unstated. | Abstract made generic; Ex 5.9(d) and 5.17 state they use a full 32-node job. |
| N-05 | Minor | Capture script robustness/format. | ACS line format matches lab data (parse_gdr reads only the BDF and "ReqRedir+"); optional tools guarded with `|| echo "# unavailable"` under `set -e`; `bash -n` clean. |

After these fixes: solution checks pass, starter fails gracefully, `python scripts/validate_labs.py ch04 ch05
ch06` is OK on all columns, and manuscripts stay under 11,000 words. The next independent score is pending.
