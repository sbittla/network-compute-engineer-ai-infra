# R2 — A dated job-posting register

Source: manuscript Section 1.8 (Realism boundary) and Table 1.8. The register is the learner's own
research; the instructor checks structure and reasoning, not particular postings.

**Required fields (one row per posting):** employer, employer group (hyperscaler, AI cloud, frontier lab,
vendor), exact title, job ID, location, seniority, URL, date checked, required skills, preferred skills,
active/archived status. Deduplicate on job ID: the same role is often reposted per location.

**Register template (`register.csv`):**

```text
date_checked,employer,group,title,job_id,location,seniority,url,required,preferred,status
YYYY-MM-DD,<employer>,<group>,<exact title>,<id>,<city>,<level>,<url>,<skills>,<skills>,active
```

A full-credit register has ≥ 5 rows across ≥ 3 groups, every field filled, and dates on every row.

**What you can conclude:** which skill domains recur *in the sampled postings on the dates checked*: for
example, that several network-focused roles list RoCEv2 congestion control, or that cluster roles list
Slurm and Kubernetes together. This is useful for building your gap list (Exercise 1.3).

**What you cannot conclude:** market share, hiring volume, demand trends, salary levels, or completeness.
Five to twenty postings is a convenience sample. Titles differ across employers for the same work (Table
1.9), duplicates and evergreen requisitions inflate counts, and postings appear and disappear weekly.

**Why every "the market requires X" claim must be dated:** a posting is a time-stamped observation. Without
the date, a reader cannot check the claim (the posting may be archived) or refresh it (the requirement
may have changed), so the claim is not evidence. Dating turns an opinion into a verifiable, expiring
observation, which is the same evidence discipline the book applies to vendor specifications
(`[VENDOR-SPEC, YYYY-MM]`).
