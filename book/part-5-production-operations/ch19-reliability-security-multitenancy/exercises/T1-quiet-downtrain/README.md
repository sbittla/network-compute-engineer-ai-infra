# T1 — The quiet downtrain (★★, L1)

Type: Troubleshooting · Kind: `computed` · Points: 12

## Prompt

<!-- prompt:start -->
**T1 ★★ L1 — The quiet downtrain.** A 16-node job on ORION runs 9 % slower than its baseline since a
maintenance reboot of orion-n10 yesterday. Evidence `[ILLUSTRATIVE]`:

```text
per-node SM active: 15 nodes 0.57, orion-n10 0.57    (no compute straggler)
per-node backend NIC TX (Gb/s, 8 NICs summed): 15 nodes 1,050-1,080, orion-n10 985
per-NIC peak TX during all-reduce bursts (1 s samples): orion-n10 mlx5_2 ≈ 205 Gb/s; its other NICs and all peers' NICs ≈ 370 Gb/s
orion-n10 rdma statistic: out_of_sequence flat; rp_cnp_handled normal; link_downed 0
orion-n10 journalctl -k | grep AER: 3,400 "Corrected error ... type=Physical Layer ... RxErr" since boot (others: 0-5)
orion-n10 lspci -vvv -s 3b:00.0 (mlx5_2):  LnkCap: Speed 32GT/s, Width x16   LnkSta: Speed 32GT/s, Width x8 (downgraded)
switch counters for all 8 orion-n10 ports: clean
```

Run the diagnostic loop: hypotheses, discriminating evidence, root cause, containment (domain and
unit), fix, validation. Explain why SM activity does not single out orion-n10 here, unlike the Chapter 18
power-cap case.
*Evidence required:* hypothesis table; bandwidth arithmetic for x16 vs x8; containment decision;
validation criteria.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`
