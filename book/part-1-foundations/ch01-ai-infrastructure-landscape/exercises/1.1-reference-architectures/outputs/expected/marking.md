# Marking scheme: 1.1 Reference architectures for training and inference

Type outline-mandated · kind written · tier L1 · 20 points

**Evidence required:** Two diagrams, each with at least 6 labelled components and at least 4 labelled data paths with volumes; a dependency table per workload (layer, component, dependency, first signal); one paragraph contrasting their failure domains.

| Criterion | Points |
|---|---|
| Both diagrams show at least 6 labelled components and at least 4 labelled data paths, including the checkpoint path for W-TRAIN and the weight-load path for W-INFER | 6 |
| Volumes on the data paths are correct within 2x (TP about 1,203 GB, DP about 7.66 GB, PP about 2.15 GB per GPU per step; checkpoint about 980 GB; weights about 140 GB) | 4 |
| Dependency tables cover every layer (compute, scale-up, scale-out, frontend, storage, orchestration, observability) with a defensible first signal | 6 |
| Failure-domain paragraph contrasts the whole 256-GPU job with a single eight-GPU replica and states the capacity consequence | 4 |
