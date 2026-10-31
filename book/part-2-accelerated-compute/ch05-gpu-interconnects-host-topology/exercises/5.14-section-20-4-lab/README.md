# Exercise 5.14 — Section 20.4 lab: topology, rank maps, all-reduce comparison

★★★ · Tier L1 · outline-mandated · kind: `lab`

<!-- prompt:start -->
**5.14** ★★★ L1 / L3 — *Section 20.4 lab.* Produce an annotated topology diagram of one HX8 host, the GPU-to-HCA
mapping CSV, aligned and intentionally misaligned rank/rail maps, and a comparison of NCCL all-reduce
results — measured with nccl-tests if you have L3 hardware (lab README §8), otherwise from the labelled
model — with benchmark methodology and limitations. *Evidence required:* raw outputs, diagram, CSV, two
rank maps, results table with labels, methodology, limitations.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/raw/` — the raw topology outputs you used (lab capture files or your own L2 capture)
- `outputs/topology_diagram.md` — the annotated diagram (Mermaid or ASCII)
- `outputs/gpu_nic_mapping.csv` — GPU-to-HCA mapping keyed by GPU UUID and NIC BDF
- `outputs/rank_maps.md` — aligned and misaligned rank/rail maps
- `outputs/results.md` — results table with evidence labels, benchmark methodology and limitations

Generate the mapping and model results from the chapter's `lab/` folder:

```bash
python check.py
python starter/topo_mapper.py --data data --out ../exercises/5.14-section-20-4-lab/outputs/gpu_nic_mapping.csv
```
