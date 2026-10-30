# Editorial Review — Chapter 3: Linux, Host Systems, and Performance Diagnostics

**Independent review score history:** 9.25 → 9.35 → 9.50 (iterations 1–3; iteration 3 PASS, 2026-10-30).

| Iteration | Date | Reviewer | Weighted score | Gate |
|---|---|---|---|---|
| 1 | 2026-10-29 | Author self-review, iteration 1 | 9.13 | FAIL (D4, D9 < 9.0; open majors) |
| 2 | 2026-10-29 | Author self-review, iteration 2 | 9.50 | PASS (internal); independent review pending |

## Scores by dimension (latest: iteration 2)

| # | Dimension | Weight | It. 1 | It. 2 | Justification (iteration 2) |
|---|---|---|---|---|---|
| D1 | Technical accuracy and currency | 20 % | 9.0 | 9.5 | PCIe arithmetic (128b/130b, 8b/10b), DDR5 bandwidth, Little's law, packet rates and all-reduce volumes were re-derived independently (see below). Tool flags were checked against known usage: `lspci -vv/-s`, `numastat -p/-m`, `taskset -cp`, `mpstat -P ALL`, `pidstat -t`, `iostat -x`, `journalctl -k -b -1`, `turbostat --show/--interval`, `scontrol update ... state=drain`, `nvidia-smi --query-gpu` fields, `all_reduce_perf -b/-e/-f/-g`. Version-sensitive items (Xid catalogue, `ROW_REMAPPER` display, pciutils `(ok)/(downgraded)` annotations) are flagged. Residual risk: exact output formats vary by distribution. |
| D2 | Depth and production realism | 15 % | 9.5 | 9.5 | Covers the false-alarm traps practitioners actually hit: since-boot rows, `%iowait` dilution, NVMe/md `%util`, idle PCIe downshift, `intel_pstate` vs `acpi-cpufreq` `powersave`, `dmesg_restrict`/`CAP_SYSLOG`, and AER counting. It explains why NUMA-remote memory does not lower CPU utilization, includes the seven-mechanism "CPU low" table, and prices faults in GPU-hours. |
| D3 | Pedagogy and clarity | 15 % | 9.0 | 9.5 | Progression runs topology → scheduler → memory → storage → PCIe → interrupts → logs → method → tool. Three captioned figures and one listing. The worked example has six explicit steps, and the scenario follows the loop step by step. Objectives map to sections. |
| D4 | Hands-on lab quality | 15 % | 8.5 | 9.5 | A real, read-only collector that has been executed on Linux (container, root and non-root) and on Windows, plus an analyzer over six snapshots with planted faults and two false-alarm traps. Hashed recall/precision checks do not leak answers, and the 20 checks give granular TODO feedback. Data is deterministic, byte-identical and 796 KB. L2/L3 extensions use real commands and a record list. |
| D5 | Exercises and assessment | 10 % | 9.5 | 9.5 | 17 exercises: 7 knowledge, 2 worked, 1 case, 1 lab, 1 inventory, 1 design, 4 reflection. All three outline exercises and the deliverable are present. Each exercise carries ★, tier and evidence. The key has arithmetic, marks and common mistakes. |
| D6 | Measurement rigor and evidence labelling | 10 % | 9.5 | 9.5 | Every number is labelled. Modeled costs are presented as upper bounds with their assumptions listed (Exercise 3.16). Validation specifies warm-up, repetitions, median/p95 and spread. Lab data is labelled SIMULATED, and the collector-execution evidence sits separately in the manifest. |
| D7 | Cross-layer integration | 5 % | 9.5 | 9.5 | ORION `HX8` topology, W-TRAIN parallelism and checkpoint size, and rail-optimized design are used throughout. Cross-references go to Chapters 1, 2, 5, 6, 7, 8, 13, 14, 16, 17, 18, 19, 20 and 21 and to the capstones. |
| D8 | Operational realism and safety | 5 % | 9.5 | 9.5 | Runbook RB-HOST-03 with thresholds and escalation. Safety callouts cover `setpci`, live changes and privilege. The collector refuses mutating argv and fallbacks. Every change goes through drain and the change process. |
| D9 | Editorial polish | 5 % | 8.5 | 9.5 | Acronyms are now defined at first use (NUMA, PCIe, NIC, HBM, MFU, SMT, NPS1, DIMM, POST, UPI, CFS/EEVDF, HPC, RMA, OOM, IPC, DMA, H2D, TLB, ECC, MSI-X, NAPI, GRO, MTU, IRQ, NCCL, SRE, AER, EDAC, BMC, NVMe). American spelling is consistent. Manuscript is 9,955 words. |

Weighted (iteration 2) = 0.20·9.5 + 0.15·9.5 + 0.15·9.5 + 0.15·9.5 + 0.10·9.5 + 0.10·9.5 + 0.05·9.5 + 0.05·9.5 + 0.05·9.5 = **9.50**.
Iteration 1 = 0.20·9.0 + 0.15·9.5 + 0.15·9.0 + 0.15·8.5 + 0.10·9.5 + 0.10·9.5 + 0.05·9.5 + 0.05·9.5 + 0.05·8.5 = **9.125 → 9.13**.

## Findings

| ID | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| F1 | Blocker | `lab/tools/generate_snapshots.py` (iostat) | When r/s ≥ 100, the 9-character columns ran together (`830.00106240.00`), so real-format parsing failed. | Every column now gets a separating space; data regenerated; parser checks pass. **Fixed (it. 1).** |
| F2 | Major | Lab data, `orion-hx8-12` | The story contradicted itself: GPU utilization was 97 % on an input-starved node; md0 throughput (≈ 10 MB/s) did not match vmstat `bi` (≈ 420 MB/s); vmstat `free` did not match `free -m`. | GPUs now at 55–60 %; members at 830 r/s × 128 KiB and md0 at 830 r/s × 512 KiB (435 MB/s ≈ `bi`); vmstat `free` derived from the `free -m` arithmetic. The 435 / 725 MB/s ratio now explains the 40 % shortfall. **Fixed.** |
| F3 | Major | Manuscript (all) | Many acronyms were used before they were defined (style guide §6). | Expanded at first use; trimmed elsewhere to stay ≤ 10,000 words. **Fixed.** |
| F4 | Major | `lab/check.py` | The collector `collect` checks called the learner's `build_command_plan`, so a correct `collect` showed TODO; `write_report` depended on `analyze_fleet`. | Checks now use hand-built plans and synthetic findings; each check tests one function. **Fixed.** |
| F5 | Major | `lab/check.py` | Dataclass modules loaded through importlib were not registered in `sys.modules`, so import failed. | Registered before `exec_module`. **Fixed.** |
| F6 | Minor | §3.5 iostat excerpt | The RAID 0 latency-inheritance claim did not fit `rareq-sz` 128 on md0. | md0 now shows 512 KiB requests split across four 128 KiB member reads, with latency set by the slowest member. **Fixed.** |
| F7 | Minor | §3.13 | The `awk` filter used the wrong field indexes for `mpstat` output. | Corrected to `$1=="Average:" && ($2=="CPU" \|\| $2=="all" \|\| $3 > 90)`. **Fixed.** |
| F8 | Minor | §3.8 | Said Xid 64 "records" a row remap; it actually reports that recording failed. | Corrected. **Fixed.** |
| F9 | Minor | §3.1 | "modelled" (British) spelling; the 8 PFLOP/s figure had no label. | Fixed; `[VENDOR-SPEC, 2026-10]` added. |
| F10 | Minor | Collector Markdown | An empty `note=` was rendered in the context line. | Empty values are now suppressed. **Fixed.** |
| F11 | Minor | Lab data | The scenario needed a believable reason for heavy local I/O: W-TRAIN text batches are only ≈ 17 MB per step cluster-wide. | hx8-12 is now explicitly a W-MM image–text variant reading shards from local NVMe; the variation is stated in Exercise 3.8. **Fixed.** |

No blocker or major findings remain open.

## Independent arithmetic verification (iteration 2)

These values were recomputed with Python, not by hand:

```text
Gen5 x16 63.015 GB/s | Gen4 x16 31.508 | Gen3 x8 7.877 | Gen4 x4 7.877 | Gen4 x2 3.938 | Gen1 x16 4.000
W-TRAIN per-GPU grads S = 4.375 GB; ring all-reduce 2·7/8·S = 7.656 GB
healthy 7.656/45 = 0.170 s; Gen3x8 @6.5 GB/s = 1.178 s; Δ = 1.008 s; 1.01/18.41·6144 = 337 GPU-h/day
Gen4x16 NIC (25.8 GB/s): 0.296 s; Δ = 0.126 s; 0.0072·6144 = 44.2 GPU-h/day
nvme3 aqu-sz 830·0.0486 = 40.34; md0 830·0.0491 = 40.75; md0 830·512 KiB = 435.2 MB/s
iowait dilution 15.25/224 = 6.81 %; pps 2.766 M (9000) vs 16.25 M (1500), ratio 5.88
NUMA remote 210855.6/213171.2 = 98.91 %; ckpt shard 3.828 GB: 0.077 s vs 0.59 s
straggler 2.6/20.0 = 0.13 → 798.7 GPU-h/day; DDR5-4800 × 8 ch = 307.2 GB/s
```

## Lab verification (iteration 2)

- `python lab/check.py --impl solution` → 20/20 PASS, exit 0 (≈ 0.3 s).
- `python lab/check.py` (starter) → 0/20 PASS, 20 TODO, exit 1, no traceback.
- `python lab/tools/generate_snapshots.py --check` → byte-identical.
- `python scripts/validate_labs.py ch03` → OK.
- The reference collector was run on Windows (all sections `skipped`) and inside a `python:3.12-slim`
  Linux container on a WSL2 kernel, as root and non-root. There it correctly reported missing tools,
  denied `dmesg` (no `CAP_SYSLOG`) with the journalctl fallback attempted, and read sysfs/procfs. The
  analyzer processed that real snapshot without error.

## Release-gate items outstanding

1. **Hardware validation (L2/L3):** run the collector and analyzer on a physical H100-class
   multi-GPU host, idle and under load, as root and non-root. Confirm the parsers against real
   pciutils, sysstat and procps versions on the target OS images.
2. **Vendor verification at publication:** NVIDIA Xid catalogue entries (48, 63, 64, 79), the
   `nvidia-smi -q -d ROW_REMAPPER` display type, `--query-gpu` field names, the idle PCIe link-speed
   behaviour of the target GPU and driver, and mlx5 counter and driver strings.
3. **External expert review:** a practising GPU-cluster/Linux performance engineer should review
   §3.3–3.7 and the runbook thresholds.
4. Confirm that cross-chapter links resolve once Chapters 5–21 are published.

---

## Independent review iteration 1 + author fixes (2026-10-29)

Independent reviewer score: **9.25** (gate FAIL). The labs were valid and the data deterministic.
Before fixing, I re-read the shared docs that had changed: `docs/VERIFIED_FACTS.md` (new),
`docs/REFERENCE_CLUSTER.md` (canonical names, reliability, RTT, 1.5:1 frontend, 25.6 Tb/s) and
`docs/LAB_STANDARDS.md` (generators are instructor-only).

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| Names | Major | Hosts were `orion-hx8-NN`, not the canonical `orion-nNN`. | Renamed in the generator, data (`orion-n01…n28.json`), check.py, manuscript, exercises, key and both READMEs. Data regenerated, byte-identical. Expected-finding hashes recomputed (still 14 keys). |
| LAB_STANDARDS | Major | The lab README told learners to run and read the generator. | Regeneration and spoiler text removed from `lab/README.md`. The generator is marked instructor-only in the chapter card, manifest and key. check.py has no regeneration check; `validate_labs.py` reports `no-generator=pass`. |
| R-01 | Major | §3.13 baseline of 17.6 s was inconsistent with the 2.6 s / 13 % / 799 figures. | Uses the canonical 17.4 s baseline throughout (17.4 → 20.0 s = 2.6 s, 13 %, ≈ 799 GPU-h/day). The post-fix validation reads median 17.4 s, p95 17.7 s `[ILLUSTRATIVE]`. |
| R-02 | Major | §3.5 iostat excerpt was impossible (aqu-sz 0.92 at 99.9 % util; 19 r/s). "≈300×" disagreed with the key's "≈230×". | Excerpt now uses the snapshot's consistent values (830 r/s; aqu-sz 40.34 / 40.75; md0 424,960 kB/s). Little's law shows 830 × 0.0486 = 40.3. "≈230×" (48.6 / 0.21). |
| R-03 | Major (safety) | `is_read_only` was a deny-list: it let `nvidia-smi --power-limit=300`, `-mig 1`, `-lmc 1593` and `ethtool --set-priv-flags` through, and refused `ip -s link`. | Replaced with `ALLOWED_FORMS`, a per-tool list of exact read-only forms with typed placeholders. `--opt=value` is split before matching; default deny; primary and fallback both checked; `run_command` uses the same guard. check.py now requires 15 unsafe forms refused (including all four cited) and 5 read-only forms allowed (including `ip -s link show`). The starter carries the same `ALLOWED_FORMS` design with `argv_is_read_only` as the TODO, and its `run_command` cannot execute anything until the guard is implemented. Re-tested on real Linux in a container. |
| R-04 | Major | Drain does not move a running job. | §3.11, §3.13, RB-HOST-03 step 7 and the 3.8 key now say: drain (stops new placement), then requeue (`scontrol requeue <jobid>`) or elastically restart after the next checkpoint. The ≈ 15-min restart is priced at 64 GPU-h; payback ≈ 4.5 h (§3.11) and ≈ 2 h (§3.13). |
| R-05 | Minor | Wrongly blamed an `acpi-cpufreq` "default". | Root cause is now the stale image's tuning profile, which set `powersave`; `intel_pstate=disable` forced `acpi-cpufreq`. |
| R-06 | Minor | md %util is 0 only on older kernels or when accounting is off. | Prose corrected. Synthetic md0 now reports %util (100 on orion-n12, ≈ 5 healthy); the key and analyzer expectations were updated (orion-n12 now 1 critical / 6 warning). |
| R-07 | Minor | sysfs AER counters were missing. | Prose added in §3.6. The collector reads `aer_dev_correctable/nonfatal/fatal` totals. The analyzer uses them when the kernel log is not ok. New check "AER from sysfs when the kernel log is denied" (21 checks total); rubric C rebalanced. |
| R-08 | Minor | `critical_xids` was incomplete. | Now `[48, 74, 79, 94, 95, 119, 120, 140, 154]` `[VENDOR-SPEC, 2026-10]` in the baseline, lab README and §3.8. Prose adds the 94 vs 95 distinction from VERIFIED_FACTS. |
| R-09 | Minor | Rounded 6.5 GB/s gave 337; the 82 % efficiency was unjustified. | Full precision: 6.459 GB/s → 1.185 s → Δ 1.015 s → ≈ 339 GPU-h/day. 82 % is justified as inside ORION's 79–87 % band (50–55 of 63.0 GB/s; x8 200–220 of 252 Gb/s per VERIFIED_FACTS). |
| R-10 | Minor | The orion-n12 report had two rubrics (20 vs 10). | The key now uses the lab's 10 points (3 / 2 / 2 / 1.5 / 1.5). |
| R-11 | Minor | The runbook had no 25–50 % NUMA band. | Step 6 now reads: 25–50 % → warning ticket; > 50 % → critical. |
| R-12 | Minor | `journalctl -k -b -1` needs persistent journald. | Stated (`Storage=persistent` or an existing `/var/log/journal`). |
| R-13 | Minor | Every host had the same PID. | PIDs vary per host (41377, 52904, 48211, 39952, 57118; none for n28). |
| VERIFIED_FACTS | Minor | RoCE MTU interaction. | §3.7 and the n19 key row note that a 1500 B netdev MTU caps the RDMA active MTU at 1024 B. |
| Cuts | — | Requested trims. | §3.12 reduced to a pointer; huge-pages subsection and the Lameter/Drepper reading removed. Manuscript was 10,127 words after this iteration; 10,364 after iteration 2 (≤ 10,500). |

**Verification:** `check.py --impl solution` 21/21 (exit 0); starter 0/21, 21 TODO (exit 1, no
traceback); solution with `lab/tools/` removed: 21/21; `generate_snapshots.py --check` byte-identical;
`python scripts/validate_labs.py ch01 ch02 ch03` → 3/3 valid. The collector was re-run in a Linux
container: sysfs AER fields recorded, read-only plan accepted, missing tools reported.

**Author re-score (not a substitute for independent review):** D1 9.5, D2 9.5, D3 9.5, D4 9.5, D5 9.5,
D6 9.5, D7 9.5, D8 9.5, D9 9.5 → weighted 9.50. Open blocker/major findings: none.

---

## Independent review iteration 2 + author fixes (2026-10-30)

Independent re-review score: **9.35** (one new major). The safety guard was verified independently:
72 unsafe argv forms were run against it with zero bypasses. Before fixing I re-read the new
"Distributed training operations" section of `docs/VERIFIED_FACTS.md`: no spare nodes, drain does
not move a job, and the DP overlap window.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| R2-01 | Major | §3.11, §3.13, runbook step 7 and the key assumed a spare node. ORION-256 has none. | All four now price the options: degraded loss × time-to-repair, DP = 7 (−12.5 % = 32 GPU-h/h, two 64 GPU-h restarts, and 1,024 is not divisible by 7 so the batch must change), and a planned stop (64 GPU-h + 256 × T_repair). §3.11 now says *do not shrink* (14.1 < 32 GPU-h/h); plan a stop when the repair takes under ≈ 2.4 h (64 + 256T < 48 h × 14.1 ≈ 677 GPU-h). §3.13: shrinking is about a tie (33.3 vs 32 GPU-h/h), so stop now for the ≈ 1.5 h re-provision (448 GPU-h, against ≈ 1,600 GPU-h for waiting). Key 3.8 is priced at a ≈ 40 % loss (≈ 102 GPU-h/h); key 3.9(c) says keep running (1.8 GPU-h/h). Exercise 3.9(c) was reworded to match. |
| R2-02 | Minor | Runbook step 2 Xid handling. | Now: "Xid 48/79/95 → drain now; Xid 94 → drain when convenient"; a width fault is priced in step 7. |
| R2-03 | Minor | §3.13 per-rank table did not sum to the step time. | Added "Optimizer and other phases 2.1 s" and "Step" columns: 15.1 + 2.8 + 2.1 = 20.0; 17.7 + 0.2 + 2.1 = 20.0; pre-incident 15.1 + 0.2 + 2.1 = 17.4. |
| R2-04 | Minor | Mixed 7.66 and 7.656 GB. | 7.656 GB used throughout §3.11 and key 3.9. Also added the ≈ 70 ms PP overlap window from VERIFIED_FACTS, showing that the "≤" bound is nearly tight. |
| R2-05 | Minor | check.py's unsafe list was fully visible. | Added 12 held-out cases, base64-encoded so they are not a checklist to code against: `nvidia-smi -pm 1`, `ethtool -K rail0 tso off`, `dmesg --clear`, `ip route del default`, `journalctl --vacuum-size=1M`, `lspci -vv -w`, `nvidia-smi … -f /etc/passwd`, plus allowed forms with an extra token. All are refused by the reference guard. |
| R2-06 | Minor | `run_command` inherited the caller's PATH, and the README suggests sudo. | Tools are resolved with `shutil.which(tool, path=SAFE_PATH)`, where `SAFE_PATH = /usr/sbin:/usr/bin:/sbin:/bin`. The child gets env `{PATH: SAFE_PATH, LC_ALL: C, LANG: C}` and is run by absolute path. A tool that is not found is reported `missing`. The starter carries the same code. |

**Verification:** solution 21/21 (exit 0); starter 0/21, 21 TODO (exit 1); `validate_labs.py` OK
(solution, starter, no-generator, docs). Manuscript 10,364 words.

**Author re-score:** 9.50; no dimension below 9.5; no open blocker or major findings.

---

## Independent review iteration 3 (2026-10-30)

Independent score 9.50 (PASS). The minor findings N3-* raised at this pass are closed: the wording fixes listed in the coordinator's iteration-3 notes are applied, and `python scripts/validate_labs.py` is OK.
