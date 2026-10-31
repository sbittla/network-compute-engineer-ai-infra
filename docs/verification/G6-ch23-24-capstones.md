# G6 phase 2 — ch23-24-capstones (copyedit register applied)

Date: 2026-10-30. Scope: every file in the Ch 23 and Ch 24 folders plus the whole `capstones/` tree,
excluding `review/`. Lint was run in both default scope and `--all` (which adds solutions, templates,
instructor guides and lab data in scope).

## Counts applied

- **MECHANICAL: 171.** 167 lint replacements applied by position (bottom-up, right-to-left), plus 4
  by hand: Capstone H `§15.10–15.12` → "Sections 15.10–15.12" (range kept plural); Capstone E
  line 117 three bare labels backticked. Covers -ize, analyse/analysed, judgement, rerun/reimage/retest,
  toward, catalogue, modeled, center, data-center, rail-optimized, KV cache, p95/p99, FP32, tokens/s,
  model FLOPs utilization, ≈ for `~`, unspaced ratios, backticked labels.
- **JUDGEMENT: 102.**
  - Acronym first-use expansions: 95. Ch 23 (13) and Ch 24 (3), Capstones E (14), F (7), G (14)
    and H (10): added to the existing Acronyms paragraph. Where the first use comes before that
    paragraph, the term is expanded inline: SRE in the E/F/G Audience rows, ECC and NIC in the
    G intro, RDMA in the H intro. Capstones A (10), B (11), C (5) and D (8) have no Acronyms
    paragraph, so their expansions are inline at first body use. Ch 23's PXN entry now reads
    "PCI × NVLink, NCCL's cross-rail path".
  - Capstone F: "MTTR (mean time to recover)" → "mean time to restore". Capstone E:
    "Fleet/Datacenter Operations" → "Fleet/Data Center Operations".
  - Labels: Ch 23 lab README line 162 and Capstone E line 117 use the template `[VENDOR-SPEC, YYYY-MM]`.
  - Ch 24 line 701: "> ~10 %" reworded to "more than ≈ 10 %".
  - Ch 24 captions (2): *Table 24.14a* (hypothesis ranking) and *Table 24.15a* (runbook excerpt,
    `[ILLUSTRATIVE]`). These are letter suffixes, so no tables were renumbered.
- **NVLS rule: 3 edits.** The single-node canary busbw of 452.85 GB/s now says "NVLS assumed" in
  Capstone E `instructor/EXEMPLAR.md` (row 7) and `instructor/GRADING_GUIDE.md` (P14 row and the
  P14 arithmetic). No numbers were changed. The Capstone E README already stated NVLS. Capstone C
  already distinguishes ring and NVLS.
- **Coordinator correction ("analyses"): 1 revert.** Ch 24 manuscript "lab-quality analyzes" →
  "analyses" (plural noun). Ch 23 manuscript "if it analyzes supplied traces" is a verb, so it was kept.
- **Organisation:** no "Network team" or Storage-team mentions in scope; nothing to change.

## Skipped findings (with reasons)

- STYLE glossary-paragraph form (6: Ch 23, Ch 24, Capstones E, F, G, H): the register marks these
  optional. Converting each list to the `**Acronyms.** ACR (expansion)` form would rewrite more
  prose than a copyedit should.
- Ch 23 manuscript, SLI (line ≈ 393): the Acronyms paragraph already defines it as "SLO/SLI
  service-level objective/indicator". The lint does not parse the combined form.
- Capstone G, RPO and RTO (line 29): that line is the Acronyms paragraph itself, and it already
  defines "RPO/RTO (recovery point/time objective)".

## Remaining lint exceptions

- Default scope (`copyedit_lint.py ch23 ch24 capstones/`): **0 findings in 25 files.**
- `--all`: 15 findings remain in `ch23 .../lab/data/bundle_kestrel_capA/design.md` and
  `bundle_orion_reference/design.md`. These are generated lab input data, written by
  `lab/tools/generate_bundles.py` and graded by `design_lint.py`, whose findings depend on line
  numbers and label patterns. They are data, so they were not edited and no ignore markers were added.
  The other 11 `--all` findings are in `docs/verification/` files, which are outside this scope.
- No `<!-- copyedit-lint: ignore -->` markers were added.

## validate_labs

`python scripts/validate_labs.py ch23 ch24 capstone-` → **10/10 labs valid** (solution pass,
starter fails gracefully, no-generator pass, docs ok). Ch 24 lab data and the 2026-10 register
CSVs were not touched.
