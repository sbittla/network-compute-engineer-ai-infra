# Chapter 4 — Exercise folders

One folder per exercise in [`../exercises.md`](../exercises.md). Each folder holds the prompt
(`README.md`) and an empty `outputs/` directory for your deliverables. Kinds: `computed` (numeric or
algorithmic answer: show formula → substitution → result), `lab` (completed by doing the chapter lab;
the checker output is part of the evidence), `written` (reasoning, design or reflection).

| ID | Title | Type | ★ | Tier | Kind |
|---|---|---|---|---|---|
| [4.1](4.1-sm-warp-block-grid/) | SM, warp, thread block and grid | knowledge check | ★ | L1 | written |
| [4.2](4.2-coalescing-sector-counts/) | Coalescing and 32-byte sectors | knowledge check | ★ | L1 | computed |
| [4.3](4.3-implicit-sync-patterns/) | Implicit host-device synchronization in PyTorch | knowledge check | ★ | L1 | written |
| [4.4](4.4-pageable-vs-pinned-copies/) | Pageable versus pinned cudaMemcpyAsync | knowledge check | ★ | L1 | written |
| [4.5](4.5-gpu-util-meaning/) | What nvidia-smi GPU-Util measures | knowledge check | ★ | L1 | written |
| [4.6](4.6-nvtx-cpu-side-ranges/) | NVTX ranges versus GPU kernel extent | knowledge check | ★★ | L1 | written |
| [4.7](4.7-occupancy-latency-hiding/) | Occupancy versus latency hiding | knowledge check | ★★ | L1 | computed |
| [4.8](4.8-occupancy-bytes-in-flight/) | Occupancy and bytes in flight | worked problem | ★★ | L1 | computed |
| [4.9](4.9-launch-bound-copy-cost/) | Launch-bound loop and copy cost | worked problem | ★★ | L1 | computed |
| [4.10](4.10-lab-trace-analysis/) | Lab 4: trace analysis of a training step | hands-on lab | ★★ | L1 | lab |
| [4.11](4.11-trace-matmul-end-to-end/) | Trace an operation end to end | outline-mandated | ★ | L1 | computed |
| [4.12](4.12-bottleneck-classes-from-trace/) | Identify the bottleneck class from a trace | outline-mandated | ★★ | L1 | computed |
| [4.13](4.13-waves-layout-intensity/) | Batch size and data layout | outline-mandated | ★★ | L1 | computed |
| [4.14](4.14-p99-allocator-churn/) | p99 tripled after a release | troubleshooting case | ★★★ | L1 | written |
| [4.15](4.15-input-step-overhead-design/) | Input and step-overhead strategy for HX8 | design challenge | ★★★ | L1 | computed |
| [4.16](4.16-evidence-labels-worked-example/) | Evidence labels in the worked example | reflection | ★ | L1 | written |
| [4.17](4.17-gap-classifier-calibration/) | Calibrating the gap classifier | reflection | ★ | L1 | written |
| [4.18](4.18-single-gpu-trace-limits/) | What a single-GPU trace cannot show | reflection | ★★ | L1 | written |
| [4.19](4.19-prioritization-by-cost/) | Prioritize by cost, not interest | reflection | ★ | L1 | written |

Exercise count: 19
