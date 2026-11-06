# Exercise 5.16 — One node slow after a rack move

★★★ · Tier L1 · troubleshooting case · kind: `written`

<!-- prompt:start -->
**5.16** ★★★ L1 — After a rack move, eight ORION nodes were re-cabled. A 64-GPU job's busbw fell from
≈ 350 to ≈ 300 GB/s with p99 iteration time up 40 %; one node, `orion-n12`, shows these facts `[ILLUSTRATIVE]`:
LLDP for `enp153s0np0` (the rail-4 NIC, `mlx5_4`) → `orion-be-leaf-r5 Ethernet12`, for `enp163s0np0` (the
rail-5 NIC, `mlx5_5`) → `orion-be-leaf-r4 Ethernet12`; `nvidia-smi topo -m` golden; the leaf ports'
interface counters clean; NCCL log shows all NICs in use with `/GDRDMA`. This pod is a declared variation
from ORION's routed /31 plan: all backend NICs share **one stretched L2 domain** (one VLAN and IP subnet
spanning all rail leaves, stretched over the spines with EVPN-VXLAN). Rank hypotheses, identify the root cause, explain why the job
still runs but slower, give a safe fix and validation.
*Evidence required:* ranked hypotheses with tests, root cause, traffic-path explanation, fix, validation.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 5 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 5.4 model parameters.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
