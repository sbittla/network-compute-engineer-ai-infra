# 11.5 — Rail locality: every DP peer of rank 19 is on rail leaf 3

**Rank order** (Megatron, TP fastest, then DP, then PP; Section 11.8). With TP = 8, DP = 8, PP = 4:

```text
r = tp + 8·dp + 64·pp
rank 19: tp = 19 mod 8 = 3;  dp = ⌊19/8⌋ mod 8 = 2;  pp = ⌊19/64⌋ = 0
```

**DP group of rank 19.** Same tp and pp, dp = 0…7:

```text
{3 + 8k : k = 0..7} = {3, 11, 19, 27, 35, 43, 51, 59}
```

**Placement.** `torchrun --nproc-per-node=8` puts global rank r on node ⌊r/8⌋ as local rank
r mod 8. For every member, r mod 8 = 3 (because r = 3 + 8k), so each DP peer is local rank 3 on nodes
0…7. Local rank 3 → GPU 3 → NIC 3 → **rail leaf 3**. ∎

The same argument covers the PP peers 19 + 64j (j = 0…3): 19 + 64j ≡ 3 (mod 8), so pipeline traffic
also stays on rail 3. With TP = 8 = GPUs per node, the TP group is exactly one node (NVLink), and every
DP/PP collective is rail-local: no spine hop is needed.

**Assumptions to state.** (1) `CUDA_VISIBLE_DEVICES` is not reordered, so local rank i drives GPU i;
(2) GPU i uses NIC i (the PIX-attached NIC; `NCCL_IB_HCA` not overridden). Break either and DP traffic
crosses rails through the spines (Chapter 12 shows the cost).

**Common wrong answers.** Using a DP-fastest order (r = dp + 8·tp …), which puts DP peers on the same
node; forgetting the PP peers; stating the result without the mod-8 argument.
