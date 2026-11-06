# T1 — The interview troubleshooting round, version 2 (★★★, L1)

Troubleshooting case · difficulty ★★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**T1 ★★★ L1 — The interview troubleshooting round, version 2.** An interviewer gives you this
`[ILLUSTRATIVE]` evidence: a 32-node W-TRAIN job on ORION-256 is 12 % slower than yesterday
(step-time p50 17.4 s → 19.5 s). Per-rank timing shows ranks on `orion-n22` are last to arrive at every
pipeline send. On `orion-n22`, `nvidia-smi -q -d PERFORMANCE` shows for GPU 5 (abridged):

```text
    Clocks Event Reasons
        Idle                              : Not Active
        SW Power Cap                      : Not Active
        HW Slowdown                       : Not Active
            HW Thermal Slowdown           : Not Active
            HW Power Brake Slowdown       : Not Active
        SW Thermal Slowdown               : Active
```

Its SM clock is 1,585 MHz against ≈ 1,830 MHz on peers (ORION's typical sustained clock under dense
training; peers show `SW Power Cap` intermittently, which is routine); GPU temperature is 89 °C
against 64–70 °C on peers. The fabric dashboard also shows ECN-marked packets on rail-5 leaf ports rising 3× since
yesterday, and the facilities log records a fan-tray replacement in `rack-06` (which holds `orion-n22`) at
02:10. Walk the diagnostic loop: rank at least three hypotheses by information value, cost and risk;
name the discriminating test(s); state the root cause and what remains correlation; propose a safe
change and a validation; check that the clock deficit explains the size of the slowdown; and propose
an explanation for the ECN signal and how you would test it.
*Evidence required:* hypothesis table; discriminating test with expected outcomes; root-cause statement
separated into proven and inferred; magnitude check with arithmetic; safe action; validation with
repetitions; ECN hypothesis with its test.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`
