# L1 — Role-readiness scorer and register validator: instructor solution

Reference: `solutions/lab/career_lab.py`; `python lab/check.py --impl solution` → **12/12 PASS** (golden
report in `solutions/lab/outputs/check_solution.txt`). All results `[MODELED]` on synthetic data.

**Expected results.** AI Network Engineer readiness 100.0 / 94.1 / 78.4 / 69.6 % for junior / mid / senior /
staff (Table 24.5 reproduces the senior 78.4 %: 13.333 / 17). Senior gap plan: observability (priority 4),
congestion (3), host_topology (2), physical_layer (2). Register summary: 61 rows → 51 unique postings → 40
complete → **31 active and fresh**, 25 issues; top required skills over the 31: python 27, kubernetes 12,
inference serving 7, nccl 7, traffic generators 7.

**Flag explanation (the 20-point item).** The learner must give rule, reason and action for each:

| Item | Flag / rule | Why the rule exists | Learner action |
|---|---|---|---|
| E02, E03, E09 | type caps (course 1, lab_l1 2, self 1) | Evidence type bounds what it can show (Table 24.2) | Produce higher-type evidence |
| E05 | SIMULATION_CLAIMED_AS_MEASURED → 1 | Integrity failure: interviewers discount everything else | Relabel `[SIMULATED]`/`[MODELED]` |
| E06, E17 | STALE (> 1,095 days) −1 | Describes a previous technology generation | Refresh with current work |
| E07 | PRODUCTION_UNVERIFIED (cap 3) + STALE → 2 | Unverifiable production claims are the commonest inflation | Name a verifier |
| E10 | NO_ARTIFACT → 1 | Nothing a stranger can check | Publish the case study |
| E04 copy | DUPLICATE_EVIDENCE | Same artifact counted twice | Remove the duplicate |
| E14 | UNKNOWN_COMPETENCY (`bgp_evpn`) | Not in the catalogue, so ignored | Map it to `l3_fabric` |
| E19 | NO_DATE → treated stale, 1 → 0 | Undated evidence is unfalsifiable | Add the date |

**Rest of the rubric.** The learner's own matrix (target plus two adjacent roles, each level tied to an
artifact), a dated top-three gap plan, and a limitations statement: the score is `[MODELED]` from
self-reported evidence against teaching matrices, says nothing about supply, interview performance or a
given employer's ladder, and is not a hiring decision (see R1 and M1).

**Register discussion (explanation credit).** Rows 15/42: the tie-break keeps the re-post's ID (dates tie, lower index wins); a
production tool should keep all IDs as aliases, prefer the earliest-seen ID and keep the latest
`date_checked`. Row 27's upper-case employer shows that display fields of the representative should be
normalized too. Row 39 (archived, checked 2026-05-01) is correctly *not* flagged: staleness only matters for
"active" claims.

**Common mistakes.** Explaining a flag by restating its name; counting duplicates before field validation
in a way that changes representatives; treating the real 2026-10 register as checker input (it is
reference data and is not used by `check.py`).
