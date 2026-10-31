# Copyedit Register — Release Gate G6, Phase 1

**Status:** phase 1 (survey and register) complete on 2026-10-30. No chapter has been edited. Phase 2 agents
apply this register chapter by chapter, then re-run the lint.

**Scope surveyed:** every `manuscript.md`, `exercises.md`, chapter `README.md` and `lab/README.md` under
`book/`, plus `capstones/README.md`, each `capstones/*/README.md` and each `capstones/*/starter-kit/README.md`
(113 files). `review/REVIEW.md` files are historical records and are excluded. Fenced code, inline code, log
samples, CLI output, YAML/JSON, link targets and identifiers are never normalised: the lint masks them before
any rule runs.

**Authorities, in order:** [STYLE_GUIDE.md](STYLE_GUIDE.md) → [VERIFIED_FACTS.md](VERIFIED_FACTS.md) →
[REFERENCE_CLUSTER.md](REFERENCE_CLUSTER.md) → this register (for questions the first three leave open) →
majority usage in the book.

**Tool:** [`scripts/copyedit_lint.py`](../scripts/copyedit_lint.py) re-detects every MECHANICAL finding,
plus broken relative links and anchors and Section/Table/Figure/Chapter references that do not resolve.
Run `python scripts/copyedit_lint.py ch07` before and after editing a chapter. It exits non-zero while
findings remain.

## How to apply (phase 2)

1. Work one file at a time from §(d). Apply edits **bottom-up** (highest line first), and within one line
   **right-to-left** (highest Col first), so the positions and context of the remaining items stay valid.
2. **MECHANICAL**: replace *Current* with *Replacement* on that line. Both cells quote the exact text with
   one word of context. If the line has moved, `python scripts/copyedit_lint.py <path-fragment>` gives the new
   position.
3. **JUDGEMENT**: read the paragraph, then make the change the *Replacement* column describes, or record in
   the chapter's review notes why you did not. Never change a number that VERIFIED_FACTS or
   REFERENCE_CLUSTER pins.
4. Do not touch text inside backticks or fences, cited titles of external works, or verbatim quotations.
   If a MECHANICAL rule fires on such text, add `<!-- copyedit-lint: ignore -->` to the line and note it in
   the chapter's review notes.
5. Re-run the lint on the chapter. MECHANICAL categories must reach zero. Report any JUDGEMENT item you
   left open.

## Summary

| Category | What it covers | MECHANICAL | JUDGEMENT | Total |
|---|---|---|---|---|
| UNIT | unit/number formatting (no bits-vs-bytes errors found) | 63 | 3 | 66 |
| XREF | Section/Table/Figure/Chapter target missing | 0 | 0 | 0 |
| LINK | broken relative link or anchor | 0 | 0 | 0 |
| ORION | deviation from REFERENCE_CLUSTER / VERIFIED_FACTS | 0 | 20 | 20 |
| LABEL | evidence-label form, date, missing caption label | 41 | 17 | 58 |
| ACRONYM | first-use expansion and expansion wording | 15 | 320 | 335 |
| TERM | product/protocol/book terms | 110 | 1 | 111 |
| SPELLING | general-English house spelling | 236 | 0 | 236 |
| XREF-STYLE | "§N.M" → "Section N.M" | 47 | 0 | 47 |
| CAPTION | table without a caption | 0 | 64 | 64 |
| STYLE | "vs." and glossary-paragraph form | 7 | 11 | 18 |
| **All** | | **519** | **436** | **955** |

**955 findings in 80 files** (of 113 in scope). The lint reproduces all MECHANICAL items, the four label-date items and the Ch 8 ethtool line; its current output is:

```text
526 finding(s) in 75 file(s) of 113 scanned
  ACRONYM     15
  LABEL       45
  SPELLING    236
  STYLE       7
  TERM        110
  UNIT        66
  XREF-STYLE  47
    ACRONYM/exp-ber                  2
    ACRONYM/exp-mfu                  8
    ACRONYM/exp-pfc                  2
    ACRONYM/exp-pxn                  1
    ACRONYM/exp-rma                  2
    LABEL/label-backticks            41
    LABEL/label-vendor-date          4
    SPELLING/analyse                 21
    SPELLING/artefact                9
    SPELLING/catalog                 1
    SPELLING/centre                  1
    SPELLING/compounds               5
    SPELLING/fibre                   5
    SPELLING/ize                     131
    SPELLING/judgement               10
    SPELLING/labeled                 9
    SPELLING/microbatch              1
    SPELLING/modelled                12
    SPELLING/queuing                 1
    SPELLING/rerun                   28
    SPELLING/towards                 2
    STYLE/vs-period                  7
    TERM/datacenter                  1
    TERM/datacentre                  10
    TERM/kvcache                     29
    TERM/parallel-eq                 12
    TERM/percentile                  18
    TERM/precision                   1
    TERM/railopt                     10
    TERM/tensorcore                  29
    UNIT/approx-tilde                56
    UNIT/ratio-spaced                4
    UNIT/thousands-space             5
    UNIT/unit-space                  1
    XREF-STYLE/section-sign          47
```


### What was checked and came back clean

- **Cross-references:** all 908 `Section N.M` / `§N.M` / `Table N.M` / `Figure N.M` references resolve
  to a real heading or caption, and every `Chapter N` and `Capstone X` exists. Where a reference names its
  target ("Section 7.3 (Table 7.2)", "Table 9.4 (Section 9.8)"), the table or figure really sits in that
  section. Chapter-title paraphrases in "Chapter N (…)" all match the chapter's subject.
- **Links:** all 769 relative markdown links in scope (and in every other `.md` outside `review/`)
  resolve on disk. All `#anchor` fragments match a GitHub heading slug.
- **Bits vs bytes:** no unit *errors* found. Searches covered switch capacity in TB/s, HBM in Tb/s, NVLink in
  Gb/s, NIC/port rates in GB/s, memory or storage in Gb/s, "Gb"/"Mb" for capacity, and every
  `N Gb/s = M GB/s` / `N Tb/s = M TB/s` conversion (all equal ÷ 8). Every NIC-related "400 GB/s" is the node aggregate of
  8 × 400 Gb/s, and it is stated as such.
- **ORION canonical numbers:** node and switch names, rack/rail/spine counts, ASNs, MTUs, DSCP/TC, RTT/BDP,
  HBM/peak/TDP, node/rack/circuit power, PUE, MTBF/restart, W-TRAIN/W-INFER parameters and storage
  throughput all agree with REFERENCE_CLUSTER, or are declared variations (ORION-128 in Ch 2, expansion
  nodes n33–n40 in Ch 21 and Capstone E, Capstone G's 480-node job, Ch 24's 1,024-GPU interview design).
  The deviations that remain are in §(d), category ORION.
- **Units already uniform:** no `Gbps`/`GBps`/`Tbps`, no `us` for microseconds, no Greek-mu `μs`, no
  missing number–unit space in prose (one exception, ethtool output in Ch 8), no `%` without a space,
  no `x` used as a multiplication sign, `°C` always spaced, `kW` always correct.

### Top 10 most serious findings

There are no bits/bytes errors and no broken cross-references or links, so this list ranks the remaining
findings by how much they could mislead a reader or a grader.

| # | Where | Problem | Fix |
|---|---|---|---|
| 1 | `ch11 manuscript.md:532` | "≈ 450 GB/s large-message plateau of Chapter 12" presented as a plain NVLink figure. VERIFIED_FACTS: a plain ring reaches ≈ 360–380 GB/s; ≈ 450 implies NVLS. Ch 11's TP model inherits the wrong baseline. | Say NVLS and give the ring figure. |
| 2 | `ch12 lab/README.md:46` | Lab acceptance criterion "plateaus ≈ 450 GB/s (c1)" does not say NVLS is assumed (VERIFIED_FACTS: "Acceptance floors must state whether NVLS is assumed"). | Add "(NVLS)" after confirming c1's config. |
| 3 | `ch16 manuscript.md:983` | Validation "busbw 466 GB/s at 8 GiB" exceeds the 450 GB/s per-direction link and is only possible with NVLS; the line does not say so. The label on the same line is also unbackticked. | Add "(NVLS)". |
| 4 | Ch 9, 14, 18, 22 (7 lines) | A Halcyon **Storage** team/on-call appears, but REFERENCE_CLUSTER §5 has no such team. Ch 2 also has "Network team", "Architecture team", "IT team". | Editor decision: add Storage to §5 (recommended), and map the others to Fabric/Facilities/Fleet. |
| 5 | `ch15 exercises.md:117` | RAG design challenge sets TTFT p95 ≤ 1.5 s and TPOT p95 ≤ 40 ms without declaring it a variation from W-INFER's 800 ms / 50 ms. | Declare the variation. |
| 6 | `ch02 manuscript.md:1017`, `ch13 exercises.md:22`, `ch23 lab/README.md:162`, `capstone-e README.md:117` | `[VENDOR-SPEC]` without the checked month (STYLE_GUIDE §3). | Add `, 2026-10`, or use the template `[VENDOR-SPEC, YYYY-MM]` where the label is being described. |
| 7 | 13 quantitative tables (Ch 2, 7, 8, 10, 13, 18, 19, 21, 22) | Caption carries no evidence label although cells hold thresholds or figures (e.g. Table 18.5 burn rates, Table 19.5, Table 10.8 acceptance thresholds). | Add the label suggested in §(d). |
| 8 | Ch 16 (29 labels), Ch 7 (5), Capstone E (6), Ch 22 lab (1) | 41 evidence labels written bare (`[ILLUSTRATIVE]`) instead of in backticks like the other 96 % of labels. | MECHANICAL: wrap in backticks. |
| 9 | 230 manuscript + 80 capstone first uses | Acronym used before (or without) its expansion in that chapter. Most frequent: NIC (18 chapters), NCCL (16), RDMA (12), ECC (10), TP/SM/PXN (9 each). STYLE_GUIDE §6: "Define every acronym on first use in each chapter." | Expand per §(b). |
| 10 | Ch 3 (16), Ch 20 (30), Capstone H (1) | 47 book-section references written `§N.M` instead of "Section N.M" (STYLE_GUIDE §10). Ch 3 also has 11 tables and no table captions at all, unlike every other chapter. | MECHANICAL for `§`. Captions are JUDGEMENT. |

## (a) Canonical terms

### Product, protocol and project names (vendor or standards-body spelling)

| Variant(s) found or to be rejected | Canonical | Reason / evidence |
|---|---|---|
| RoCE v2, RoCE-v2, ROCEv2 | **RoCEv2** | STYLE_GUIDE §6; IBTA Annex A17 usage. 131 uses in 19 files, no variants in prose. |
| Infiniband, infiniband (prose) | **InfiniBand** (IB) | IBTA trademark spelling; STYLE_GUIDE §6. Lower case only appears in paths and directory names, and those stay as they are. |
| allreduce, AllReduce, All-Reduce; allgather/AllGather; reducescatter/ReduceScatter; alltoall/AllToAll | **all-reduce, all-gather, reduce-scatter, all-to-all** (sentence-initial "All-reduce") | STYLE_GUIDE §6; 161 vs 0 in prose. API names (`ncclAllReduce`, `all_reduce_perf`) stay in backticks. "all reduce the power" (Ch 21:729) is a verb phrase, not the collective. |
| GPU Direct, GPUdirect, GDR (unexpanded) | **GPUDirect RDMA** (GDR); **GPUDirect Storage** (GDS) | NVIDIA spelling. "GPUDirect" alone only for the product family. |
| NVlink, NvLink; NVswitch | **NVLink**, **NVSwitch**, **NVLink SHARP (NVLS)** | NVIDIA spelling; 237 / 69 uses, no variants. |
| tensor core(s), tensor-core, Tensor core | **Tensor Core(s)**, also as a modifier ("Tensor Core GEMM") | NVIDIA's own spelling ("H100 Tensor Core GPU"). The book has 29 lower-case uses. Rule `tensorcore`. |
| Nvidia; Connect-X; Bluefield; Pytorch; Deepspeed; VLLM | **NVIDIA, ConnectX, BlueField, PyTorch, DeepSpeed, vLLM, Megatron-LM, nccl-tests, perftest** | Vendor/project spelling. No current violations; the lint guards them. "NCCL tests" (Ch 19, Capstone H) → "nccl-tests" when the tool is meant. |
| PCI-e, PCIE | **PCIe** ("PCI Express" only as its expansion) | PCI-SIG spelling. |
| SLURM, slurm (prose) | **Slurm** | SchedMD spelling. Keep "SLURM:" inside the cited 2003 paper title (Ch 17:1109). |
| k8s, K8s | **Kubernetes** | STYLE_GUIDE §6. None currently. |
| Xid, XID | **Xid** | STYLE_GUIDE §6; NVIDIA usage. 109 uses, no variants. |
| data centre, data-centre, datacenter (prose) | **data center** (noun), **data-center** (modifier) | The Ch 2 title is "Anatomy of an AI Data Center"; US form is used in 12 files against 6 for "centre". Proper names keep their own form (NVIDIA *Data Center* GPU Manager, *Data Center* Quantized Congestion Notification, cited titles such as *The Datacenter as a Computer*). |
| rail-optimised, rail optimized | **rail-optimized** | REFERENCE_CLUSTER spelling; 67 vs 10. |
| KV-cache, kv cache | **KV cache**, also as a modifier ("KV cache transfer") | STYLE_GUIDE §6 lists "KV cache". 38 vs 29, and the hyphenated form is concentrated in Ch 15 and Capstone H. |
| check-point | **checkpoint** | One word. None currently. |
| busbw / bus bandwidth / bus-bandwidth; algbw / algorithm bandwidth | **bus bandwidth (busbw)** on first use per chapter, then **busbw**; same for **algorithm bandwidth (algbw)** | nccl-tests column names. Both forms are fine after the first use. Rewrite "bus-bandwidth" as a modifier to "busbw" ("busbw floor"). |
| tok/s, tokens/sec, tokens per second (in tables) | **tokens/s** (prose may say "tokens per second") | 32 vs 0 abbreviations; matches "req/s". |
| leaf/spine, spine-leaf, Leaf-spine | **leaf-spine** (topology). Use an en dash, "leaf–spine", only for a link *between* a leaf and a spine ("leaf–spine /31s"), as REFERENCE_CLUSTER does. | STYLE_GUIDE §6. JUDGEMENT: the two Ch 7/13 "leaf/spine" uses mean the topology. |
| multitenant, multi tenant | **multi-tenant, multi-tenancy** | Ch 19 title "Reliability, Security, and Multi-Tenancy". The `multitenancy` directory slug is an identifier and stays. |
| P50, P95, P99 | **p50, p95, p99, p99.9** | STYLE_GUIDE §5, including Poisson/demand quantiles (Ch 19, Ch 21, Capstone G). 18 upper-case uses. |
| TP=8, PP=4 | **TP = 8, PP = 4, DP = 8** (also "TP 8 × PP 8 × DP 60" in a product of factors) | REFERENCE_CLUSTER form; 136 vs 12 in prose. Configuration names such as `T-tp4-fp8` are identifiers and stay. |
| bf16, fp8, fp32, bfloat16 | **BF16, FP8, FP16, FP32, TF32** ("bfloat16" only as BF16's expansion) | 103 vs 1 in prose. |
| §3.11, §20.5 (book sections); Ch 16 (prose) | **Section 3.11**, **Chapter 16**. "Ch N" is allowed in table cells; "§N" is allowed for another document's numbered sections (`REFERENCE_CLUSTER.md §3`, `lab/README.md §8`, "Outline §14"). | STYLE_GUIDE §10. |
| ORION names | `orion-nNN` (01–32), `rack-NN`, `orion-be-leaf-rR` (r0–r7), `orion-be-spine-S` (1–4), `orion-fe-leaf-NN`, `orionxl-nNNN`, `orionxl-s00…` (declared spares only) | REFERENCE_CLUSTER "Canonical names". No violations found. |
| Halcyon teams | **Fabric, Fleet, Platform, Training Infra, Inference, SRE, Facilities**, always capitalised ("the Fabric team", "Fabric on-call") | REFERENCE_CLUSTER §5. Open question: **Storage** (used in Ch 9, 14, 18, 22); see ORION findings. |

### General English (house style = the majority form; recorded so future editions keep it)

The book's de facto house style is a hybrid: **-ize/-yze** endings (US/Oxford), but **-our**, **-ll-** and
**-ogue** (UK) where those are the only or the majority form in use. Each row records the majority.

| Variant → canonical | Majority evidence (prose, files) | Notes |
|---|---|---|
| optimise/utilise/organise/initialise/prioritise/synchronise/authorise/localise/… → **-ize, -ization** | -ize ≈ 358 uses vs -ise ≈ 94. "optimize" is in 27 files vs 6, "utilize" in 16 vs 8. | One suffix rule for every verb in the lint's stem list. "organise" alone has a per-word majority for -ise (8 files vs 2), but it follows the family rule for consistency. Cited titles keep their spelling. |
| analyse → **analyze** | 54 vs 23 uses | Matches the lab tool names ("analyzer", which cannot change). |
| behavior → **behaviour** | 130 vs 0 | Only form in use. |
| labeled/labeling → **labelled/labelling** | 82 vs 2; 9 "labeling" in Ch 10 | Keep "labeling" in the ANSI/TIA-606 standard title. |
| modelled/modelling → **modeled/modeling** | 52 vs 9 | Matches the `[MODELED]` label. |
| centre → **center**; fibre → **fiber** | 35 vs 10; 19 vs 5 | Keep "Fibre" in IEC titles ("Fibre optic …") and in "Fibre Channel". |
| catalog → **catalogue** | 9 vs 1 | |
| artefact → **artifact** | 71 vs 9 | |
| queuing → **queueing** | 23 vs 1 | |
| judgement → **judgment** | 13 (10 files) vs 10 (4 files) | This register's MECHANICAL/JUDGEMENT tags are field names, not prose. |
| towards → **toward** | 24 vs 2 | |
| signaled/signaling → **signalled/signalling**; canceled → **cancelled**; favor → **favour** | only UK forms in use | Guarded by the lint. |
| re-run, re-image, re-test → **rerun, reimage, retest**; microbatch → **micro-batch** | rerun 9 files vs 8; reimage 12 vs 6 uses; micro-batch 67 vs 1 | "undrain" is already closed. |
| speed-up, scaleout, over-subscription, burnin, time-out, data set, run-book, post-mortem, fail-over, health-check (noun) → **speedup, scale-out, oversubscription, burn-in, timeout, dataset, runbook, postmortem, failover, health check** | all majority forms | "scale out" (verb) and "time out" (verb) are fine. Compound modifiers before a noun take a hyphen ("health-check endpoint"). |
| vs. → **vs** | 187 vs 8 | "versus" is also fine in running prose. |
| game day / game-day | **game day** (noun), **game-day** (modifier) | Both are in use correctly. Capitalise only in Capstone F's title. |
| on call / on-call | **on-call** (noun/modifier: "the Fabric on-call"); "on call" only predicatively ("the engineer on call") | JUDGEMENT; not linted. |

## (b) Canonical acronym list

Expand each acronym on its first use **in the body of every chapter**, as *expansion (ACR)*. A chapter or
capstone that opens with an **Acronyms** paragraph counts as having defined the acronyms listed there.
Generic expansions are lower case. Proper names (protocols, products, papers) keep their capitals.

| Acronym | Canonical expansion | Notes |
|---|---|---|
| ACS | access control services (PCIe) |  |
| AER | advanced error reporting (PCIe) |  |
| ASIC | application-specific integrated circuit |  |
| BDF | bus:device.function (PCIe address) | PCIe address format |
| BDP | bandwidth-delay product |  |
| BER | bit error ratio | IEEE 802.3 says "ratio"; pre-FEC BER / post-FEC BER |
| BGP | Border Gateway Protocol |  |
| BMC | baseboard management controller |  |
| CDU | coolant distribution unit | not "cooling distribution unit" |
| CNP | congestion notification packet |  |
| DCGM | NVIDIA Data Center GPU Manager | proper name, capitals kept |
| DCQCN | Data Center Quantized Congestion Notification | proper name (Zhu et al. 2015), capitals kept |
| DP | data parallelism / data-parallel |  |
| DSCP | differentiated services code point |  |
| ECC | error-correcting code |  |
| ECMP | equal-cost multipath |  |
| ECN | explicit congestion notification |  |
| FEC | forward error correction |  |
| FSDP | Fully Sharded Data Parallel (PyTorch) |  |
| GDR | GPUDirect RDMA | NCCL log token is `GDRDMA` |
| GDS | GPUDirect Storage |  |
| GQA | grouped-query attention |  |
| HBM | high-bandwidth memory |  |
| HCA | host channel adapter |  |
| IPMI | Intelligent Platform Management Interface |  |
| ITL | inter-token latency (per-token gap distribution; report p95/p99) | not a synonym of TPOT (VERIFIED_FACTS) |
| KV | key-value (as in KV cache) | write "KV cache" (no hyphen) |
| MEP | mechanical, electrical, and plumbing |  |
| MFU | model FLOPs utilization | PaLM (Chowdhery et al., 2022) term; always uses the vendor dense peak (VERIFIED_FACTS) |
| MIG | Multi-Instance GPU |  |
| MoE | mixture of experts |  |
| MTBF | mean time between failures |  |
| MTTR | mean time to repair (nodes/components, REFERENCE_CLUSTER: drain → return to service); "mean time to restore" only for a service in incident context (Ch 18, Capstone F) | see expansion column |
| MTU | maximum transmission unit |  |
| NCCL | NVIDIA Collective Communications Library |  |
| NIC | network interface card |  |
| NUMA | non-uniform memory access |  |
| NVLS | NVLink SHARP | NCCL algorithm name; NVLink SHARP is the hardware feature |
| OOB | out-of-band (management network) |  |
| PDU | power distribution unit |  |
| PFC | priority flow control | IEEE 802.1Qbb is titled "Priority-based Flow Control"; use that only when naming the standard |
| PFS | parallel file system |  |
| PP | pipeline parallelism / pipeline-parallel |  |
| PUE | power usage effectiveness | ORION canonical PUE 1.25 |
| PXN | PCI × NVLink | NCCL feature name |
| QP | queue pair |  |
| RDMA | remote direct memory access |  |
| RMA | return merchandise authorization | one book-wide form |
| RPO | recovery point objective |  |
| RTO | recovery time objective |  |
| RTT | round-trip time |  |
| SHARP | Scalable Hierarchical Aggregation and Reduction Protocol |  |
| SLA | service-level agreement | hyphenated "service-level" |
| SLI | service-level indicator | hyphenated "service-level" |
| SLO | service-level objective | hyphenated "service-level" |
| SM | streaming multiprocessor |  |
| SRE | site reliability engineering / engineer |  |
| TCO | total cost of ownership |  |
| TDP | thermal design power |  |
| ToR | top-of-rack (switch) |  |
| TP | tensor parallelism / tensor-parallel |  |
| TPOT | time per output token (per-request mean) | per-request mean; also see ITL (VERIFIED_FACTS) |
| TTFT | time to first token |  |
| UPS | uninterruptible power supply |  |
| ZeRO | Zero Redundancy Optimizer |  |
| (others) | GPU, CPU, DPU, IP, TCP, UDP, BGP-adjacent terms (eBGP, iBGP), RFC, IEEE | Expand only GPU/CPU-level terms where a chapter targets newcomers; protocol names that are household (TCP, IP) need no expansion |

Variants found and normalised by this register: "Priority-based Flow Control"/"Priority Flow Control" →
priority flow control (keep "Priority-based Flow Control" only when naming IEEE 802.1Qbb); "model FLOP
utilization/utilisation" → model FLOPs utilization; "bit error rate", "bit-error ratio" → bit error ratio;
"PCIe × NVLink" → PCI × NVLink; "return material authorisation", "return-merchandise authorization" →
return merchandise authorization; "mean time to recover" → mean time to restore (services) / mean time to
repair (nodes); "Congestion Notification Packet" → congestion notification packet.

## (c) Unit and number rules

1. **Bits for links, bytes for memory/storage** (STYLE_GUIDE §5). Write `Gb/s`, `Tb/s` for links, ports,
   NICs and switch capacity. Write `GB/s`, `TB/s` for HBM, NVLink, PCIe, host memory, storage and busbw.
   Every conversion divides by 8 (400 Gb/s = 50 GB/s line rate). Say whether a figure is line rate, payload
   or achieved.
2. **Switch capacity is Tb/s; HBM bandwidth is TB/s.** 25.6 Tb/s (switch), 3.35 TB/s (HBM). A
   node-aggregate NIC figure is written "8 × 400 Gb/s = 3.2 Tb/s = 400 GB/s".
3. **Direction and NVLS.** NVLink: "900 GB/s total, 450 GB/s per direction". A single-node all-reduce busbw
   above ≈ 400 GB/s must say NVLS (VERIFIED_FACTS). PCIe Gen5 x16: ≈ 63 GB/s per direction theoretical,
   ≈ 50–55 GB/s achievable.
4. **Never** `Gbps`, `GBps`, `Tbps`, `Gbit/s`, `/sec`. Use `Gb/s`, `GB/s`, `Tb/s`, `MB/s`.
5. **Space between number and unit**: `400 Gb/s`, `80 GB`, `5 µs`, `700 W`, `10.2 kW`, `85 °C`, `40 %`.
   Two exceptions. Port and optic shorthand `400G`, `800G`, `200G` takes no space ("64 × 400G ports").
   Ethernet standard names keep their form: `400 GbE`, `400GBASE-DR4`. The `%` and `°C` spacing is the
   house form (REFERENCE_CLUSTER; 1,070 vs 0).
6. **Time**: `ns`, `µs` (micro sign U+00B5, never `us` or Greek `μ`), `ms`, `s`, `min`, `h`, `d`.
   `GPU-h` and `node-hours` are both in use; prefer `GPU-hours` in prose and `GPU-h` in tables and formulas.
7. **Memory units**: SI (`GB` = 10⁹ B) for bandwidth, storage and checkpoint sizes; IEC (`GiB`, `KiB`) for
   memory capacity when precision matters (320 KiB/token, 2 TiB DDR5). Say so when converting.
8. **Thousands separators**: commas for quantities ≥ 1,000 (`1,536 h`, `4,096 GPUs`, `327,680 B`), never
   spaces (`400 000` → `400,000`). Identifiers and protocol values take no separator: MTU 9000/9216/4096,
   ASNs, ports, DSCP, job IDs, years, standard numbers. The lint enforces ≥ 10,000 when a unit follows.
9. **Multiplication**: `×` spaced between operands (`8 × 400 Gb/s`), unspaced for a factor (`9×`,
   `1.5× per micro-batch`). Never `x`, except `x16`/`x8` PCIe link widths.
10. **Approximation**: `≈ 50 GB/s` with a space. Never `~` (56 instances, mostly Ch 4 and Ch 14).
11. **Ranges**: en dash, no spaces: `50–55 GB/s`, `n01–n24`, `Sections 20.3–20.5`.
12. **Ratios**: no spaces: `1:1`, `3:1`, `1.5:1`, `32:24` (Ch 2 is the only chapter with spaced ratios).
13. **Percent**: `40 %`; `pp` for percentage points when comparing percentages.
14. **Percentiles**: lower case `p50`, `p95`, `p99`, `p99.9`.
15. **Large/small numbers in prose**: `1.76 × 10¹⁸ FLOP`. `1.76e18` is fine inside a displayed formula or
    code.
16. **FLOP**: `FLOP` is a count, `FLOP/s` and `TFLOP/s` are rates; never `TFLOPS`. Use "FLOPs" only as a
    plural count ("2 FLOPs per parameter") and in "model FLOPs utilization".
17. **Tokens**: `tokens/s`, `req/s`, `2k-token prompt`, `32k context` (lower-case `k` for thousands of
    tokens).
18. **Power**: `W`, `kW`, `MW`, `kWh`; IT vs facility power always named; PUE 1.25 unless declared.
19. **Show the arithmetic** (STYLE_GUIDE §5): formula → substituted values → result with units. Round only
    at the end.
20. **Evidence labels** (STYLE_GUIDE §3): write a label in backticks, `` `[MODELED]` ``; 96 % of labels
    already are. `[VENDOR-SPEC, YYYY-MM]` and `[OBSERVED, YYYY-MM-DD]` must carry the date immediately after
    the tag. A qualifier may follow inside the brackets after " — " or "; " (`` `[ILLUSTRATIVE — calibrate per
    workload]` ``). Every table caption that summarises numbers carries a label.
21. **Glossary paragraph** (optional harmonisation): `**Acronyms.** ACR (expansion), ACR (expansion), …`.
    Seven chapters and four capstones currently use four different openings.
22. **Captions**: `*Table N.M — Title. Notes `[LABEL]`.*` and `*Figure N.M — Title.*`, in italics, on the line
    after the table or diagram.

## (d) Findings by file

Columns: **Line:Col** (col 0 = whole line or locate the text on the line); **Cat**; **Type** (MECHANICAL = safe literal replacement of *Current* by *Replacement* on that line; JUDGEMENT = read the paragraph first); **Current** and **Replacement** are the exact text on the line with one word of context; **Rule / note** is the lint rule id (see §(e)) or the reason.

Line numbers are those of the working tree on 2026-10-30. Apply edits bottom-up within a file and right-to-left within a line so earlier positions stay valid, or re-run `python scripts/copyedit_lint.py <chapter>` to re-locate MECHANICAL items.


### `book/part-1-foundations/ch01-ai-infrastructure-landscape/lab/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 61:13 | SPELLING | MECHANICAL | `scaleup, scaleout,` | `scaleup, scale-out,` | compounds |

### `book/part-1-foundations/ch01-ai-infrastructure-landscape/manuscript.md`

19 finding(s): 9 MECHANICAL, 10 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 48:0 | STYLE | JUDGEMENT | `Acronyms:` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 52:75 | ACRONYM | MECHANICAL | `(model FLOP utilization),` | `(model FLOPs utilization),` | exp-mfu |
| 105:33 | STYLE | MECHANICAL | `cloud vs. AI` | `cloud vs AI` | vs-period |
| 126:23 | TERM | MECHANICAL | `\| Tensor-core compute` | `\| Tensor Core compute` | tensorcore |
| 133:23 | STYLE | MECHANICAL | `Training vs. inference` | `Training vs inference` | vs-period |
| 198:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 198:0 | ACRONYM | JUDGEMENT | `ECN` | `explicit congestion notification (ECN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 198:0 | ACRONYM | JUDGEMENT | `CNP` | `congestion notification packet (CNP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 289:71 | TERM | MECHANICAL | `depth, KV-cache occupancy` | `depth, KV cache occupancy` | kvcache |
| 331:23 | STYLE | MECHANICAL | `Scale-up vs. scale-out` | `Scale-up vs scale-out` | vs-period |
| 349:0 | ACRONYM | JUDGEMENT | `SHARP` | `Scalable Hierarchical Aggregation and Reduction Protocol (SHARP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 492:79 | TERM | MECHANICAL | `attention, KV-cache quantization,` | `attention, KV cache quantization,` | kvcache |
| 502:0 | ACRONYM | JUDGEMENT | `SM` | `streaming multiprocessor (SM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 513:63 | TERM | MECHANICAL | `the tensor cores were.` | `the Tensor Cores were.` | tensorcore |
| 590:0 | ACRONYM | JUDGEMENT | `ASIC` | `application-specific integrated circuit (ASIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 608:0 | ACRONYM | JUDGEMENT | `BGP` | `Border Gateway Protocol (BGP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 886:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 950:0 | ACRONYM | JUDGEMENT | `ZeRO` | `Zero Redundancy Optimizer (ZeRO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 960:23 | TERM | MECHANICAL | `why KV-cache memory,` | `why KV cache memory,` | kvcache |

### `book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 8:63 | SPELLING | MECHANICAL | `TDP, synchronised transients,` | `TDP, synchronized transients,` | ize |

### `book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/exercises.md`

3 finding(s): 3 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 209:50 | SPELLING | MECHANICAL | `are authorised to` | `are authorized to` | ize |
| 261:33 | SPELLING | MECHANICAL | `nine artefacts above;` | `nine artifacts above;` | artefact |
| 292:4 | SPELLING | MECHANICAL | `organisation,` | `organization,` | ize |

### `book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/lab/README.md`

6 finding(s): 1 MECHANICAL, 5 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 6:0 | ORION | JUDGEMENT | `the network team, and the facilities` | `the Fabric team, and the Facilities` | canonical Halcyon team names (REFERENCE_CLUSTER §5) |
| 64:0 | ORION | JUDGEMENT | `Architecture team's design intent` | `Fabric and Facilities teams' design intent` | no "Architecture" team at Halcyon; name the owning canonical team(s) |
| 67:0 | ORION | JUDGEMENT | `Network team` | `Fabric team` | canonical team name |
| 161:74 | SPELLING | MECHANICAL | `written authorisation for` | `written authorization for` | ize |
| 205:0 | ORION | JUDGEMENT | `facilities team` | `Facilities team` | canonical team name |
| 211:0 | ORION | JUDGEMENT | `facilities team` | `Facilities team` | canonical team name |

### `book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/manuscript.md`

27 finding(s): 15 MECHANICAL, 12 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 49:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 158:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 158:124 | TERM | MECHANICAL | `(NCCL), KV-cache transfer` | `(NCCL), KV cache transfer` | kvcache |
| 160:0 | ACRONYM | JUDGEMENT | `IPMI` | `Intelligent Platform Management Interface (IPMI)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 209:15 | UNIT | MECHANICAL | `rail 32 : 24 =` | `rail 32:24 =` | ratio-spaced |
| 209:25 | UNIT | MECHANICAL | `= 1.33 : 1 oversubscribed,` | `= 1.33:1 oversubscribed,` | ratio-spaced |
| 214:0 | ACRONYM | JUDGEMENT | `ASIC` | `application-specific integrated circuit (ASIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 220:81 | UNIT | MECHANICAL | `(9.6 : 6.4 Tb/s)` | `(9.6:6.4 Tb/s)` | ratio-spaced |
| 221:60 | UNIT | MECHANICAL | `(6.4 : 6.4 Tb/s),` | `(6.4:6.4 Tb/s),` | ratio-spaced |
| 293:33 | STYLE | MECHANICAL | `Usable vs. installed` | `Usable vs installed` | vs-period |
| 300:0 | LABEL | JUDGEMENT | `*Table 2.4 — Electrical redundancy modes. The Uptime Institute's Tier …` | add `[ILLUSTRATIVE]` (cite Uptime Institute / TIA-942 for tier figures) to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 336:37 | SPELLING | MECHANICAL | `\| Synchronised swings` | `\| Synchronized swings` | ize |
| 346:25 | SPELLING | MECHANICAL | `verified) analyses these` | `verified) analyzes these` | analyse |
| 365:0 | ACRONYM | JUDGEMENT | `MTBF` | `mean time between failures (MTBF)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 631:27 | SPELLING | MECHANICAL | `commonly organised in` | `commonly organized in` | ize |
| 635:1 | SPELLING | MECHANICAL | `synchronised load` | `synchronized load` | ize |
| 661:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 803:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 830:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis (prior) \| Fits "afternoon only, one rack"? …` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 930:66 | SPELLING | MECHANICAL | `and over-subscribe circuits` | `and oversubscribe circuits` | compounds |
| 940:0 | CAPTION | JUDGEMENT | `\| Signal \| Threshold \| Severity \| Safe action \| Escalate to …` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 951:0 | ORION | JUDGEMENT | `the IT team's universal safe action` | `the Fleet team's universal safe action` | no "IT" team at Halcyon; draining is a Fleet/Platform action — confirm from context |
| 961:16 | SPELLING | MECHANICAL | `under synchronised transients,` | `under synchronized transients,` | ize |
| 978:3 | SPELLING | MECHANICAL | `- Synchronised training` | `- Synchronized training` | ize |
| 1017:35 | LABEL | JUDGEMENT | `` `[VENDOR-SPEC — verify the current edition]`. `` | add ", 2026-10" (or the month actually checked) right after VENDOR-SPEC; keep the qualifier after " — " | label-vendor-date |
| 1019:44 | SPELLING | MECHANICAL | `by synchronised GPU` | `by synchronized GPU` | ize |
| 1021:3 | SPELLING | MECHANICAL | `Analyses training` | `Analyzes training` | analyse |

### `book/part-1-foundations/ch03-linux-host-systems-diagnostics/exercises.md`

4 finding(s): 4 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 67:76 | UNIT | MECHANICAL | `a ~40` | `a ≈ 40` | approx-tilde |
| 84:21 | XREF-STYLE | MECHANICAL | `of §3.11 and` | `of Section 3.11 and` | section-sign |
| 90:61 | XREF-STYLE | MECHANICAL | `of §3.11 Step` | `of Section 3.11 Step` | section-sign |
| 159:5 | XREF-STYLE | MECHANICAL | `The §3.11 cost` | `The Section 3.11 cost` | section-sign |

### `book/part-1-foundations/ch03-linux-host-systems-diagnostics/lab/README.md`

9 finding(s): 9 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 50:49 | XREF-STYLE | MECHANICAL | `\| §3.2 \|` | `\| Section 3.2 \|` | section-sign |
| 51:64 | XREF-STYLE | MECHANICAL | `\| §3.3 \|` | `\| Section 3.3 \|` | section-sign |
| 52:48 | XREF-STYLE | MECHANICAL | `\| §3.4 \|` | `\| Section 3.4 \|` | section-sign |
| 53:66 | XREF-STYLE | MECHANICAL | `\| §3.5 \|` | `\| Section 3.5 \|` | section-sign |
| 54:52 | XREF-STYLE | MECHANICAL | `\| §3.6 \|` | `\| Section 3.6 \|` | section-sign |
| 55:47 | XREF-STYLE | MECHANICAL | `\| §3.7 \|` | `\| Section 3.7 \|` | section-sign |
| 56:50 | XREF-STYLE | MECHANICAL | `\| §3.8 \|` | `\| Section 3.8 \|` | section-sign |
| 57:28 | XREF-STYLE | MECHANICAL | `\| §3.10 \|` | `\| Section 3.10 \|` | section-sign |
| 134:4 | SPELLING | MECHANICAL | `utilisation is` | `utilization is` | ize |

### `book/part-1-foundations/ch03-linux-host-systems-diagnostics/manuscript.md`

35 finding(s): 19 MECHANICAL, 16 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 57:0 | CAPTION | JUDGEMENT | `\| Host responsibility \| Resource it consumes \| What breaks w…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 66:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 67:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line is the first body use; currently expanded only at line 791 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 275:18 | ACRONYM | MECHANICAL | `under return-merchandise authorization (RMA)` | `under return merchandise authorization (RMA)` | exp-rma |
| 352:31 | XREF-STYLE | MECHANICAL | `in §3.2 matters.` | `in Section 3.2 matters.` | section-sign |
| 377:3 | TERM | MECHANICAL | `data-centre NVMe` | `data-center NVMe` | datacentre |
| 378:30 | SPELLING | MECHANICAL | `means queuing behind` | `means queueing behind` | queuing |
| 458:0 | CAPTION | JUDGEMENT | `\| Pattern \| Typical causes \| Verdict \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 460:226 | SPELLING | MECHANICAL | `replace, re-test.` | `replace, retest.` | rerun |
| 462:91 | TERM | MECHANICAL | `NVIDIA data-centre GPUs,` | `NVIDIA data-center GPUs,` | datacentre |
| 495:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line is the first body use; currently expanded only at line 526 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 584:8 | UNIT | MECHANICAL | `(400 000 Mb/s` | `(400,000 Mb/s` | thousands-space |
| 584:32 | UNIT | MECHANICAL | `rails, 200 000 Mb/s` | `rails, 200,000 Mb/s` | thousands-space |
| 600:0 | CAPTION | JUDGEMENT | `\| Component \| Read-only command \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 626:0 | CAPTION | JUDGEMENT | `\| Source \| Pattern (abbreviated) \| Meaning \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 650:0 | CAPTION | JUDGEMENT | `\| Resource \| Utilization \| Saturation \| Errors \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 666:0 | CAPTION | JUDGEMENT | `\| Mechanism \| Why the CPU average looks low \| Discriminating…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 753:52 | XREF-STYLE | MECHANICAL | `Using §3.6:` | `Using Section 3.6:` | section-sign |
| 829:0 | ACRONYM | JUDGEMENT | `PXN` | `PCI × NVLink (PXN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 840:14 | XREF-STYLE | MECHANICAL | `of §3.10 and` | `of Section 3.10 and` | section-sign |
| 854:0 | CAPTION | JUDGEMENT | `\| Ranks \| Node \| Forward + backward (s) \| Waiting in DP all-…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 881:0 | CAPTION | JUDGEMENT | `` \| Signal \| `orion-n31` \| Peer `orion-n30` \| `` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 888:22 | UNIT | MECHANICAL | `\| 400 000 Mb/s` | `\| 400,000 Mb/s` | thousands-space |
| 891:31 | UNIT | MECHANICAL | `\| 800 000 kHz` | `\| 800,000 kHz` | thousands-space |
| 891:45 | UNIT | MECHANICAL | `\| 3 100 000 kHz` | `\| 3,100,000 kHz` | thousands-space |
| 895:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| Prior (post-RMA) \| Discriminating test \| …` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 924:6 | SPELLING | MECHANICAL | `then re-imaged from` | `then reimaged from` | rerun |
| 941:13 | SPELLING | MECHANICAL | `node re-runs acceptance,` | `node reruns acceptance,` | rerun |
| 955:58 | SPELLING | MECHANICAL | `partial re-image.` | `partial reimage.` | rerun |
| 959:0 | CAPTION | JUDGEMENT | `\| Decision \| Option A \| Option B \| Criteria that decide \| Wh…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 964:0 | ACRONYM | JUDGEMENT | `DCGM` | `NVIDIA Data Center GPU Manager (DCGM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 976:0 | CAPTION | JUDGEMENT | `\| Step \| Action (read-only unless stated) \| Healthy signal \|…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 986:64 | SPELLING | MECHANICAL | `(draining, re-imaging,` | `(draining, reimaging,` | rerun |
| 1059:3 | XREF-STYLE | MECHANICAL | `§3.9's` | `Section 3.9's` | section-sign |
| 1066:84 | XREF-STYLE | MECHANICAL | `for §3.7.` | `for Section 3.7.` | section-sign |

### `book/part-2-accelerated-compute/ch04-gpu-architecture-cuda-execution/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 8:32 | TERM | MECHANICAL | `matters, tensor cores,` | `matters, Tensor Cores,` | tensorcore |

### `book/part-2-accelerated-compute/ch04-gpu-architecture-cuda-execution/exercises.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 40:27 | TERM | MECHANICAL | `a tensor-core GEMM` | `a Tensor Core GEMM` | tensorcore |

### `book/part-2-accelerated-compute/ch04-gpu-architecture-cuda-execution/lab/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 101:35 | SPELLING | MECHANICAL | `and analyse your` | `and analyze your` | analyse |

### `book/part-2-accelerated-compute/ch04-gpu-architecture-cuda-execution/manuscript.md`

40 finding(s): 26 MECHANICAL, 14 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 8:84 | TERM | MECHANICAL | `and tensor cores —` | `and Tensor Cores —` | tensorcore |
| 31:18 | TERM | MECHANICAL | `quantization, tensor-core alignment,` | `quantization, Tensor Core alignment,` | tensorcore |
| 62:0 | ACRONYM | JUDGEMENT | `HBM` | `high-bandwidth memory (HBM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 89:86 | TERM | MECHANICAL | `one tensor core \|` | `one Tensor Core \|` | tensorcore |
| 91:3 | TERM | MECHANICAL | `\| Tensor cores \|` | `\| Tensor Cores \|` | tensorcore |
| 102:54 | TERM | MECHANICAL | `Hopper, tensor-core instructions` | `Hopper, Tensor Core instructions` | tensorcore |
| 104:30 | SPELLING | MECHANICAL | `therefore organised around` | `therefore organized around` | ize |
| 254:0 | CAPTION | JUDGEMENT | `\| Level \| Capacity \| Scope \| Approx. latency \| Aggregate ban…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 256:65 | UNIT | MECHANICAL | `\| ~1` | `\| ≈ 1` | approx-tilde |
| 257:96 | UNIT | MECHANICAL | `\| ~30` | `\| ≈ 30` | approx-tilde |
| 257:109 | UNIT | MECHANICAL | `\| ~30+` | `\| ≈ 30+` | approx-tilde |
| 258:34 | UNIT | MECHANICAL | `\| ~200–300` | `\| ≈ 200–300` | approx-tilde |
| 258:52 | UNIT | MECHANICAL | `\| ~10` | `\| ≈ 10` | approx-tilde |
| 259:46 | UNIT | MECHANICAL | `\| ~500–800` | `\| ≈ 500–800` | approx-tilde |
| 260:54 | UNIT | MECHANICAL | `\| ~1–2` | `\| ≈ 1–2` | approx-tilde |
| 261:58 | UNIT | MECHANICAL | `\| ~1–2` | `\| ≈ 1–2` | approx-tilde |
| 374:0 | CAPTION | JUDGEMENT | `\| Code pattern \| Why it synchronizes \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 483:52 | TERM | MECHANICAL | `asynchronous tensor-core work` | `asynchronous Tensor Core work` | tensorcore |
| 506:8 | TERM | MECHANICAL | `4.8 Tensor cores,` | `4.8 Tensor Cores,` | tensorcore |
| 508:1 | TERM | MECHANICAL | `Tensor cores execute` | `Tensor Cores execute` | tensorcore |
| 513:41 | TERM | MECHANICAL | `use tensor cores with` | `use Tensor Cores with` | tensorcore |
| 515:6 | TERM | MECHANICAL | `TF32 tensor cores only` | `TF32 Tensor Cores only` | tensorcore |
| 517:0 | ACRONYM | JUDGEMENT | `DCGM` | `NVIDIA Data Center GPU Manager (DCGM)` | first occurrence on the line is the first body use; currently expanded only at line 554 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 520:22 | TERM | MECHANICAL | `alignment.** Tensor-core kernels` | `alignment.** Tensor Core kernels` | tensorcore |
| 523:1 | SPELLING | MECHANICAL | `speed-up because` | `speedup because` | compounds |
| 542:16 | TERM | MECHANICAL | `use tensor-core kernels` | `use Tensor Core kernels` | tensorcore |
| 557:0 | CAPTION | JUDGEMENT | `\| DCGM field \| Meaning \| Healthy training example \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 600:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 735:0 | CAPTION | JUDGEMENT | `\| Quantity \| Value (ns) \| Share of 85,574,931 ns \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 762:0 | CAPTION | JUDGEMENT | `\| Cause \| Gaps \| Idle time \| Where \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 775:0 | CAPTION | JUDGEMENT | `\| Copy \| Bytes \| Duration \| Bandwidth \| Host memory \| Overla…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 798:0 | CAPTION | JUDGEMENT | `\| # \| Root cause \| Change \| Saving per step \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 822:7 | SPELLING | MECHANICAL | `` 1.35× speed-up `[MODELED]` `` | `` 1.35× speedup `[MODELED]` `` | compounds |
| 882:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| Predicts \| Cheapest discriminating test \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 933:72 | UNIT | MECHANICAL | `at ~100` | `at ≈ 100` | approx-tilde |
| 965:0 | CAPTION | JUDGEMENT | `\| Signal \| Source \| Investigate when \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 978:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 998:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 1018:15 | TERM | MECHANICAL | `roof. Tensor-core kernels` | `roof. Tensor Core kernels` | tensorcore |
| 1049:77 | SPELLING | MECHANICAL | `SM organisation,` | `SM organization,` | ize |

### `book/part-2-accelerated-compute/ch05-gpu-interconnects-host-topology/manuscript.md`

14 finding(s): 2 MECHANICAL, 12 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 54:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 59:0 | ACRONYM | JUDGEMENT | `HCA` | `host channel adapter (HCA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 61:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 143:0 | ORION | JUDGEMENT | `the platform team's BIOS/kernel baseline` | `the Fleet team's BIOS/kernel baseline` | BIOS/kernel baselines belong to Fleet (bare-metal lifecycle) per §5; or capitalise "Platform" if meant |
| 236:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 253:0 | ACRONYM | JUDGEMENT | `NUMA` | `non-uniform memory access (NUMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 380:0 | CAPTION | JUDGEMENT | `` \| Column \| Source command `[L2]` \| Notes \| `` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 496:8 | ACRONYM | MECHANICAL | `(PCIe × NVLink).**` | `(PCI × NVLink).**` | exp-pxn |
| 564:0 | ACRONYM | JUDGEMENT | `NVLS` | `NVLink SHARP (NVLS)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 572:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 671:24 | SPELLING | MECHANICAL | `Validate.** Re-run node` | `Validate.** Rerun node` | rerun |
| 713:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| Predicts \| Test \| Result \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 716:0 | ACRONYM | JUDGEMENT | `FEC` | `forward error correction (FEC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 773:0 | CAPTION | JUDGEMENT | `\| Check \| Pass criterion (ORION HX8 golden layout) \| Severit…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |

### `book/part-2-accelerated-compute/ch06-gpu-performance-engineering/manuscript.md`

18 finding(s): 8 MECHANICAL, 10 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 56:0 | ACRONYM | JUDGEMENT | `HBM` | `high-bandwidth memory (HBM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 68:0 | ACRONYM | JUDGEMENT | `SM` | `streaming multiprocessor (SM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 102:83 | TERM | MECHANICAL | `mix: tensor-core BF16` | `mix: Tensor Core BF16` | tensorcore |
| 171:69 | TERM | MECHANICAL | `use tensor cores at` | `use Tensor Cores at` | tensorcore |
| 187:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 205:197 | TERM | MECHANICAL | `(tensor cores,` | `(Tensor Cores,` | tensorcore |
| 207:39 | TERM | MECHANICAL | `Use tensor cores (precision,` | `Use Tensor Cores (precision,` | tensorcore |
| 257:0 | ACRONYM | JUDGEMENT | `DCGM` | `NVIDIA Data Center GPU Manager (DCGM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 263:122 | TERM | MECHANICAL | `for tensor-core GEMMs` | `for Tensor Core GEMMs` | tensorcore |
| 264:89 | TERM | MECHANICAL | `"Are tensor cores doing` | `"Are Tensor Cores doing` | tensorcore |
| 330:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 330:0 | ACRONYM | JUDGEMENT | `MIG` | `Multi-Instance GPU (MIG)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 448:0 | CAPTION | JUDGEMENT | `\| Condition \| Decision \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 516:0 | CAPTION | JUDGEMENT | `\| Arm \| Run medians \| Median of run medians \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 567:34 | SPELLING | MECHANICAL | `and analyse your` | `and analyze your` | analyse |
| 603:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| Discriminating test \| Result \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 624:150 | SPELLING | MECHANICAL | `limit. Re-run the` | `limit. Rerun the` | rerun |
| 651:0 | CAPTION | JUDGEMENT | `\| Signal \| Threshold \| Action \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |

### `book/part-3-networking/ch07-ethernet-datacenter-network-foundations/manuscript.md`

29 finding(s): 9 MECHANICAL, 20 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 65:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 70:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 72:62 | LABEL | MECHANICAL | `design [ILLUSTRATIVE, qualitative].*` | `` design `[ILLUSTRATIVE, qualitative]`.* `` | label-backticks |
| 127:0 | ACRONYM | JUDGEMENT | `BGP` | `Border Gateway Protocol (BGP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 193:0 | LABEL | JUDGEMENT | `` *Table 7.2 — ORION backend addressing. Node n is `orion-nNN` (01–32). … `` | add `[ILLUSTRATIVE]` (ORION plan, REFERENCE_CLUSTER) to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 249:60 | LABEL | MECHANICAL | `MTU [MODELED].` | `` MTU `[MODELED]`. `` | label-backticks |
| 275:52 | LABEL | MECHANICAL | `4096 [MODELED].` | `` 4096 `[MODELED]`. `` | label-backticks |
| 279:64 | UNIT | MECHANICAL | `are ~4.2` | `are ≈ 4.2` | approx-tilde |
| 482:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 509:0 | ACRONYM | JUDGEMENT | `ASIC` | `application-specific integrated circuit (ASIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 518:23 | UNIT | MECHANICAL | `that ~1/32` | `that ≈ 1/32` | approx-tilde |
| 551:57 | LABEL | MECHANICAL | `fabric [MODELED].*` | `` fabric `[MODELED]`.* `` | label-backticks |
| 599:0 | ACRONYM | JUDGEMENT | `PXN` | `PCI × NVLink (PXN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 640:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line is the first body use; currently expanded only at line 646 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 640:0 | ACRONYM | JUDGEMENT | `ECN` | `explicit congestion notification (ECN)` | first occurrence on the line is the first body use; currently expanded only at line 646 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 644:40 | LABEL | MECHANICAL | `classes [ILLUSTRATIVE].*` | `` classes `[ILLUSTRATIVE]`.* `` | label-backticks |
| 646:0 | ACRONYM | JUDGEMENT | `DCQCN` | `Data Center Quantized Congestion Notification (DCQCN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 786:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 786:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 786:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line is the first body use; currently expanded only at line 788 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 796:0 | ACRONYM | JUDGEMENT | `MoE` | `mixture of experts (MoE)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 841:89 | UNIT | MECHANICAL | `is ~55` | `is ≈ 55` | approx-tilde |
| 847:0 | ACRONYM | JUDGEMENT | `RMA` | `return merchandise authorization (RMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 916:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| Prior \| Fits \| Does not fit \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 925:3 | SPELLING | MECHANICAL | `- Re-run the` | `- Rerun the` | rerun |
| 983:0 | ACRONYM | JUDGEMENT | `ToR` | `top-of-rack (ToR)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 988:0 | LABEL | JUDGEMENT | `*Table 7.10 — Fabric design trade-offs.*` | add `[ILLUSTRATIVE]` to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 996:0 | CAPTION | JUDGEMENT | `\| Signal \| Threshold \| First checks \| Safe action \| Escalate…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 1003:0 | ACRONYM | JUDGEMENT | `FEC` | `forward error correction (FEC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `book/part-3-networking/ch08-rdma-rocev2-infiniband/lab/README.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 16:36 | SPELLING | MECHANICAL | `combinations, summarises bandwidth` | `combinations, summarizes bandwidth` | ize |
| 31:97 | SPELLING | MECHANICAL | `as modelled` | `as modeled` | modelled |

### `book/part-3-networking/ch08-rdma-rocev2-infiniband/manuscript.md`

25 finding(s): 10 MECHANICAL, 15 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 49:16 | TERM | MECHANICAL | `for KV-cache transfer.` | `for KV cache transfer.` | kvcache |
| 54:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 153:75 | SPELLING | MECHANICAL | `` (`lkey`) authorises the `` | `` (`lkey`) authorizes the `` | ize |
| 158:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 181:0 | ACRONYM | JUDGEMENT | `MTU` | `maximum transmission unit (MTU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 274:0 | ACRONYM | JUDGEMENT | `DSCP` | `differentiated services code point (DSCP)` | first occurrence on the line is the first body use; currently expanded only at line 289 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 366:0 | ACRONYM | JUDGEMENT | `SM` | `streaming multiprocessor (SM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 404:0 | ACRONYM | JUDGEMENT | `SHARP` | `Scalable Hierarchical Aggregation and Reduction Protocol (SHARP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 574:0 | ACRONYM | JUDGEMENT | `ACS` | `access control services (ACS)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 579:0 | ACRONYM | JUDGEMENT | `PXN` | `PCI × NVLink (PXN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 600:0 | ACRONYM | JUDGEMENT | `BGP` | `Border Gateway Protocol (BGP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 601:118 | SPELLING | MECHANICAL | `\| Centralised:` | `\| Centralized:` | ize |
| 605:0 | ACRONYM | JUDGEMENT | `FEC` | `forward error correction (FEC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 772:0 | ACRONYM | JUDGEMENT | `NUMA` | `non-uniform memory access (NUMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 785:0 | ACRONYM | JUDGEMENT | `BDF` | `bus:device.function (BDF)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 789:47 | SPELLING | MECHANICAL | `A modelled ceiling` | `A modeled ceiling` | modelled |
| 809:74 | SPELLING | MECHANICAL | `as modelled;` | `as modeled;` | modelled |
| 815:40 | SPELLING | MECHANICAL | `NCCL initialisation.` | `NCCL initialization.` | ize |
| 841:27 | TERM | MECHANICAL | `every data-centre switch.*` | `every data-center switch.*` | datacentre |
| 845:73 | SPELLING | MECHANICAL | `low-volume initialisation.` | `low-volume initialization.` | ize |
| 900:0 | LABEL | JUDGEMENT | `*Table 8.9 — Design decisions for RDMA fabrics.*` | add `[ILLUSTRATIVE]` to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 917:0 | UNIT | JUDGEMENT | `Ethernet, 400000Mb/s` | `` `Ethernet, 400000Mb/s` `` | verbatim tool output (ethtool) belongs in backticks; do not reformat the number (supersedes the lint unit-space/thousands hits on this line) |
| 936:0 | LABEL | JUDGEMENT | `*Table 8.10 — RDMA deployment-readiness checklist.*` | add `[ILLUSTRATIVE]` thresholds to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 945:43 | SPELLING | MECHANICAL | `of modelled ceiling` | `of modeled ceiling` | modelled |
| 990:53 | SPELLING | MECHANICAL | `a modelled ceiling,` | `a modeled ceiling,` | modelled |

### `book/part-3-networking/ch09-congestion-control-lossless-fabrics/README.md`

2 finding(s): 1 MECHANICAL, 1 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 5:0 | ACRONYM | JUDGEMENT | `Priority-based Flow Control` | `priority flow control` | as above |
| 81:83 | TERM | MECHANICAL | `(KV-cache transfer` | `(KV cache transfer` | kvcache |

### `book/part-3-networking/ch09-congestion-control-lossless-fabrics/exercises.md`

3 finding(s): 2 MECHANICAL, 1 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 6:21 | SPELLING | MECHANICAL | `in fibre,` | `in fiber,` | fibre |
| 56:82 | SPELLING | MECHANICAL | `m fibre runs.` | `m fiber runs.` | fibre |
| 141:0 | ORION | JUDGEMENT | `The Storage team` | `The Storage team (keep) — and add **Storage** to REFERENCE_CLUSTER §5 team list` | REFERENCE_CLUSTER §5 lists Fabric, Fleet, Platform, Training Infra, Inference, SRE, Facilities; "Storage" is used in Ch 9, 14, 18, 22. Editor decision: add Storage to §5 (recommended, one doc edit) or map to Platform |

### `book/part-3-networking/ch09-congestion-control-lossless-fabrics/lab/README.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 128:96 | STYLE | MECHANICAL | `proven vs. correlated` | `proven vs correlated` | vs-period |
| 149:58 | SPELLING | MECHANICAL | `are authorised to` | `are authorized to` | ize |

### `book/part-3-networking/ch09-congestion-control-lossless-fabrics/manuscript.md`

15 finding(s): 3 MECHANICAL, 12 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 5:0 | ACRONYM | JUDGEMENT | `Priority-based Flow Control` | `priority flow control` | canonical PFC expansion; keep "Priority-based Flow Control" only when naming the IEEE 802.1Qbb standard |
| 60:1 | TERM | MECHANICAL | `KV-cache transfers` | `KV cache transfers` | kvcache |
| 80:0 | ACRONYM | JUDGEMENT | `Congestion Notification Packets` | `congestion notification packets` | generic expansions are lower case (unless sentence-initial or a heading) |
| 155:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 156:0 | ACRONYM | JUDGEMENT | `Congestion Notification Packet` | `congestion notification packet` | as above |
| 195:0 | ACRONYM | JUDGEMENT | `DCQCN` | `Data Center Quantized Congestion Notification (DCQCN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 211:0 | ACRONYM | JUDGEMENT | `Priority-based Flow Control` | `priority flow control (or keep if the sentence names IEEE 802.1Qbb)` | as above |
| 257:0 | CAPTION | JUDGEMENT | `\| Term \| Meaning \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 261:143 | SPELLING | MECHANICAL | `in fibre,` | `in fiber,` | fibre |
| 401:16 | SPELLING | MECHANICAL | `2016) analyse further` | `2016) analyze further` | analyse |
| 422:0 | CAPTION | JUDGEMENT | `\| Role \| Device \| Job \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 428:0 | ACRONYM | JUDGEMENT | `Congestion Notification Packet` | `congestion notification packet` | as above |
| 802:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| Predicts \| Evidence so far \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 874:0 | CAPTION | JUDGEMENT | `\| Signal \| Threshold \| Severity \| First action \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 935:0 | ACRONYM | JUDGEMENT | `Priority-based Flow Control` | keep if this is the 802.1Qbb citation; otherwise priority flow control | as above |

### `book/part-3-networking/ch10-switches-optics-physical-layer/README.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 12:23 | SPELLING | MECHANICAL | `and labeling,` | `and labelling,` | labeled |
| 21:38 | SPELLING | MECHANICAL | `and labeling scheme,` | `and labelling scheme,` | labeled |

### `book/part-3-networking/ch10-switches-optics-physical-layer/exercises.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 138:55 | SPELLING | MECHANICAL | `cable labeling**` | `cable labelling**` | labeled |

### `book/part-3-networking/ch10-switches-optics-physical-layer/lab/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 18:14 | SPELLING | MECHANICAL | `a labeled **cabling` | `a labelled **cabling` | labeled |

### `book/part-3-networking/ch10-switches-optics-physical-layer/manuscript.md`

25 finding(s): 15 MECHANICAL, 10 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 6:7 | ACRONYM | MECHANICAL | `raw bit-error ratio (BER)` | `raw bit error ratio (BER)` | exp-ber |
| 10:40 | SPELLING | MECHANICAL | `commissioning, labeling,` | `commissioning, labelling,` | labeled |
| 27:38 | SPELLING | MECHANICAL | `and labeling scheme,` | `and labelling scheme,` | labeled |
| 57:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 57:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 119:0 | ACRONYM | JUDGEMENT | `ECN` | `explicit congestion notification (ECN)` | first occurrence on the line is the first body use; currently expanded only at line 127 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 158:71 | UNIT | MECHANICAL | `and ~100` | `and ≈ 100` | approx-tilde |
| 371:0 | CAPTION | JUDGEMENT | `\| Absolute power (dBm) \| +3 \| 0 \| −3 \| −6 \| −10 \| −40 \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 493:97 | UNIT | MECHANICAL | `within ~2` | `within ≈ 2` | approx-tilde |
| 497:39 | UNIT | MECHANICAL | `\| ~10⁻⁸` | `\| ≈ 10⁻⁸` | approx-tilde |
| 500:0 | ACRONYM | JUDGEMENT | `MTU` | `maximum transmission unit (MTU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 560:68 | UNIT | MECHANICAL | `falling ~5` | `falling ≈ 5` | approx-tilde |
| 634:32 | SPELLING | MECHANICAL | `and labeling` | `and labelling` | labeled |
| 699:158 | UNIT | MECHANICAL | `bin ~8` | `bin ≈ 8` | approx-tilde |
| 701:7 | SPELLING | MECHANICAL | `\| Labeling \|` | `\| Labelling \|` | labeled |
| 701:53 | SPELLING | MECHANICAL | `ends labeled with` | `ends labelled with` | labeled |
| 704:0 | LABEL | JUDGEMENT | `*Table 10.8 — Link commissioning checklist. Acceptance thresholds are …` | add `[ILLUSTRATIVE]` thresholds to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 733:9 | SPELLING | MECHANICAL | `**minimise part` | `**minimize part` | ize |
| 734:0 | ACRONYM | JUDGEMENT | `RMA` | `return merchandise authorization (RMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 828:0 | ACRONYM | JUDGEMENT | `PXN` | `PCI × NVLink (PXN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 830:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 920:58 | SPELLING | MECHANICAL | `rows, standardise on` | `rows, standardize on` | ize |
| 928:0 | CAPTION | JUDGEMENT | `\| Signal \| Warning \| Critical / page \| First safe action \| E…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 949:41 | SPELLING | MECHANICAL | `` lab analyses `[SIMULATED]` `` | `` lab analyzes `[SIMULATED]` `` | analyse |
| 979:3 | SPELLING | MECHANICAL | `minimise part` | `minimize part` | ize |

### `book/part-4-distributed-ai/ch11-distributed-training-architecture/manuscript.md`

13 finding(s): 7 MECHANICAL, 6 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 110:85 | TERM | MECHANICAL | `(baseline TP=8,` | `(baseline TP = 8,` | parallel-eq |
| 110:91 | TERM | MECHANICAL | `TP=8, PP=4,` | `TP=8, PP = 4,` | parallel-eq |
| 111:1 | TERM | MECHANICAL | `DP=8).` | `DP = 8).` | parallel-eq |
| 147:47 | SPELLING | MECHANICAL | `and re-runs the` | `and reruns the` | rerun |
| 170:0 | ACRONYM | JUDGEMENT | `FSDP` | `Fully Sharded Data Parallel (FSDP)` | first occurrence on the line is the first body use; currently expanded only at line 176 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 421:0 | ACRONYM | JUDGEMENT | `PXN` | `PCI × NVLink (PXN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 532:0 | ORION | JUDGEMENT | `≈ 450 GB/s large-message plateau of Chapter 12` | `≈ 450 GB/s NVLS large-message plateau of Chapter 12 (a plain ring reaches ≈ 360–380 GB/s)` | VERIFIED_FACTS: single-node busbw near 450 GB/s implies NVLS; state the assumption |
| 540:1 | SPELLING | MECHANICAL | `re-run;` | `rerun;` | rerun |
| 600:79 | SPELLING | MECHANICAL | `or re-test with` | `or retest with` | rerun |
| 840:130 | UNIT | JUDGEMENT | `> ~4B` | `> ≈ 4B` | approx-tilde after a comparison sign: reword (e.g. "> ~4B" → "more than about 4B") |
| 843:81 | UNIT | MECHANICAL | `1), ~1` | `1), ≈ 1` | approx-tilde |
| 860:0 | CAPTION | JUDGEMENT | `` \| Signal \| Threshold `[ILLUSTRATIVE]` \| First action \| `` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 865:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `book/part-4-distributed-ai/ch12-collective-communication-nccl/lab/README.md`

1 finding(s): 0 MECHANICAL, 1 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 46:0 | ORION | JUDGEMENT | `plateaus ≈ 450 GB/s` | `plateaus ≈ 450 GB/s (c1, NVLS active — confirm against data/configs.yaml)` | VERIFIED_FACTS: acceptance figures must state whether NVLS is assumed |

### `book/part-4-distributed-ai/ch12-collective-communication-nccl/manuscript.md`

18 finding(s): 1 MECHANICAL, 17 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 58:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 66:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line is the first body use; currently expanded only at line 68 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 67:0 | ACRONYM | JUDGEMENT | `FSDP` | `Fully Sharded Data Parallel (FSDP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 69:0 | ACRONYM | JUDGEMENT | `MoE` | `mixture of experts (MoE)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 99:0 | ACRONYM | JUDGEMENT | `ZeRO` | `Zero Redundancy Optimizer (ZeRO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 137:0 | ACRONYM | JUDGEMENT | `NVLS` | `NVLink SHARP (NVLS)` | first occurrence on the line is the first body use; currently expanded only at line 175 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 164:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 175:0 | ACRONYM | JUDGEMENT | `SHARP` | `Scalable Hierarchical Aggregation and Reduction Protocol (SHARP)` | first occurrence on the line is the first body use; currently expanded only at line 178 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 291:0 | ACRONYM | JUDGEMENT | `SM` | `streaming multiprocessor (SM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 310:0 | ACRONYM | JUDGEMENT | `PXN` | `PCI × NVLink (PXN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 335:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 354:0 | ORION | JUDGEMENT | `set by platform team` | `set by the Platform team` | canonical team name |
| 362:0 | ACRONYM | JUDGEMENT | `ECMP` | `equal-cost multipath (ECMP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 563:0 | ACRONYM | JUDGEMENT | `HCA` | `host channel adapter (HCA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 703:0 | CAPTION | JUDGEMENT | `` \| Signal \| Threshold `[ILLUSTRATIVE]` \| First action \| `` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 705:87 | SPELLING | MECHANICAL | `\| Re-run 3×;` | `\| Rerun 3×;` | rerun |
| 708:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 714:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `book/part-4-distributed-ai/ch13-gpu-data-movement/exercises.md`

1 finding(s): 0 MECHANICAL, 1 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 22:11 | LABEL | JUDGEMENT | `` `[VENDOR-SPEC]`. `` | `` `[VENDOR-SPEC, YYYY-MM]`. `` | label-vendor-date: the text names the label for the learner, so use the template form |

### `book/part-4-distributed-ai/ch13-gpu-data-movement/manuscript.md`

20 finding(s): 1 MECHANICAL, 19 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 53:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line is the first body use; currently expanded only at line 57 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 53:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line is the first body use; currently expanded only at line 59 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 53:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line is the first body use; currently expanded only at line 58 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 58:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 74:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 75:0 | ACRONYM | JUDGEMENT | `SM` | `streaming multiprocessor (SM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 76:0 | ACRONYM | JUDGEMENT | `NVLS` | `NVLink SHARP (NVLS)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 109:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 199:0 | ACRONYM | JUDGEMENT | `HBM` | `high-bandwidth memory (HBM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 227:0 | ACRONYM | JUDGEMENT | `NUMA` | `non-uniform memory access (NUMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 288:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 303:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 303:0 | ACRONYM | JUDGEMENT | `ECN` | `explicit congestion notification (ECN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 325:0 | ACRONYM | JUDGEMENT | `DCGM` | `NVIDIA Data Center GPU Manager (DCGM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 346:0 | ACRONYM | JUDGEMENT | `DCQCN` | `Data Center Quantized Congestion Notification (DCQCN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 347:0 | ACRONYM | JUDGEMENT | `CNP` | `congestion notification packet (CNP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 413:0 | LABEL | JUDGEMENT | `*Table 13.4 — Distinguishing the three causes. Real incidents often co…` | add `[ILLUSTRATIVE]` to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 506:39 | SPELLING | MECHANICAL | `closure.** Re-run the` | `closure.** Rerun the` | rerun |
| 588:0 | CAPTION | JUDGEMENT | `\| Finding \| Owner \| Safe action \| Validation \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 619:0 | CAPTION | JUDGEMENT | `` \| Signal \| Threshold `[ILLUSTRATIVE]` \| First action \| `` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |

### `book/part-4-distributed-ai/ch14-storage-pipelines-checkpointing/exercises.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 63:31 | UNIT | MECHANICAL | `to ~5` | `to ≈ 5` | approx-tilde |
| 68:43 | UNIT | MECHANICAL | `sustains ~50,000` | `sustains ≈ 50,000` | approx-tilde |

### `book/part-4-distributed-ai/ch14-storage-pipelines-checkpointing/lab/README.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 26:65 | SPELLING | MECHANICAL | `` C analyse `[SIMULATED]` `` | `` C analyze `[SIMULATED]` `` | analyse |
| 180:35 | SPELLING | MECHANICAL | `an initialised process` | `an initialized process` | ize |

### `book/part-4-distributed-ai/ch14-storage-pipelines-checkpointing/manuscript.md`

45 finding(s): 32 MECHANICAL, 13 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 188:4 | UNIT | MECHANICAL | `~50` | `≈ 50` | approx-tilde |
| 188:28 | UNIT | MECHANICAL | `alone, ~25` | `alone, ≈ 25` | approx-tilde |
| 198:18 | UNIT | MECHANICAL | `carry ~1,067` | `carry ≈ 1,067` | approx-tilde |
| 203:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 295:39 | SPELLING | MECHANICAL | `+ amortised open)` | `+ amortized open)` | ize |
| 301:42 | UNIT | MECHANICAL | `GB/s, ~1,200` | `GB/s, ≈ 1,200` | approx-tilde |
| 319:0 | ORION | JUDGEMENT | `storage team` | `Storage team` | team name capitalised as a Halcyon team (see Ch 9 ex. 141 note) |
| 375:47 | UNIT | MECHANICAL | `of ~3.4` | `of ≈ 3.4` | approx-tilde |
| 377:87 | UNIT | MECHANICAL | `of ~0.26` | `of ≈ 0.26` | approx-tilde |
| 391:1 | SPELLING | MECHANICAL | `amortises over` | `amortizes over` | ize |
| 415:0 | ACRONYM | JUDGEMENT | `NUMA` | `non-uniform memory access (NUMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 434:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 434:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 495:66 | UNIT | MECHANICAL | `from ~60` | `from ≈ 60` | approx-tilde |
| 495:76 | UNIT | MECHANICAL | `to ~200–240` | `to ≈ 200–240` | approx-tilde |
| 496:32 | UNIT | MECHANICAL | `to ~3` | `to ≈ 3` | approx-tilde |
| 500:0 | ACRONYM | JUDGEMENT | `RPO` | `recovery point objective (RPO)` | first occurrence on the line is the first body use; currently expanded only at line 603 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 521:28 | SPELLING | MECHANICAL | `memory, finalise in` | `memory, finalize in` | ize |
| 642:84 | UNIT | MECHANICAL | `(~78` | `(≈ 78` | approx-tilde |
| 711:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 711:84 | SPELLING | MECHANICAL | `NCCL initialisation)` | `NCCL initialization)` | ize |
| 744:57 | UNIT | MECHANICAL | `is ~6` | `is ≈ 6` | approx-tilde |
| 752:4 | UNIT | MECHANICAL | `~65` | `≈ 65` | approx-tilde |
| 789:65 | UNIT | MECHANICAL | `every ~10.7` | `every ≈ 10.7` | approx-tilde |
| 790:63 | UNIT | MECHANICAL | `from ~18.5` | `from ≈ 18.5` | approx-tilde |
| 790:74 | UNIT | MECHANICAL | `to ~96` | `to ≈ 96` | approx-tilde |
| 811:0 | ORION | JUDGEMENT | `storage team dashboard` | `Storage team dashboard` | as above |
| 813:24 | UNIT | MECHANICAL | `\| ~600` | `\| ≈ 600` | approx-tilde |
| 813:31 | UNIT | MECHANICAL | `\| ~2,700` | `\| ≈ 2,700` | approx-tilde |
| 816:48 | UNIT | MECHANICAL | `for ~16` | `for ≈ 16` | approx-tilde |
| 816:71 | UNIT | MECHANICAL | `for ~95` | `for ≈ 95` | approx-tilde |
| 817:18 | SPELLING | MECHANICAL | `spine utilisation \|` | `spine utilization \|` | ize |
| 823:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| Fits \| Does not fit \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 828:54 | SPELLING | MECHANICAL | `Spine utilisation 1` | `Spine utilization 1` | ize |
| 830:0 | ORION | JUDGEMENT | `the storage team's` | `the Storage team's` | as above |
| 836:88 | UNIT | MECHANICAL | `MDS's ~2,700` | `MDS's ≈ 2,700` | approx-tilde |
| 847:62 | UNIT | MECHANICAL | `peak ~600/s.` | `peak ≈ 600/s.` | approx-tilde |
| 852:35 | SPELLING | MECHANICAL | `lesson generalises:` | `lesson generalizes:` | ize |
| 868:18 | UNIT | MECHANICAL | `exceeds ~1` | `exceeds ≈ 1` | approx-tilde |
| 877:0 | CAPTION | JUDGEMENT | `\| Signal \| Threshold \| Action \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 899:0 | ORION | JUDGEMENT | `the Storage team` | `the Storage team (keep)` | depends on the §5 decision |
| 929:78 | UNIT | MECHANICAL | `blocks ~17.8` | `blocks ≈ 17.8` | approx-tilde |
| 930:20 | UNIT | MECHANICAL | `one ~0.65` | `one ≈ 0.65` | approx-tilde |
| 943:56 | UNIT | MECHANICAL | `add ~20` | `add ≈ 20` | approx-tilde |
| 963:0 | ACRONYM | JUDGEMENT | `ZeRO` | `Zero Redundancy Optimizer (ZeRO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `book/part-4-distributed-ai/ch15-llm-inference-serving/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 18:18 | TERM | MECHANICAL | `**Calculate** KV-cache bytes` | `**Calculate** KV cache bytes` | kvcache |

### `book/part-4-distributed-ai/ch15-llm-inference-serving/exercises.md`

1 finding(s): 0 MECHANICAL, 1 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 117:0 | ORION | JUDGEMENT | `The SLOs are TTFT p95 ≤ 1.5 s and TPOT p95 ≤ 40 ms.` | `The SLOs — a declared variation from W-INFER's 800 ms / 50 ms targets — are TTFT p95 ≤ 1.5 s and TPOT p95 ≤ 40 ms.` | REFERENCE_CLUSTER: a varied parameter must be declared |

### `book/part-4-distributed-ai/ch15-llm-inference-serving/lab/README.md`

8 finding(s): 8 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 10:77 | TERM | MECHANICAL | `into KV-cache budget,` | `into KV cache budget,` | kvcache |
| 27:48 | SPELLING | MECHANICAL | `B analyses a` | `B analyzes a` | analyse |
| 53:3 | TERM | MECHANICAL | `\| KV-cache sizing` | `\| KV cache sizing` | kvcache |
| 69:73 | TERM | MECHANICAL | `**TP=2 with` | `**TP = 2 with` | parallel-eq |
| 88:12 | TERM | MECHANICAL | `(TP=8 BF16);` | `(TP = 8 BF16);` | parallel-eq |
| 88:38 | TERM | MECHANICAL | `(TP=4 FP8);` | `(TP = 4 FP8);` | parallel-eq |
| 88:61 | TERM | MECHANICAL | `(TP=2 FP8).` | `(TP = 2 FP8).` | parallel-eq |
| 90:7 | TERM | MECHANICAL | `on TP=8 BF16` | `on TP = 8 BF16` | parallel-eq |

### `book/part-4-distributed-ai/ch15-llm-inference-serving/manuscript.md`

27 finding(s): 14 MECHANICAL, 13 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 20:18 | TERM | MECHANICAL | `**Calculate** KV-cache bytes` | `**Calculate** KV cache bytes` | kvcache |
| 84:43 | TERM | MECHANICAL | `extra KV-cache hop` | `extra KV cache hop` | kvcache |
| 134:0 | ACRONYM | JUDGEMENT | `MFU` | `model FLOPs utilization (MFU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 165:11 | TERM | MECHANICAL | `\| Tensor-core FLOP/s` | `\| Tensor Core FLOP/s` | tensorcore |
| 168:36 | TERM | MECHANICAL | `` prompt, TP=8 `[MODELED]` `` | `` prompt, TP = 8 `[MODELED]` `` | parallel-eq |
| 180:10 | TERM | MECHANICAL | `the tensor cores are.` | `the Tensor Cores are.` | tensorcore |
| 198:31 | TERM | MECHANICAL | `the tensor cores or` | `the Tensor Cores or` | tensorcore |
| 199:0 | ACRONYM | JUDGEMENT | `DCGM` | `NVIDIA Data Center GPU Manager (DCGM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 223:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 230:7 | TERM | MECHANICAL | `× TP=8,` | `× TP = 8,` | parallel-eq |
| 231:7 | TERM | MECHANICAL | `× TP=4,` | `× TP = 4,` | parallel-eq |
| 232:7 | TERM | MECHANICAL | `× TP=2,` | `× TP = 2,` | parallel-eq |
| 343:95 | TERM | MECHANICAL | `FP8 tensor cores double` | `FP8 Tensor Cores double` | tensorcore |
| 396:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line is the first body use; currently expanded only at line 539 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 396:0 | ACRONYM | JUDGEMENT | `ECN` | `explicit congestion notification (ECN)` | first occurrence on the line is the first body use; currently expanded only at line 544 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 396:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 455:26 | TERM | MECHANICAL | `carry KV-cache bytes` | `carry KV cache bytes` | kvcache |
| 477:10 | TERM | MECHANICAL | `15.10 KV-cache transfer:` | `15.10 KV cache transfer:` | kvcache |
| 538:0 | ACRONYM | JUDGEMENT | `DSCP` | `differentiated services code point (DSCP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 545:0 | ACRONYM | JUDGEMENT | `DCQCN` | `Data Center Quantized Congestion Notification (DCQCN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 570:15 | TERM | MECHANICAL | `leaves tensor cores idle` | `leaves Tensor Cores idle` | tensorcore |
| 801:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| For \| Against \| Rank \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 804:8 | TERM | MECHANICAL | `\| KV-cache exhaustion` | `\| KV cache exhaustion` | kvcache |
| 846:0 | ACRONYM | JUDGEMENT | `SM` | `streaming multiprocessor (SM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 880:0 | CAPTION | JUDGEMENT | `\| Signal \| Threshold \| First check \| Safe action \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 889:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 908:0 | ACRONYM | JUDGEMENT | `MTU` | `maximum transmission unit (MTU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `book/part-5-production-operations/ch16-bare-metal-fleet-lifecycle/exercises.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 118:7 | LABEL | MECHANICAL | `swaps [ILLUSTRATIVE].` | `` swaps `[ILLUSTRATIVE]`. `` | label-backticks |

### `book/part-5-production-operations/ch16-bare-metal-fleet-lifecycle/lab/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 111:63 | SPELLING | MECHANICAL | `are authorised to` | `are authorized to` | ize |

### `book/part-5-production-operations/ch16-bare-metal-fleet-lifecycle/manuscript.md`

65 finding(s): 49 MECHANICAL, 16 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 52:80 | SPELLING | MECHANICAL | `Change](../ch20-automation-safe-change/)) generalises the` | `Change](../ch20-automation-safe-change/)) generalizes the` | ize |
| 58:0 | STYLE | JUDGEMENT | `**Acronyms**` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 61:76 | ACRONYM | MECHANICAL | `MFU model FLOP utilisation;` | `MFU model FLOPs utilization;` | exp-mfu |
| 63:36 | ACRONYM | MECHANICAL | `RMA return material authorisation;` | `RMA return merchandise authorization;` | exp-rma |
| 71:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 78:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 116:35 | SPELLING | MECHANICAL | `Repaired, re-imaged,` | `Repaired, reimaged,` | rerun |
| 119:0 | ACRONYM | JUDGEMENT | `PDU` | `power distribution unit (PDU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 141:0 | ACRONYM | JUDGEMENT | `RMA` | `return merchandise authorization (RMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 194:1 | LABEL | MECHANICAL | `[ILLUSTRATIVE].` | `` `[ILLUSTRATIVE]`. `` | label-backticks |
| 215:52 | LABEL | MECHANICAL | `vary [VENDOR-SPEC, 2026-10].*` | `` vary `[VENDOR-SPEC, 2026-10]`.* `` | label-backticks |
| 259:79 | UNIT | MECHANICAL | `first ~1` | `first ≈ 1` | approx-tilde |
| 267:130 | SPELLING | MECHANICAL | `small artefacts \|` | `small artifacts \|` | artefact |
| 275:56 | SPELLING | MECHANICAL | `of containerised actions),` | `of containerized actions),` | ize |
| 279:66 | LABEL | MECHANICAL | `GB [ILLUSTRATIVE] ×` | `` GB `[ILLUSTRATIVE]` × `` | label-backticks |
| 280:45 | LABEL | MECHANICAL | `port [MODELED],` | `` port `[MODELED]`, `` | label-backticks |
| 287:66 | SPELLING | MECHANICAL | `stays initialised between` | `stays initialized between` | ize |
| 289:46 | SPELLING | MECHANICAL | `to initialise until` | `to initialize until` | ize |
| 290:22 | LABEL | MECHANICAL | `exactly [VENDOR-SPEC, 2026-10].` | `` exactly `[VENDOR-SPEC, 2026-10]`. `` | label-backticks |
| 294:0 | ACRONYM | JUDGEMENT | `ACS` | `access control services (ACS)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 297:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 297:0 | ACRONYM | JUDGEMENT | `CNP` | `congestion notification packet (CNP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 297:0 | ACRONYM | JUDGEMENT | `MTU` | `maximum transmission unit (MTU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 297:0 | ACRONYM | JUDGEMENT | `DSCP` | `differentiated services code point (DSCP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 304:58 | TERM | MECHANICAL | `— tensor cores,` | `— Tensor Cores,` | tensorcore |
| 325:71 | LABEL | MECHANICAL | `are [ILLUSTRATIVE] planning` | `` are `[ILLUSTRATIVE]` planning `` | label-backticks |
| 353:47 | LABEL | MECHANICAL | `state [ILLUSTRATIVE output].` | `` state `[ILLUSTRATIVE output]`. `` | label-backticks |
| 361:48 | LABEL | MECHANICAL | `GB/s [MODELED].` | `` GB/s `[MODELED]`. `` | label-backticks |
| 421:84 | SPELLING | MECHANICAL | `` No`, re-run `dcgmi `` | `` No`, rerun `dcgmi `` | rerun |
| 427:66 | LABEL | MECHANICAL | `candidate) [VENDOR-SPEC, 2026-10].` | `` candidate) `[VENDOR-SPEC, 2026-10]`. `` | label-backticks |
| 430:35 | LABEL | MECHANICAL | `burn-in [ILLUSTRATIVE].` | `` burn-in `[ILLUSTRATIVE]`. `` | label-backticks |
| 435:32 | LABEL | MECHANICAL | `GPU [VENDOR-SPEC, 2026-10].` | `` GPU `[VENDOR-SPEC, 2026-10]`. `` | label-backticks |
| 436:16 | SPELLING | MECHANICAL | `manager initialised the` | `manager initialized the` | ize |
| 455:53 | LABEL | MECHANICAL | `state [ILLUSTRATIVE].` | `` state `[ILLUSTRATIVE]`. `` | label-backticks |
| 485:55 | LABEL | MECHANICAL | `Gb/s [ILLUSTRATIVE].` | `` Gb/s `[ILLUSTRATIVE]`. `` | label-backticks |
| 494:8 | LABEL | MECHANICAL | `KiB [ILLUSTRATIVE];` | `` KiB `[ILLUSTRATIVE]`; `` | label-backticks |
| 521:117 | LABEL | MECHANICAL | `common [ILLUSTRATIVE].` | `` common `[ILLUSTRATIVE]`. `` | label-backticks |
| 542:1 | LABEL | MECHANICAL | `[ILLUSTRATIVE];` | `` `[ILLUSTRATIVE]`; `` | label-backticks |
| 571:0 | ACRONYM | JUDGEMENT | `NVLS` | `NVLink SHARP (NVLS)` | first occurrence on the line is the first body use; currently expanded only at line 578 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 571:99 | LABEL | MECHANICAL | `NVLS [ILLUSTRATIVE].` | `` NVLS `[ILLUSTRATIVE]`. `` | label-backticks |
| 575:15 | SPELLING | MECHANICAL | `bandwidth normalises algorithm` | `bandwidth normalizes algorithm` | ize |
| 578:0 | ACRONYM | JUDGEMENT | `SHARP` | `Scalable Hierarchical Aggregation and Reduction Protocol (SHARP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 581:1 | LABEL | MECHANICAL | `[MODELED ceiling; VENDOR-SPEC, 2026-10].` | `` `[MODELED ceiling; VENDOR-SPEC, 2026-10]`. `` | label-backticks |
| 583:47 | SPELLING | MECHANICAL | `actually initialised,` | `actually initialized,` | ize |
| 585:8 | LABEL | MECHANICAL | `(Ring) [ILLUSTRATIVE],` | `` (Ring) `[ILLUSTRATIVE]`, `` | label-backticks |
| 605:16 | LABEL | MECHANICAL | `are [ILLUSTRATIVE] teaching` | `` are `[ILLUSTRATIVE]` teaching `` | label-backticks |
| 632:40 | SPELLING | MECHANICAL | `a modelled step` | `a modeled step` | modelled |
| 643:71 | LABEL | MECHANICAL | `communication [ILLUSTRATIVE split],` | `` communication `[ILLUSTRATIVE split]`, `` | label-backticks |
| 658:44 | LABEL | MECHANICAL | `GB/s) [ILLUSTRATIVE]:` | `` GB/s) `[ILLUSTRATIVE]`: `` | label-backticks |
| 668:43 | TERM | MECHANICAL | `or KV-cache transfer` | `or KV cache transfer` | kvcache |
| 673:36 | LABEL | MECHANICAL | `minutes [ILLUSTRATIVE]:` | `` minutes `[ILLUSTRATIVE]`: `` | label-backticks |
| 745:84 | SPELLING | MECHANICAL | `fabric uninitialised and` | `fabric uninitialized and` | ize |
| 753:1 | SPELLING | MECHANICAL | `generalised to` | `generalized to` | ize |
| 771:71 | SPELLING | MECHANICAL | `(modelled as` | `(modeled as` | modelled |
| 816:55 | LABEL | MECHANICAL | `% [ILLUSTRATIVE]);` | `` % `[ILLUSTRATIVE]`); `` | label-backticks |
| 859:0 | ACRONYM | JUDGEMENT | `MTBF` | `mean time between failures (MTBF)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 861:24 | LABEL | MECHANICAL | `2.5 [MODELED].` | `` 2.5 `[MODELED]`. `` | label-backticks |
| 862:60 | LABEL | MECHANICAL | `% [MODELED].` | `` % `[MODELED]`. `` | label-backticks |
| 961:34 | LABEL | MECHANICAL | `evidence [ILLUSTRATIVE; exact log wording varies by version].*` | `` evidence `[ILLUSTRATIVE; exact log wording varies by version]`.* `` | label-backticks |
| 965:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| Supporting evidence \| Discriminating test…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 967:195 | SPELLING | MECHANICAL | `an uninitialised NVSwitch` | `an uninitialized NVSwitch` | ize |
| 983:0 | ORION | JUDGEMENT | `busbw 466 GB/s at 8 GiB` | `busbw 466 GB/s at 8 GiB (NVLS)` | busbw above 450 GB/s is only possible with NVLS (VERIFIED_FACTS); Table at line 600 already says so |
| 984:1 | LABEL | MECHANICAL | `[ILLUSTRATIVE].` | `` `[ILLUSTRATIVE]`. `` | label-backticks |
| 1015:0 | CAPTION | JUDGEMENT | `\| Signal \| Threshold \| Safe action \| Escalate to \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 1044:25 | SPELLING | MECHANICAL | `ORION, modelled),` | `ORION, modeled),` | modelled |

### `book/part-5-production-operations/ch17-kubernetes-slurm-scheduling/exercises.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 167:7 | SPELLING | MECHANICAL | `guide organised by` | `guide organized by` | ize |

### `book/part-5-production-operations/ch17-kubernetes-slurm-scheduling/lab/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 181:36 | STYLE | MECHANICAL | `block vs. different` | `block vs different` | vs-period |

### `book/part-5-production-operations/ch17-kubernetes-slurm-scheduling/manuscript.md`

10 finding(s): 1 MECHANICAL, 9 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 75:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 248:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 560:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 560:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 728:63 | TERM | MECHANICAL | `tokenization, KV-cache offload,` | `tokenization, KV cache offload,` | kvcache |
| 741:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 862:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 971:0 | CAPTION | JUDGEMENT | `\| # \| Hypothesis \| Evidence for \| Discriminating test \| Resu…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 1030:0 | ACRONYM | JUDGEMENT | `SLO` | `service-level objective (SLO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 1032:0 | CAPTION | JUDGEMENT | `\| Signal \| Source \| Threshold \| First safe action \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |

### `book/part-5-production-operations/ch18-observability-slos-incident-response/lab/README.md`

5 finding(s): 5 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 7:79 | UNIT | MECHANICAL | `looks ~18` | `looks ≈ 18` | approx-tilde |
| 83:1 | SPELLING | MECHANICAL | `judgement.` | `judgment.` | judgement |
| 112:70 | SPELLING | MECHANICAL | `are authorised to` | `are authorized to` | ize |
| 115:64 | SPELLING | MECHANICAL | `and re-run Tasks` | `and rerun Tasks` | rerun |
| 127:48 | SPELLING | MECHANICAL | `and synchronisation (for` | `and synchronization (for` | ize |

### `book/part-5-production-operations/ch18-observability-slos-incident-response/manuscript.md`

43 finding(s): 11 MECHANICAL, 32 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 9:51 | SPELLING | MECHANICAL | `alerts, organise dashboards` | `alerts, organize dashboards` | ize |
| 45:0 | STYLE | JUDGEMENT | `Acronyms used throughout:` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 47:58 | SPELLING | MECHANICAL | `data-modelling language` | `data-modeling language` | modelled |
| 48:49 | ACRONYM | MECHANICAL | `(Priority Flow Control),` | `(priority flow control),` | exp-pfc |
| 49:0 | ACRONYM | JUDGEMENT | `Congestion Notification Packet` | `congestion notification packet` | as above |
| 49:59 | ACRONYM | MECHANICAL | `(model FLOP utilization),` | `(model FLOPs utilization),` | exp-mfu |
| 60:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 66:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 125:12 | SPELLING | MECHANICAL | `18.1 summarises the` | `18.1 summarizes the` | ize |
| 135:0 | ACRONYM | JUDGEMENT | `AER` | `advanced error reporting (AER)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 136:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 137:0 | ACRONYM | JUDGEMENT | `BGP` | `Border Gateway Protocol (BGP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 149:0 | CAPTION | JUDGEMENT | `\| Key \| Example \| Present in \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 154:0 | ACRONYM | JUDGEMENT | `HCA` | `host channel adapter (HCA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 154:0 | ACRONYM | JUDGEMENT | `BDF` | `bus:device.function (BDF)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 169:90 | TERM | MECHANICAL | `supported datacenter` | `supported data center` | datacenter |
| 175:0 | CAPTION | JUDGEMENT | `\| Family \| Metrics \| Unit \| Operational use \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 184:74 | TERM | MECHANICAL | `\| KV-cache headroom` | `\| KV cache headroom` | kvcache |
| 190:0 | ACRONYM | JUDGEMENT | `SM` | `streaming multiprocessor (SM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 210:0 | ACRONYM | JUDGEMENT | `TDP` | `thermal design power (TDP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 252:0 | ACRONYM | JUDGEMENT | `DCQCN` | `Data Center Quantized Congestion Notification (DCQCN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 298:0 | CAPTION | JUDGEMENT | `\| What \| Path (OpenConfig unless noted) \| Mode \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 333:31 | TERM | MECHANICAL | `and KV-cache usage` | `and KV cache usage` | kvcache |
| 358:44 | SPELLING | MECHANICAL | `18.2; synchronise clocks` | `18.2; synchronize clocks` | ize |
| 365:0 | ACRONYM | JUDGEMENT | `KV` | `key-value (KV)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 370:80 | SPELLING | MECHANICAL | `to localise hangs.` | `to localize hangs.` | ize |
| 460:0 | ACRONYM | JUDGEMENT | `MTBF` | `mean time between failures (MTBF)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 480:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line is the first body use; currently expanded only at line 999 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 486:0 | ACRONYM | JUDGEMENT | `RPO` | `recovery point objective (RPO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 489:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 519:0 | LABEL | JUDGEMENT | `*Table 18.5 — Multiwindow burn-rate policy for a 30-day SLO (Google SR…` | add `[MODELED]` (burn-rate arithmetic from the SRE workbook) to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 625:0 | LABEL | JUDGEMENT | `*Table 18.6 — Dashboard mock-up specification for ORION (queries refer…` | add `[ILLUSTRATIVE]` thresholds to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 638:0 | ACRONYM | JUDGEMENT | `FEC` | `forward error correction (FEC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 688:0 | CAPTION | JUDGEMENT | `\| Milestone \| Definition \| Source \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 707:0 | CAPTION | JUDGEMENT | `\| Blaming \| Blameless \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 734:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 735:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 735:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 820:34 | SPELLING | MECHANICAL | `chapter's analyses on` | `chapter's analyzes on` | analyse |
| 873:0 | ACRONYM | JUDGEMENT | `BMC` | `baseboard management controller (BMC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 921:0 | LABEL | JUDGEMENT | `*Table 18.10 — Observability design trade-offs.*` | add `[ILLUSTRATIVE]` to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 935:0 | ORION | JUDGEMENT | `Fabric/Storage on-call` | `Fabric/Storage on-call (keep)` | depends on the §5 decision |
| 978:0 | ACRONYM | JUDGEMENT | `RTO` | `recovery time objective (RTO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `book/part-5-production-operations/ch19-reliability-security-multitenancy/exercises.md`

6 finding(s): 6 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 35:23 | SPELLING | MECHANICAL | `two artefacts that` | `two artifacts that` | artefact |
| 35:38 | SPELLING | MECHANICAL | `that localise a` | `that localize a` | ize |
| 36:53 | SPELLING | MECHANICAL | `two artefacts.` | `two artifacts.` | artefact |
| 98:79 | TERM | MECHANICAL | `(P99)` | `(p99)` | percentile |
| 110:32 | SPELLING | MECHANICAL | `assumes synchronised clocks.` | `assumes synchronized clocks.` | ize |
| 146:44 | SPELLING | MECHANICAL | `six artefacts.` | `six artifacts.` | artefact |

### `book/part-5-production-operations/ch19-reliability-security-multitenancy/lab/README.md`

4 finding(s): 4 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 25:77 | SPELLING | MECHANICAL | `real artefacts —` | `real artifacts —` | artefact |
| 62:135 | TERM | MECHANICAL | `Poisson P99 at` | `Poisson p99 at` | percentile |
| 72:7 | SPELLING | MECHANICAL | `\| Localise \|` | `\| Localize \|` | ize |
| 123:6 | SPELLING | MECHANICAL | `with authorisation,` | `with authorization,` | ize |

### `book/part-5-production-operations/ch19-reliability-security-multitenancy/manuscript.md`

51 finding(s): 21 MECHANICAL, 30 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 6:14 | SPELLING | MECHANICAL | `FMEA; recognise GPU,` | `FMEA; recognize GPU,` | ize |
| 44:0 | STYLE | JUDGEMENT | `Acronyms:` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 48:25 | ACRONYM | MECHANICAL | `(bit error rate),` | `(bit error ratio),` | exp-ber |
| 97:0 | ACRONYM | JUDGEMENT | `MTTR` | `mean time to repair (MTTR)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 133:0 | ACRONYM | JUDGEMENT | `HBM` | `high-bandwidth memory (HBM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 133:0 | ACRONYM | JUDGEMENT | `MIG` | `Multi-Instance GPU (MIG)` | first occurrence on the line is the first body use; currently expanded only at line 953 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 133:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 166:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 167:0 | ACRONYM | JUDGEMENT | `SLO` | `service-level objective (SLO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 173:62 | SPELLING | MECHANICAL | `that minimises jobs` | `that minimizes jobs` | ize |
| 208:0 | CAPTION | JUDGEMENT | `\| State \| Meaning \| Action \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 210:0 | ACRONYM | JUDGEMENT | `RMA` | `return merchandise authorization (RMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 244:1 | SPELLING | MECHANICAL | `initialisation ("system` | `initialization ("system` | ize |
| 248:0 | ACRONYM | JUDGEMENT | `DCGM` | `NVIDIA Data Center GPU Manager (DCGM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 282:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 290:68 | SPELLING | MECHANICAL | `the fibre.` | `the fiber.` | fibre |
| 294:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 324:72 | SPELLING | MECHANICAL | `itself localises nothing.` | `itself localizes nothing.` | ize |
| 325:46 | SPELLING | MECHANICAL | `fault. Localisation needs` | `fault. Localization needs` | ize |
| 361:0 | ACRONYM | JUDGEMENT | `SM` | `streaming multiprocessor (SM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 362:0 | ACRONYM | JUDGEMENT | `ECMP` | `equal-cost multipath (ECMP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 363:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 363:0 | ACRONYM | JUDGEMENT | `ECN` | `explicit congestion notification (ECN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 363:0 | ACRONYM | JUDGEMENT | `CNP` | `congestion notification packet (CNP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 364:0 | ACRONYM | JUDGEMENT | `NUMA` | `non-uniform memory access (NUMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 420:61 | SPELLING | MECHANICAL | `join materialised for` | `join materialized for` | ize |
| 422:5 | SPELLING | MECHANICAL | `### Localising with` | `### Localizing with` | ize |
| 460:24 | SPELLING | MECHANICAL | `node-health-check script` | `node-health check script` | compounds |
| 479:0 | LABEL | JUDGEMENT | `*Table 19.5 — Containment decisions for the lab incident.*` | add `[SIMULATED]` (lab incident data) to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 514:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 514:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 560:3 | SPELLING | MECHANICAL | `finalisation step` | `finalization step` | ize |
| 581:0 | ACRONYM | JUDGEMENT | `RTO` | `recovery time objective (RTO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 588:27 | SPELLING | MECHANICAL | `it towards the` | `it toward the` | towards |
| 632:0 | ORION | JUDGEMENT | `the platform team` | `the Platform team` | canonical team name |
| 639:0 | ACRONYM | JUDGEMENT | `BMC` | `baseboard management controller (BMC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 641:0 | ACRONYM | JUDGEMENT | `OOB` | `out-of-band (OOB)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 641:0 | ACRONYM | JUDGEMENT | `IPMI` | `Intelligent Platform Management Interface (IPMI)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 697:0 | CAPTION | JUDGEMENT | `\| Step \| Example \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 699:0 | ACRONYM | JUDGEMENT | `TTFT` | `time to first token (TTFT)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 700:0 | ACRONYM | JUDGEMENT | `SLI` | `service-level indicator (SLI)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 703:45 | SPELLING | MECHANICAL | `spine utilisation and` | `spine utilization and` | ize |
| 724:12 | SPELLING | MECHANICAL | `— Localise the` | `— Localize the` | ize |
| 760:98 | SPELLING | MECHANICAL | `the fibre` | `the fiber` | fibre |
| 767:0 | CAPTION | JUDGEMENT | `\| Hypothesis \| Evidence \| Verdict \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 796:92 | UNIT | MECHANICAL | `by ~10` | `by ≈ 10` | approx-tilde |
| 839:26 | SPELLING | MECHANICAL | `test.** Re-run on` | `test.** Rerun on` | rerun |
| 873:6 | SPELLING | MECHANICAL | `**Localise (≤` | `**Localize (≤` | ize |
| 895:87 | SPELLING | MECHANICAL | `and synchronised` | `and synchronized` | ize |
| 912:19 | SPELLING | MECHANICAL | `timeout localises nothing;` | `timeout localizes nothing;` | ize |
| 932:66 | SPELLING | MECHANICAL | `two artefacts should` | `two artifacts should` | artefact |

### `book/part-5-production-operations/ch20-automation-safe-change/exercises.md`

5 finding(s): 5 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 23:39 | XREF-STYLE | MECHANICAL | `of §20.5 and` | `of Section 20.5 and` | section-sign |
| 43:62 | XREF-STYLE | MECHANICAL | `in §20.5.1.` | `in Section 20.5.1.` | section-sign |
| 191:49 | XREF-STYLE | MECHANICAL | `of §20.13.` | `of Section 20.13.` | section-sign |
| 211:29 | SPELLING | MECHANICAL | `both artefacts;` | `both artifacts;` | artefact |
| 218:8 | XREF-STYLE | MECHANICAL | `The §20.11 expected-loss` | `The Section 20.11 expected-loss` | section-sign |

### `book/part-5-production-operations/ch20-automation-safe-change/lab/README.md`

9 finding(s): 9 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 56:48 | XREF-STYLE | MECHANICAL | `\| §20.3,` | `\| Section 20.3,` | section-sign |
| 56:55 | XREF-STYLE | MECHANICAL | `§20.3, §20.4 \|` | `§20.3, Section 20.4 \|` | section-sign |
| 57:54 | XREF-STYLE | MECHANICAL | `\| §20.5 \|` | `\| Section 20.5 \|` | section-sign |
| 58:48 | XREF-STYLE | MECHANICAL | `\| §20.7 \|` | `\| Section 20.7 \|` | section-sign |
| 59:33 | XREF-STYLE | MECHANICAL | `\| §20.8 \|` | `\| Section 20.8 \|` | section-sign |
| 60:60 | XREF-STYLE | MECHANICAL | `\| §20.9 \|` | `\| Section 20.9 \|` | section-sign |
| 61:20 | XREF-STYLE | MECHANICAL | `\| §20.10 \|` | `\| Section 20.10 \|` | section-sign |
| 62:67 | XREF-STYLE | MECHANICAL | `\| §20.11 \|` | `\| Section 20.11 \|` | section-sign |
| 165:56 | SPELLING | MECHANICAL | `own judgement.` | `own judgment.` | judgement |

### `book/part-5-production-operations/ch20-automation-safe-change/manuscript.md`

33 finding(s): 27 MECHANICAL, 6 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 38:0 | ACRONYM | JUDGEMENT | `Congestion Notification Packets` | `congestion notification packets` | as above |
| 38:24 | ACRONYM | MECHANICAL | `with Priority Flow Control (PFC),` | `with priority flow control (PFC),` | exp-pfc |
| 44:22 | SPELLING | MECHANICAL | `chapter generalises.` | `chapter generalizes.` | ize |
| 70:0 | ACRONYM | JUDGEMENT | `BMC` | `baseboard management controller (BMC)` | first occurrence on the line is the first body use; currently expanded only at line 116 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 79:62 | XREF-STYLE | MECHANICAL | `(§20.3–§20.5).` | `(Section 20.3–§20.5).` | section-sign |
| 79:68 | XREF-STYLE | MECHANICAL | `(§20.3–§20.5).` | `(§20.3–Section 20.5).` | section-sign |
| 81:4 | XREF-STYLE | MECHANICAL | `(§20.7,` | `(Section 20.7,` | section-sign |
| 81:11 | XREF-STYLE | MECHANICAL | `(§20.7, §20.9).` | `(§20.7, Section 20.9).` | section-sign |
| 82:42 | XREF-STYLE | MECHANICAL | `(§20.8).` | `(Section 20.8).` | section-sign |
| 83:50 | XREF-STYLE | MECHANICAL | `(§20.10).` | `(Section 20.10).` | section-sign |
| 108:75 | XREF-STYLE | MECHANICAL | `(§20.9).` | `(Section 20.9).` | section-sign |
| 118:168 | SPELLING | MECHANICAL | `YANG modelling language` | `YANG modeling language` | modelled |
| 119:309 | XREF-STYLE | MECHANICAL | `(§20.3)` | `(Section 20.3)` | section-sign |
| 192:59 | XREF-STYLE | MECHANICAL | `APIs). §20.13 walks` | `APIs). Section 20.13 walks` | section-sign |
| 239:103 | XREF-STYLE | MECHANICAL | `of §20.3.3 at` | `of Section 20.3.3 at` | section-sign |
| 248:31 | XREF-STYLE | MECHANICAL | `(§20.5),` | `(Section 20.5),` | section-sign |
| 278:0 | ACRONYM | JUDGEMENT | `BGP` | `Border Gateway Protocol (BGP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 383:43 | XREF-STYLE | MECHANICAL | `of §20.3 to` | `of Section 20.3 to` | section-sign |
| 398:29 | XREF-STYLE | MECHANICAL | `(§20.13).` | `(Section 20.13).` | section-sign |
| 399:19 | XREF-STYLE | MECHANICAL | `of §20.7:` | `of Section 20.7:` | section-sign |
| 564:0 | ACRONYM | JUDGEMENT | `QP` | `queue pair (QP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 564:45 | SPELLING | MECHANICAL | `\| Re-run reconciler` | `\| Rerun reconciler` | rerun |
| 576:81 | SPELLING | MECHANICAL | `"Re-image the` | `"Reimage the` | rerun |
| 649:28 | XREF-STYLE | MECHANICAL | `8, §8.7](../../part-3-networking/ch08-rdma-rocev2-infiniband/)).` | `8, Section 8.7](../../part-3-networking/ch08-rdma-rocev2-infiniband/)).` | section-sign |
| 739:38 | SPELLING | MECHANICAL | `GPU-h. Organisations rightly` | `GPU-h. Organizations rightly` | ize |
| 762:41 | SPELLING | MECHANICAL | `the re-run is` | `the rerun is` | rerun |
| 763:1 | XREF-STYLE | MECHANICAL | `§20.7 over` | `Section 20.7 over` | section-sign |
| 792:17 | SPELLING | MECHANICAL | `telemetry artefact;` | `telemetry artifact;` | artefact |
| 871:0 | CAPTION | JUDGEMENT | `\| Signal \| Threshold \| Action \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 887:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line is the first body use; currently expanded only at line 943 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 899:7 | XREF-STYLE | MECHANICAL | `The §20.11 expected-loss` | `The Section 20.11 expected-loss` | section-sign |
| 900:63 | SPELLING | MECHANICAL | `not judgement;` | `not judgment;` | judgement |
| 962:80 | XREF-STYLE | MECHANICAL | `in §20.6.2,` | `in Section 20.6.2,` | section-sign |

### `book/part-5-production-operations/ch21-capacity-power-economics/exercises.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 102:30 | SPELLING | MECHANICAL | `your organisation would` | `your organization would` | ize |
| 110:94 | TERM | MECHANICAL | `a P90 demand` | `a p90 demand` | percentile |

### `book/part-5-production-operations/ch21-capacity-power-economics/manuscript.md`

29 finding(s): 14 MECHANICAL, 15 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 34:68 | SPELLING | MECHANICAL | `22's optimisation decisions,` | `22's optimization decisions,` | ize |
| 37:0 | STYLE | JUDGEMENT | `Acronyms:` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 38:14 | ACRONYM | MECHANICAL | `(model FLOP utilization),` | `(model FLOPs utilization),` | exp-mfu |
| 47:0 | CAPTION | JUDGEMENT | `\| Definition \| Numerator / denominator \| Measured from \| Typ…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 65:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 87:0 | ACRONYM | JUDGEMENT | `MTBF` | `mean time between failures (MTBF)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 148:0 | ACRONYM | JUDGEMENT | `SLO` | `service-level objective (SLO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 158:33 | TERM | MECHANICAL | `(P50 and` | `(p50 and` | percentile |
| 158:41 | TERM | MECHANICAL | `and P90 demand)` | `and p90 demand)` | percentile |
| 164:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 165:0 | ACRONYM | JUDGEMENT | `TTFT` | `time to first token (TTFT)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 165:0 | ACRONYM | JUDGEMENT | `TPOT` | `time per output token (TPOT)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 184:15 | TERM | MECHANICAL | `a P50 and` | `a p50 and` | percentile |
| 184:25 | TERM | MECHANICAL | `a P90 scenario,` | `a p90 scenario,` | percentile |
| 185:60 | TERM | MECHANICAL | `for P90,` | `for p90,` | percentile |
| 185:74 | TERM | MECHANICAL | `for P50,` | `for p50,` | percentile |
| 233:0 | CAPTION | JUDGEMENT | `\| Component \| Formula \| ORION-256 \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 289:52 | TERM | MECHANICAL | `the P90 moment` | `the p90 moment` | percentile |
| 292:61 | TERM | MECHANICAL | `the P90 scenario` | `the p90 scenario` | percentile |
| 305:0 | CAPTION | JUDGEMENT | `\| Per node \| Design A — H100-class, air \| Design B — next-ge…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 357:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 380:44 | SPELLING | MECHANICAL | `different optimisations.` | `different optimizations.` | ize |
| 403:0 | ACRONYM | JUDGEMENT | `BMC` | `baseboard management controller (BMC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 427:0 | ACRONYM | JUDGEMENT | `DCGM` | `NVIDIA Data Center GPU Manager (DCGM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 660:59 | SPELLING | MECHANICAL | `jobs. Re-run the` | `jobs. Rerun the` | rerun |
| 668:0 | LABEL | JUDGEMENT | `*Table 21.7 — Capacity and economics trade-offs.*` | add `[ILLUSTRATIVE]` to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 684:75 | TERM | MECHANICAL | `(P50/P90)` | `(p50/P90)` | percentile |
| 684:79 | TERM | MECHANICAL | `(P50/P90)` | `(P50/p90)` | percentile |
| 719:0 | ACRONYM | JUDGEMENT | `MTTR` | `mean time to repair (MTTR)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `book/part-5-production-operations/ch22-cross-layer-performance-engineering/README.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 10:1 | SPELLING | MECHANICAL | `analyse scaling` | `analyze scaling` | analyse |
| 25:23 | SPELLING | MECHANICAL | `**recognise**` | `**recognize**` | ize |

### `book/part-5-production-operations/ch22-cross-layer-performance-engineering/exercises.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 21:40 | SPELLING | MECHANICAL | `the utilisation metric;` | `the utilization metric;` | ize |
| 172:46 | SPELLING | MECHANICAL | `one-sentence judgement.` | `one-sentence judgment.` | judgement |

### `book/part-5-production-operations/ch22-cross-layer-performance-engineering/lab/README.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 21:63 | LABEL | MECHANICAL | `**[SIMULATED]**,` | `` **`[SIMULATED]`**, `` | label-backticks |
| 118:23 | SPELLING | MECHANICAL | `are authorised to` | `are authorized to` | ize |

### `book/part-5-production-operations/ch22-cross-layer-performance-engineering/manuscript.md`

24 finding(s): 15 MECHANICAL, 9 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 25:23 | SPELLING | MECHANICAL | `**recognise**` | `**recognize**` | ize |
| 69:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 88:0 | ACRONYM | JUDGEMENT | `SM` | `streaming multiprocessor (SM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 90:94 | SPELLING | MECHANICAL | `m microbatches \|` | `m micro-batches \|` | microbatch |
| 111:6 | ACRONYM | MECHANICAL | `% model FLOP utilisation (MFU)` | `% model FLOPs utilization (MFU)` | exp-mfu |
| 139:39 | SPELLING | MECHANICAL | `than randomised,` | `than randomized,` | ize |
| 154:0 | CAPTION | JUDGEMENT | `\| Layer \| Question \| Signal / tool \| Grain \| Blind spot \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 158:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 162:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 165:196 | STYLE | MECHANICAL | `order vs. physical` | `order vs physical` | vs-period |
| 185:28 | SPELLING | MECHANICAL | `% utilised.` | `% utilized.` | ize |
| 279:49 | SPELLING | MECHANICAL | `cannot rationalise afterwards.` | `cannot rationalize afterwards.` | ize |
| 285:60 | SPELLING | MECHANICAL | `log analyses (tier-split` | `log analyzes (tier-split` | analyse |
| 430:80 | TERM | MECHANICAL | `ORION's rail-optimised design` | `ORION's rail-optimized design` | railopt |
| 477:107 | SPELLING | MECHANICAL | `fabric utilisation during` | `fabric utilization during` | ize |
| 520:145 | SPELLING | MECHANICAL | `producer utilisation near` | `producer utilization near` | ize |
| 536:0 | LABEL | JUDGEMENT | `*Table 22.9 — Cross-layer performance anti-patterns.*` | add `[ILLUSTRATIVE]` to the caption | caption of a table with quantitative cells and no evidence label (STYLE_GUIDE §3: label in every table caption) |
| 549:29 | UNIT | MECHANICAL | `"~20` | `"≈ 20` | approx-tilde |
| 667:0 | ACRONYM | JUDGEMENT | `NVLS` | `NVLink SHARP (NVLS)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 678:0 | ACRONYM | JUDGEMENT | `PXN` | `PCI × NVLink (PXN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 836:26 | SPELLING | MECHANICAL | `(localise).**` | `(localize).**` | ize |
| 959:0 | ORION | JUDGEMENT | `Storage on-call` | `Storage on-call (keep)` | depends on the §5 decision |
| 962:62 | SPELLING | MECHANICAL | `no localised cause` | `no localized cause` | ize |
| 994:3 | SPELLING | MECHANICAL | `amortised checkpoint` | `amortized checkpoint` | ize |

### `book/part-6-applied-engineering/ch23-capstone-production-ai-cluster/README.md`

5 finding(s): 5 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 9:80 | SPELLING | MECHANICAL | `and prioritising a` | `and prioritizing a` | ize |
| 26:6 | SPELLING | MECHANICAL | `**Analyse**` | `**Analyze**` | analyse |
| 34:35 | SPELLING | MECHANICAL | `a prioritised next-step` | `a prioritized next-step` | ize |
| 38:41 | TERM | MECHANICAL | `(data-centre anatomy),` | `(data-center anatomy),` | datacentre |
| 56:21 | SPELLING | MECHANICAL | `a prioritised next-step` | `a prioritized next-step` | ize |

### `book/part-6-applied-engineering/ch23-capstone-production-ai-cluster/exercises.md`

4 finding(s): 4 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 23:38 | SPELLING | MECHANICAL | `rack towards its` | `rack toward its` | towards |
| 84:30 | SPELLING | MECHANICAL | `(re-run).**` | `(rerun).**` | rerun |
| 102:67 | TERM | MECHANICAL | `cross-rail KV-cache transfer` | `cross-rail KV cache transfer` | kvcache |
| 144:52 | SPELLING | MECHANICAL | `a prioritised next-step` | `a prioritized next-step` | ize |

### `book/part-6-applied-engineering/ch23-capstone-production-ai-cluster/lab/README.md`

3 finding(s): 2 MECHANICAL, 1 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 79:99 | SPELLING | MECHANICAL | `not analysed \|` | `not analyzed \|` | analyse |
| 162:56 | LABEL | JUDGEMENT | `` `[VENDOR-SPEC]` `` | `` `[VENDOR-SPEC, YYYY-MM]` `` | label-vendor-date: the text names the label for the learner, so use the template form |
| 183:65 | SPELLING | MECHANICAL | `column. Re-run the` | `column. Rerun the` | rerun |

### `book/part-6-applied-engineering/ch23-capstone-production-ai-cluster/manuscript.md`

45 finding(s): 30 MECHANICAL, 15 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 6:82 | SPELLING | MECHANICAL | `arithmetic, analyse failure` | `arithmetic, analyze failure` | analyse |
| 8:78 | SPELLING | MECHANICAL | `a prioritised backlog.` | `a prioritized backlog.` | ize |
| 23:6 | SPELLING | MECHANICAL | `**Analyse**` | `**Analyze**` | analyse |
| 31:35 | SPELLING | MECHANICAL | `a prioritised next-step` | `a prioritized next-step` | ize |
| 37:0 | STYLE | JUDGEMENT | `**Acronyms used here.**` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 40:32 | ACRONYM | MECHANICAL | `MFU model FLOPs utilisation;` | `MFU model FLOPs utilization;` | exp-mfu |
| 42:68 | SPELLING | MECHANICAL | `merchandise authorisation;` | `merchandise authorization;` | ize |
| 73:1 | SPELLING | MECHANICAL | `organisation to` | `organization to` | ize |
| 95:38 | SPELLING | MECHANICAL | `\| Centre of` | `\| Center of` | centre |
| 99:183 | SPELLING | MECHANICAL | `vs optimised,` | `vs optimized,` | ize |
| 100:0 | ACRONYM | JUDGEMENT | `TTFT` | `time to first token (TTFT)` | first occurrence on the line is the first body use; currently expanded only at line 158 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 100:0 | ACRONYM | JUDGEMENT | `TPOT` | `time per output token (TPOT)` | first occurrence on the line is the first body use; currently expanded only at line 158 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 101:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line is the first body use; currently expanded only at line 998 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 103:0 | ACRONYM | JUDGEMENT | `RPO` | `recovery point objective (RPO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 103:0 | ACRONYM | JUDGEMENT | `RTO` | `recovery time objective (RTO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 104:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 104:152 | TERM | MECHANICAL | `pools, KV-cache transfer` | `pools, KV cache transfer` | kvcache |
| 107:73 | SPELLING | MECHANICAL | `it analyses supplied` | `it analyzes supplied` | analyse |
| 155:68 | SPELLING | MECHANICAL | `FLOPs Utilisation (MFU),` | `FLOPs Utilization (MFU),` | ize |
| 157:56 | TERM | MECHANICAL | `concurrency, KV-cache bytes` | `concurrency, KV cache bytes` | kvcache |
| 187:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 221:0 | ACRONYM | JUDGEMENT | `BGP` | `Border Gateway Protocol (BGP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 222:56 | TERM | MECHANICAL | `disaggregated-inference KV-cache transfers` | `disaggregated-inference KV cache transfers` | kvcache |
| 223:20 | TERM | MECHANICAL | `(1) Rail-optimised 400` | `(1) Rail-optimized 400` | railopt |
| 224:42 | TERM | MECHANICAL | `NDR rail-optimised fat` | `NDR rail-optimized fat` | railopt |
| 240:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 334:30 | TERM | MECHANICAL | `a rail-optimised fabric` | `a rail-optimized fabric` | railopt |
| 339:0 | ACRONYM | JUDGEMENT | `PXN` | `PCI × NVLink (PXN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 342:28 | TERM | MECHANICAL | `models, KV-cache transfer` | `models, KV cache transfer` | kvcache |
| 387:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 389:100 | SPELLING | MECHANICAL | `NIC; re-run acceptance` | `NIC; rerun acceptance` | rerun |
| 391:0 | ACRONYM | JUDGEMENT | `ECMP` | `equal-cost multipath (ECMP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 393:0 | ACRONYM | JUDGEMENT | `SLI` | `service-level indicator (SLI)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 397:17 | SPELLING | MECHANICAL | `and prioritising:` | `and prioritizing:` | ize |
| 399:42 | SPELLING | MECHANICAL | `(FMEA, standardised in` | `(FMEA, standardized in` | ize |
| 483:0 | ACRONYM | JUDGEMENT | `MTU` | `maximum transmission unit (MTU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 486:71 | SPELLING | MECHANICAL | `class analysed.` | `class analyzed.` | analyse |
| 489:130 | SPELLING | MECHANICAL | `Backlog prioritised with` | `Backlog prioritized with` | ize |
| 640:5 | SPELLING | MECHANICAL | `### Prioritising the` | `### Prioritizing the` | ize |
| 657:34 | TERM | MECHANICAL | `in rail-optimised design` | `in rail-optimized design` | railopt |
| 746:16 | SPELLING | MECHANICAL | `scatter/gather optimisation each` | `scatter/gather optimization each` | ize |
| 905:32 | SPELLING | MECHANICAL | `been re-imaged from` | `been reimaged from` | rerun |
| 911:69 | SPELLING | MECHANICAL | `and re-run B-02` | `and rerun B-02` | rerun |
| 976:8 | TERM | MECHANICAL | `a rail-optimised fabric,` | `a rail-optimized fabric,` | railopt |
| 983:14 | SPELLING | MECHANICAL | `a prioritised backlog` | `a prioritized backlog` | ize |

### `book/part-6-applied-engineering/ch24-career-paths-engineering-practice/README.md`

2 finding(s): 2 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 19:32 | SPELLING | MECHANICAL | `technical judgement,` | `technical judgment,` | judgement |
| 23:60 | SPELLING | MECHANICAL | `paths, analyse failure` | `paths, analyze failure` | analyse |

### `book/part-6-applied-engineering/ch24-career-paths-engineering-practice/exercises.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 60:24 | TERM | MECHANICAL | `switches, rail-optimised and` | `switches, rail-optimized and` | railopt |

### `book/part-6-applied-engineering/ch24-career-paths-engineering-practice/lab/README.md`

3 finding(s): 3 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 8:18 | SPELLING | MECHANICAL | `a prioritised gap` | `a prioritized gap` | ize |
| 13:21 | SPELLING | MECHANICAL | `fields, normalise and` | `fields, normalize and` | ize |
| 25:48 | SPELLING | MECHANICAL | `24.8a) summarises what` | `24.8a) summarizes what` | ize |

### `book/part-6-applied-engineering/ch24-career-paths-engineering-practice/manuscript.md`

40 finding(s): 33 MECHANICAL, 7 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 22:32 | SPELLING | MECHANICAL | `technical judgement,` | `technical judgment,` | judgement |
| 26:60 | SPELLING | MECHANICAL | `paths, analyse failure` | `paths, analyze failure` | analyse |
| 63:0 | STYLE | JUDGEMENT | `Acronyms:` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 69:18 | ACRONYM | MECHANICAL | `(model FLOP utilisation),` | `(model FLOPs utilization),` | exp-mfu |
| 79:65 | SPELLING | MECHANICAL | `hash-polarised ECMP` | `hash-polarized ECMP` | ize |
| 88:5 | SPELLING | MECHANICAL | `**Utilisation is` | `**Utilization is` | ize |
| 112:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line is the first body use; currently expanded only at line 1030 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 119:77 | TERM | MECHANICAL | `families: data-centre facilities` | `families: data-center facilities` | datacentre |
| 192:40 | TERM | MECHANICAL | `fictional data-centre network` | `fictional data-center network` | datacentre |
| 226:16 | SPELLING | MECHANICAL | `technical judgement,` | `technical judgment,` | judgement |
| 230:128 | SPELLING | MECHANICAL | `An organisation's` | `An organization's` | ize |
| 232:13 | SPELLING | MECHANICAL | `Technical judgement \|` | `Technical judgment \|` | judgement |
| 234:99 | SPELLING | MECHANICAL | `\| Organisation and` | `\| Organization and` | ize |
| 235:94 | SPELLING | MECHANICAL | `lab-quality analyses \|` | `lab-quality analyzes \|` | analyse |
| 287:15 | SPELLING | MECHANICAL | `The organisations named` | `The organizations named` | ize |
| 290:35 | SPELLING | MECHANICAL | `Representative organisations (outline)` | `Representative organizations (outline)` | ize |
| 293:159 | SPELLING | MECHANICAL | `provisioning, utilisation and` | `provisioning, utilization and` | ize |
| 293:251 | SPELLING | MECHANICAL | `isolation, utilisation economics` | `isolation, utilization economics` | ize |
| 297:62 | SPELLING | MECHANICAL | `Groups, organisations and` | `Groups, organizations and` | ize |
| 298:65 | SPELLING | MECHANICAL | `2026-10); organisations are` | `2026-10); organizations are` | ize |
| 364:50 | TERM | MECHANICAL | `4 data-centre facilities` | `4 data-center facilities` | datacentre |
| 400:73 | TERM | MECHANICAL | `"therefore rail-optimised".` | `"therefore rail-optimized".` | railopt |
| 401:23 | SPELLING | MECHANICAL | `you optimise.**` | `you optimize.**` | ize |
| 428:71 | TERM | MECHANICAL | `12 fp32 master/m/v)` | `12 FP32 master/m/v)` | precision |
| 519:0 | ACRONYM | JUDGEMENT | `PXN` | `PCI × NVLink (PXN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 542:50 | SPELLING | MECHANICAL | `per pre-tokenised token` | `per pre-tokenized token` | ize |
| 543:35 | SPELLING | MECHANICAL | `shows judgement.` | `shows judgment.` | judgement |
| 554:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 585:3 | SPELLING | MECHANICAL | `> recognising that` | `> recognizing that` | ize |
| 587:4 | TERM | MECHANICAL | `"rail-optimised"` | `"rail-optimized"` | railopt |
| 603:3 | TERM | MECHANICAL | `A rail-optimised two-tier` | `A rail-optimized two-tier` | railopt |
| 701:74 | UNIT | JUDGEMENT | `> ~10` | `> ≈ 10` | approx-tilde after a comparison sign: reword (e.g. "> ~4B" → "more than about 4B") |
| 703:33 | SPELLING | MECHANICAL | `Port utilisation,` | `Port utilization,` | ize |
| 789:133 | TERM | MECHANICAL | `\| Data-centre architecture,` | `\| Data-center architecture,` | datacentre |
| 796:157 | SPELLING | MECHANICAL | `transfer modelling,` | `transfer modeling,` | modelled |
| 877:49 | SPELLING | MECHANICAL | `without authorisation and` | `without authorization and` | ize |
| 935:0 | CAPTION | JUDGEMENT | `\| Hypothesis \| Prior \| Cost to test \| Risk of test \| Discrim…` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 944:21 | SPELLING | MECHANICAL | `power localises it` | `power localizes it` | ize |
| 979:0 | CAPTION | JUDGEMENT | `\| Step \| Action \| Signal / threshold \| Escalate when \|` | `low priority: add a caption line *Table N.M — title [LABEL].* — use a letter suffix (e.g. 4.3a) to avoid renumbering, or renumber and fix every reference (lint XREF check)` | table has no caption; captions carry the evidence label (STYLE_GUIDE §3/§7) |
| 1006:38 | SPELLING | MECHANICAL | `ambiguity, judgement,` | `ambiguity, judgment,` | judgement |

### `capstones/capstone-a-256-gpu-training-cluster/README.md`

11 finding(s): 1 MECHANICAL, 10 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 10:60 | TERM | MECHANICAL | `the data-centre floor.` | `the data-center floor.` | datacentre |
| 32:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 32:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 43:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 43:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 44:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 107:0 | ACRONYM | JUDGEMENT | `ECMP` | `equal-cost multipath (ECMP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 108:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 108:0 | ACRONYM | JUDGEMENT | `ECN` | `explicit congestion notification (ECN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 108:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 134:0 | ACRONYM | JUDGEMENT | `MFU` | `model FLOPs utilization (MFU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `capstones/capstone-a-256-gpu-training-cluster/starter-kit/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 45:51 | SPELLING | MECHANICAL | `component catalog (USD,` | `component catalogue (USD,` | catalog |

### `capstones/capstone-b-network-telemetry-troubleshooting/README.md`

11 finding(s): 0 MECHANICAL, 11 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 28:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 29:0 | ACRONYM | JUDGEMENT | `PFC` | `priority flow control (PFC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 29:0 | ACRONYM | JUDGEMENT | `ECN` | `explicit congestion notification (ECN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 29:0 | ACRONYM | JUDGEMENT | `DSCP` | `differentiated services code point (DSCP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 35:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 35:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 35:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 38:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 49:0 | ACRONYM | JUDGEMENT | `ECMP` | `equal-cost multipath (ECMP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 112:0 | ACRONYM | JUDGEMENT | `CNP` | `congestion notification packet (CNP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 112:0 | ACRONYM | JUDGEMENT | `FEC` | `forward error correction (FEC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `capstones/capstone-b-network-telemetry-troubleshooting/starter-kit/README.md`

3 finding(s): 3 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 46:75 | UNIT | MECHANICAL | `tables, ~60` | `tables, ≈ 60` | approx-tilde |
| 47:73 | UNIT | MECHANICAL | `per ~60` | `per ≈ 60` | approx-tilde |
| 48:72 | UNIT | MECHANICAL | `host, ~120` | `host, ≈ 120` | approx-tilde |

### `capstones/capstone-c-distributed-training-performance/README.md`

5 finding(s): 0 MECHANICAL, 5 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 7:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 20:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 21:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 26:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 26:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `capstones/capstone-d-llm-inference-platform/README.md`

8 finding(s): 0 MECHANICAL, 8 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 4:0 | ACRONYM | JUDGEMENT | `SLO` | `service-level objective (SLO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 4:0 | ACRONYM | JUDGEMENT | `SLI` | `service-level indicator (SLI)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 5:0 | ACRONYM | JUDGEMENT | `TTFT` | `time to first token (TTFT)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 9:0 | ACRONYM | JUDGEMENT | `KV` | `key-value (KV)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 10:0 | ACRONYM | JUDGEMENT | `TPOT` | `time per output token (TPOT)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 10:0 | ACRONYM | JUDGEMENT | `ITL` | `inter-token latency (ITL)` | first occurrence on the line is the first body use; currently expanded only at line 65 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 33:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line is the first body use; currently expanded only at line 97 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 35:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `capstones/capstone-d-llm-inference-platform/starter-kit/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 4:14 | TERM | MECHANICAL | `many KV-cache tokens` | `many KV cache tokens` | kvcache |

### `capstones/capstone-e-fleet-lifecycle-automation/README.md`

24 finding(s): 7 MECHANICAL, 17 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 14:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line is the first body use; currently expanded only at line 298 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 14:0 | TERM | JUDGEMENT | `Fleet/Datacenter Operations` | `Fleet/Data Center Operations` | data center (two words); capitalised here as a role title |
| 20:0 | STYLE | JUDGEMENT | `Acronyms used throughout:` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 33:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 52:28 | LABEL | MECHANICAL | `2026-10-19 [ILLUSTRATIVE]:` | `` 2026-10-19 `[ILLUSTRATIVE]`: `` | label-backticks |
| 60:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 65:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 65:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 65:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 70:9 | LABEL | MECHANICAL | `floor [ILLUSTRATIVE agreements].` | `` floor `[ILLUSTRATIVE agreements]`. `` | label-backticks |
| 117:208 | LABEL | MECHANICAL | `labelled [ILLUSTRATIVE]/[VENDOR-SPEC]/[MEASURED];` | `` labelled `[ILLUSTRATIVE]`/[VENDOR-SPEC]/[MEASURED]; `` | label-backticks |
| 117:223 | LABEL | MECHANICAL | `[ILLUSTRATIVE]/[VENDOR-SPEC]/[MEASURED];` | `` [ILLUSTRATIVE]/`[VENDOR-SPEC]`/[MEASURED]; `` | label-backticks |
| 117:223 | LABEL | JUDGEMENT | `[ILLUSTRATIVE]/[VENDOR-SPEC]/[MEASURED];` | `` [ILLUSTRATIVE]/`[VENDOR-SPEC, YYYY-MM]`/[MEASURED]; `` | label-vendor-date: the text names the label for the learner, so use the template form |
| 117:237 | LABEL | MECHANICAL | `[ILLUSTRATIVE]/[VENDOR-SPEC]/[MEASURED];` | `` [ILLUSTRATIVE]/[VENDOR-SPEC]/`[MEASURED]`; `` | label-backticks |
| 120:247 | LABEL | MECHANICAL | `reasons; [MODELED] capacity` | `` reasons; `[MODELED]` capacity `` | label-backticks |
| 179:0 | ACRONYM | JUDGEMENT | `HBM` | `high-bandwidth memory (HBM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 183:70 | SPELLING | MECHANICAL | `explicitly authorised to` | `explicitly authorized to` | ize |
| 203:0 | ACRONYM | JUDGEMENT | `NUMA` | `non-uniform memory access (NUMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 206:0 | ACRONYM | JUDGEMENT | `FEC` | `forward error correction (FEC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 211:0 | ACRONYM | JUDGEMENT | `SLI` | `service-level indicator (SLI)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 212:0 | ACRONYM | JUDGEMENT | `OOB` | `out-of-band (OOB)` | first occurrence on the line is the first body use; currently expanded only at line 304 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 233:0 | ACRONYM | JUDGEMENT | `NVLS` | `NVLink SHARP (NVLS)` | first occurrence on the line is the first body use; currently expanded only at line 236 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 236:0 | ACRONYM | JUDGEMENT | `SHARP` | `Scalable Hierarchical Aggregation and Reduction Protocol (SHARP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 265:0 | ACRONYM | JUDGEMENT | `TPOT` | `time per output token (TPOT)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `capstones/capstone-e-fleet-lifecycle-automation/starter-kit/README.md`

1 finding(s): 1 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 101:32 | SPELLING | MECHANICAL | `are authorised to` | `are authorized to` | ize |

### `capstones/capstone-f-reliability-game-day/README.md`

13 finding(s): 4 MECHANICAL, 9 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 13:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line is the first body use; currently expanded only at line 280 — move the expansion here (or into the chapter's Acronyms paragraph) |
| 19:0 | ACRONYM | JUDGEMENT | `MTTR (mean time to recover)` | `MTTR (mean time to restore)` | canonical MTTR wording for a service in an incident (register §(b)) |
| 19:0 | STYLE | JUDGEMENT | `Acronyms:` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 25:67 | SPELLING | MECHANICAL | `explicitly authorised to` | `explicitly authorized to` | ize |
| 50:4 | SPELLING | MECHANICAL | `is modelled as` | `is modeled as` | modelled |
| 54:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 54:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 54:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 73:0 | ACRONYM | JUDGEMENT | `MTBF` | `mean time between failures (MTBF)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 73:63 | SPELLING | MECHANICAL | `launch, initialise communicators` | `launch, initialize communicators` | ize |
| 159:62 | SPELLING | MECHANICAL | `day analysed (T3–T5)` | `day analyzed (T3–T5)` | analyse |
| 188:0 | ACRONYM | JUDGEMENT | `BMC` | `baseboard management controller (BMC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 189:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |

### `capstones/capstone-f-reliability-game-day/starter-kit/README.md`

4 finding(s): 4 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 80:18 | SPELLING | MECHANICAL | `Backlog prioritisation \|` | `Backlog prioritization \|` | ize |
| 89:3 | SPELLING | MECHANICAL | `- Re-run the` | `- Rerun the` | rerun |
| 106:41 | SPELLING | MECHANICAL | `written authorisation for` | `written authorization for` | ize |
| 114:160 | SPELLING | MECHANICAL | `then re-run acceptance` | `then rerun acceptance` | rerun |

### `capstones/capstone-g-fault-tolerant-512-node-training/README.md`

24 finding(s): 8 MECHANICAL, 16 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 6:0 | ACRONYM | JUDGEMENT | `ECC` | `error-correcting code (ECC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 7:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 15:0 | ACRONYM | JUDGEMENT | `SRE` | `site reliability engineering (SRE)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 26:0 | STYLE | JUDGEMENT | `Acronyms:` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 27:69 | TERM | MECHANICAL | `(data-centre infrastructure` | `(data-center infrastructure` | datacentre |
| 28:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 29:0 | ACRONYM | JUDGEMENT | `RPO` | `recovery point objective (RPO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 29:0 | ACRONYM | JUDGEMENT | `RTO` | `recovery time objective (RTO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 54:0 | ACRONYM | JUDGEMENT | `MTBF` | `mean time between failures (MTBF)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 58:65 | TERM | MECHANICAL | `(P95 needs` | `(p95 needs` | percentile |
| 58:86 | TERM | MECHANICAL | `spares, P99 52).` | `spares, p99 52).` | percentile |
| 62:46 | TERM | MECHANICAL | `nodes; P95 =` | `nodes; p95 =` | percentile |
| 62:56 | TERM | MECHANICAL | `23, P99 =` | `23, p99 =` | percentile |
| 62:87 | TERM | MECHANICAL | `> P99.` | `> p99.` | percentile |
| 63:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 63:0 | ACRONYM | JUDGEMENT | `PP` | `pipeline parallelism (PP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 63:0 | ACRONYM | JUDGEMENT | `DP` | `data parallelism (DP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 88:0 | ACRONYM | JUDGEMENT | `MFU` | `model FLOPs utilization (MFU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 105:0 | ACRONYM | JUDGEMENT | `NUMA` | `non-uniform memory access (NUMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 108:38 | SPELLING | MECHANICAL | `— normalise kernel,` | `— normalize kernel,` | ize |
| 204:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 212:0 | ACRONYM | JUDGEMENT | `FEC` | `forward error correction (FEC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 219:0 | ACRONYM | JUDGEMENT | `SLO` | `service-level objective (SLO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 282:25 | UNIT | MECHANICAL | `54-day, ~16k-GPU` | `54-day, ≈ 16k-GPU` | approx-tilde |

### `capstones/capstone-h-disaggregated-llm-serving/README.md`

21 finding(s): 10 MECHANICAL, 11 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 5:0 | ACRONYM | JUDGEMENT | `RDMA` | `remote direct memory access (RDMA)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 5:13 | TERM | MECHANICAL | `model KV-cache bytes` | `model KV cache bytes` | kvcache |
| 20:0 | STYLE | JUDGEMENT | `Acronyms:` | `**Acronyms.** ACR (expansion), ACR (expansion), …` | optional: one glossary-paragraph form book-wide (register §(c).7) |
| 21:66 | ACRONYM | MECHANICAL | `(model FLOP utilisation),` | `(model FLOPs utilization),` | exp-mfu |
| 36:0 | ACRONYM | JUDGEMENT | `SLO` | `service-level objective (SLO)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 42:0 | ACRONYM | JUDGEMENT | `TP` | `tensor parallelism (TP)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 44:0 | ACRONYM | JUDGEMENT | `SLI` | `service-level indicator (SLI)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 66:8 | TERM | MECHANICAL | `**KV-cache size` | `**KV cache size` | kvcache |
| 85:7 | TERM | MECHANICAL | `\| KV-cache size` | `\| KV cache size` | kvcache |
| 119:0 | ACRONYM | JUDGEMENT | `NIC` | `network interface card (NIC)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 128:58 | SPELLING | MECHANICAL | `link normalisation done;` | `link normalization done;` | ize |
| 138:0 | ACRONYM | JUDGEMENT | `HBM` | `high-bandwidth memory (HBM)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 159:0 | ACRONYM | JUDGEMENT | `MTU` | `maximum transmission unit (MTU)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 160:0 | ACRONYM | JUDGEMENT | `NCCL` | `NVIDIA Collective Communications Library (NCCL)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 160:0 | ACRONYM | JUDGEMENT | `ACS` | `access control services (ACS)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 173:0 | ACRONYM | JUDGEMENT | `DCQCN` | `Data Center Quantized Congestion Notification (DCQCN)` | first occurrence on the line; acronym never expanded in this file — expand at first body use (or add to the Acronyms paragraph) |
| 178:146 | SPELLING | MECHANICAL | `token, utilisation,` | `token, utilization,` | ize |
| 207:29 | XREF-STYLE | MECHANICAL | `(§15.10–15.12).**` | `(Section 15.10–15.12).**` | section-sign |
| 230:59 | SPELLING | MECHANICAL | `with utilisations;` | `with utilizations;` | ize |
| 239:46 | SPELLING | MECHANICAL | `the utilisation of` | `the utilization of` | ize |
| 268:3 | TERM | MECHANICAL | `KV-cache-centric` | `KV cache-centric` | kvcache |

### `capstones/capstone-h-disaggregated-llm-serving/starter-kit/README.md`

3 finding(s): 3 MECHANICAL, 0 JUDGEMENT.

| Line:Col | Cat | Type | Current | Replacement | Rule / note |
|---|---|---|---|---|---|
| 54:60 | SPELLING | MECHANICAL | `rate, utilisation cap,` | `rate, utilization cap,` | ize |
| 63:110 | SPELLING | MECHANICAL | `bandwidth; utilisation of` | `bandwidth; utilization of` | ize |
| 110:72 | SPELLING | MECHANICAL | `CPU utilisation for` | `CPU utilization for` | ize |

## (e) Lint rules (`scripts/copyedit_lint.py --list-rules`)

The *Rule / note* column in §(d) refers to these ids.

```text
TERM       roce                 RoCEv2 (IBTA Annex A17 spelling, STYLE_GUIDE §6)
TERM       infiniband           InfiniBand (IBTA trademark spelling)
TERM       allreduce            all-reduce in prose (STYLE_GUIDE §6); API names stay in backticks
TERM       allgather            all-gather in prose
TERM       reducescatter        reduce-scatter in prose
TERM       alltoall             all-to-all in prose
TERM       gpudirect            GPUDirect (NVIDIA spelling)
TERM       nvlink               NVLink (NVIDIA spelling)
TERM       nvswitch             NVSwitch (NVIDIA spelling)
TERM       nvidia               NVIDIA (company spelling)
TERM       tensorcore           Tensor Core(s) (NVIDIA spelling), also as a modifier: 'Tensor Core GEMM'
TERM       connectx             ConnectX (NVIDIA spelling)
TERM       bluefield            BlueField (NVIDIA spelling)
TERM       pytorch              PyTorch (project spelling)
TERM       deepspeed            DeepSpeed (project spelling)
TERM       vllm                 vLLM (project spelling)
TERM       pcie                 PCIe (PCI-SIG spelling)
TERM       slurm                Slurm (SchedMD spelling)
TERM       k8s                  Kubernetes in prose
TERM       datacentre           data center (noun) / data-center (modifier); majority and Ch 2 title
TERM       datacenter           data center (two words) in prose
TERM       railopt              rail-optimized (REFERENCE_CLUSTER)
TERM       kvcache              KV cache, also as a modifier (STYLE_GUIDE §6)
TERM       checkpoint           checkpoint (one word)
TERM       multitenant          multi-tenant / multi-tenancy (Ch 19 title)
TERM       tokps                tokens/s
TERM       percentile           lowercase percentiles p50/p95/p99 (STYLE_GUIDE §5)
TERM       parallel-eq          spaced 'TP = 8' (REFERENCE_CLUSTER)
TERM       precision            uppercase BF16/FP8/FP16/FP32/TF32 in prose
XREF-STYLE section-sign         book sections are 'Section N.M' (STYLE_GUIDE §10); '§N' for other documents' sections is allowed
XREF-STYLE ch-abbrev            'Chapter N' in prose (STYLE_GUIDE §10); 'Ch N' is allowed in table cells
ACRONYM    exp-mfu              MFU = model FLOPs utilization (PaLM paper term; majority)
ACRONYM    exp-pfc              PFC = priority flow control (lower case like other generic expansions); 'Priority-based Flow Control' only when naming IEEE 802.1Qbb
ACRONYM    exp-pxn              PXN = PCI × NVLink (NCCL's own expansion)
ACRONYM    exp-rma              RMA = return merchandise authorization
ACRONYM    exp-ber              BER = bit error ratio (IEEE 802.3 term)
STYLE      vs-period            'vs' without a period (majority form)
UNIT       approx-tilde         approximation sign '≈ ' with a space, not '~'
UNIT       ratio-spaced         ratios as 'N:1' without spaces (majority form)
SPELLING   ize                  -ize/-ization (house style; majority of chapters)
SPELLING   analyse              analyze (house -yze; lab tools are 'analyzer')
SPELLING   behavior             behaviour (only form in use)
SPELLING   labeled              labelled / labelling (majority)
SPELLING   modelled             modeled / modeling (majority; matches [MODELED])
SPELLING   centre               center (majority)
SPELLING   fibre                fiber (majority)
SPELLING   catalog              catalogue (majority)
SPELLING   artefact             artifact (majority)
SPELLING   queuing              queueing (majority)
SPELLING   judgement            judgment (majority)
SPELLING   towards              toward (majority)
SPELLING   signaled             signalled / signalling (only form in use)
SPELLING   canceled             cancelled / cancelling (only form in use)
SPELLING   favor                favour (only form in use)
SPELLING   rerun                rerun / reimage / retest (closed compounds)
SPELLING   microbatch           micro-batch (majority)
SPELLING   compounds            closed/hyphenated compound as used by the majority
UNIT       gbps                 bit rates as Gb/s, Mb/s, Tb/s (STYLE_GUIDE §5)
UNIT       GBps                 byte rates as GB/s, MB/s
UNIT       gbit                 bit rates as Gb/s
UNIT       per-sec              '/s', not '/sec'
UNIT       usec                 microseconds as 'µs' (U+00B5)
UNIT       mu-greek             micro sign U+00B5, not Greek mu U+03BC
UNIT       kw                   kW
UNIT       unit-space           space between number and unit (STYLE_GUIDE §5)
UNIT       degC                 'N °C' with a space and the degree sign
UNIT       times-x              multiplication sign '×' (spaced between operands, unspaced for a factor: '9×')
UNIT       pct-space            '40 %' with a space (house form, REFERENCE_CLUSTER)
UNIT       thousands-space      thousands separator is a comma
UNIT       thousands-missing    numbers ≥ 10,000 that carry a unit take comma separators
LABEL      label-backticks      evidence labels are written in backticks (house form, 96 % of labels)
LABEL      label-malformed      malformed evidence label; use one of STYLE_GUIDE §3 exactly
LABEL      label-vendor-date    [VENDOR-SPEC] needs ', YYYY-MM' (month checked) immediately after the tag; the literal template '[VENDOR-SPEC, YYYY-MM]' is allowed when the label itself is being described (STYLE_GUIDE §3)
LABEL      label-observed-date  [OBSERVED] needs ', YYYY-MM-DD' (STYLE_GUIDE §3)
LINK       broken-link          relative link target does not exist
LINK       broken-anchor        #anchor not found in target .md
XREF       missing-target       Section/Table/Figure/Chapter/Capstone reference does not resolve
```

Commands: `python scripts/copyedit_lint.py [filters…]` (text), `--summary`, `--only CAT,rule`, `--format json`, `--all` (every `.md` except `review/`). Exit status 1 while findings remain. Suppress a deliberate exception with `<!-- copyedit-lint: ignore -->` on the line (or `ignore-next-line` on the line above) and record why in the chapter's review notes.
