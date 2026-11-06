# Sources and versions review: Appendix E, reading list, VERIFIED_FACTS

**Date:** 2026-11-05.
**Nature of review:** AI-assisted review with web verification against primary sources (tagged source code, vendor documentation, RFCs, IEEE/OIF material, NVD). This is **not** an independent external human review.
**Scope:** `concise/back/e-sources-and-versions.md` (Appendix E), `concise/further-reading.md`, `docs/VERIFIED_FACTS.md`. Chapters were grepped only. No chapter files were edited.

## 1. Resolving the unverified claims (former Table E.13)

| Claim | Ch. | Outcome | Evidence | Chapter text |
|---|---|---|---|---|
| MPS gives no fault isolation (Volta+) | 17, 19 | **Confirmed**, moved to the new Table E.13 | NVIDIA MPS docs, `when-to-use-mps.html`, "Memory Protection and Error Containment": a fatal fault from one Volta MPS client is reported to all clients on the GPUs it shares, and those clients must exit. MIG intro confirms MIG's bandwidth and fault isolation. | ch17 Table 17.1 "None (a fatal fault hits all clients)": correct |
| MPS gives no memory-bandwidth isolation | 17 | **Still unverified**, kept as E.14 row 1 | The MPS docs describe only SM (active-thread) and memory-capacity provisioning. No statement either way. | Hedged: Table 17.1 is `[ILLUSTRATIVE]` |
| Several NICs offer "lossy RoCE" modes | 9 | **Partly confirmed** (one vendor); kept in E.14 | NVIDIA ConnectX lossy-RoCE accelerations: adaptive retransmission (DOCA "Adaptive Retransmission" page) and slow restart (mlx5 `counters.c` has `roce_adp_retrans` and `roce_slow_restart`). No second vendor was confirmed from primary documentation. | Hedged: ch09:243 `[VENDOR-SPEC, 2026-10 — verify per NIC and firmware]` |
| CMIS VDM: bad media side + clean host side → fiber/optics | 10 | **Confirmed (definitions)**, moved to E.13 | OIF-CMIS-05.3 defines separate Media Input and Host Input VDM observables (SNR, LTP, pre-FEC BER, FERC). The localization step is engineering inference, and the row says so. | ch10:188–192 OK |
| BFD fabrics usually disable GR or let BFD override it | 7 | **Standards part confirmed**, moved to E.13. The "usually" part is practice and stays in E.14 | RFC 5882 §4.3.1: with control-plane-independent BFD (C bit set), a BFD failure SHOULD abort an in-progress graceful restart | ch07:217–219: suggested tightening below (optional) |

## 2. Version check per component

"Latest known" is the newest release found on 2026-11-05 (GitHub releases API or vendor docs).

| Component | Stated in App. E | Exists? | Latest known (2026-11-05) | Framing OK? |
|---|---|---|---|---|
| CUDA / Programming Guide | Guide v13.4.2; GPUDirect "CUDA 12.x–13.x" | Yes | CUDA 13.5 (R620 branch); Guide v13.5 (updated 2026-10-31) | Yes ("Applies to" is stated). The E.1 CC 9.0 row now notes v13.5 is unchanged. |
| NVIDIA driver / nvidia-smi | R525/R530/R570, v590, "doc to v610" | Yes | nvidia-smi doc covers to v615; CUDA 13.5 pairs with R620 | Yes |
| NCCL | 2.19–2.32.3 tags | Yes, all tags resolve | v2.32.3-1 (2026-09-17) is the latest | Yes, current |
| nccl-tests | `master` | Yes | — | Yes |
| DCGM | 3.3.9, 4.5.3, 4.6.0/4.6.1, 4.7.0 | Yes | v4.7.0 is the latest tag | Yes, current |
| dcgm-exporter | 4.8.4 | Yes | 4.8.4 (2026-09-18) | Yes, current |
| PyTorch | 2.15 docs / `main` | Yes | v2.15.0 (2026-10-28) | Yes, current |
| Megatron-LM | `main`, 2026-10 | Yes | core_v0.20.0 (2026-10-29) | Yes. The row was reworded (see §3). |
| vLLM | v0.19.1, v0.20.0, v0.32.0 | Yes | v0.32.0 stable (2026-10-18); v0.33.0rc3 pre-release | Yes |
| Kubernetes | 1.34 | Yes | v1.37.2 | Yes ("as of 1.34"). DRA GA in 1.34 still holds. |
| Kueue | v0.15.0, v0.20.0, v0.20.4 | Yes; release dates match (2025-11-28, 2026-09-30, 2026-10-29) | v0.20.5 (2026-11-05) | **Fixed**: "v0.20.4 (latest, 2026-10-29)" now reads "released 2026-10-29; v0.20.5 followed on 2026-11-05" |
| Slurm | 25.05 / 26.05 docs | Yes | 26.05.5 (26.11.0rc1 tagged) | Yes. bf_window 1,440 min and bf_resolution 60 s confirmed. |
| GPU Operator / device plugin | Not versioned in App. E (GFD/device plugin `main`) | — | GPU Operator v26.7.2; k8s-device-plugin v0.20.1 | OK. The new CVE row states GPU Operator < 24.6.2. |
| NVIDIA Container Toolkit | (new) v1.20.1 | Yes | v1.20.1 | New E.13 row |
| NIC firmware / MLNX_OFED / DOCA | Not versioned in App. E; MFT 4.35 | MFT 4.35 doc page resolves | MFT 4.37; DOCA 3.5.0 docs | Yes for MFT. Chapter firmware strings (ch20 28.42.1000 and 28.43.1014; ch23 28.39.1002) are real ConnectX-7 releases. ch20's 28.44.0500 has no release notes, but the scenario uses it as a deliberately out-of-policy value, so that is fine. |
| Switch OS (SONiC, FRR) | `master` | Yes | FRR 10.7.1 | Yes |
| Storage (S3, fio, GDS) | AWS current; fio 3.x; GDS v1.19.1 | Yes | fio 3.43; GDS docs at v1.20 | Yes |
| Nsight Systems / Compute | (new) 2026.6 / 2025.4 vs 2026.1 | Yes | nsys 2026.6; ncu 2026.4 | New E.13 rows. **Chapter contradiction** found (§5). |
| pciutils, rdma-core | 3.6–3.15; `master` | Yes | pciutils 3.15.0; rdma-core v65.0 | Yes |

**Chapter versus Appendix E:** grep found no chapter version statement that contradicts Appendix E (ch01/02/04/18 DCGM 4.6/4.7; ch08 NCCL 2.21/2.22; ch13 NCCL 2.29; ch17 K8s 1.34; ch06 driver 575.57.08, which is a real release). The one contradiction is ch04's Nsight Compute clock default (§5).

**REFERENCE_CLUSTER.md lag.** The software baseline (docs/REFERENCE_CLUSTER.md lines 90–92) is older than the releases Appendix E checks. Proposed replacement:

- Old: `Ubuntu 22.04/24.04 LTS; NVIDIA data-center driver 550/570-series; CUDA 12.x; NCCL 2.2x;`
  New: `Ubuntu 22.04/24.04 LTS; NVIDIA data-center driver 570/580-series or newer; CUDA 12.x–13.x; NCCL 2.2x–2.3x (Appendix E checks 2.32.3);`
- Old: `PyTorch 2.x; vendor RDMA stack (MLNX_OFED/DOCA-host class) with matching NIC firmware; Slurm 23.x/24.x;`
  New: `PyTorch 2.x (Appendix E checks 2.15); vendor RDMA stack (MLNX_OFED/DOCA-host class) with matching NIC firmware; Slurm 24.x–26.x (Appendix E checks 25.05/26.05);`
- Old: `Kubernetes 1.30+ with the NVIDIA GPU Operator/device plugin; Prometheus + Grafana; DCGM exporter.`
  New: `Kubernetes 1.34+ (DRA GA) with the NVIDIA GPU Operator/device plugin; Prometheus + Grafana; DCGM 4.x with dcgm-exporter 4.x.`

## 3. Appendix E and VERIFIED_FACTS fixes made

| Location | Fix |
|---|---|
| E intro | Added a note on rows dated 2026-11-05 |
| E.1, CC 9.0 row | Source corrected: the Programming Guide gives the per-SM limits but **not** the 132-SM count, which comes from the H100 architecture whitepaper. Guide v13.5 noted. |
| E.2, Megatron row | The old row ("expects `CUDA_DEVICE_MAX_CONNECTIONS=1`") was imprecise. Current `arguments.py` asserts `=1` only for TP/CP > 1 on arch < 10 (Hopper and earlier). It is not required from Blackwell, and FSDP asserts ≠ 1. |
| E.8, Kueue row | "latest" corrected (v0.20.5 was released 2026-11-05) |
| E.11, DR4 row | Source clarified: the values are clause 124 standard text. The Stassar slides [80] confirm only the −2.9 dBm launch minimum. |
| New E.13 | 13 verified rows: nsys flags and reports; ncu `-k regex:`/`-c` and the `--clock-control` default change; `ERR_NVGPUCTRPERM`/`NVreg_RestrictProfilingToAdminUsers`; MPS error containment; MIG isolation; Container Toolkit envvar default; CVE-2024-0132; PSS levels; `rdma system set netns exclusive`; `cosign verify`; RFC 5882 BFD/GR; CMIS VDM host/media observables; reading-list serving projects. Sources [86]–[101]. |
| E.13 → E.14 | The unverified table is renumbered E.14 and narrowed to three residual claims. The MPS index URL is renumbered [102]. No file outside Appendix E refers to "Table E.13". |
| VERIFIED_FACTS, NCCL GDR log lines | Old: "INFO level (2.18–2.28; newer builds may demote these lines to TRACE)". New: INFO through 2.29 (2.29 format change), TRACE from 2.30. Checked in `paths.cc` at v2.18.6, v2.28.9, v2.29.7, v2.30.3 and v2.32.3. It now agrees with Table E.4. |
| VERIFIED_FACTS, DCGM ECC/row remap | `ROW_REMAP_FAILURE` 395 → `ROW_REMAP_FAILED` 395 (canonical from 4.6; `_FAILURE` alias), to match E.3 and `dcgm_fields.h` v4.7.0 |
| VERIFIED_FACTS, new section | Added the 2026-11-05 additions (ncu clock default, MPS containment, Megatron, Container Toolkit/CVE, RFC 5882, SM-count source) |

Content spot-checks against tagged source matched Appendix E and VERIFIED_FACTS for all of the following: DCGM field IDs, aliases and units (4.7.0, 4.6.1, 4.5.3, 3.3.9); exporter default counters; `dcgmi` pause/resume/-P; the NCCL IB_TIMEOUT 18→20 change; RETRY_CNT, QPS, TC and GID defaults (2.20 = 0, 2.21 = −1 + ROCE_VERSION_NUM 2); the four WARN formats; PXN, CROSS_NIC and NVLS defaults; `/GDRDMA`; `P2P/CUMEM` vs `P2P/IPC` (2.32.3 also prints `P2P/MNNVL` on multi-node NVLink); LL128; nccl-tests warm-up; vLLM block size and the 0.9 → 0.92 change; V1 metric names; PyTorch DDP, timeout, flight recorder, DCP and torchrun; Megatron rank order; Kueue condition/cohortName and release notes; Topology Manager; device plugins; drain flags; GFD labels; Slurm backfill, fair-tree and gres; mlx5 counters; H100 product-page specs (989/1,979 dense = datasheet 1,979/3,958 with sparsity; 3.35 TB/s; 900 GB/s NVLink; 700 W; PCIe Gen5 128 GB/s bidirectional).

**Not re-confirmed on current pages, but not contradicted:** "topology/block from 23.11, reworked 24.05". The current Topology Guide mentions only the 25.05 `topology.yaml` change. QOS enforcement "`limits,qos`": slurm.conf says `limits` enforces association limits and `qos` requires a valid QOS. The combination is sufficient, but the docs do not phrase it as "only with". Both rows were left as dated 2026-10-30.

**Cross-file consistency (H100 SXM, NVLink, PCIe Gen5, ConnectX-7, 400G optics).** Chapters, Appendix E and VERIFIED_FACTS agree: 989/1,979 TFLOP/s dense, 3.35 TB/s, 450 GB/s per direction (900 total), 700 W, 10.2 kW node, Gen5 x16 ≈ 63 GB/s raw and 50–55 GB/s achievable, x8 ≈ 200–220 Gb/s, DR4 −2.9/+4.0/−5.9 dBm and 3.0 dB, RS(544,514) ≈ 78 M codewords/s. No contradictions found.

## 4. Bibliography fixes

All entries in `further-reading.md` were checked against known publication metadata. RFC titles and dates were checked against rfc-editor.org JSON for 17 RFCs. arXiv metadata was checked for Choukse et al. 2508.14318, Kokolis et al. 2410.21680 and Dixit et al. 2102.11245.

| Entry | Fix |
|---|---|
| Ch. 7, RFC 5881 | Abbreviated title "BFD for IPv4 and IPv6 (Single Hop)" changed to the full RFC title "Bidirectional Forwarding Detection (BFD) for IPv4 and IPv6 (Single Hop)" |
| Ch. 7, PMTUD RFCs | Added the missing years: RFC 1191 (1990), 8201 (2017), 4821 (2007), 8899 (2020) |

No wrong authors, venues or years were found elsewhere.

## 5. Dead links

All 102 numbered URLs in Appendix E were fetched with HTTP status checks: the original 86 (one renumbered to [102]) plus 16 new. A control fetch of non-existent tags and pages returned 404, so the 200s are meaningful. **All returned 200. Dead links: 0.** More than 60 of them were also content-checked (see §3). One redirect: the old MLNX_EN docs on docs.nvidia.com now 302 to networking-docs.nvidia.com. That page is not cited in Appendix E.

## 6. Coordinator items

| Item | Result |
|---|---|
| NCCL GDR log level (VERIFIED_FACTS vs App. E) | Appendix E was right; VERIFIED_FACTS was corrected (§3) |
| Nsight rows for ch04 | Added to E.13. Found the ch04 contradiction (below). |
| Ch15 SGLang/TRT-LLM/NIXL/TGI | The concise `ch15.md` names **none** of these (case-insensitive grep). Only `further-reading.md` names vLLM, SGLang, TensorRT-LLM and Dynamo, and an E.13 row now records their latest releases. TGI maintenance mode is verified (`huggingface/text-generation-inference` README: "now in maintenance mode"). NIXL exists (ai-dynamo/nixl v1.5.2). Neither appears in the concise text, so no row was added. Use these facts if the full edition needs them. |
| Ch19 security facts | All five verified and added to E.13 (Toolkit envvar default `true` at v1.20.1; CVE-2024-0132 < 1.16.2 / GPU Operator < 24.6.2; PSS levels, with baseline forbidding privileged and hostPath; `rdma system set netns exclusive`; `cosign verify`). No chapter correction is needed. |

## 7. Chapter edits needed (not made)

1. **Required. `concise/ch04.md` line 218** (Nsight Compute default changed in 2026.1):
   - Old: `It locks clocks to\nbase by default, so pass `--clock-control none` to compare with production.` (the text wraps after "locks clocks to")
   - New: `It locks clocks by default\n(to base through 2025.4, to boost from 2026.1), so pass `--clock-control none` to compare with production.`
2. **Optional (precision). `concise/ch07.md` lines 217–219:**
   - Old: `BGP graceful\nrestart left on alongside BFD keeps forwarding on stale routes and masks the failure BFD detected, so\nBFD-based fabrics usually disable it or let BFD override it`
   - New: `BGP graceful\nrestart left on alongside BFD can keep forwarding on stale routes and mask the failure BFD detected unless a BFD failure aborts the restart (RFC 5882 §4.3), so\nBFD-based fabrics usually disable it or let BFD override it`
3. **Optional (precision). `concise/ch13.md` line 173:**
   - Old: `Megatron-style TP overlap sets `CUDA_DEVICE_MAX_CONNECTIONS=1` `[VENDOR-SPEC, 2026-10]`.`
   - New: `Megatron-style TP overlap sets `CUDA_DEVICE_MAX_CONNECTIONS=1` on Hopper-class GPUs (current Megatron drops the requirement from Blackwell; FSDP wants it unset) `[VENDOR-SPEC, 2026-10]`.`
4. **`docs/REFERENCE_CLUSTER.md` lines 90–92:** the software-baseline update in §2.
