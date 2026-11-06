# K4 — The register: model answer

Source: Section 24.4, "Scope note: job-posting claims need a register", and Table 24.8.

**Fields the course outline requires.** Employer; exact title; job ID; location; seniority; URL; date
checked; required skills; preferred skills; active/archived status (ten fields).

**Field → market-claim error it prevents** (any three):

| Field | Error it prevents |
|---|---|
| `employer` + `job_id` (posting key) | One posting cross-listed on three boards counted three times, inflating that employer's skills |
| canonical `url` (tracking queries stripped) | The same requisition counted again under a board's tracking link. A re-post under a new ID normally has a new URL, so it needs a role key (employer + title minus location qualifier) |
| `date_checked` + `status` | Describing a closed market as current: postings closed months ago still counted |
| `required_skills` vs `preferred_skills` | Counting "preferred" skills as requirements, overstating the hiring bar |
| controlled `seniority` vocabulary | "Senior", "Sr." and blank treated as different levels, breaking level breakdowns |

**Evidence from the lab.** On the synthetic register these rules take 61 rows to 51 postings, 40 complete
and 31 active and fresh, about half the starting rows `[ILLUSTRATIVE — synthetic data]`. On the real
register a role-level key was also needed: 60 requisitions became 50 roles `[OBSERVED, 2026-11-06]`
(Table 24.9).

**Common mistakes.** Omitting `date checked` or `status`; merging required and preferred skills into one
list; saying a field exists "for documentation" without naming the error it prevents.
