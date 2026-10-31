# 7.W2 — Failure capacity of ORION-384 (★★★, L1)

Type: Worked problem · kind: `computed` · 12 points

## Prompt

<!-- prompt:start -->
**7.W2** ★★★ L1 — Using your design from 7.W1(a):
(a) Compute raw uplink, ECMP-aware ingress, and spine-layer bisection capacity (one direction) for
baseline, one leaf-spine link down, and one spine down. Use `fabric_capacity` from the lab and show
the hand arithmetic for at least the ingress values.
(b) Compare the single-link-failure penalty with ORION-256's (Table 7.8) and explain the difference.
(c) Four 400 Gb/s flows are hashed uniformly onto the 4 links between one leaf and one spine.
Compute P(no collision) and the expected number of links used.
*Evidence required:* a results table, formulas with substituted values, and a 3–5 sentence comparison.
<!-- prompt:end -->

## What to submit

Build the results table from your lab's `fabric_capacity`, and show the hand arithmetic for the ingress values. Put every deliverable in `outputs/`:

- `outputs/answer.md`
- `outputs/capacity.txt` (your `fabric_capacity` output for the three scenarios)

Run:

```bash
cd ../../lab/starter && python -c "import fabric_lab as f; print(f.fabric_capacity([[4]*8 for _ in range(16)], 400))"
```
