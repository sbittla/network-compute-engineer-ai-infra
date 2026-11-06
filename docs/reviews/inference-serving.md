# Specialist review: Chapter 15, LLM Inference and Serving Infrastructure

**Review type.** AI-assisted specialist technical review (LLM inference-serving perspective). This is
**not** an independent external human review and does not replace one.

**Date.** 2026-11-05

**Scope.**

- `concise/ch15.md` (published concise text): full technical review, fixes applied.
- `book/part-4-distributed-ai/ch15-llm-inference-serving/manuscript.md` (full edition): consistency
  with the concise text, recomputation, fixes applied.
- `capstones/capstone-d-llm-inference-platform/README.md`, `capstones/capstone-h-disaggregated-llm-serving/README.md`:
  read-only consistency check (no numeric errors found, so nothing was edited).
- Canonical sources: `docs/REFERENCE_CLUSTER.md` (HX8, ORION-256, W-INFER), `docs/VERIFIED_FACTS.md`,
  `concise/back/a-reference-configuration.md`, `concise/back/e-sources-and-versions.md` (Table E.6, vLLM),
  Chapter 21's $3.00 per nominal GPU-hour, the L2 bundle `lab/l2/results/gpu-rtx-4060-laptop-gpu/` and the
  hands-on run `lab/handson/results/wsl2-rtx4060-laptop/` (vLLM 0.30.0, RTX 4060 Laptop GPU 8 GB).

**Word budget.** The concise chapter was at 3,997 words before the review and is at **3,998** after it
(`python scripts/build_concise.py --check`: `OK ch15 3998 words`). To make room for the additions, I
trimmed redundant wording (findings F13–F14). `scripts/copyedit_lint.py ch15`: 0 findings.

## Findings

Severity: **High** = wrong number or a misleading evidence claim a reader would act on; **Medium** =
a stale or incomplete version statement, a mislabel, or a missing scope item; **Low** = clarity,
consistency or editorial; **Info** = checked, no change needed.

| ID | Section | Severity | Finding | Resolution |
|---|---|---|---|---|
| F1 | 15.3 (both editions) | Medium | "leaving 86 % of post-weight memory for KV `[MEASURED]`": only the 138 MB activation reserve was measured. The 6.25 GB / 86 % is arithmetic with an assumed 0.90 fraction, and the L2 report labels it `[MODELED]`. The concise sentence also did not name the host inline. | **Fixed.** Now reads 138 MB `[MEASURED]`, then 86 % `[MODELED]`. The concise text says "L2 laptop run" (Table 15.2 names the RTX 4060 Laptop GPU). |
| F2 | 15.4 concise / 15.5 manuscript | Medium | "vLLM ... currently defaults to recompute" suggests swap is a selectable alternative. Per Appendix E (v0.32.0), V1 preempts the last-admitted request under FCFS, and its preemption is recompute; swap was a V0 mode. | **Fixed.** Concise: "vLLM V1 preempts the most recently admitted sequence, by recompute". Manuscript: same, plus "swap was a V0 option". The generic swap description stays as a technique. |
| F3 | Troubleshooting (concise) | Medium | The metrics sample uses the V0 gauge `vllm:gpu_cache_usage_perc` with only "names vary by version". Appendix E says the Chapter 15 sample is labelled as an older release, and a reader could copy the V0 name into a V1 alert. The manuscript already has the V0/V1 note. | **Fixed.** Now reads "(older-release names; V1 reports `vllm:kv_cache_usage_perc` ...)". This matches E.6 and the hands-on run, which exposed `vllm:kv_cache_usage_perc`. |
| F4 | 15.6 concise / 15.8 manuscript | Medium (scope) | Serving economics: the chapter recommends "T for cost per token" but never states a cost per token. No other chapter prices inference tokens (Chapter 21 prices training tokens). | **Fixed.** Concise: one clause, $0.53 (T) vs $2.43 (L) per million output tokens at saturation, at Chapter 21's $3.00/GPU-h `[MODELED]`. Manuscript: the same, plus the worked example's realized ≈ $3.26 per million output tokens (5 nodes). |
| F5 | Safety box (concise) | Medium (scope) | Autoscaling was absent from the concise text apart from "scale out" in the runbook. The key infrastructure point, that cold start outlasts a burst, was missing. The manuscript has an "Autoscaling and cold start" paragraph. | **Fixed.** Concise clause: start-up "outlasting a 45-second burst. Absorb bursts with N+1 headroom, not reactive scale-out". |
| F6 | 15.2 | Low (scope) | Pipeline parallelism for serving was not mentioned in either edition. | **Fixed in the manuscript** (one paragraph: PP across nodes for models larger than one NVLink domain, 16 KiB per sequence per stage boundary, a per-step network hop; W-INFER fits one HX8). **Open in the concise text**: no word budget. *Recommendation:* if words are freed later, add "Pipeline parallelism across nodes serves models larger than one node, at a network hop per stage per step." |
| F7 | 15.4 concise | Low (scope) | Quantization in the concise text covers FP8 weights and FP8 KV only. INT8/INT4 are in manuscript Table 15.4. | Accepted as sufficient for the concise scope. No change. |
| F8 | Fig. 15.1 (both) | Low | The figure says "TP all-reduce per layer"; the prose says two per layer (160 per step). Not wrong, only less specific. | No change. |
| F9 | Capstone H README | Low | "Relation to Chapter 15 (Sections 15.10–15.12)" uses full-edition numbering. In the concise edition these are 15.7 and the worked example. | **Open** (capstones are read-only). *Recommendation:* name the sections ("KV cache transfer", "Worked example") instead of numbering them. |
| F10 | Capstone H README | Info | It uses its own declared assumptions (RDMA 90 %, 4 ms overhead, prefill MFU 0.5, TP = 8 BF16, 30 req/s) and states how they differ from Chapter 15. All arithmetic recomputed correctly (see below). | No change. |
| F11 | Capstone D README | Info | Consistent with the chapter: 320 KiB/token, BF16 140 GB / FP8 70 GB, the SLOs, and cost per million tokens as a deliverable. | No change. |
| F12 | 15.4 (both) | Low | "Continuous batching, introduced by Orca ... `[VENDOR-SPEC, 2026-10]`": a peer-reviewed paper claim carries a vendor label. This follows the book's convention for external sources. | **Open.** *Recommendation:* decide book-wide whether literature claims carry `[VENDOR-SPEC]` or a plain citation. |
| F13 | 15.5 concise | Low (editorial) | "and 3.5× at ρ = 0.71". The value is correct (Erlang p95/mean = 3.49) but nothing else in the concise text uses it. | Removed from the concise text for word budget; kept in the manuscript. |
| F14 | 15.1, 15.7, Troubleshooting concise | Low (editorial) | Redundant wording: "only the last column comes from a run" (the caption already says which column is measured); "(3:1 by port count)"; "perhaps" before an `[ILLUSTRATIVE]` range; "(SM)", an acronym used once. | Trimmed for word budget. The canonical 1.5:1-by-bandwidth and 1:1-as-populated statements are kept. |
| F15 | 15.4 manuscript | Low (version) | SGLang, TensorRT-LLM, NIXL/Dynamo, Mooncake and the "TGI in maintenance mode" claim have no rows in Appendix E. They carry `[VENDOR-SPEC, 2026-10]` and "verify", but no source date in E. The concise text does not mention them. | **Open.** *Recommendation:* add E rows for the TGI maintenance-mode claim and the KV-connector names, or soften the manuscript to "check current docs". |
| F16 | 15.8 / 15.11 (models) | Info | The speculative-decoding verification model ignores attention FLOPs and extra KV reads during verification. The decode step model uses one HBM efficiency. Both are labelled `[MODELED]` with assumptions stated, and the realism boundaries cover them. | No change. |
| F17 | Simulated results | Info | The canary trace states what it models (seed 15, V0-like vLLM, chunked prefill off, recompute preemption, HBM efficiency 0.60, Poisson + burst + `longctx`) in Table 15.1a. The concise Table 15.2 keeps the essentials (simulator patterned on an older vLLM, chunked prefill off). The scenario is labelled `[ILLUSTRATIVE]` over `[SIMULATED]` data. | No change. |
| F18 | Generalization | Info | H100 values are labelled `[VENDOR-SPEC, 2026-10]`. ORION/HX8, the SLOs and the efficiencies are `[ILLUSTRATIVE]`. The L2 caption says shapes transfer and absolute latencies do not. The canary deviation (TP = 2 on `orion-n29`) is declared. | No change. |
| F19 | Mermaid | Info | Fig. 15.1 (both editions) and Fig. 15.3 (manuscript: P1..P6 and D1/D2, i.e. 6P + 2D; blocks reserved before prefill) match the prose. | No change. |

**Counts.** High 0; Medium 5 (F1–F5, all fixed); Low 9 (F6, F8, F9, F12, F13, F14 fixed or no change
needed; F6 open in the concise text only; F9, F12, F15 open); Info 5.

## Recomputations

All checked against the text. No numeric error was found in either edition.

```text
Ridge  BF16 989e12/3.35e12 = 295.2 FLOP/B; FP8 1,979e12/3.35e12 = 590.7
Decode attention intensity: FLOP 4·ctx·8,192 / bytes 4,096·ctx = 8 FLOP/B
Prefill 2×70e9×2,048 = 2.867e14; TP8 BF16 /(8×989e12×0.40 = 3.165e15) = 90.6 ms;
        TP4 FP8 /(4×1,979e12×0.40 = 3.166e15) = 90.55 ms
Causal attention 2×80×2,048²×8,192 = 5.50e12 (1.9 % of prefill); ×256 at 32k
Decode floor TP8 BF16 140e9/(8×3.35e12) = 5.22 ms → 191 tok/s
TP all-reduce 32×8,192×2 = 512 KiB; ring 1.75×512 KiB/450 GB/s = 2.0 µs; 160 × 5–15 µs ≈ 0.8–2.4 ms
KV/token 2×80×8×128×2 = 327,680 B; 4,096 tok = 1.342 GB; MHA (64 heads) 8× = 10.7 GB
Budgets  TP8: 576−140−16 = 420 GB → 420e9/5,242,880 = 80,108 blocks → 312 seqs
         TP4: 288−70−8 = 210 GB → 40,054 → 156;  TP2: 144−70−4 = 70 GB → 13,351 → 52
Theory→usable (TP4 FP8): 250 GB → 186; 218 GB → 162; 210 GB → 156; ×0.90 → 140 (75 %)
TP2 70e9/327,680 = 213,623 tokens
Swap 10k tok = 3.28 GB; recompute 10k on TP2 FP8 = 10,000 × 88.4 µs = 0.88 s
Chunk 2×70e9/(4×1,979e12×0.4) = 44.2 µs/token × 512 = 22.6 ms; worst ITL 12.7+22.6 = 35.3 ms
FP8 KV 210e9/(16×163,840) = 80,108 blocks → 312 seqs
L2 KV 8.59 GB×0.90 − 1.34 − 0.138 = 6.25 GB; 6.25/7.25 = 86.2 %  (138 MB MEASURED; rest MODELED)
Little 40×256×0.023 = 236 sequences
M/D/1 (numerical Erlang CDF): ρ=0.45 mean 0.409 t_s, p95 1.766 t_s (4.32×);
      ρ=0.4528 mean 0.414, p95 1.780 (4.30×); ρ=0.71 mean 1.224, p95 4.277 (3.49×)
Layouts  L: 3 + (140e9+32×713.03e6)/18.76e12 = 3+8.68 = 11.68 ms; 32/0.01168 = 2,740 tok/s; 86 tok/s/user
         T: 3 + (70e9+128×713.03e6)/9.38e12 = 3+17.19 = 20.19 ms; 256/0.02019 = 12,678 tok/s (4.63×); 50/user
Economics (new) node 8×$3.00 = $24/h
         T 12,678×3,600 = 45.64 M tok/h → $0.526/M;  L 2,740×3,600 = 9.86 M/h → $2.43/M
         worked example 5 nodes $120/h ÷ (10,240×3,600 = 36.86 M/h) = $3.26/M output tokens
KV transfer 2,048×327,680 = 671.09 MB; ×40 = 26.84 GB/s = 214.7 Gb/s;
         per layer 8.39 MB / 170 GB/s = 49 µs vs 90.6/80 = 1.13 ms prefill
         RDMA 30 µs + 5.369e9 b/1.36e12 = 3.98 ms; TCP 1 ms + 5.369e9/100e9 = 54.7 ms
Spec decoding E = (1−0.8^5)/0.2 = 3.36; 3.36/1.2 = 2.80×
         B=128,k=4: 2×70e9×640/3.166e15 = 28.3 ms vs 17.2 ms memory → +3 = 31.3/20.19 = 1.55;
         3.36/(0.2+1.55) = 1.92×;  k=2: 384 tok → 16.98 ms (memory-bound) → 2.44/1.1 = 2.22×
         k=8: 1,152 tok → 50.9+3 = 53.9/20.19 = 2.67; E=4.33 → 1.41×;  α=0.5,k=8: 2.0/1.4 = 1.43×
         effective ridge 591×0.4/0.7 = 338 vs 8.96e13/161.3e9 = 556 FLOP/B
Worked example t_d = 3 + 7.463 + 0.0760·B ms
         shared 8: ρ=0.4528, Wq = 37.5 ms, TTFT 128 ms; TPOT = 0.010463/(0.5472−0.0973) = 23.3 ms, B 29.8
         six: ρ=0.6037, TPOT = 0.010463/(0.3963−0.1297) = 39.2 ms → rejected
         KV in use 8×29.8×713 MB = 170 GB of 1,680 (10 %); TTFT p95 161+90.6 = 252 ms
         Poisson(29.7) p95 = 39 → (255×12.73+39×90.55)/255 = 26.6 ms; 1−e^−0.1165 = 11 % of gaps
         P:D  4:4 ρ .906 TTFT 524 TPOT 13.0 B 33 | 5:3 .724 210 14.1 48 | 6:2 .604 160 17.1 88 | 7:1 .517 139 47.2 484
         RDMA 107.4/1,360 = 7.9 %; TCP 107.4/100 = 107 %; 5:3 71.6/100 = 72 %
Safety 8 nodes × 140 GB = 1.12 TB / 160 GB/s = 7.0 s; one node 140 GB / 50 GB/s = 2.8 s
r3 prefill share 1.7 × (1,444×88.4 µs + 3 ms) = 0.22
Capstone H 436 GB/327,680 = 1,330,566 tok; prefill 2.922e14/3.956e15 = 73.9 ms; 32k 1.52 s (23 % attention);
         decode 358 GB/18.76 TB/s = 19.1+4 = 23.1 ms; KV 0.671 GB /360 = 1.86 ms, /45 = 14.9, /30 = 22.4 ms;
         prefill emit 28,300 tok/s × 327,680 = 9.3 GB/s = 74 Gb/s (2.3 % of 3.2 Tb/s; 31 % of 30 GB/s);
         30×2,422×327,680 = 23.8 GB/s; 5P2D 11.9 GB/s (3 % RDMA, 40 % TCP); D=1 79 %
```

## Version-sensitive guidance (Appendix E consistency)

- `--gpu-memory-utilization` default (0.90 → 0.92 at v0.20.0): the concise text says "changed between
  releases, set it explicitly"; the manuscript says "0.90 in older releases, 0.92 now". Both are consistent with E.6.
- 16-token default block: consistent (E.6, v0.32.0).
- Preemption policy and mode: fixed to match E.6 (F2).
- Metric names: fixed in the concise text (F3). The manuscript's V0/V1 note matches E.6.
- `--max-num-seqs` / `--max-num-batched-tokens` (manuscript): consistent with E.6.
- SGLang, TensorRT-LLM, Dynamo/NIXL, Mooncake, TGI: manuscript only, hedged, with no E rows (F15, open).

## Completeness verdict

For the book's stated scope (an infrastructure book, not a serving-internals book), the chapter is
**sufficient after this review**:

| Topic | Concise | Manuscript |
|---|---|---|
| Continuous batching, prefill interference, chunked prefill | Yes | Yes |
| KV-cache pressure, preemption, storm signature | Yes | Yes |
| Paged attention | Yes | Yes |
| Prefix caching | Yes (brief, with demand effect and risks) | Yes |
| Speculative decoding (incl. large-batch breakdown) | Yes | Yes |
| Tensor parallelism for serving | Yes | Yes |
| Pipeline parallelism for serving | **Gap (open, F6)**: implied only by "TP beyond NVLink rarely pays" | Added (F6) |
| Quantization | FP8 weights and KV only (acceptable) | FP8/INT8/INT4/FP8 KV |
| SLOs (TTFT/TPOT/ITL, goodput, phase SLIs) | Yes | Yes |
| Autoscaling and cold start | Added (F5), one clause | Yes |
| Serving economics ($/M tokens) | Added (F4) | Added (F4) |
| Disaggregation (KV bytes, transport, QoS, failure) | Yes | Yes |

**Release gate:** pass for Chapter 15 technical content. Open items F6 (concise only), F9, F12 and F15
are low severity and do not block release.
