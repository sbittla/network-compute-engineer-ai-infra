# 11.1 — Collectives per strategy

Method: Sections 11.3–11.7 and the traffic profile of Table 11.2.

| Strategy | Collective(s) | How often per optimizer step |
|---|---|---|
| DDP | All-reduce of gradient buckets (≈ 25 MB each) | Once per step per bucket, overlapped with backward; with gradient accumulation (`no_sync()`), only on the last micro-batch |
| ZeRO-1 (distributed optimizer) | Reduce-scatter of gradients, then all-gather of updated BF16 weights | Once per step (same total bytes as one all-reduce, split in two halves) |
| ZeRO-3 / FSDP full shard | All-gather of weights before forward, all-gather again before backward, reduce-scatter of gradients | Per layer (FSDP unit) per micro-batch — 1.5 all-reduce-equivalents of the shard per micro-batch |
| Megatron TP + sequence parallelism | All-gather and reduce-scatter of activations (2 all-reduce-equivalents in forward, 2 in backward per layer) | Per layer per micro-batch — 4 × 20 × 128 = 10,240 per step for the W-TRAIN baseline |
| Pipeline parallelism | Point-to-point send/recv of activations (forward) and activation gradients (backward) | Per micro-batch per stage boundary (2 × 128 messages per GPU per step in the baseline) |
| Expert parallelism (MoE) | All-to-all dispatch and all-to-all combine (2 in forward, 2 in backward) | Per MoE layer per micro-batch |

**Why the frequencies matter.** Frequency, not just volume, decides where a collective must run:
TP fires 10,240 times per step and sits on the critical path, so it must stay on NVLink inside a node;
DP fires once per step and can be hidden behind the backward pass, so it can cross the rail fabric
(Section 11.8).

**Common wrong answers.**

- "ZeRO-1 uses all-reduce plus extra traffic." It uses the *same* bytes as all-reduce, split into
  reduce-scatter and all-gather (Table 11.1); only ZeRO-3 adds traffic (1.5×).
- Saying TP uses one all-reduce per layer: Megatron uses one in forward and one in backward per
  sub-block (attention and MLP), i.e. four per layer; with sequence parallelism each becomes a
  reduce-scatter/all-gather pair.
- Listing all-reduce for pipeline parallelism.
