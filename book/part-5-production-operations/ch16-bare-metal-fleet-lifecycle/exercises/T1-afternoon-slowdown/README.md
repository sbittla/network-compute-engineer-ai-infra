# T1 · The afternoon slowdown in rack-04 (★★★ · L1)

Type: troubleshooting · Kind: written · Points: 20

<!-- prompt:start -->
**T1 ★★★ (L1 tabletop; L2/L3 to reproduce signals) — The afternoon slowdown.** Training Infra reports
that a 128-GPU job has a step-time p99 that is 9 % above p50 every afternoon, and only when it is
placed on nodes in rack-04. The nodes passed acceptance three months ago. Evidence:

```text
# nvidia-smi --query-gpu=index,temperature.gpu,clocks.sm,clocks_event_reasons.active --format=csv (orion-n14, 15:10)
4, 86, 1650 MHz, 0x0000000000000024
5, 87, 1590 MHz, 0x0000000000000024
6, 79, 1980 MHz, 0x0000000000000004
# same query at 03:10: all GPUs 71–76 C, 1980 MHz, 0x0000000000000004
# BMC inlet temperature (ipmitool sdr type Temperature), rack-04 nodes:
            03:00   09:00   15:00
orion-n13   23 C    25 C    31 C
orion-n14   23 C    26 C    32 C
orion-n15   24 C    25 C    31 C
orion-n16   23 C    25 C    32 C
# rack-03 and rack-05 nodes at 15:00: 24–25 C inlet
# Facilities ticket FAC-2210 (2 weeks ago): "rack-04 cold-aisle containment door panel removed for cable work"
```

Clock-reason bitmask reference (verify for your driver): `0x4` = SW Power Cap, `0x20` = SW Thermal
Slowdown. (1) Decode the reasons. (2) Rank three hypotheses. (3) Name the discriminating test for
each. (4) State root cause, the safe change, and how you validate it. (5) Which lifecycle actions, if
any, are appropriate for the four nodes?
*Evidence required:* decoded bitmask; ranked hypotheses with discriminating tests; a root cause that
explains *time of day* and *rack locality*; a validation measurement with a pass threshold; a
lifecycle decision with justification.
<!-- prompt:end -->

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line; cite the
manuscript Section, table, or lab file you relied on, and label every number with its evidence class
(`[MODELED]`, `[ILLUSTRATIVE]`, `[SIMULATED]`, ...).

On a single GPU host you can reproduce the clock-event-reason signals with `python scripts/hw_labs.py run ch16 --device gpu`
(CPU fallback with `--device cpu`). Inlet temperature and rack locality need the real rack.
