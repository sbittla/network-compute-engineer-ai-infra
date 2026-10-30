# Editorial and Technical Review Rubric

Each chapter package and capstone is scored by an independent reviewer acting as both a **senior AI
infrastructure engineer** (technical reviewer) and a **developmental/technical editor**. A package is
iterated until it passes the gate below.

## 1. Dimensions and weights

| # | Dimension | Weight | What a 9.5–10 looks like |
|---|---|---|---|
| D1 | Technical accuracy and currency | 20% | No factual errors. Numbers are correct and labelled. Protocol behaviour, hardware limits, and software behaviour are described as a senior practitioner would. No invented flags/APIs. Version-sensitive claims flagged. |
| D2 | Depth and production realism | 15% | Goes beyond "what" to "how it fails, how you see it, how you fix it at scale". Includes numbers practitioners actually use, failure signatures, and operational trade-offs. |
| D3 | Pedagogy and clarity | 15% | Clear progression, motivated concepts, worked example with every step shown, diagrams that teach the mechanism, objectives that the content actually delivers. |
| D4 | Hands-on lab quality | 15% | Lab mirrors a real task, runs deterministically, `check.py` passes on the solution and gives useful feedback on the starter, includes intentionally flawed data that teaches diagnosis, has an L2/L3 extension with real commands. |
| D5 | Exercises and assessment | 10% | Full standard exercise set plus all outline-mandated exercises; difficulty range; objective "evidence required"; complete answer key with marking guidance. |
| D6 | Measurement rigor and evidence labelling | 10% | Every quantitative claim labelled MEASURED/MODELED/SIMULATED/ILLUSTRATIVE/VENDOR-SPEC; benchmark discipline (warm-up, repetitions, percentiles, variance, manifests); measured vs modeled never confused. |
| D7 | Cross-layer integration | 5% | Uses the ORION reference cluster; connects compute, network, storage, orchestration; correct cross-references to other chapters and capstones. |
| D8 | Operational realism and safety | 5% | Runbook excerpt, signals/thresholds, safe-change practices, explicit safety boundaries. |
| D9 | Editorial polish | 5% | Consistent terminology and units, acronyms defined, figures captioned, no typos, no filler, correct Markdown, working relative links. |

**Weighted score** = Σ(score × weight). Scores use 0.5 increments.

## 2. Release gate (internal)

A package passes the internal editorial gate when **all** hold:

1. Weighted score ≥ **9.5**.
2. No dimension below **9.0**.
3. `python scripts/validate_labs.py` passes for the package (solution passes, starter fails gracefully).
4. Zero open *blocker* or *major* findings.
5. All outline-mandated exercises and the deliverable for this chapter are present.

## 3. Severity definitions

- **Blocker** — factually wrong in a way that would mislead a practitioner, unsafe instruction, lab
  does not run, or a mandated element is missing.
- **Major** — significant gap in depth, missing failure mode, unlabelled numbers in a key section,
  weak/absent answer key, unclear explanation of a core mechanism.
- **Minor** — style, terminology, small clarity issues, missing caption, typo.

## 4. Reviewer procedure

1. Read `README.md`, `manuscript.md`, `exercises.md`, `lab/README.md`, `solutions/exercises-key.md`.
2. Run `python lab/check.py --impl solution` and `--impl starter`.
3. Verify every calculation in the worked example and answer key independently.
4. Spot-check every vendor-specific claim, CLI command, and environment variable for existence and
   correct semantics. Flag anything uncertain.
5. Score each dimension with a one-paragraph justification; list findings with severity and location.
6. Record in `review/REVIEW.md` (append a new iteration; never delete history).

## 5. What the internal score does *not* certify

Following the course outline's own release gates, the internal score is an editorial assessment of
the manuscript and Level-1 labs. It does **not** replace: review by a practising GPU-cluster/network
engineer and a data-centre facilities specialist, validation of L2/L3 labs on real hardware, or
verification of vendor claims against current primary documentation at publication time. Those items
are tracked in [RELEASE_GATES.md](RELEASE_GATES.md).
