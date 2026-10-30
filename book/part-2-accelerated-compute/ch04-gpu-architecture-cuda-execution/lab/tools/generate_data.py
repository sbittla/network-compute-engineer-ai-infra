#!/usr/bin/env python3
"""Generate the synthetic profiler capture used by the Chapter 4 lab.

The output imitates the tables you get from an Nsight Systems capture exported to CSV
(GPU activity trace, CUDA API trace, NVTX ranges) for two training steps of a
single-GPU fine-tuning job on ORION node HX8 GPU0. It is produced by a small
discrete-event model of one CPU launch thread and two CUDA streams; it is
[SIMULATED] data, not a real capture.

All times are integer nanoseconds. Regenerating with the same seed produces
byte-identical files.

Usage:
    python tools/generate_data.py            # writes into ../data
    python tools/generate_data.py --out DIR
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

SEED = 4
COMPUTE_STREAM = 7
COPY_STREAM = 13
T0_NS = 1_000_000_000  # capture-relative origin, 1 s

# Model dimensions [ILLUSTRATIVE]: 12-layer transformer, hidden 2048, 8192 tokens per step.
LAYERS = 12
HIDDEN = 2048
TOKENS = 8192

DEVICE = {
    "name": "H100-SXM-class (ORION HX8 GPU0)",
    "evidence": "VENDOR-SPEC, 2026-10 (compute capability 9.0 limits; verify against the CUDA C++ Programming Guide)",
    "compute_capability": "9.0",
    "sm_count": 132,
    "warp_size": 32,
    "max_threads_per_sm": 2048,
    "max_warps_per_sm": 64,
    "max_blocks_per_sm": 32,
    "regs_per_sm": 65536,
    "max_regs_per_thread": 255,
    "reg_alloc_unit_per_warp": 256,
    "warp_alloc_granularity": 4,
    "smem_per_sm_bytes": 233472,
    "max_smem_per_block_bytes": 232448,
    "smem_reserved_per_block_bytes": 1024,
    "peak_bf16_dense_flops": 989e12,
    "hbm_bytes_per_s": 3.35e12,
    "pcie_gen5_x16_bytes_per_s_per_dir_theoretical": 63e9,
}


class Sim:
    """Tiny discrete-event model: one CPU thread issuing work to two streams."""

    def __init__(self, rng: np.random.Generator) -> None:
        self.rng = rng
        self.cpu = T0_NS
        self.ready = {COMPUTE_STREAM: T0_NS, COPY_STREAM: T0_NS}
        self.corr = 0
        self.gpu: list[dict] = []
        self.api: list[dict] = []
        self.nvtx: list[dict] = []
        self.gid = 0

    # -- helpers -----------------------------------------------------------------
    def _n(self, mean: float, sd: float, lo: float) -> int:
        return int(max(lo, self.rng.normal(mean, sd)))

    def _api(self, name: str, start: int, end: int) -> int:
        self.corr += 1
        self.api.append({"correlation_id": self.corr, "name": name, "start_ns": start,
                         "end_ns": end, "thread_id": 41817})
        return self.corr

    def _gpu(self, **row) -> None:
        self.gid += 1
        base = {"id": self.gid, "kind": "", "name": "", "stream": 0, "start_ns": 0, "end_ns": 0,
                "correlation_id": 0, "copy_kind": "", "src_mem": "", "dst_mem": "", "bytes": 0,
                "grid_x": 0, "block_x": 0, "regs_per_thread": 0, "smem_per_block_bytes": 0,
                "flop": 0, "dram_bytes": 0}
        base.update(row)
        self.gpu.append(base)

    def python_overhead(self, mean_ns: float) -> None:
        self.cpu += self._n(mean_ns, mean_ns * 0.15, mean_ns * 0.5)

    # -- CUDA operations -------------------------------------------------------------
    def launch(self, name: str, dur_ns: int, *, block: int, grid: int, regs: int, smem: int,
               flop: float = 0.0, dram_bytes: float = 0.0, stream: int = COMPUTE_STREAM,
               overhead_ns: float = 22_000) -> None:
        a_start = self.cpu
        a_end = a_start + self._n(4_800, 500, 3_200)
        corr = self._api("cudaLaunchKernel", a_start, a_end)
        g_start = max(self.ready[stream] + self._n(1_100, 150, 700), a_start + self._n(4_200, 300, 3_000))
        g_end = g_start + int(dur_ns)
        self.ready[stream] = g_end
        self._gpu(kind="kernel", name=name, stream=stream, start_ns=g_start, end_ns=g_end,
                  correlation_id=corr, grid_x=grid, block_x=block, regs_per_thread=regs,
                  smem_per_block_bytes=smem, flop=int(flop), dram_bytes=int(dram_bytes))
        self.cpu = a_end
        self.python_overhead(overhead_ns)

    def memcpy(self, nbytes: int, copy_kind: str, mem: str, gbps_mean: float, *,
               stream: int = COMPUTE_STREAM, overhead_ns: float = 30_000) -> None:
        """cudaMemcpyAsync. Pageable source/destination makes the call block the host."""
        a_start = self.cpu
        g_start = max(self.ready[stream] + self._n(1_200, 150, 700), a_start + self._n(6_000, 600, 4_000))
        bw = max(1e-3, self.rng.normal(gbps_mean, gbps_mean * 0.02)) * 1e9
        dur = int(nbytes / bw * 1e9) + 1_500  # fixed per-copy cost
        g_end = g_start + dur
        self.ready[stream] = g_end
        if mem == "pageable":
            a_end = g_end + self._n(5_000, 500, 3_000)   # host blocked until staged copy completes
        else:
            a_end = a_start + self._n(7_500, 600, 5_000)  # async: returns after enqueue
        corr = self._api("cudaMemcpyAsync", a_start, a_end)
        src, dst = (mem, "device") if copy_kind == "HtoD" else ("device", mem)
        self._gpu(kind="memcpy", name=f"[CUDA memcpy {'Host-to-Device' if copy_kind == 'HtoD' else 'Device-to-Host'}]",
                  stream=stream, start_ns=g_start, end_ns=g_end, correlation_id=corr,
                  copy_kind=copy_kind, src_mem=src, dst_mem=dst, bytes=nbytes)
        self.cpu = a_end
        self.python_overhead(overhead_ns)

    def host_callback_wait(self, duration_ns: int) -> None:
        """Planted cross-stream dependency: the side stream waits for the compute stream (event e1), runs a
        host function (cudaLaunchHostFunc) for `duration_ns`, records e2, and the compute stream waits on e2.
        Already-queued compute work cannot start until the callback returns. Consumes no random numbers."""
        cpu = self.cpu
        for name in ("cudaEventRecord", "cudaStreamWaitEvent", "cudaLaunchHostFunc", "cudaEventRecord",
                     "cudaStreamWaitEvent"):
            self._api(name, cpu, cpu + 2_000)
            cpu += 2_500
        cb_start = max(self.ready[COMPUTE_STREAM], cpu) + 3_000
        cb_end = cb_start + duration_ns
        self.ready[COPY_STREAM] = max(self.ready[COPY_STREAM], cb_end)
        self.ready[COMPUTE_STREAM] = cb_end
        self.cpu = cpu

    def stream_sync(self, stream: int = COMPUTE_STREAM, name: str = "cudaStreamSynchronize") -> None:
        a_start = self.cpu
        target = max(self.ready.values()) if name == "cudaDeviceSynchronize" else self.ready[stream]
        a_end = max(a_start, target) + self._n(4_000, 400, 2_500)
        self._api(name, a_start, a_end)
        self.cpu = a_end

    def item(self, overhead_after_ns: float) -> None:
        """tensor.item(): 4-byte D2H copy + stream sync + Python work before next launch."""
        self.memcpy(4, "DtoH", "pageable", 0.004, overhead_ns=0)
        self.stream_sync()
        self.python_overhead(overhead_after_ns)

    def range_push(self, name: str, level: int) -> dict:
        r = {"name": name, "start_ns": self.cpu, "end_ns": 0, "level": level}
        self.nvtx.append(r)
        return r

    def range_pop(self, r: dict) -> None:
        r["end_ns"] = self.cpu


def gemm_time(flop: float, rng: np.random.Generator) -> int:
    achieved = rng.normal(0.62, 0.02) * DEVICE["peak_bf16_dense_flops"]
    return int(flop / achieved * 1e9)


def mem_time(nbytes: float, frac: float, rng: np.random.Generator) -> int:
    achieved = rng.normal(frac, frac * 0.03) * DEVICE["hbm_bytes_per_s"]
    return int(nbytes / achieved * 1e9) + 2_000


GEMM_CFG = dict(block=384, regs=168, smem=213_000)        # 1 CTA/SM by design (warp-specialised GEMM)
FLASH_FWD_CFG = dict(block=128, regs=255, smem=163_840)
FLASH_BWD_CFG = dict(block=256, regs=255, smem=196_608)
ELEM_CFG = dict(block=256, regs=32, smem=0)
LN_FWD_CFG = dict(block=512, regs=40, smem=8_192)
LN_BWD_CFG = dict(block=256, regs=168, smem=16_384)       # planted: register-limited, memory-bound
TINY_CFG = dict(block=512, regs=24, smem=0)
ADAM_CFG = dict(block=512, regs=40, smem=0)


def act_bytes(n_tensors: float) -> float:
    return n_tensors * TOKENS * HIDDEN * 2  # BF16 activations


def simulate_step(sim: Sim, step: int) -> None:
    rng = sim.rng
    h, t = HIDDEN, TOKENS
    step_r = sim.range_push(f"train_step_{step}", 0)

    # --- data: two host-to-device copies from PAGEABLE memory (planted) ----------
    r = sim.range_push("h2d_batch", 1)
    sim.memcpy(96 * 1024 * 1024, "HtoD", "pageable", 11.8)  # pixels, fp16
    sim.memcpy(4 * 1024 * 1024, "HtoD", "pageable", 9.5)    # labels / masks
    sim.range_pop(r)

    # --- forward -------------------------------------------------------------------
    r = sim.range_push("forward", 1)
    gemms = {"qkv": 3 * h, "attn_out": h, "mlp_up": 4 * h, "mlp_down": 4 * h}
    for _layer in range(LAYERS):
        if _layer == 6:
            # planted: a monitoring library's activation-statistics callback (host function on a side stream);
            # the compute stream waits on it, so queued forward kernels stall with the GPU idle
            sim.host_callback_wait(310_000)
        sim.launch("layer_norm_fwd_kernel", mem_time(act_bytes(2.2), 0.80, rng), grid=t // 4,
                   dram_bytes=act_bytes(2.2), **LN_FWD_CFG)
        f = 2 * t * h * gemms["qkv"]
        sim.launch("sm90_xmma_gemm_bf16bf16_bf16f32_tn_128x256_cublas", gemm_time(f, rng), grid=132, flop=f,
                   dram_bytes=act_bytes(4) + 2 * h * 3 * h, **GEMM_CFG)
        f = 4 * t * 2048 * h / 2 * 1.0
        sim.launch("flash_fwd_kernel", int(f / (rng.normal(0.50, 0.02) * DEVICE["peak_bf16_dense_flops"]) * 1e9),
                   grid=4 * 16 * 16, flop=f, dram_bytes=act_bytes(4), **FLASH_FWD_CFG)
        f = 2 * t * h * gemms["attn_out"]
        sim.launch("sm90_xmma_gemm_bf16bf16_bf16f32_tn_128x128_cublas", gemm_time(f, rng), grid=132, flop=f,
                   dram_bytes=act_bytes(2) + 2 * h * h, **GEMM_CFG)
        f = 2 * t * h * gemms["mlp_up"]
        sim.launch("sm90_xmma_gemm_bf16bf16_bf16f32_tn_128x256_cublas", gemm_time(f, rng), grid=132, flop=f,
                   dram_bytes=act_bytes(5) + 2 * h * 4 * h, **GEMM_CFG)
        sim.launch("vectorized_elementwise_kernel<GeluFunctor>", mem_time(act_bytes(8), 0.85, rng), grid=t * 4 * h // 1024,
                   dram_bytes=act_bytes(8), **ELEM_CFG)
        f = 2 * t * h * gemms["mlp_down"]
        sim.launch("sm90_xmma_gemm_bf16bf16_bf16f32_tn_128x256_cublas", gemm_time(f, rng), grid=132, flop=f,
                   dram_bytes=act_bytes(5) + 2 * h * 4 * h, **GEMM_CFG)
    sim.launch("cross_entropy_fwd_kernel", mem_time(t * 32000 * 2, 0.7, rng), grid=t, dram_bytes=t * 32000 * 2, **ELEM_CFG)
    sim.range_pop(r)

    # loss logging: loss.item() every step (one sync per step)
    r = sim.range_push("log_loss", 1)
    sim.item(overhead_after_ns=180_000)
    sim.range_pop(r)

    # --- backward ------------------------------------------------------------------
    r = sim.range_push("backward", 1)
    # prefetch next step's distillation targets on a side stream from PINNED memory (good practice)
    sim.memcpy(64 * 1024 * 1024, "HtoD", "pinned", 49.0, stream=COPY_STREAM)
    for layer in range(LAYERS):
        lr = sim.range_push(f"bwd_layer_{LAYERS - 1 - layer}", 2)
        for name, n in (("mlp_down", 4 * h), ("mlp_up", 4 * h)):
            for _which in ("dgrad", "wgrad"):
                f = 2 * t * h * n
                sim.launch("sm90_xmma_gemm_bf16bf16_bf16f32_nt_128x256_cublas", gemm_time(f, rng), grid=132, flop=f,
                           dram_bytes=act_bytes(5) + 2 * h * n, **GEMM_CFG)
            if name == "mlp_up":
                sim.launch("vectorized_elementwise_kernel<GeluBackwardFunctor>", mem_time(act_bytes(12), 0.85, rng),
                           grid=t * 4 * h // 1024, dram_bytes=act_bytes(12), **ELEM_CFG)
        f = 2.5 * 4 * t * 2048 * h / 2
        sim.launch("flash_bwd_dq_dk_dv_loop_kernel", int(f / (rng.normal(0.45, 0.02) * DEVICE["peak_bf16_dense_flops"]) * 1e9),
                   grid=4 * 16 * 16, flop=f, dram_bytes=act_bytes(7), **FLASH_BWD_CFG)
        for _which in ("dgrad", "wgrad"):
            f = 2 * t * h * 4 * h  # qkv (3h) + out (h)
            sim.launch("sm90_xmma_gemm_bf16bf16_bf16f32_nt_128x256_cublas", gemm_time(f, rng), grid=132, flop=f,
                       dram_bytes=act_bytes(6) + 2 * h * 4 * h, **GEMM_CFG)
        ln_bytes = act_bytes(6)
        sim.launch("layernorm_bwd_fused_kernel", mem_time(ln_bytes, 0.22, rng), grid=t // 2,
                   dram_bytes=ln_bytes, **LN_BWD_CFG)
        sim.range_pop(lr)
        # planted: debug hook calls grad.norm().item() after every layer
        dr = sim.range_push("debug_grad_norm_hook", 2)
        sim.launch("reduce_kernel<NormTwoOps>", mem_time(2 * 12 * h * h, 0.6, rng), grid=264, dram_bytes=2 * 12 * h * h, **ELEM_CFG)
        sim.item(overhead_after_ns=float(rng.normal(360_000, 40_000)))
        sim.range_pop(dr)
    sim.range_pop(r)

    # --- optimizer: unfused per-tensor ops over many small tensors (planted) ---------
    r = sim.range_push("optimizer_step", 1)
    small_ops = ("MulFunctor", "AddFunctor", "AddcmulFunctor", "SqrtFunctor", "AddcdivFunctor")
    for _tensor in range(120):  # LayerNorm weights/biases and linear biases
        for op in small_ops:
            sim.launch(f"vectorized_elementwise_kernel<{op}>", int(rng.normal(2_600, 250)), grid=4,
                       dram_bytes=4 * 2048 * 4, overhead_ns=4_500, **TINY_CFG)
    n_big = 12 * 12 * h * h  # large weight matrices, fused multi-tensor Adam
    for _chunk in range(12):
        sim.launch("multi_tensor_apply_kernel<AdamFunctor>", mem_time(n_big / 12 * 16, 0.82, rng), grid=1320,
                   dram_bytes=n_big / 12 * 16, **ADAM_CFG)
    sim.range_pop(r)

    # step timing with a device-wide sync (planted: unnecessary for correctness)
    sim.stream_sync(name="cudaDeviceSynchronize")
    sim.python_overhead(60_000)
    sim.range_pop(step_r)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row[k] for k in fields})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    sim = Sim(np.random.default_rng(args.seed))
    for step in (41, 42):
        simulate_step(sim, step)

    sim.gpu.sort(key=lambda r: (r["start_ns"], r["id"]))
    write_csv(args.out / "gpu_trace.csv", sim.gpu,
              ["id", "kind", "name", "stream", "start_ns", "end_ns", "correlation_id", "copy_kind",
               "src_mem", "dst_mem", "bytes", "grid_x", "block_x", "regs_per_thread",
               "smem_per_block_bytes", "flop", "dram_bytes"])
    write_csv(args.out / "cuda_api_trace.csv", sim.api, ["correlation_id", "name", "start_ns", "end_ns", "thread_id"])
    write_csv(args.out / "nvtx_ranges.csv", sim.nvtx, ["name", "start_ns", "end_ns", "level"])
    with (args.out / "device.json").open("w", newline="\n", encoding="utf-8") as fh:
        json.dump(DEVICE, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"wrote {len(sim.gpu)} GPU activities, {len(sim.api)} API calls, {len(sim.nvtx)} NVTX ranges to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
