# Concise Edition: Specification and Rubric

The concise edition is a reading edition of the 24 chapters, published as PDF and Word. It is built from
`concise/chNN.md` by `python scripts/build_concise.py`. The full chapter (`book/**/manuscript.md`) is the
**only** source for each condensed chapter. [REFERENCE_CLUSTER.md](REFERENCE_CLUSTER.md),
[VERIFIED_FACTS.md](VERIFIED_FACTS.md) and [STYLE_GUIDE.md](STYLE_GUIDE.md) still apply in full.

## 1. Length and scope

- **Target 3,500 words per chapter. Hard range: 3,000 to 4,000 words.** This counts the words a reader
  reads in prose, tables and code. Markdown table syntax (pipes, separator rows) and code-fence lines are
  not counted. `build_concise.py --check` enforces it. Do not use `wc -w`, because it counts table pipes.
- Condense; never invent. Every fact, number, command, flag and claim must already be in the full
  chapter, with the same evidence label. Do not add new vendor claims. If you shorten a number's context,
  keep its label and its qualifiers (line rate or payload, per direction or bidirectional, which platform).
- Keep the mechanisms a practitioner needs. Cut secondary examples, long derivations (give the result and
  the formula), repeated caveats, and most command listings.

## 2. Chapter structure

```
# Chapter N — <title as in the full edition>

<opening paragraph, 80–150 words: the problem and why it matters>

**What you will learn**
- 4–6 bullets, each an outcome (verb first)

## N.1 … ## N.k   core sections (usually 5–8), numbered like the full chapter but renumbered consecutively

## Trade-offs                      the full chapter's trade-offs / design-decisions table, condensed (rows may be merged, never dropped wholesale)
## Worked example: <title>        condensed, every step and number still shown
## Troubleshooting: <title>        one scenario through the diagnostic loop (symptom → evidence → root cause → safe change → validation)
## Operating notes                 runbook excerpt: signals, thresholds, safe-change rules, safety boundaries
## Key takeaways                   5–8 bullets
> **Hands-on.** One box: the repo lab path (`book/<part>/<chapter>/lab/`), what it makes you do in one or
> two sentences, the exercise set (`exercises.md`), and the L2/L3 extension (`lab/l2/`) where one exists.
> Answer keys are instructor-only: never cite `solutions/`.
```

- **Diagrams:** at most two per chapter, as fenced `mermaid` blocks copied or simplified from the full
  chapter, each followed by a caption line `*Figure N.x — …*`. Diagrams must stay simple enough to read
  at page width.
- **Tables:** keep the decision tables and key-number tables; caption each one `*Table N.x — …*`, ending
  with its evidence label (`[LABEL]`) whenever the table contains quantitative claims, as in the full chapter.
  A purely qualitative table (definitions, a validation ladder) needs no label.
- **Code:** at most four short blocks per chapter (≤ 12 lines each), keeping their level tag (L1/L2/L3)
  and the `[ILLUSTRATIVE]` marking of sample output.
- **Cross-references:** refer to other chapters by number and exact title, using the list below. No
  relative Markdown links, because the PDF has no repository.
- **Callouts:** a `>` block needs a blank line before it; otherwise pandoc merges it into the previous
  paragraph and prints a literal ">". The check enforces this.
- **Acronyms:** expand every acronym on first use *in this chapter*, even if an earlier chapter already
  did, because readers dip into single chapters. Universal ones (CPU, GPU, RAM, OS, API, CLI, URL) are
  exempt.
- **Derivations:** if a number in the worked example or troubleshooting case is derived, show the
  arithmetic that produces it, or state it as given. A reader must be able to reproduce every number
  from what the chapter states.

**Chapter titles (canonical):** 1 The AI Infrastructure Landscape · 2 Anatomy of an AI Data Center ·
3 Linux, Host Systems, and Performance Diagnostics · 4 GPU Architecture and CUDA Execution ·
5 GPU Interconnects and Host Topology · 6 GPU Performance Engineering · 7 Ethernet and Data-Center
Network Foundations · 8 RDMA, RoCEv2, and InfiniBand · 9 Congestion Control and Lossless-Fabric
Engineering · 10 Switches, Optics, Cabling, and Physical-Layer Operations · 11 Distributed Training
Architecture · 12 Collective Communication and NCCL · 13 GPU-to-GPU and GPU-to-NIC Data Movement ·
14 Storage, Data Pipelines, and Checkpointing · 15 LLM Inference and Serving Infrastructure ·
16 Bare-Metal GPU Fleet Lifecycle · 17 Kubernetes, Slurm, and Workload Scheduling · 18 Observability,
SLOs, and Incident Response · 19 Reliability, Security, and Multi-Tenancy · 20 Infrastructure Automation
and Safe Change · 21 Capacity, Power, and Infrastructure Economics · 22 Cross-Layer Performance
Engineering · 23 Capstone: Design and Operate a Production-Scale AI Cluster · 24 Career Paths and
Engineering Practice.
- Drop: the learning-objectives list (replaced by "What you will learn"), prerequisites, review questions,
  further reading (a consolidated reading list is in the back matter), and lab-internal detail.

## 3. Rubric for the concise edition

Each chapter is scored by an independent reviewer acting as a senior AI-infrastructure engineer and a
technical editor. **Scores use 0.5 increments.**

| # | Dimension | Weight | What 9.5–10 looks like |
|---|---|---|---|
| C1 | Technical accuracy | 25% | No errors. Nothing is distorted by condensing: qualifiers, units, labels and caveats survive. Nothing is absent from the full chapter. |
| C2 | Fidelity and coverage | 15% | Every core mechanism and decision of the full chapter is present. A practitioner loses breadth, not understanding. |
| C3 | Pedagogy and clarity | 20% | Motivated progression, the worked example still teaches with every step shown, and diagrams teach the mechanism. It reads as a book chapter, not as notes. |
| C4 | Concision | 15% | 3,000–4,000 words, no filler, no repeated points, and the right amount of depth for each topic. |
| C5 | Evidence labelling | 10% | Quantitative claims labelled as in the full chapter. Measured, modeled and illustrative values are never confused. |
| C6 | Production realism | 5% | Failure signatures, thresholds and trade-offs stay concrete. The troubleshooting scenario uses the diagnostic loop. |
| C7 | Integration | 5% | ORION reference cluster used consistently, chapter cross-references correct, and the hands-on box points at the right lab. |
| C8 | Editorial polish | 5% | Style-guide terminology and units, acronyms defined on first use in the chapter, every figure and table captioned, clean Markdown. |

**Gate:** weighted ≥ 9.5, no dimension below 9.0, word count in range, and zero open blocker or major
findings (severities as in [EDITORIAL_RUBRIC.md](EDITORIAL_RUBRIC.md)). Reviews are recorded in
`concise/review/chNN.md`. Append each iteration and never delete history. Status is tracked in
`concise/review/STATUS.md`.

The internal score is an editorial assessment. It does not replace the external gates in
[RELEASE_GATES.md](RELEASE_GATES.md), and the edition must not be described as externally reviewed.
