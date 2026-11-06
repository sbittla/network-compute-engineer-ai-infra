# 7.O2 — BGP/ECMP routing plan and failure behaviour (★★, L1)

Type: Outline-mandated · kind: `computed` · 10 points

## Prompt

<!-- prompt:start -->
**7.O2** ★★ L1 **[Outline]** — Write a one-page BGP/ECMP routing plan for the ORION-256 backend:
ASN plan, what each tier originates and accepts (with prefix filters), multipath settings
(`maximum-paths` values at leaf and spine with justification), BFD and BGP timers, and the drain
procedure. Then describe, for a **link**, a **spine**, and a **leaf** failure: detection mechanism and
time, routes withdrawn (by whom, which prefixes), resulting ECMP width at an unaffected leaf, capacity
impact (from Table 7.8 or your lab), and workload impact.
*Evidence required:* the plan, a failure table with all five columns for all three failures, and
consistency with your lab's `fabric_capacity` output.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/7.O2-bgp-ecmp-routing-plan/` (instructor material in the full repository; removed from student releases).

## What to submit

Write the plan (≤ one page) and the five-column failure table; every capacity must match your lab's `fabric_capacity` output. Put every deliverable in `outputs/`:

- `outputs/answer.md`
- `outputs/capacity.txt` (your `fabric_capacity` output for link, spine and leaf failure)

Run all four scenarios on ORION-256 (8 leaves, 4 spines, 8 links per pair, 400 Gb/s). `link_matrix`
(provided in `fabric_lab.py`) uses 0-based indices: leaf `i` is `orion-be-leaf-r<i>`, spine `s` is
`orion-be-spine-<s+1>`. `failed_links=((leaf, spine),)` removes one link from that pair,
`failed_spines=(spine,)` zeroes a spine's column, and `failed_leaves=(leaf,)` zeroes a leaf's row:

```bash
cd ../../lab/starter && python -c "
import fabric_lab as f
for name, c in [('baseline', f.link_matrix(8, 4, 8)),
                ('link down: leaf-r0 to spine-1', f.link_matrix(8, 4, 8, failed_links=((0, 0),))),
                ('spine down: spine-2', f.link_matrix(8, 4, 8, failed_spines=(1,))),
                ('leaf down: leaf-r3', f.link_matrix(8, 4, 8, failed_leaves=(3,)))]:
    print(name, f.fabric_capacity(c, 400))
" > ../../exercises/7.O2-bgp-ecmp-routing-plan/outputs/capacity.txt
```

For the leaf failure, the failed leaf's own entries read 0 (its rail is unreachable) and the
bisection is fabric-wide. `fabric_capacity` does not report ECMP width: count it yourself at an
unaffected leaf (for example leaf-r7) as its healthy uplinks toward the spines that still reach the
destination leaf.
