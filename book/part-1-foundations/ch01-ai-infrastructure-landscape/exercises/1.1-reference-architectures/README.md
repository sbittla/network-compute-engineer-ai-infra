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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/1.1-reference-architectures/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/training.md`: W-TRAIN diagram (Mermaid or an embedded image) with volumes on the data paths
- `outputs/inference.md`: W-INFER diagram with volumes on the data paths
- `outputs/dependencies.md`: one dependency table per workload and the failure-domain paragraph

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`).
