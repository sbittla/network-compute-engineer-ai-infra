# 14.5 — Commit protocol: worked solution

**Order (Section 14.10, "Atomic commit and metadata durability"):**

1. **write shard files** (every rank).
2. **fsync shard files.** Shard data must be durable before anything references it. Otherwise a crash
   leaves a manifest pointing at bytes still in the page cache.
3. **barrier.** Every rank succeeded. Any failure aborts the checkpoint.
4. **write manifest** (coordinator: every shard with size and checksum).
5. **fsync manifest.** The description of the checkpoint is durable before the commit refers to it.
   Otherwise the commit marker can survive a crash while the manifest is torn.
6. **write `COMMIT.tmp`.**
7. **fsync `COMMIT.tmp`.** The marker's contents (for example the manifest hash) are durable *before*
   the marker becomes visible under its final name.
8. **rename `COMMIT.tmp` → `COMMIT`.** POSIX `rename` is atomic within one file system, so readers see
   either no marker or a complete one.
9. **fsync the directory.** The rename is a change to the directory entry. Without this, a crash can
   lose the new name and the checkpoint silently reverts to uncommitted.
10. **advance `latest`,** preferably only after validation (Table 14.5).

**On an object store.** There is no rename and there are no real directories. Upload all shards, then
upload the **manifest last**. The manifest's existence, plus validation, *is* the commit, and readers
treat a prefix without a valid manifest as nonexistent. Use unique keys per checkpoint (or conditional
writes such as if-none-match) so that nothing is overwritten. Never "list then assume complete": listings
can be incomplete or lag, so readers resolve shards from the manifest. Retention must also respect the
protocol and never delete the last validated checkpoint while the next one is still persisting.

**Common wrong answers.** Advancing `latest` at snapshot time, the root cause in 14.12. Omitting the
directory fsync. fsyncing the marker only after the rename.
