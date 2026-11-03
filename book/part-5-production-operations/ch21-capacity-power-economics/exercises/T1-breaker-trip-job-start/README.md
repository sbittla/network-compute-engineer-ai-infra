# T1 — The breaker that tripped at job start (★★, L1)

Type: Troubleshooting · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
**T1 ★★ L1 — The breaker that tripped at job start.** *Declared variation:* Halcyon's legacy expansion hall
(Section 21.8) has racks with **one** canonical circuit per side (32.78 kW continuous, 2N A/B). At 09:02 rack
lh-03 (expansion nodes orion-n37 to orion-n40) loses its A side when a 32-node job starts. Evidence
`[ILLUSTRATIVE]`:

```text
capacity plan for lh-03: 4 HX8 nodes, "41 kW max <= 2 x 32.78 kW available"
change calendar: 08:00-12:00 UPS-B maintenance (legacy hall) - all B sides de-energized
lh-03 PDU-A (circuit continuous 32.78 kW = 48 A; PDU electronic overcurrent protection set at 48 A):
      08:55 load 12.1 kW (4 idle nodes) -> 09:02:10 40.8 kW (~60 A/phase) -> PDU overcurrent trip at 09:02:12
job start: 32 nodes ramp from idle to full training power within ~3 s (synchronised first step)
node BMC: 4 x "PSU input lost" at 09:02:11 ; GPUs at 700 W default limit
rack lh-04 (3 nodes): peak 30.6 kW on its A circuit, no trip
main-hall racks (two circuits per side, 65.55 kW, both feeds up): rack totals 39-41 kW (A + B), ~20 kW per side, no trip
```

Walk the diagnostic loop: hypotheses, discriminating evidence, root cause (system, not person), immediate
mitigation, and the guardrail that would have prevented it (with the cap value computed).
*Evidence required:* hypothesis table; arithmetic for the cap; guardrail statement with trigger and owner.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`

Run:

```bash
python solve.py --out outputs/     # your own script; show every formula and substitution
```
