# 11.18 — Why "the configuration fits in 80 GB" is not an acceptance criterion

**Why it is insufficient.**

- **Peak, not steady state.** The model estimates the steady 1F1B footprint; real peaks occur during
  pipeline warm-up, the optimizer step (temporary FP32 buffers), NCCL buffer allocation and gradient
  bucket flattening.
- **Fragmentation.** The PyTorch caching allocator reserves more than it allocates; varying tensor
  sizes fragment the pool, so a job that "fits" at 76 GB allocated can OOM at 80 GB reserved after
  hours.
- **Other code paths.** Evaluation (different batch shapes), checkpoint save (state-dict copies,
  staging buffers for async checkpointing), logging hooks and profilers add memory on steps the
  estimate never sees.
- **Future changes.** Longer sequences, a larger micro-batch, a new optimizer or a library upgrade
  push a tight configuration over the edge; a 3 % margin is consumed by the first change.

**Evidence to require.**

1. Allocator peak statistics (`torch.cuda.max_memory_allocated()` and `max_memory_reserved()` per rank,
   all pipeline stages, especially stage 0) over **≥ 200 steps that include an evaluation pass and a
   checkpoint save**.
2. Peak reserved ≤ 85 % of HBM (the chapter's 68 GB planning limit, i.e. **≥ 15 % headroom**).
3. Zero allocator retries/OOM events (`num_alloc_retries` from `memory_stats()`), and a stable reserved
   curve (no upward drift).
4. The same test repeated after any change to sequence length, batch, or software versions.

Planted trap J in the lab (70.4 GB: fits 80 GB, violates headroom) is exactly this case.
