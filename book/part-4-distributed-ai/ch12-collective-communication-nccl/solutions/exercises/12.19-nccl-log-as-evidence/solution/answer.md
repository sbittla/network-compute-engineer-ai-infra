# 12.19 — What to add to a single nccl-tests log before accepting it as evidence

A lone log shows numbers, not their context. For an incident review require:

1. **An environment manifest.** Driver, CUDA, NCCL and nccl-tests versions; NIC and switch firmware;
   container image digest; every `NCCL_*` variable (and `UCX_*`, if relevant); GPU and NIC topology
   (`nvidia-smi topo -m`, NCCL topology dump); the exact command line.
2. **The node list and rank map.** Which hosts, in which order, ranks per host — so the result can be
   tied to specific NICs and rails (c6 differed from c5 only by one node).
3. **Repetition.** Several launches (≥ 5) with the spread (median, min, CV), plus the warm-up and
   iteration counts used; a single launch can be bimodal or an outlier.
4. **A baseline for comparison.** The same test, same shape, from a known-good time or node set, so the
   reader can see the delta rather than an absolute number.
5. **The fabric state.** Confirmation that the fabric was otherwise idle, or a statement of what else
   ran, plus switch and NIC counters (PFC, ECN, discards, FEC) from before and after the run.
6. **Timestamps and the INFO start-up log** (`NCCL_DEBUG=INFO`): channels, NIC bindings, `GDRDMA`
   status, chosen algorithms — the lines that let a reviewer check the mechanism, not just the result.

Label it `[MEASURED]` with date and environment; anything less is an anecdote.
