# 14.20 — Per-directory create limit: worked solution

All values are `[MODELED]` from the prompt's `[ILLUSTRATIVE]` rates: ≈ 2,700 creates/s into one
directory (the per-directory ceiling: one metadata target and one contended directory lock and index) and ≈ 30,000 creates/s in aggregate across
many directories. Files per checkpoint N = ranks × files per rank = 256 × F.

**(a) One directory, F = 1,025.** N = 256 × 1,025 = 262,400; t = N / 2,700 = 262,400 / 2,700 =
**97.2 s**. That is the ≈ 96 s checkpoint completion of Section 14.14: the creates alone explain it.

**(b) One subdirectory per rank.** Each of the 256 directories receives 1,025 creates. At the
per-directory limit that takes 1,025 / 2,700 = 0.38 s, but all directories share one metadata
service, so the aggregate limit binds: t = max(262,400 / 30,000, 1,025 / 2,700) = max(8.75, 0.38) =
**8.75 s**.

**(c) Old format, F = 2, one directory.** N = 512; t = 512 / 2,700 = **0.190 s**.

**(d) Largest F in one directory.** Budget = 0.05 × L = 0.05 × 18.49 s = 0.9245 s. Creates allowed
= 0.9245 × 2,700 = 2,496; per rank 2,496 / 256 = 9.75, rounded down to **9 files per rank**.

**(e) Recommendation.** Take the file-count fix first: return the format to a few files per rank. It
removes the metadata load instead of spreading it, needs no change on the shared file system, and is
46× faster than (b) (0.190 s vs 8.75 s). Subdirectories per rank or a striped directory across several
metadata targets (Lustre DNE, `lfs setdirstripe`, `[VENDOR-SPEC, 2026-10]`) are the fallback for a
format that genuinely needs many files, and they must be agreed with the Storage team: even (b) runs
the whole metadata service at its aggregate limit for 8.75 s per checkpoint, which every other tenant
feels as slow `open` and `ls`. Add a files-per-checkpoint SLI so the regression is caught at image
build time.

*Common mistake:* answering (b) with 0.38 s, which ignores the service's aggregate limit.
