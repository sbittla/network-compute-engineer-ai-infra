# 14.5 — Commit protocol (★, L1)

Type: knowledge-check · Kind: written

## Prompt

<!-- prompt:start -->
**14.5 Commit protocol** ★ · L1
Put these steps in the correct order and say what failure each `fsync` protects against: write
`COMMIT.tmp`; fsync shard files; barrier; write manifest; rename `COMMIT.tmp` → `COMMIT`; fsync the
directory; fsync manifest; fsync `COMMIT.tmp`; write shard files; advance `latest`. How does the
protocol change on an object store? *Evidence required:* ordered list with one justification per
fsync.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
