# Exercise 5.10 — Lab 5: topology mapper

★★ · Tier L1 · hands-on lab · kind: `lab`

<!-- prompt:start -->
**5.10** ★★ L1 (L3 extension) — Complete [Lab 5](../../lab/README.md): implement `topo_mapper.py`, pass
`python check.py`, produce the mapping CSV for all four hosts, a findings table, the scenario table, and
`topology_report.md`. *Evidence required:* per the lab rubric.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/check.txt` — the checker output for your implementation (all PASS)
- `outputs/gpu_nic_mapping.csv` — the mapping CSV for all four hosts
- `outputs/topology_report.md` — diagram, findings table, scenario table, recommendations, validation checklist, methodology, limitations (at most 3 pages)

Run from the chapter's `lab/` folder:

```bash
python check.py | tee ../exercises/5.10-lab-topology-mapper/outputs/check.txt
python starter/topo_mapper.py --data data --out ../exercises/5.10-lab-topology-mapper/outputs/gpu_nic_mapping.csv
```
