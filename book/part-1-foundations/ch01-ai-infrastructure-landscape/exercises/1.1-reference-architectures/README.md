# Exercise 1.1 — Reference architectures for training and inference

**Difficulty:** ★★ · **Tier:** L1 · **Type:** outline-mandated · **Kind:** written · **Points:** 20

## Prompt

<!-- prompt:start -->
Draw two reference architectures on ORION: (a) the W-TRAIN model-training workload and (b) the
W-INFER online-inference service. For each, show compute, scale-up network, scale-out network,
frontend network, storage, orchestration, and observability components, and the data paths between
them. Annotate each diagram with: the dominant data flow and its approximate volume (per step or per
request); for every layer, one dependency the workload has on it and the first signal you would see
if it degraded; and the failure domain of the workload (what fails together).

**Evidence required:** two diagrams (Mermaid, draw.io, or hand-drawn and photographed) each with ≥ 6
labelled components and ≥ 4 labelled data paths with volumes; a dependency table per workload (layer,
component, dependency, first signal); one paragraph contrasting their failure domains.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/training.md`: W-TRAIN diagram (Mermaid or an embedded image) with volumes on the data paths
- `outputs/inference.md`: W-INFER diagram with volumes on the data paths
- `outputs/dependencies.md`: one dependency table per workload and the failure-domain paragraph

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
