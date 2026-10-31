# 7.L — Progressive Lab 2: fabric design and validation (★★, L1)

Type: Hands-on lab · kind: `lab` · 100 points

## Prompt

<!-- prompt:start -->
**7.L** ★★ L1 (L2/L3 extensions) — **Progressive Lab 2: fabric design and validation.** Complete
[lab/README.md](../../lab/README.md) Tasks 1–6: implement the five functions in
`lab/starter/fabric_lab.py` until `python lab/check.py` reports 19/19 PASS, then write the design
note. **Stretch:** specify (as a written rule plus a five-row test table) a `QOS_MISMATCH` validator
rule covering DSCP trust on host ports, the DSCP→traffic-class map, and the lossless priority, and
state which intent fields it needs that the supplied dataset lacks.
*Evidence required:* checker output (19/19), your findings report, the design note, and (stretch)
the rule specification.
<!-- prompt:end -->

## What to submit

Complete lab Tasks 1–6 in `lab/starter/fabric_lab.py` until the checker reports 19/19 PASS. Put every deliverable in `outputs/`:

- `outputs/check_output.txt` (the full checker output)
- `outputs/findings.md` (one line per finding: what, consequence, severity)
- `outputs/design_note.md` (Task 6: diagram, routing policy, failure-convergence table)
- `outputs/qos_mismatch_rule.md` (stretch: rule text and five-row test table)

Run:

```bash
cd ../../lab && python check.py | tee ../exercises/7.L-fabric-design-lab/outputs/check_output.txt
```

**Hardware run (course harness).** L2 on the course harness: `python scripts/hw_labs.py run ch07` probes
for containerlab and records the container-fabric part as not runnable there. It also reproduces Section
7.6's ECMP statistics with a hashing Monte Carlo (`[SIMULATED]`); see `lab/l2/results/`.
