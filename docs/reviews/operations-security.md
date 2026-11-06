# Pre-publication technical review: production operations, reliability and security (Chapters 16–20)

> **Nature of this review.** This is an AI-assisted specialist review (Claude, acting as an SRE /
> platform-security reviewer). It is **not** an independent external human review and does not
> replace one.

- **Date:** 2026-11-05
- **Scope:** concise edition `concise/ch16.md`–`ch20.md` (published text); matching full manuscripts in
  `book/part-5-production-operations/ch16–ch20*/manuscript.md`; lab instructions
  `ch16–ch20*/lab/README.md` and `ch16*/lab/handson/README.md` (plus the `handson` scripts' fio
  invocation). `concise/ch14.md` was read, not edited, to check consistency.
- **Canonical sources used:** `docs/REFERENCE_CLUSTER.md`, `docs/VERIFIED_FACTS.md`,
  `concise/back/e-sources-and-versions.md` (Appendix E). No web research was done.
- **Review areas:** evidence labels; recomputation of models; security and multi-tenancy
  completeness; reliability and recovery consistency with Chapter 14; operational safety of risky
  operations in the text and labs; vendor/version scoping; Mermaid diagrams against the prose.

## Findings

Severity: **High** = wrong guidance or a safety/security gap that could cause harm; **Medium** = an
inconsistency or mislabel a careful reader would trip on; **Low** = clarity or completeness.

| ID | Chapter / section | Severity | Finding | Resolution |
|----|----|----|----|----|
| OS-01 | ch17 §17.3, Table 17.1 (concise and manuscript) | Medium | The MPS column's "Multi-tenant production" row said "With care". That contradicts ch19 Table 19.5 / 19.7 ("time-slicing/MPS … same tenant only"), Appendix C ("time-slicing and MPS for one tenant only") and VERIFIED_FACTS (no fault isolation, no bandwidth isolation). This is security guidance, so the inconsistency matters. | **Fixed:** "No (same tenant only)" in concise and manuscript. |
| OS-02 | ch18 Troubleshooting, root cause (concise) | Medium | Halcyon's BMC policy (450 W GPU cap on PSU-redundancy loss, 8.2 kW) was labelled `[VENDOR-SPEC, 2026-10; platform-specific]`. Halcyon is fictional, so its policy and numbers cannot be vendor specification. The manuscript applies the label only to "such policies are platform-specific". | **Fixed:** `[ILLUSTRATIVE; such policies are platform-specific]`. |
| OS-03 | ch19 §19.1 (concise and manuscript) | Low | The text cites Chapter 14 for "δ ≈ 1 min" asynchronous blocking cost, but Chapter 14 models δ_async ≈ 1.19 s for W-TRAIN on ORION-256. 1 min is a conservative ORION-XL assumption, not a Chapter 14 result. The conclusion (restart overhead dominates) still holds, and gets stronger with the smaller δ. | **Fixed:** now reads "a deliberately conservative assumption; Chapter 14 … models ≈ 1.2 s on ORION-256". |
| OS-04 | ch19 §19.7, Table 19.6 BMC/firmware row (concise and manuscript) | Low (security completeness) | Firmware trust covered signed firmware and Secure Boot but not measured boot or attestation, which are what prove a returned or repaired node booted the expected firmware. | **Fixed:** added "measured boot with TPM attestation". |
| OS-05 | ch19 §19.7 checklist item 4 / manuscript V8 | Low (security) | The tenant-to-BMC reachability check tested only TCP 443 (Redfish). IPMI-over-LAN (UDP 623) is the older, weaker surface. | **Fixed:** the check also requires IPMI (UDP 623) to be unreachable. |
| OS-06 | ch16 §16.5 wave plan code block | Low | The label "fleet capacity ≈ 1.5 %" could be read as total campaign cost. It covers only drained node-hours: it leaves out the 8 elastic restarts of W-TRAIN (≈ 8 × 0.25 h × 224 GPUs ≈ 448 GPU-h) that ch20 §20.5 says must be priced ("the stalled gang is the cost"). | **Partly fixed:** relabelled "capacity out" (no word-count change; ch16 is at the 4,000 cap). **Open:** add one sentence pricing the restarts when ch16 next has room. |
| OS-07 | ch17 lab README §8 L2 | Medium (lab safety) | The lab adds a taint, a ResourceQuota and a Slurm DRAIN but gave cleanup only for the taint and DRAIN, inline. The quota and a final state check were missing. | **Fixed:** added an explicit cleanup step (untaint, delete quota, RESUME, verify allocatable/`sinfo`). |
| OS-08 | ch17 lab README §8 L3 | Medium (lab safety) | "A node with one rail administratively down" gave no scope or restore step. | **Fixed:** limited to a lab node with no other jobs on a lab switch port; port restored and verified (speed, `PORT_ACTIVE`, pair test) before the node rejoins a pool. |
| OS-09 | ch19 lab README §9 L3 | Medium (lab safety) | The link-flap trials disable a backend port three times. There was an authorization note but no before-state capture, restore, or check between trials. | **Fixed:** record port state/counters, re-enable and verify after each trial, and keep nodes drained until a pair test passes. |
| OS-10 | ch20 lab README §8 L2 | Medium (lab safety) | `ip link set … mtu 9000` and a soft-RoCE device were created with no warning about locking yourself out over the management interface, and no cleanup. | **Fixed:** use a non-management interface, record the original MTU, and restore it and `rdma link delete rxe0` afterwards. |
| OS-11 | ch18 lab README §9 L3 | Low (secrets) | `gnmic … -p <pass>` puts a switch password on the command line (shell history, `ps`). `--skip-verify` was not scoped. | **Fixed:** uses `"$GNMI_PASSWORD"` (consistent with ch20's lab) and a comment limiting `--skip-verify` to a lab switch. |
| OS-12 | Appendix E vs ch19 §19.7 | Medium (version sensitivity) | ch19's security controls are labelled `[VENDOR-SPEC, 2026-10]` (Container Toolkit key `accept-nvidia-visible-devices-envvar-when-unprivileged`, CVE-2024-0132, PSA levels, `rdma system set netns exclusive`, cosign verification), but Appendix E has no row or source for any of them. E.7 covers only scheduling. | **Open:** add an Appendix E row group for these with release and source (toolkit release that fixed CVE-2024-0132, toolkit config docs, Kubernetes PSA docs, iproute2 `rdma` man page). Back matter is outside this review's edit scope. |
| OS-13 | ch17 §17.1 vs Figure 17.1 | Low | The prose lists the five questions "in order" as Eligible → Allowed → Ordered → Fits → Where. The figure (and the lab) run validity → quota → order → filter (eligibility) → fit → score, so eligibility is evaluated after ordering. Both are defensible; the order differs. | **Open:** drop "in order" or note that the lab filters after ordering. Not changed (stylistic). |
| OS-14 | ch19 §19.1 model vs ch14 §14.8 | Low | ch19's waste model uses lost work τ/2 + R. ch14 adds completion latency L (τ/2 + L) for asynchronous saves. At ORION-XL values (L ≈ 72 s, τ ≈ 19 min) the difference is ≈ 0.7 % of goodput, and VERIFIED_FACTS endorses ch19's form. | **Open (accept):** consistent to first order; optionally mention L in a future edition. |
| OS-15 | ch19 INC-3107 / lab data | — (verified) | ckpt-0081 at 01:00 does not fall on the :10/:40 cadence of attempt 2. The lab data confirm it belongs to the earlier job 900198, so this is not an error. | No change. |

**Counts:** High 0 · Medium 7 (OS-01, 02, 07, 08, 09, 10, 12) · Low 7 (OS-03, 04, 05, 06, 11, 13, 14),
plus 1 verified non-issue (OS-15). **Fixed:** 11 (OS-06 counted as fixed for the label, with a
remaining open note). **Open:** 4 (OS-06 residual, OS-12, OS-13, OS-14).

## Recomputations (all agree with the text unless noted)

**ch16**
- PCIe Gen5 x16: 32 GT/s × 16 × 128/130 / 8 = 63.0 GB/s; x8 = 31.5 GB/s. ✓
- Canary detection: 1 − e^(−0.01×2×72) = 1 − e^(−1.44) = 0.763; 4 nodes: 1 − e^(−2.88) = 0.944; 95 % needs λNT ≥ ln 20 = 2.996, so NT ≥ 300 node-h. ✓
- Waves: max(⌈30/4⌉, ⌈4/1⌉) = 8 (7×4 + 2); calendar 75 + 8×15 = 195 h; 32×3 = 96 node-h = 768 GPU-h; 96/6,240 = 1.54 %. ✓ (see OS-06)
- Spares: λ = 32/1,536 h⁻¹ × 24 = 0.5/day; L = 0.5 × 5 = 2.5; Poisson(2.5) P(≤4) = 0.891, P(≤5) = 0.958. ✓
- Defects: 0.99⁸ × 0.99⁸ × 0.97 = 0.8515 × 0.97 = 0.826; 32 × 0.174 = 5.57; 1 − 0.826³² = 1 − e^(−6.12) = 0.998. ✓
- Defect A: 0.8 × 17.4/0.75 + 3.48 = 22.04 s; loss 21.05 % × 256 = 54 GPU-eq. Defect B: 7.66/45 = 0.170 s → 0.340 s; +0.98 %. ✓
- Acceptance: 31 + 45 + 1,440 + 10 = 1,526 min = 25.4 h; 256 × 25.4 = 6,510 GPU-h; 54 × 168 = 9,072 GPU-h. ✓
- busbw 267.02 × 2(7)/8 = 467.3 GB/s; burn-in rack 4 × 10.2 = 40.8 kW. ✓

**ch17**
- $3.00 × 8 = $24/node-h; gang deadlock 32 GPUs × 8 h = 256 GPU-h = $768; preemption 64 × (0.25 + 0.25) = 32 GPU-h. ✓
- Time-slicing: 2 × (1/2.56) = 0.78. ✓ MIG mixed 7 × 8 = 56. ✓
- Monday queue: allocated 96 + 18 + 10 + 27 = 151; free 105; ineligible 32; usable 73 = 52 + 21; every share in Table 17.5 recomputed (27/48, 96/160, 10/32, 18/48, 18/32, 31/48, 33/48, 112/160, 41/48, 34/48, 42/48, 22/32) ✓; placed 69 → 220/256 = 85.9 %; leftover 36 = 24 + 12. ✓
- Troubleshooting: 8 + 4 + 6 + 8 = 26 shown, 18 eligible; QOS 20 + 16 = 36 ≤ 48. ✓ Quota overcommit 296/256 = 1.16. ✓
- Rail-down busbw 0.875 × 350 = 306 GB/s ✓ (note: 350 is reused as both degraded raw bandwidth and healthy achievable busbw; correct, slightly confusing).

**ch18**
- 256 × 2 × 0.18 = 92.2 GPU-h = $276; ORION-XL 1,475 GPU-h. ✓ Cardinality 320 / 10,240 / 163,840. ✓
- Counter wrap 2³²/50 GB/s = 0.086 s; microburst 50 MB/(1.5 TB) = 0.0033 %. ✓
- Budgets on 43,200 min: 43.2 / 216 / 432 min. ✓ 16-node MTBF 96 h, e^(−0.25) = 0.779. ✓ Poisson(2.5) P(≤1) = 0.287, P(≤8) = 0.9989. ✓
- Burn-rate table: 14.4/720 = 2 %, 36/720 = 5 %, 72/720 = 10 %. ✓
- Blip: 5-min burn 0.04/0.001 = 40; 1 h (0.28 + 53 × 0.0002)/60 = 0.00484 → 4.84; 30 min (0.28 + 0.0046)/30 → 9.49; 6 h (0.28 + 0.0706)/360 → 0.97; neither pair pages. ✓ Max burn 1/0.05 = 20. ✓
- Training burn: 0.144 × 60 = 8.64 bad min; ≈ 5 + 8.6 + 2 ≈ 15.6 min → "15–17". ✓
- INC-2291: ratios 0.819 / 0.846; tokens/s 120,595 → 98,736; 7,020 s; 45.2 + 19.2 = 64.4 GPU-h; 62.4 × $3 = $187; SLI 244/360 = 0.678; 116/432 = 26.9 %; TTD 48, TTM 118, TTR 140; 48/118 = 41 %. ✓
- n12: 4.6 + 8 × 0.45 = 8.2 kW; 1,830/1,540 = 1.19; 13 × 0.19 = 2.47 → 19.87 s → 0.876; continue 20 × 128 × 0.12 = 307; restart 0.5 × 128 = 64. ✓

**ch19**
- Job MTBF 1,536/32 = 48 h, /512 = 3 h. ✓ Young: √(2 × 1 × 180) = 18.97 min; 1/19 + 24.5/180 = 0.189; τ = 30: 0.200. ✓ (With Chapter 14's δ ≈ 0.02 min, τ_opt ≈ 2.7 min and overhead ≈ 0.098, so restart overhead dominates even more; see OS-03.)
- FMEA: 10×2×2 = 40 → 200; 8×7×6 = 336; 9×3×7 = 189; 9×3×3 = 81. ✓
- Straggler: 1 − 0.999³² = 3.2 %; 1 − 0.999⁵¹² = 40.1 %. ✓
- Retry budget: 8 × 4.096 µs × 2¹⁸ = 8.59 s (NCCL 2.22 default timeout 18, matches Appendix E). ✓
- Spares: 512 × 24/1,536 = 8/day × 5 d = 40; Poisson(40) P(≤54) = 0.986, P(≤55) = 0.990 → 55 nodes = 10.7 %. ✓ Elastic ⌊472/8⌋ = 59 (−7.8 %); worst case 64 − 40 = 24 (−62.5 %). ✓
- INC-3107: n212 ranks (212−1)×8 = 1688–1695; n389 3104–3111; stage 3 = n193–n256; rank 1693 → n212, mlx5_5, NUMA 1 (Fig. 19.1). ✓ DOM −4.3 dB → 0.372 (2.7×). ✓ RPO 31.0 min ≤ τ + L = 31.2 min (consistent with ch14's τ + L worst case); RTO 50.0; 4,096 × 81/60 = 5,529.6; attempt 1 12.7 / 39.4 / 3,561.2; total 9,090.8 GPU-h × $3 = $27,272. ✓ Watchdog cost 10 × 4,096/60 = 683 GPU-h. ✓

**ch20**
- Waves 2+3+4+8+8+7 = 32, slot-major, ≤ 1 node per rack per wave (25 % of a rack). ✓
- Detection 1 − 0.9^k: k = 2 → 0.19, 5 → 0.41, 9 → 0.61, 17 → 0.83. ✓
- Noise: 1.25 × 0.25/√12 = 0.090, /√6 = 0.128, combined 0.156; 2.2/0.156 = 14.1 SE. ✓
- MTU: 4,160 ≤ 9,000; 9,022 ≤ 9,216; 9,238 > 9,216; ping 8,972 + 28 = 9,000. ✓ Wire 1,106 / 4,178 B; 92.6 % / 98.0 %; 45.2 M / 12.0 M pps; +5.9 %, 3.8×. ✓
- Plan: 24 − 3 − 1 + 1 = 21 MTU actions + 3 drift = 24 on 22 targets; ⌈22/8⌉ = 3 batches. ✓
- Rollout pricing: 1,440 + 48 + 80 = 1,568; big bang 176, expected 176 + 0.05 × 1,408 = 246; staged 1,568 + 0.05 × 208 = 1,578; batch only 256 + 57.6 = 314; hybrid 608 + 9.6 = 618; canary 240 vs 57.6; 22/32 = 69 %, 24/32 = 75 %. ✓
- Abort: 39.41/43.67 = −9.8 %; rollback 2 + 2 + 4 = 8 nodes; gNMI 3/8 = 37.5 %. ✓

## Reliability and recovery consistency with Chapter 14

ch19 is consistent with ch14 on every point checked:
- A checkpoint counts only after its metadata commit (ch14 §14.6–14.7: `.metadata` / manifest-last is the commit point). ch19 restores `ckpt-0084` because `ckpt-0085`'s commit was in progress.
- RPO stays within ch14's worst case of τ + L.
- Lost accelerator-hours use the same currency.
- Restart overhead uses the canonical R ≈ 15 min. ch19 explains why the observed RTOs (39–50 min) exceed it.
- With no spares on ORION-256, the options are wait, restart at reduced DP, or borrow. ch14's swap-in time assumes a declared external spare pool, and ch16/ch19 declare the same variation.

Node failure, rank replacement (same local ranks, rail alignment), elastic restart at DP-replica
granularity (consistent with REFERENCE_CLUSTER §4) and the restart-loop gate (Figure 19.2) are all
covered. The only differences are OS-03 (now fixed) and OS-14 (accepted).

## Security and multi-tenancy completeness verdict

**PASS for the book's scope, with OS-12 open.**

| Area | Coverage |
|----|----|
| GPU memory isolation | Complete. MIG vs MPS vs time-slicing are in ch17 Table 17.1 (now consistent with ch19, OS-01) and ch19 Tables 19.5–19.6, with residue and reset on tenant change and in-process non-zeroing. |
| Tenant boundaries | Complete. Namespaced RBAC, PSA, default-deny NetworkPolicy (with its RDMA-secondary-interface gap stated), VRF/VNI, P_Key enforcement and duplicate-key pitfalls, exclusive RDMA netns with SR-IOV VFs, and the `NVIDIA_VISIBLE_DEVICES` bypass. |
| Privileged management interfaces | Complete. ch16 covers OOB isolation, credential rotation, cipher suite 0 and power-action rate limits; ch19 covers per-operator Redfish accounts and the reachability check (now including IPMI, OS-05). |
| Firmware and supply-chain trust | Complete. Signed firmware, Secure Boot, measured boot / TPM attestation (OS-04), anti-rollback, cosign at admission, digest pinning, SBOM/provenance, safetensors, and automation identity (ch20). |
| Secrets | Covered. KMS encryption at rest, short-lived tokens and rotation. |
| Data sanitization | Complete. GPU reset or residue test, scratch wipe, NIST SP 800-88 NVMe sanitize with certificate. |
| Failure containment | Covered. Containment exercise with an abort on non-target burn rate. |
| Not covered (acceptable at this length) | Device-level attestation of GPUs/NICs (SPDM) and confidential-computing operational detail. Noted only. |

## Operational and lab safety verdict

**PASS after fixes OS-07 to OS-11.**

Chapter text: every risky operation quoted in ch16–ch20 has prerequisites, warnings, scope and a
rollback or approval path:
- drain/cordon/RESUME: lifecycle single writer, change review, the RESUME pitfall;
- reimage and firmware flash: waves, abort conditions, per-component rollback, anti-rollback caveat;
- burn-in: facility warning;
- sanitize: irreversibility, serial-confirmed, approved retirement only;
- scheduler policy changes: reviewed change with a revert criterion;
- fabric changes and automation: dry run, caps, kill switch, commit-confirm, recorded exception for the batch shapes;
- fault injection, GPU resets and residue tests: drained or lab-only Safety boxes in ch18 and ch19.

Labs: the L1 labs are simulation only. The ch16 L2 and `handson` fio runs are `--readonly` (verified
in `collect_host.py`). Nothing writes to raw devices. The ch16 handson has an explicit Safety section
and a teardown that only stops lab processes. The missing cleanup and restore steps for taints,
quotas, rail-down, link-flap trials and MTU changes were added (OS-07 to OS-10).

## Generalization and version sensitivity

- Vendor-specific behaviour is scoped with `[VENDOR-SPEC, 2026-10]` labels and "verify for your
  driver branch / release" notes: Xid tables, DCGM field renames (consistent with Appendix E 4.6/4.7
  rows), NCCL_IB_TIMEOUT 18 → 20 (E.4), PyTorch watchdog 10 min (E.5), DRA GA 1.34 and Kueue
  `QuotaReserved` (E.7–E.8), `bf_window` 1,440 default (E.9), DR4 −5.9 dBm (E.11). Nothing stale was found.
- The only gap is OS-12: ch19's security keys and CVE have no Appendix E entries.
- ORION and Halcyon are presented as illustrative throughout, and OS-02 removes the one place where a
  Halcyon policy carried a vendor label.

## Diagrams

The following agree with the prose: Figures 16.1 (no edge from repair/imaged to schedulable; retire
needs a certificate), 16.2 (stage durations sum to the 31-minute quick-check total), 18.1, 19.1
(rank 1693 → n212 / mlx5_5 / NUMA 1), 19.2, 20.1 and the 20.2 wave table. Figure 17.1 has a minor
ordering difference from the prose (OS-13, open).

## Checks run

- `python scripts/build_concise.py --check`: ch16 4,000, ch17 3,951, ch18 3,931, ch19 3,955,
  ch20 3,964 words, all OK. (ch14 FAILs at 4,001 words. It was already failing before this review
  and is outside this review's scope.)
- `python -m pytest docker/harness/test_package.py --pkg <abs path> -q`: ch17 86 passed, ch18 86
  passed, ch19 98 passed, ch20 90 passed. The ch16 lab was not edited.
- `python scripts/validate_labs.py`: 32/32 labs valid. A first run showed 31/32 while other reviewers
  were editing concurrently; the rerun was clean.
