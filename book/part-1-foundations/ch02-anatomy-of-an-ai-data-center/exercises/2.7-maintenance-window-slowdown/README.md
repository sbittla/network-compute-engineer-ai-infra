# Exercise 2.7 — The maintenance-window slowdown

**Difficulty:** ★★★ · **Tier:** L1 · **Type:** troubleshooting · **Kind:** computed · **Points:** 20

## Prompt

<!-- prompt:start -->
During a planned two-hour UPS-B maintenance window (feed B de-energised by Facilities), W-TRAIN's step
time rose from 17.4 s to 22.6 s. After feed B returned, step time recovered. Evidence available so
far `[ILLUSTRATIVE]`:

```text
DCGM, during the window (per-rack medians)
rack    sm_clock_mhz  power_w  clock_event_reasons_active
rack-01  1830          655      none
rack-02  1050          330      HW Slowdown, HW Power Brake Slowdown
rack-03  1050          332      HW Slowdown, HW Power Brake Slowdown
rack-04  1830          652      none
rack-05..rack-08 (all)  1830  650-657  none

Rack PDU feed A, during the window
rack    feed_A_kw   breaker_events
rack-01  34.0        none
rack-02  24.1        none
rack-03  24.3        none
rack-04  33.8        none
```

Nobody has yet looked at the nodes' power-supply inventory or the PDU outlet maps.

Tasks:

1. Compute the slowdown and explain why 8 of 32 nodes slowed the whole job by that much.
2. Rank at least three hypotheses for why only rack-02 and rack-03 braked when the other racks, on the
   same feed A, did not.
3. List the discriminating evidence you would collect next, with the exact read-only commands or data
   sources, and what result would confirm or reject each hypothesis.
4. Assume the evidence shows that every node in rack-02 and rack-03 has two PSUs corded to feed A and
   four to feed B. Explain the braking with arithmetic, propose the safe fix, and say how you would
   validate it *without* waiting for the next maintenance window.
5. Propose one line for the node acceptance checklist (the tests a node must pass before it joins
   the cluster; Chapter 16 covers it in full) that would prevent a recurrence.

**Evidence required:** slowdown arithmetic; ranked hypothesis table; evidence plan with commands;
root-cause arithmetic; fix and validation plan; one acceptance-checklist line.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the assumptions of the chapter's Sections 2.2–2.10.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/2.7-maintenance-window-slowdown/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/report.md`: slowdown arithmetic, ranked hypotheses, evidence plan with commands, root-cause arithmetic, fix, validation and the checklist line

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
