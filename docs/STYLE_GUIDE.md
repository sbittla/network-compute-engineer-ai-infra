# Editorial and Technical Style Guide

Every chapter, lab, exercise, and capstone in this book follows these rules. Reviewers score against
them (see [EDITORIAL_RUBRIC.md](EDITORIAL_RUBRIC.md)). When this guide conflicts with personal
preference, this guide wins.

## 1. Voice and audience

- Write for a working engineer: a network engineer, Linux/HPC engineer, ML platform engineer, SRE, or
  performance engineer moving into AI infrastructure. Assume Linux, Python, and IP networking literacy.
  Do **not** assume CUDA, RDMA, or ML depth — introduce them progressively.
- Voice: direct, precise, second person for instructions ("Run…", "You will see…"), first person plural
  for reasoning ("We can now bound the step time…"). No marketing language, no hype, no filler.
- Every abstraction gets grounded in a mechanism: what moves, where, how many bytes, how long, and what
  evidence shows it.
- Prefer short paragraphs (3–6 sentences). Use tables for comparisons, numbered lists for procedures.

## 2. The book's central method (use it explicitly)

> **Observe a symptom → collect evidence → trace the bottleneck across compute, network, storage, and
> orchestration → identify root cause → make a safe change → validate with repeatable measurements.**

Every chapter must apply this loop at least once (usually in the worked example and troubleshooting
scenario). Refer to it as *the diagnostic loop*.

## 3. Evidence labels (mandatory)

Any number that describes performance, capacity, power, latency, or cost must be attributable. Use these
inline labels the first time a figure appears in a section, and in every table caption:

| Label | Meaning |
|---|---|
| `[MEASURED]` | Produced by running a stated procedure on stated hardware/software. Must cite the environment manifest. |
| `[MODELED]` | Computed from a stated formula and stated assumptions. Show the formula. |
| `[SIMULATED]` | Output of a software simulation/emulation. State what the simulator does *not* capture. |
| `[ILLUSTRATIVE]` | A plausible example value chosen for teaching. Not a claim about any product. |
| `[VENDOR-SPEC, YYYY-MM]` | Taken from vendor documentation; include the platform and the month checked. Readers must re-verify. |

Planning assumptions (growth rates, MTBF, prices, utilization targets) use `[ILLUSTRATIVE]` and
should also appear in the chapter's or project's assumptions register.

Never present simulated or modeled output as a physical measurement. The book's labs run mostly at
Level 1 (laptop) — say so plainly.

## 4. Vendor neutrality and version sensitivity

- Teach **protocol fundamentals and portable principles first**, then vendor implementation in a clearly
  marked box: `> **Vendor implementation note (NVIDIA / Broadcom / Arista / AMD / Cisco …):**`.
- Version-sensitive facts (driver/firmware matrices, CLI flags, API names, NCCL env vars, Kubernetes
  feature gates) must be marked `[VENDOR-SPEC, 2026-10]` or carry a "verify against current docs" note.
- Never invent CLI flags, environment variables, config keys, metric names, or API calls. If you are not
  certain a flag exists, describe the capability generically instead.
- The reference platform in [REFERENCE_CLUSTER.md](REFERENCE_CLUSTER.md) is illustrative and
  H100-class. Use it as the running example; do not drift to other numbers without saying why.

## 5. Units, numbers, and notation

- Bits for links (`Gb/s`), bytes for memory and storage (`GB/s`, `GiB`). Always state which.
  400 Gb/s = 50 GB/s raw line rate; say whether a figure is line rate, payload, or achieved.
- Use SI (GB = 10^9) for bandwidth and storage throughput; use IEC (GiB = 2^30) for memory capacity when
  precision matters. Be explicit when converting.
- Time: `ns`, `µs`, `ms`, `s`. Percentiles: `p50`, `p99`, `p99.9`.
- Show the arithmetic for every worked calculation: formula → substituted values → result with units.
- Round only at the final step; keep 2–3 significant figures in prose.
- Bidirectional vs. unidirectional bandwidth must always be stated (e.g., NVLink "900 GB/s total,
  450 GB/s per direction").

## 6. Terminology (canonical forms)

Use these spellings consistently: GPU, CPU, NIC, HCA, DPU, PCIe, NVLink, NVSwitch, NUMA, RDMA, RoCEv2,
InfiniBand (IB), GPUDirect RDMA, NCCL, PyTorch Distributed, all-reduce, all-gather, reduce-scatter,
all-to-all, leaf-spine, ECMP, BGP, eBGP, ECN, PFC, DCQCN, MTU, SLO, SLI, SLA, RPO, RTO, TTFT, TPOT
(time per output token; also "inter-token latency", ITL), KV cache, prefill, decode, Kubernetes, Slurm,
BMC, Redfish, IPMI, Xid, ECC, AER, BDF (bus:device.function), CDU, PDU, UPS, MEP, TDP.

Define every acronym on first use in each chapter (readers jump between chapters).

## 7. Diagrams

- Use Mermaid (` ```mermaid `) for flows, state machines, sequence diagrams, and topologies; use ASCII
  art inside fenced `text` blocks for byte layouts, rack elevations, and PCIe trees where Mermaid is
  awkward. Every diagram has a caption line: `*Figure N.M — description.*`
- Required data-path diagrams across the book (each owning chapter must include its own):
  GPU↔GPU (Ch 5, 13), GPU↔NIC (Ch 5, 13), NIC↔switch (Ch 8, 10), host↔storage (Ch 14),
  end-to-end training step (Ch 11, 13), end-to-end inference request (Ch 15).

## 8. Callouts

Use GitHub-flavoured blockquote callouts, sparingly:

- `> **Key idea:**` — the one sentence a reader should remember.
- `> **Pitfall:**` — a real failure mode practitioners hit.
- `> **Production note:**` — what changes at scale or in operations.
- `> **Realism boundary:**` — what a laptop/simulation cannot show.
- `> **Safety:**` — anything that could disrupt shared or production systems.

## 9. Safety boundaries

No instruction in this book may direct a reader to make production changes, run disruptive fault
injection, or modify shared fabrics. All fault-injection and change exercises target a dedicated lab,
a simulation, or a tabletop, and say so.

## 10. Cross-references

- Refer to chapters as "Chapter 7" and sections as "Section 7.3". Link with relative paths.
- Each chapter's "Connections" section names where its concepts are prerequisites and where they are
  applied (especially the capstones).

## 11. Citations and further reading

- Prefer primary sources: RFCs, IEEE standards, IBTA specifications, vendor documentation, original
  papers (e.g., Megatron-LM, ZeRO, DCQCN, Roofline, vLLM/PagedAttention, DistServe/Splitwise, Speculative
  Decoding), and well-known engineering books.
- Give title, author/organization, and year. Do not fabricate URLs; give a URL only if you are confident
  it is stable (e.g., `https://www.rfc-editor.org/rfc/rfc7938`). Otherwise cite by title.
- Each further-reading item gets one sentence on *why* to read it.

## 12. Code

- Python 3.10+, standard library plus `numpy`, `pandas`, `matplotlib`, `pyyaml` only (see
  `requirements.txt`). Shell examples target Bash on Linux.
- Code must run. Labs ship a `check.py` that is executed by `scripts/validate_labs.py`.
- Deterministic: seed every random generator; synthetic datasets are produced by a committed generator.
- Code style: type hints on public functions, docstrings that state units, no global mutable state,
  `if __name__ == "__main__":` entry points, `argparse` for CLIs.
- Commands that require hardware or root are shown in the manuscript, never run silently by lab code,
  and are labelled with their tier.
