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

## Before you start

- **Chapter:** Chapter 7 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Build the results table from your lab's `fabric_capacity`, and show the hand arithmetic for the ingress values. Put every deliverable in `outputs/`:

- `outputs/answer.md`
- `outputs/capacity.txt` (your `fabric_capacity` output for the three scenarios)

Run it for all three scenarios, substituting your 7.W1(a) design for `L`, `S` and `K` (leaves,
spines, parallel links per leaf-spine pair). `link_matrix` (provided in `fabric_lab.py`) builds the
`c[leaf][spine]` matrix with 0-based indices: `failed_links=((leaf, spine),)` removes one link from that
pair, and `failed_spines=(spine,)` zeroes that spine's column. If your design is not uniform, write
the matrix by hand and set the failed entries yourself.

```bash
cd ../../lab/starter && python -c "
import fabric_lab as f
L, S, K = 0, 0, 0   # <- your 7.W1(a) leaves, spines, links per pair
for name, c in [('baseline', f.link_matrix(L, S, K)),
                ('one leaf-spine link down (leaf 0, spine 0)', f.link_matrix(L, S, K, failed_links=((0, 0),))),
                ('one spine down (spine 0)', f.link_matrix(L, S, K, failed_spines=(0,)))]:
    print(name, f.fabric_capacity(c, 400))
" > ../../exercises/7.W2-orion-384-failure-capacity/outputs/capacity.txt
```

Read the affected leaf's entry (index 0) in `uplink_gbps` and `ecmp_ingress_gbps`; `bisection_gbps` is
fabric-wide.
