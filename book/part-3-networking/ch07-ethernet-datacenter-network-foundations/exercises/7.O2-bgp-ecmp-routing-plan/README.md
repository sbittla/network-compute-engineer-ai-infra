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

## What to submit

Write the plan (≤ one page) and the five-column failure table; every capacity must match your lab's `fabric_capacity` output. Put every deliverable in `outputs/`:

- `outputs/answer.md`
- `outputs/capacity.txt` (your `fabric_capacity` output for link, spine and leaf failure)

Run:

```bash
cd ../../lab/starter && python -c "import fabric_lab as f; print(f.fabric_capacity([[8]*4 for _ in range(8)], 400))"
```
