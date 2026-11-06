# Single-Machine Hands-On Labs: Standard

Each chapter's Level 1 lab analyses recorded data. A **hands-on lab** is different: the reader runs
real software on one Linux machine and measures what happens. Examples are Soft-RoCE verbs, a
containerlab BGP fabric, `tc` ECN marking, a kind cluster with Kueue, and vLLM on a laptop GPU. This
document is the contract every hands-on lab follows.

## 1. Platform

| Item | Requirement |
|---|---|
| OS | Linux. Tested on **WSL2 Ubuntu 24.04** (kernel 6.18.54.1, plus a Soft-RoCE build for Ch 8; see §6). Native Ubuntu 22.04/24.04 is expected to work. |
| GPU | Optional per lab. Tested on an **NVIDIA RTX 4060 Laptop GPU (8 GB)**. Labs that need a GPU say so and size every workload for 8 GB. |
| Docker | Needed only by the labs that say so (containerlab, kind, Prometheus). |
| Memory | Fits in 7 GB of WSL memory. No lab assumes more than one GPU or more than one host. |
| Cost | Free. No cloud account. Downloads happen only in `setup.sh` and are pinned to exact versions. |

## 2. Layout

```text
book/<part>/chNN-*/lab/handson/
  README.md      the lab text (see §3)
  setup.sh       idempotent install of everything the lab needs; pinned versions; prints them
  run.sh         runs the whole lab unattended and writes results/<run-id>/ (used to produce the evidence)
  teardown.sh    removes everything the lab created (namespaces, qdiscs, containers, clusters, rxe links)
  check.py       python check.py results/<run-id>: validates a results directory (the reader's or ours)
  <helpers>      small scripts the steps call (Python 3.12+ standard library, plus what setup.sh installs)
  results/wsl2-rtx4060-laptop/   committed evidence from the reference machine (see §4)
```

Shared helpers live in `scripts/handson/`:

- `common.sh`: `need_root`, `need_gpu`, `need_docker`, the locks (`with_gpu_lock`, `with_docker_lock`) and `env_manifest`.
- `venv.sh`: the shared Python virtual environment at `~/.venvs/ai-infra-handson` with pinned PyTorch.

`scripts/handson.py list|run|check <chNN>` drives a lab from the repo root. On Windows it runs the lab
inside WSL.

## 3. README structure

1. **What you will do**: the real-world task, in two or three sentences.
2. **What is real here, and what is not**: what is measured on real software and hardware, and what
   one machine cannot show (scale, real switch ASICs, multi-node behaviour). It points to the
   chapter's Level 3 extension for the rest.
3. **Requirements**: GPU yes or no, Docker yes or no, root yes or no, disk, RAM, time.
4. **Safety**: what the lab changes on the host. Labs touch only network namespaces, veth pairs,
   their own containers and their own processes. Never the host's real interfaces, routes or GPU
   clocks.
5. **Setup**.
6. **Steps**: numbered. Each step gives the commands, what to look for, and one question to answer
   in `results/<run-id>/answers.md`.
7. **Check your results**: `python check.py results/<run-id>`.
8. **Reference results**: what the reference machine measured, with a link to the evidence bundle.
   Results on other hardware will differ; the check tests physical sense, not equality.
9. **Clean up**.
10. **Connect to the chapter**: the sections this lab makes concrete.

## 4. Evidence

`run.sh` writes `results/<run-id>/` containing:

- `environment.json`: OS, kernel, CPU, memory, GPU, driver, CUDA, tool versions and the time.
- the **raw outputs** of every measured step, unedited;
- `summary.json`: the numbers the lab reports;
- `report.md`: a short human-readable result, every number labelled `[MEASURED]` with the step that
  produced it.

The reference run goes in `results/wsl2-rtx4060-laptop/` and is committed. Never edit raw outputs. If
a run is wrong, fix the lab and re-run it.

`check.py` exits 0 only if the bundle is complete and physically sensible. Examples: an ECN-enabled
queue marks packets and a drop-tail one doesn't; prefix caching lowers time to first token on
repeated prompts; a `RESET` QP refuses traffic. It prints PASS/FAIL lines in the style of the Level 1
checkers, and it must give a useful FAIL message on an incomplete or implausible bundle.

## 5. Concurrency and safety rules for building the labs

- **GPU:** wrap every GPU-using command in `with_gpu_lock` (flock on `/tmp/handson-gpu.lock`). One
  GPU job at a time; the 8 GB card is shared.
- **Docker:** wrap cluster or fabric bring-up and tear-down in `with_docker_lock`.
- **Names:** each lab prefixes its namespaces, containers, clusters and rxe devices with `chNN`
  (e.g. `ch09-sw`, `kind-ch17`), so labs never collide and teardown is exact.
- `teardown.sh` must leave the machine as it found it. `run.sh` calls it at the end, even after a
  failure (`trap`).

## 6. The Soft-RoCE kernel (Ch 8)

The stock WSL2 kernel does not include `CONFIG_RDMA_RXE`. The reference machine runs a custom build
of `microsoft/WSL2-Linux-Kernel` at tag `linux-msft-wsl-6.18.54.1`. It uses the running kernel's
config plus `INFINIBAND`, `INFINIBAND_USER_ACCESS`, `INFINIBAND_ADDR_TRANS` and `RDMA_RXE`, all built
in, and is selected with `kernel=` in `%UserProfile%\.wslconfig`. `book/.../ch08-*/lab/handson/README.md`
gives the steps. Native Ubuntu kernels include `rdma_rxe` as a module (`modprobe rdma_rxe`).

## 7. Lab catalogue

R = needs root, G = needs the GPU, D = needs Docker. The wave is the build order: wave A starts once
the Soft-RoCE kernel is installed (installing it stops WSL); wave B needs Docker running.

| Ch | Lab | You do and measure | Needs | Wave |
|---|---|---|---|---|
| 1 | Your GPU against its ceilings | Train a small transformer step; measure tokens/s, achieved FLOP/s and MFU against the clock-adjusted peak; classify the step as compute- or memory-bound | G | A |
| 2 | Power, clocks and throttling | Drive the GPU through idle, memory-bound and compute-bound phases; record power, SM clock, temperature and clock-event reasons at 100 ms; find where the power limit binds | G | A |
| 3 | Host diagnostics | CPU pinning with `taskset`, pinned vs pageable host memory, `ulimit -l`, page-cache effects on reads, `dmesg` and `/proc` signals, the chapter's safe first-ten-minutes collector run on this host | R | A |
| 4 | Profile a training step | `torch.profiler` (and Nsight Systems if installed) on a step with a hidden host sync; find it in the trace, remove it, re-measure; try CUDA Graphs | G | A |
| 5 | Host topology from the inside | `nvidia-smi topo -m` and `-q` (PCIe gen and width, current vs max), measured H2D/D2H bandwidth against the link's theoretical rate, and what changes under load | G | A |
| 6 | Benchmark it properly | The chapter's protocol on a real GPU: warm-up, interleaved A/B, A/A noise floor, clock telemetry, permutation test and bootstrap CI; an empirical roofline from a GEMM and a copy | G | A |
| 7 | A BGP leaf-spine on your laptop | containerlab with FRR: 2 spines, 4 leaves, eBGP unnumbered or /31s per Ch 7, ECMP across spines, BFD; fail a link, measure reconvergence and flow loss | D, R | B |
| 8 | Real RDMA verbs with Soft-RoCE | Two network namespaces joined by a veth pair, an rxe device on each; `rdma link`, `ibv_devinfo`, the GID table, `ib_write_bw`/`ib_read_lat` across them; the effect of MTU; a QP that won't connect, diagnosed | R | A |
| 9 | ECN and incast with `tc` | Namespaces and a bridge with a bottleneck qdisc; an N:1 incast with iperf3; drop-tail vs RED with ECN marking; measure marks, drops, queue delay and goodput | R | A |
| 11 | Multi-process training | `torchrun` DDP across processes (gloo on CPU; the GPU where possible); measure step time vs rank count, gradient-bucket effects, checkpoint and restart after killing a rank | G | A |
| 12 | Collectives you can measure | `torch.distributed` all-reduce, all-gather and reduce-scatter across processes; fit α–β from message-size sweeps; ring vs tree where the backend allows; compare with the chapter's model | G | A |
| 13 | Moving data to the GPU | Pinned vs pageable copies, async copies overlapped with compute on streams, DataLoader worker and prefetch settings; find the configuration that keeps the GPU busy | G | A |
| 14 | Storage and checkpoints | `fio` sequential and random reads at several queue depths on local disk; checkpoint save and load time and size for a model; the page cache's effect on "storage" benchmarks | R, G | A |
| 15 | Serve an LLM | vLLM on the GPU with a small instruct model; a load generator measuring TTFT, ITL and throughput vs concurrency; prefix caching on and off; KV-cache usage from `/metrics` | G | A |
| 16 | Accept this node | A node acceptance suite against this machine: GPU stress with numerical checks, memory and PCIe checks, NIC and disk checks; a PASS/WARN/FAIL report in the chapter's format | G | A |
| 17 | Scheduling with Kueue | kind cluster, extended GPU resources on fake nodes, Kueue ClusterQueues with quotas, gang admission, preemption by priority; watch a job wait, then run | D | B |
| 18 | Observe it | Prometheus, Grafana and a GPU exporter in Docker; scrape this GPU; write an SLO and multi-window burn-rate alerts; inject load and watch the alert fire and clear | D, G | B |
| 19 | Lock down a cluster | kind with Pod Security Admission, RBAC, NetworkPolicy (Calico); show a privileged pod and a device-injection attempt rejected; fault injection on a training job and recovery from checkpoint | D | B |
| 20 | Change it safely | Ansible against the Ch 7 containerlab fabric: idempotent config, dry-run diff, canary on one leaf with automatic rollback when a health check fails | D, R | B |
| 21 | Performance per watt | Run a fixed workload while recording power; compute energy per unit of work and cost per useful GPU-hour from your own measurements; where clocks can be locked, compare settings | G | A |
| 22 | Find the bottleneck | A training loop with injected bottlenecks (dataloader stall, CPU contention, host sync, network delay via `tc`); diagnose each from evidence, fix it, and validate with an A/B test | G, R | A |
| 23 | ORION-mini | Integration: a training job and an inference service on this machine, observed by Prometheus; run a design review with measured evidence | D, G | B |

No hands-on lab: **Ch 10** (optics and physical layer, where one machine has no optics to measure) and
**Ch 24** (careers). Both keep their Level 1 labs.
