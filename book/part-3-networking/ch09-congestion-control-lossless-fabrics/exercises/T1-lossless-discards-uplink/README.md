# T1 — Lossless discards on one uplink (★★★, L1)

Type: Troubleshooting case · kind: `computed` · 15 points

## Prompt

<!-- prompt:start -->
**T1 ★★★ L1 — Lossless discards on one uplink.** Two days after rail leaf `orion-be-leaf-r5` was replaced,
the lossless-class discard alert fires (`[ILLUSTRATIVE]` evidence below). No other leaf has discards;
NCCL jobs on rail 5 show occasional retransmission-driven slowdowns. Spine-1 sits in the same network
rack as the leaf; spine-4 sits in the second network rack, across the hall.

```text
orion-be-leaf-r5, 5-minute window
port      peer                        length   pfc_tx/s   pfc_rx/s   q_tc3_wm_kb   discards_tc3 (5 min)
eth1/7    orion-n07 mlx5_5              30 m       820          0          410            0
eth1/33   orion-be-spine-1 eth1/41      20 m     2,880          0        2,090            0
eth1/57   orion-be-spine-4 eth1/41     100 m     2,950          0        2,120        1,214

orion-be-leaf-r5 buffer profile (all ports): lossless PG3 headroom computed for cable_length = 5m
```

(a) List and rank at least three hypotheses. (b) Compute the headroom the profile provides and the
headroom the 100 m uplink needs (port MTU 9,216 B, t_resp 1 µs), and the deficit. (c) Explain why
eth1/33 has the same pause rate but no discards, and say whether this evidence shows eth1/33 is safe.
(d) Propose a safe fix and validation.
*Evidence required:* ranked hypotheses with the evidence that discriminates them; two headroom values
and the deficit with arithmetic; the eth1/33 headroom calculation and an explicit statement of what
the evidence can and cannot prove about it; fix with change-control steps and validation criteria.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Rank hypotheses with discriminating evidence, show the headroom arithmetic, and route the fix through change control. Put every deliverable in `outputs/`:

- `outputs/answer.md`
