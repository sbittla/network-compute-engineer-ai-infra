# Exercise 5.10 — Lab 5: topology mapper

★★ · Tier L1 · hands-on lab · kind: `lab`

<!-- prompt:start -->
**5.10** ★★ L1 (L3 extension) — Complete [Lab 5](../../lab/README.md): implement `topo_mapper.py`, pass
`python check.py`, produce the mapping CSV for all four hosts, a findings table, the scenario table, and
`topology_report.md`. *Evidence required:* per the lab rubric.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 5 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 5.4 model parameters.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

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

**Hardware run (course harness).** Optional hardware capture on the course harness: `python
scripts/hw_labs.py run ch05 --device gpu` runs your parser on the host's real `nvidia-smi topo -m` and
records the PCIe link and GDR prerequisites in `lab/l2/results/`. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.