# Test results

Every chapter lab and capstone starter kit, with its exercises, tested by the package suite (`docker/harness/test_package.py`). Each package's full table is in its `lab/expected/` (capstones: `starter-kit/expected/`) folder; each exercise's own tests are in `exercises/<ID>/outputs/expected/test_results.md`.

**32/32 packages passed, 2,160 tests.**

| Package | Result | Tests | Failed | Skipped | Details |
|---|---|---|---|---|---|
| ch01 | PASS | 94 | 0 | 0 | [ch01](../book/part-1-foundations/ch01-ai-infrastructure-landscape/lab/expected/test_results.md) |
| ch02 | PASS | 94 | 0 | 0 | [ch02](../book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/lab/expected/test_results.md) |
| ch03 | PASS | 74 | 0 | 0 | [ch03](../book/part-1-foundations/ch03-linux-host-systems-diagnostics/lab/expected/test_results.md) |
| ch04 | PASS | 82 | 0 | 0 | [ch04](../book/part-2-accelerated-compute/ch04-gpu-architecture-cuda-execution/lab/expected/test_results.md) |
| ch05 | PASS | 90 | 0 | 0 | [ch05](../book/part-2-accelerated-compute/ch05-gpu-interconnects-host-topology/lab/expected/test_results.md) |
| ch06 | PASS | 86 | 0 | 0 | [ch06](../book/part-2-accelerated-compute/ch06-gpu-performance-engineering/lab/expected/test_results.md) |
| ch07 | PASS | 78 | 0 | 0 | [ch07](../book/part-3-networking/ch07-ethernet-datacenter-network-foundations/lab/expected/test_results.md) |
| ch08 | PASS | 86 | 0 | 0 | [ch08](../book/part-3-networking/ch08-rdma-rocev2-infiniband/lab/expected/test_results.md) |
| ch09 | PASS | 86 | 0 | 0 | [ch09](../book/part-3-networking/ch09-congestion-control-lossless-fabrics/lab/expected/test_results.md) |
| ch10 | PASS | 86 | 0 | 0 | [ch10](../book/part-3-networking/ch10-switches-optics-physical-layer/lab/expected/test_results.md) |
| ch11 | PASS | 86 | 0 | 0 | [ch11](../book/part-4-distributed-ai/ch11-distributed-training-architecture/lab/expected/test_results.md) |
| ch12 | PASS | 86 | 0 | 0 | [ch12](../book/part-4-distributed-ai/ch12-collective-communication-nccl/lab/expected/test_results.md) |
| ch13 | PASS | 78 | 0 | 0 | [ch13](../book/part-4-distributed-ai/ch13-gpu-data-movement/lab/expected/test_results.md) |
| ch14 | PASS | 86 | 0 | 0 | [ch14](../book/part-4-distributed-ai/ch14-storage-pipelines-checkpointing/lab/expected/test_results.md) |
| ch15 | PASS | 98 | 0 | 0 | [ch15](../book/part-4-distributed-ai/ch15-llm-inference-serving/lab/expected/test_results.md) |
| ch16 | PASS | 86 | 0 | 0 | [ch16](../book/part-5-production-operations/ch16-bare-metal-fleet-lifecycle/lab/expected/test_results.md) |
| ch17 | PASS | 86 | 0 | 0 | [ch17](../book/part-5-production-operations/ch17-kubernetes-slurm-scheduling/lab/expected/test_results.md) |
| ch18 | PASS | 86 | 0 | 0 | [ch18](../book/part-5-production-operations/ch18-observability-slos-incident-response/lab/expected/test_results.md) |
| ch19 | PASS | 98 | 0 | 0 | [ch19](../book/part-5-production-operations/ch19-reliability-security-multitenancy/lab/expected/test_results.md) |
| ch20 | PASS | 90 | 0 | 0 | [ch20](../book/part-5-production-operations/ch20-automation-safe-change/lab/expected/test_results.md) |
| ch21 | PASS | 86 | 0 | 0 | [ch21](../book/part-5-production-operations/ch21-capacity-power-economics/lab/expected/test_results.md) |
| ch22 | PASS | 86 | 0 | 0 | [ch22](../book/part-5-production-operations/ch22-cross-layer-performance-engineering/lab/expected/test_results.md) |
| ch23 | PASS | 86 | 0 | 0 | [ch23](../book/part-6-applied-engineering/ch23-capstone-production-ai-cluster/lab/expected/test_results.md) |
| ch24 | PASS | 86 | 0 | 0 | [ch24](../book/part-6-applied-engineering/ch24-career-paths-engineering-practice/lab/expected/test_results.md) |
| capstone-a | PASS | 10 | 0 | 5 | [capstone-a](../capstones/capstone-a-256-gpu-training-cluster/starter-kit/expected/test_results.md) |
| capstone-b | PASS | 10 | 0 | 5 | [capstone-b](../capstones/capstone-b-network-telemetry-troubleshooting/starter-kit/expected/test_results.md) |
| capstone-c | PASS | 10 | 0 | 5 | [capstone-c](../capstones/capstone-c-distributed-training-performance/starter-kit/expected/test_results.md) |
| capstone-d | PASS | 10 | 0 | 5 | [capstone-d](../capstones/capstone-d-llm-inference-platform/starter-kit/expected/test_results.md) |
| capstone-e | PASS | 10 | 0 | 5 | [capstone-e](../capstones/capstone-e-fleet-lifecycle-automation/starter-kit/expected/test_results.md) |
| capstone-f | PASS | 10 | 0 | 5 | [capstone-f](../capstones/capstone-f-reliability-game-day/starter-kit/expected/test_results.md) |
| capstone-g | PASS | 10 | 0 | 5 | [capstone-g](../capstones/capstone-g-fault-tolerant-512-node-training/starter-kit/expected/test_results.md) |
| capstone-h | PASS | 10 | 0 | 5 | [capstone-h](../capstones/capstone-h-disaggregated-llm-serving/starter-kit/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
