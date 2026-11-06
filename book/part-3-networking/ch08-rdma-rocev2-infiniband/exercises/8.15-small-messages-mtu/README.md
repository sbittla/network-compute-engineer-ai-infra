# 8.15 — Small messages work, large ones do not (★★★, L1)

Type: Troubleshooting case · kind: `computed` · 20 points

## Prompt

<!-- prompt:start -->
**8.15 Small messages work, large ones do not** ★★★ · L1 (tabletop) / L3 (reproduce in a lab)
After the rail-6 leaf was replaced over the weekend (its configuration restored from a template), NCCL
jobs that include any `rack-04` node (`orion-n13`…`orion-n16`) hang during the first large all-reduce and
later fail with `IBV_WC_RETRY_EXC_ERR`; jobs without `rack-04` nodes are healthy. Evidence collected so far
`[ILLUSTRATIVE]`:

- `ibv_devinfo` on `orion-n13` and `orion-n14`: `mlx5_6` `PORT_ACTIVE`, `active_mtu 4096 (5)`.
- `ip -o link`: `ens7np0 … mtu 9000` on both nodes.
- `ib_write_bw -d mlx5_6 -x 3 -a -F --report_gbits 10.100.6.29` from n13 to n14 prints rows up to
  `#bytes 1024` normally, then stops producing output; after several seconds the client exits with a
  completion error.
- `ibv_rc_pingpong -d mlx5_6 -g 3 10.100.6.29` (default options) completes normally.
- `orion-be-leaf-r6`, ports to n13 and n14: link up at 400G, zero FEC uncorrectable and CRC errors; an
  "oversize/giant frames dropped" counter (vendor name varies) is non-zero and rising.

(a) Rank three hypotheses. (b) Propose two discriminating tests that are safe to run, with exact
commands. (c) State the most likely root cause and the mechanism by which it produces *exactly* this
pattern (which message sizes pass and why). (d) Describe the safe fix and the validation.
*Evidence required:* hypotheses ranked with reasons; real commands; packet-size arithmetic showing
which sizes fit; fix routed through the Fabric team with change control; validation criteria.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/8.15-small-messages-mtu/` (instructor material in the full repository; removed from student releases).

## What to submit

Rank hypotheses with reasons, give exact (real) commands, and show the packet-size arithmetic. Put every deliverable in `outputs/`:

- `outputs/answer.md`
