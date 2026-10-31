# Exercise 5.16 — One node slow after a rack move

★★★ · Tier L1 · troubleshooting case · kind: `written`

<!-- prompt:start -->
**5.16** ★★★ L1 — After a rack move, eight ORION nodes were re-cabled. A 64-GPU job's busbw fell from
≈ 350 to ≈ 300 GB/s with p99 iteration time up 40 %; one node, `orion-n12`, shows these facts `[ILLUSTRATIVE]`:
LLDP for `enp153s0np0` → `orion-be-leaf-r5 Ethernet12`, for `enp163s0np0` → `orion-be-leaf-r4 Ethernet12`;
`nvidia-smi topo -m` golden; the leaf ports' interface counters clean; NCCL log shows all NICs in use with
`/GDRDMA`; the ORION backend in this pod runs as an **L2 rail VLAN** (not routed /31). Rank hypotheses,
identify the root cause, explain why the job still runs but slower, give a safe fix and validation.
*Evidence required:* ranked hypotheses with tests, root cause, traffic-path explanation, fix, validation.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
