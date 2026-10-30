# Capstone H Starter Kit — Serving Model and Simulator

## 1. Goal and the real-world task it mirrors

Before an inference team buys hardware or reshapes a fabric for disaggregated serving, someone
builds exactly this: a closed-form capacity model, a simulator to check it against queueing
effects, and a short list of numbers that decide the architecture. `starter/serve.py` is your
model; `sim/serving_sim.py` (given) is the simulator.

## 2. Tier and realism boundary

**Tier L1.** Functions you write produce `[MODELED]` numbers; simulator outputs are `[SIMULATED]`.
Read the simulator's module docstring and quote its "does NOT capture" list in your report. The
dataset is synthetic and seeded (the generator is an instructor copy only). Two accelerator rows
(`compute-dense-class`, `hbm-rich-class`) are hypothetical teaching profiles.

## 3. Setup

```bash
cd capstones/capstone-h-disaggregated-llm-serving/starter-kit
python -m pip install -r ../../../requirements.txt     # numpy, pandas, pyyaml
python check.py                                        # 1/11 PASS at the start
```

## 4. Using the simulator

```python
import sys; sys.path.insert(0, ".")                      # run from starter-kit/
import pandas as pd
from sim import serving_sim as sim
trace = pd.read_csv("data/trace.csv").to_dict("records")
dis = {"kind": "disaggregated", "prefill": 5, "decode": 2,
       "link_GBps": 360.0, "link_overhead_s": 5e-5, "layer_pipelined": True}
col = {"kind": "colocated", "instances": 7, "chunk_tokens": None}   # or 512 for chunked prefill
res = sim.run(trace, dis, admission=None)                # admission: callable(req, state) -> "admit"/"reject" (both modes)
# add "util_window_s": 115.0 to an arch to get util["prefill_window"] over [0, 115 s]
print(sim.summarize(res), res.util)
```

Per-request records carry `ttft_s`, `tpot_s`, `end_s`, `status` and (disaggregated) `kv_exposed_s`.
`summarize()` reports TTFT p50/p95 for prompts ≤ 4,096 tokens, long-prompt TTFT p95, TPOT p50/p95
(per-request mean), ITL p50/p95/p99 (per-token gaps), the second-token gap p95/max (disaggregated),
output tokens/s and the rejection rate. Pass a `hw_prefill` / `hw_decode` (or `hw`) dict from
`serve.hw_profile()` to try other accelerator classes.

## 5. The dataset

| File | Contents |
|---|---|
| `data/trace.csv` | 10,394 requests over 300 s: Poisson arrivals at 30 req/s with a 2.5× burst; prompt and output lengths with a long tail |
| `data/hardware.csv` | Accelerator profiles: H100-class (ORION) and two hypothetical classes, with `[ILLUSTRATIVE]` prices |
| `data/links.csv` | KV transport profiles (line rate, unit, NIC count, efficiency, per-transfer overhead) |
| `data/qos_proposal.yaml` | The Fabric team's proposed QoS mapping for KV traffic |
| `data/slo.yaml`, `data/config.yaml` | SLOs, target rate, utilisation cap, candidate deployments |

## 6. Tasks

| Task | Function(s) | Acceptance criterion | Points |
|---|---|---|---|
| **T1** KV size | `kv_cache_bytes` | 327,680 B/token from model dimensions | 6 |
| **T2** Links | `link_capacity` | Achievable GB/s per instance; implausible profiles rejected with a reason | 10 |
| **T3** Roofline and transfer | `prefill_time_s`, `decode_step_time_s`, `kv_capacity_tokens`, `kv_transfer_exposed_s` | Match the documented formulas | 16 |
| **T4** Capacity and bottleneck | `size_pools`, `utilizations` | Pool sizes, decode batch and KV bandwidth; utilisation of prefill, decode, KV egress *and decode-side fan-in*; bottleneck at 30 req/s (and when it moves to the network); model within 5 % of simulation over the same window | 20 |
| **T5** Admission control | `admission_policy` | With 5P2D over RDMA: TTFT p95 ≤ 0.8 s, long TTFT p95 ≤ 3 s, TPOT p95 ≤ 50 ms, ITL p99 ≤ 100 ms, second-token gap p95 ≤ 100 ms, ≤ 10 % rejected | 18 |
| **T6** Speculative decoding | `speculative_gain`, `best_draft_length`, `speculative_gain_at_batch` | Leviathan et al. expectation and best draft length; batch-aware speedup at the operating point (verification turns compute-bound) | 10 |
| **T7** QoS audit | `audit_qos` | All findings on the proposal; a corrected design passes | 12 |
| **T8** Cost | `cost_per_million_tokens` | USD per million output tokens | 8 |
| | | **Total** | **100** |

Then use the functions and the simulator for the design artifacts: compare colocated (with and
without chunked prefill) against disaggregated at the target load *and* at low load; compare RDMA
and TCP by the distribution of `kv_exposed_s` with and without layer pipelining; try
heterogeneous pools.

## 7. Running the checker

```bash
python check.py        # ≈ 4 s; PASS/FAIL/TODO/SKIP per check; exit 0 only when all pass or skip
```

The first check verifies dataset integrity and runs only in the instructor copy (`SKIP` in the
student release, counted as passed).

## 8. L2/L3 extension

> **Safety:** Dedicated lab only. Bandwidth floods and QoS changes on a shared fabric can pause or
> slow other tenants' traffic.

**L2 — calibrate the roofline on one GPU host.** Run a supported open model on a supported serving
stack (for example vLLM or SGLang; use their own benchmark tooling and documentation for flags).
Measure prefill latency for prompt lengths 256–8,192 with output length 1, and decode step time
for batch 1–256 at fixed context. Fit `mfu_prefill`, `hbm_eff` and `step_overhead_s`, then rerun
the capacity model with the measured values (≥ 5 repetitions per point, report median and p95).

**L3 — measure the KV path on two RDMA nodes, one rail at a time.**

```bash
ulimit -l unlimited                                   # locked memory for RDMA registration (also in Slurm/containers)
lsmod | grep nvidia_peermem                           # one GPUDirect RDMA mechanism (DMA-BUF is another)
sudo lspci -vvv | grep -i ACSCtl                      # ACS on PCIe switch ports above GPU and NIC
ibv_devinfo -d mlx5_3 | grep -E 'state|active_mtu'    # RDMA path MTU (4096 expected on ORION)
# GPU memory to GPU memory over rail 3 (perftest built with CUDA support)
ib_write_bw -d mlx5_3 --use_cuda=3 --report_gbits                    # server, node A
ib_write_bw -d mlx5_3 --use_cuda=3 --report_gbits <nodeA_rail3_ip>   # client, node B
# TCP baseline over the frontend
iperf3 -s                                             # node A
iperf3 -c <nodeA_frontend_ip> -P 8 -t 30              # node B
```

Record per rail: message size, achieved Gb/s (median of ≥ 5 runs), CPU utilisation for TCP, and
whether GDR was actually used (a `/GDRDMA` channel suffix in NCCL logs if you also run NCCL tests).
If your serving stack supports disaggregated prefill, measure TTFT, second-token latency and TPOT
for 2k and 32k prompts with KV over RDMA and over TCP.

Record (copy `manifest.yaml`, `tier: L3`, `evidence_class: MEASURED`): GPU, driver, CUDA, NIC
firmware, RDMA stack, perftest and iperf3 versions, path MTU, host MTU, switch QoS configuration,
serving stack and version, model and precision, repetitions and warm-up policy.

## 9. Files

```text
starter-kit/
├── README.md  manifest.yaml  check.py
├── sim/serving_sim.py     given simulator
├── data/                  dataset (do not edit)
└── starter/serve.py       implement here
```
