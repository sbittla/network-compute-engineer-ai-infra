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

## Independent review r1 (2026-11-01)

Independent reviewer scores (before author fixes): D1 9.5, D2 9.0, D3 9.5, D4 9.5, D5 9.0, D6 9.5, D7 9.5,
D8 9.5, D9 9.0 — weighted **9.35** (gate fail; two majors). The reviewer reproduced every number and ran
`check.py` (solution 11/11, starter 0/11 graceful). Each finding was re-verified by the author before any change.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| N05-01 | Minor | §5.12 symptom says 64-GPU job, hypothesis-table caption says 128-GPU. | Verified; Table 5.5a caption now "slow 64-GPU job". |
| N05-02 | Major | Host-side PCIe/NVLink failure modes missing (AER, MPS/MRRS/Relaxed Ordering, BAR1, NVLink counters, Fabric Manager, retraining under load). | New Table 5.9 "Host-side PCIe and NVLink failure signatures" in the runbook section (signal → command → healthy → failing → action; thresholds `[ILLUSTRATIVE]`, commands `[VENDOR-SPEC, 2026-10 — verify]`): correctable/uncorrectable AER via sysfs `aer_dev_*` and kernel log, link retraining sampled under load, `nvidia-smi -q` replay counters, DevCtl `RlxdOrd`/`MaxPayload`/`MaxReadReq`, BAR1 via `nvidia-smi -q -d MEMORY`, `nvidia-smi nvlink -e` and DCGM NVLink CRC/replay/recovery fields, Fabric Manager state. Table 5.8 gains PCIe-error and device-control rows; PCIe-link and NVLink rows extended (read under load, error counters). Forward pointer from §5.2; hypothesis H5 added to Table 5.5a; summary bullet extended. Filler cut elsewhere (prerequisites, lab overview, realism boundary, Step 5) to hold length (≈ 10,250 words). Table numbered 5.9 so that 5.1–5.8 keep their numbers. |
| N05-03 | Major | Ex 5.16 "L2 rail VLAN" premise implausible; key's PXN clause hand-wavy. | Verified. Prompt now states a declared variation: one stretched L2 domain (one VLAN and subnet spanning all rail leaves through the spines) and names the NICs (`mlx5_4`/`mlx5_5`). Key and model answer: NCCL cannot see the cabling error and still pairs GPU4 with `mlx5_4`; rail-4 and rail-5 flows to n12 cross the spines (extra hop, hash collisions → tail). PXN clause deleted. Exercise folder prompt, meta.yaml marking and marking.json regenerated. |
| N05-04 | Minor | `ib_write_bw` without `-s` cannot print an 8 MiB row. | Verified; added `-s 8388608`. |
| N05-05 | Minor | Ex 5.3 wording conflicts with data (on n01 the HCA name does match the rail). | Verified; reworded as suggested (column index ≠ rail; `mlx5_0` is a software label; authoritative source). Evidence line, folder prompt, meta.yaml, marking.json, key (with marking) and model answer updated. |
| N05-06 | Minor | udev-naming premise for n17's `mlx5_3` unexplained. | Verified. §5.6.1 now says ORION's naming step writes the udev rule from the rail recorded for each card's MAC in the asset database; §5.10 Step 2 says the technician recorded the card as "rail-3 NIC", so it was named `mlx5_3` regardless of slot. Key 5.20 and the 5.3/5.20 model answers aligned. |
| N05-07 | Minor | Mid-sentence acronym expansions, over-long lines. | NIC, HCA, LLDP, RDMA defined in the opening callout; BDF, NUMA, IOMMU, ACS, NCCL in the objectives; DMA at first use in §5.1. Removed the later expansions (§5.1, §5.4, §5.5) and rewrapped. |
| N05-08 | Minor | Table 5.5 CV could be read as run-to-run variance. | Caption now defines median/p99/CV over 200 modeled iterations of one run (iteration-level, independent samples, not Chapter 6's run-to-run variance); column renamed "CV (iteration-level)". |
| N05-09 | Minor | +9 % step vs −41 % busbw needs the overlap assumption. | Added: data-parallel job without pipeline stages overlaps most of its all-reduce; 0.09 / (350/205 − 1) ≈ 13 % of the step was exposed communication `[MODELED]` (consistent with the VERIFIED_FACTS overlap rule, which applies to PP jobs). |
| N05-10 | Minor | Slurm alternative only in prose; `--bind-to numa` semantics. | Lab README L3 block: comment on what `--bind-to numa` does, explicit `srun -N 2 --ntasks-per-node=8 --gpus-per-task=1 --cpu-bind=map_ldom:0,0,0,0,1,1,1,1 ./hca_wrap.sh …` line. |
| D3 next-0.5 | — | PXN paragraph dense. | Split into lead + three bullets: the rule → the n17 example → when it helps. |
| D4 next-0.5 | — | Add an lstopo-vs-nvidia-smi disagreement capture. | Not done this round: it changes lab data, generator and checker counts; Exercise 5.21 and §5.6.2 keep the report item. Candidate for the next lab revision. |
| D9 | — | Ad-hoc numbers 5.2a / 5.5a. | Partly rejected: renumbering 5.3–5.8 would break references in committed L2 evidence (`lab/l2/results/*/report.md` cites "Table 5.3"), `experiment.py`, and the concise edition. Kept the two lettered sub-tables; the new table is 5.9. |
| Netdev naming | — | Cross-chapter netdev names differ (shared-docs note). | Raw lab data keep PCI-path names; §5.6.2 now maps them once to the canonical `ens<i+1>np0` alternative name (rail 0 = `mlx5_0` / `enp25s0np0` / `ens1np0`; rail 3 = `mlx5_3` / `ens4np0`) `[ILLUSTRATIVE]`. |

Verified after fixes: `python lab/check.py --impl solution` 11/11 PASS; `--impl starter` 0/11 with TODO lines
(graceful, exit 1); `python scripts/validate_labs.py ch05` OK on all columns; `python scripts/copyedit_lint.py`
0 findings in ch05 files; package harness (`docker/harness/test_package.py`, run locally) 90/90 passed, incl.
prompt sync and regenerated marking.json. Author re-score: D2 9.5, D5 9.5, D9 9.5, others unchanged →
weighted ≈ 9.5. An independent re-review is pending.

---

## Independent review r2 (2026-11-01)

Independent reviewer scores: D1 9.0, D2 9.5, D3 9.5, D4 9.5, D5 9.5, D6 9.5, D7 9.5, D8 10.0, D9 9.0 →
weighted **9.40** (gate fail; one major). Findings: 0 blocker, 1 major, 11 minor. Each finding was checked
before it was changed.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R05-01 | Major | The worked example models a 128-rank all-reduce for a TP = 8, PP = 2, DP = 8 job that has none. | Step 1 now observes the job's DP all-reduce time (≈ 2.1×) and step time (+18 %, `[ILLUSTRATIVE]`; with PP only the last micro-batch hides DP, so 0.16 × 1.1 ≈ 18 %). Step 4 opens with "Which collective?": 16 concurrent 8-rank rings (8 GPU indices × 2 stages), one rail each, ring factor 2 × 7/8 = 1.75. With a 1 GiB shard: healthy 39.1 ms, n02's stage 55.9 ms, n17's GPU3 ring (PXB shared, 22.5 GB/s) 83.5 ms, which is 2.13×, the observed ratio. The lab model is now named as what it is, the fleet's 128-rank `all_reduce_perf` check of the same 16 nodes; the same slowest path gates it, so the ratio is the same (5.549 → 11.837 ms = 2.13×). §5.9 Structure, the Table 5.5 caption, the S3 bullet, Table 5.7's column, the summary and the chapter README are updated, with Ch 11/12 cross-references. Exercise 5.9 now models a 256-rank health check, not a "W-TRAIN job" (prompt and folder README). The lab, its data and the checker are unchanged, so every committed lab number still holds. |
| R05-02 | Minor | "NIC *i*±1" is wrong for odd GPUs. | "the other NIC of its pair (NIC *i* XOR 1, e.g. GPU0↔NIC1, GPU1↔NIC0)". |
| R05-03 | Minor | `srun --gpus-per-task=1` hides peer GPUs and NCCL falls back to SHM. | §5.7 and the lab README now use `--gpus-per-node=8 --gpu-bind=none`, with a pitfall comment to check intra-node channels for `P2P/CUMEM`/`P2P/IPC` rather than SHM. |
| R05-04 | Minor | Key 5.19 says time correlation raises p99. | Rewritten in the key, the answer and meta.yaml: long-run p99 is unchanged if the marginals are. What changes is clustering, run-to-run variance, how representative a short benchmark is, and the need for windowed statistics. |
| R05-05 | Minor | "PCI bus order" for NIC columns is stated as a rule. | §5.6.1, key 5.3, the 5.3 answer and meta.yaml now say the lab captures (and commonly) follow PCI enumeration order, labelled `[VENDOR-SPEC, 2026-10 — verify]`; read the NIC Legend. |
| R05-06 | Minor | Restart cost (GPU-h) compared with a bandwidth fraction. | Step 5: 18 % longer steps waste 0.18 / 1.18 ≈ 15 % of 128 GPUs ≈ 19.5 GPU-h per hour `[MODELED]`; the 32 GPU-h restart pays back in ≈ 1.6 h. |
| R05-07 | Minor | 5.16's mechanism depends on how L2 is stretched. | The prompt says EVPN-VXLAN, and the key explains ECMP hashing on the underlay. The key, the answer and meta.yaml accept an STP/MLAG answer if it is stated (no per-flow hashing; blocked or pinned paths concentrate flows). |
| R05-08 | Minor | The capture script reads ACSCtl only on the parent bridge. | `capture_topology.sh` now walks every bridge from each GPU/NIC to its root port and prints each one once, in the same line format (`bash -n` clean; walk logic tested on a sample sysfs path). Table 5.3 row 5 says so. |
| R05-09 | Minor | GPUs on a shared NIC draw independent samples. | Listed under "What the model ignores". The model is unchanged, so committed scenario numbers stay valid. |
| R05-10 | Minor | Step 1 and §5.12 observed numbers have no label. | `[ILLUSTRATIVE]` inline at first use (Step 1 rewritten; §5.12 symptom). |
| R05-11 | Minor | Acronyms missing expansions. | AER, BAR1 (Base Address Register window), GDR (now first used with a forward pointer), TLP, DLLP, HBM, OFED/DOCA-host and UPI are now expanded. |
| R05-12 | Minor | Lettered table numbers. | "Table 5.5a" is now 5.6, and 5.6–5.9 shift to 5.7–5.10, with every in-text reference updated. "Table 5.2a" is now an uncaptioned column table introduced by its sentence. Fully renumbering it would push the GDR checklist off 5.3, and Table 5.3 is cited inside the committed `[MEASURED]` L2 bundle, which must not be edited. No file outside the manuscript cited the shifted numbers. |
| D7 advice | — | Link capstones to files. | Capstone A and G links now point to their README files. |
| D3 advice | — | Split the dense S3/S4 bullet. | Split into "S3" and "S4 vs S3". |
| Length | — | — | Trimmed §5.1 and §5.11. Manuscript 10,629 words (r1: 10,245). |

Verification: `check.py --impl solution` 11/11; `--impl starter` 0/11 (TODOs, no traceback);
`validate_labs.py ch05` OK on all columns; `copyedit_lint.py` 0 findings; package harness 90 passed.
Outputs were regenerated with `generate_outputs.py`. Only the marking.json files for 5.3, 5.16 and 5.19
changed. The concise edition was not edited.
