# 14.12 — The resume that trained worse: worked solution

**(a) Diagnostic loop.** *Symptom:* the loss was 1.82 and falling before the failure. Since the
03:28 resume it has been 2.25–2.31 and is not recovering.

| # | Hypothesis | Evidence for / against | Discriminating test |
|---|---|---|---|
| H1 | Restored an **incomplete checkpoint**: `latest` → `step_088327`, whose persist was in flight | Snapshot 03:12:55, failure 03:13:02: 7 s into an ≈ 19 s persist (88290 took 18.9 s). **No `COMMIT`** file. 257 entries = manifest + 256 shards (all names present). 31 load warnings. `missing=0` checked only file existence | Run the validator: NO_COMMIT plus size/checksum defects. Compare shard sizes with the manifest |
| H2 | LR scheduler / step state reset | Would show the LR back in warm-up | Logged LR at step 88328 vs 88327 |
| H3 | Data-loader state lost (replay/skip) | Usually a small, transient effect, not +0.45 persistent | Sample IDs after resume vs planned order |
| H4 | Faulty replacement node computing wrongly | Possible after a node swap | Per-rank gradient norms. Rerun one step with the new node excluded |

**(b) Root cause.** The trainer advanced `latest` at **snapshot** time, not after commit, and the restart
controller trusted `latest`. The persist of 88327 was interrupted, so `orion-n21`'s eight shards and
possibly others were truncated. The 31 warnings most likely report size/shape mismatches or missing
keys in truncated optimizer-state shards. The loader then default-initialized those entries (for
example zeroed Adam moments), giving a valid-looking but corrupt state.

**(c) Recovery.** Stop the job now. Run the validator. Restore from **`step_088290`**, committed at
03:02:30 (completion 18.9 s), and verify that its first-step loss is ≈ 1.82. Cost `[MODELED]`:

```text
2 h of damaged training discarded      2 h × 256 GPUs                    = 512.0 GPU-h
steps 88290 → 88327 recomputed         37 × 17.4 s = 643.8 s × 256 / 3600 =  45.8 GPU-h
another soft restart (Section 14.12)   (300+330+20+150 + 8.2 load) = 808.2 s × 256 / 3600 = 57.5 GPU-h
total                                                                      ≈ 615 GPU-h
```

That is better than continuing to train a damaged model, which would waste every further GPU-hour.

**(d) Prevention (Section 14.10).**

1. Advance `latest` only after commit **and** validation (commit protocol step 5). The restart controller
   runs the validation ladder (Table 14.5) itself and never trusts `latest` blindly.
2. Add the **semantic check** (last row of Table 14.5). Compare the first-step loss after resume with the
   loss recorded at save, and abort outside a tolerance. It would have caught this at 03:28.

**Common wrong answers.** Blaming the new node first without testing. Restoring 88327 again.
