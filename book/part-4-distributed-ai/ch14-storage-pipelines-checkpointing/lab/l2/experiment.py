"""Ch 14 L2: checkpoint blocking vs completion time, save/restore throughput, and a restore test, on one GPU.

What it teaches (Sections 14.6-14.8; lab Part A ``strategy_timings`` and Part C ``validate_checkpoint``):
a synchronous checkpoint stalls training for the whole write, an asynchronous one stalls only for the
device-to-host snapshot, and the background persist still costs something (interference). A checkpoint
you cannot verify is not a checkpoint. This experiment (exercise 14.19):

1. Trains an MLP whose model + Adam state is >= 1 GB (full mode) on the GPU.
2. Times ``torch.distributed.checkpoint.save`` and ``async_save`` (one warm-up each, then >= 5 timed
   repetitions): blocking time (call -> return), completion time (call -> files written and fsync'd),
   step time before / during / after the background persist, and peak host staging memory (process RSS
   sampled every 2 ms; DCP stages into pinned host buffers).
3. Measures the snapshot path on its own (pinned D2H copy of the state, GB/s) and the restore path
   (``dcp.load`` after evicting the files from the page cache with ``posix_fadvise(DONTNEED)``).
4. Plugs the measured D2H and write rates into the lab's ``async_pfs`` strategy model and compares the
   predicted blocking and completion times with the measured ones.
5. Restore test: writes a SHA-256 manifest + COMMIT marker (the lab's halcyon-ckpt-v1 format) for the
   checkpoint, corrupts 4 KiB of one data file in a scratch *copy*, shows the lab's validator rejects the
   copy (and what ``dcp.load`` does with it), restores from the intact copy and compares the first-step
   loss with the value recorded at save.

CPU fallback: the same model (smaller) lives in host memory; ``save``/``async_save`` still run (staging
is a host-to-host copy), as do the throughput, interference and restore tests. The D2H/PCIe invariants
are skipped.

Not runnable here: the fio NVMe acceptance extension (needs fio and a raw NVMe device you may wipe; the
container has neither) and the L3 shared-PFS extension (needs 2+ GPU nodes and a parallel file system).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import statistics
import tempfile
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch14-l2",
    "title": "Lab 14 L2: checkpoint blocking vs completion time, save/restore throughput and restore test",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same DCP save/async_save/load benchmark, interference and restore test with the model in "
                     "host memory (staging is a host copy, not a PCIe D2H transfer); D2H/PCIe invariants skipped"),
}

PKG = Path(__file__).resolve().parents[2]
PCIE_GBPS_PER_LANE = {3: 0.985, 4: 1.969, 5: 3.938}
LOSS_RTOL = 1e-6          # FP32, same kernels, same batch: stated before running


def _load_lab_module():
    """Lab Part A/C code: the reference solution if present (instructor tree), else the learner's starter."""
    for path in (PKG / "solutions" / "lab" / "storage_lab.py", PKG / "lab" / "starter" / "storage_lab.py"):
        if path.is_file():
            spec = importlib.util.spec_from_file_location(f"storage_lab_{path.parent.name}", path)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                return mod, path.relative_to(PKG).as_posix()
            except Exception:
                continue
    return None, "none"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(ckpt: Path, step: int) -> None:
    """halcyon-ckpt-v1 manifest (lab Part C format) over every file DCP wrote, then the COMMIT marker."""
    files = sorted(p for p in ckpt.iterdir() if p.is_file() and p.name not in ("manifest.json", "COMMIT"))
    shards = [{"rank": i, "file": p.name, "bytes": p.stat().st_size, "sha256": _sha256(p)} for i, p in enumerate(files)]
    man = json.dumps({"format": "halcyon-ckpt-v1", "step": step, "world_size": len(shards), "shards": shards,
                      "note": "every DCP output file listed as a shard"}, sort_keys=True).encode()
    (ckpt / "manifest.json").write_bytes(man)
    (ckpt / "COMMIT").write_text(hashlib.sha256(man).hexdigest() + "\n", encoding="ascii")


def validate(ckpt: Path) -> tuple[list[str], str]:
    mod, src = _load_lab_module()
    if mod is not None:
        try:
            return list(mod.validate_checkpoint(ckpt)), src
        except NotImplementedError:
            pass
    # minimal checksum check when the lab module is not implemented yet
    man = json.loads((ckpt / "manifest.json").read_bytes())
    bad = [s for s in man["shards"] if _sha256(ckpt / s["file"]) != s["sha256"]]
    return (["CHECKSUM_MISMATCH"] if bad else []), "local sha256 check"


def fsync_dir_tree(d: Path) -> None:
    for p in d.rglob("*"):
        if p.is_file():
            fd = os.open(p, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)


def evict_page_cache(d: Path) -> bool:
    ok = hasattr(os, "posix_fadvise")
    for p in d.rglob("*"):
        if p.is_file() and ok:
            fd = os.open(p, os.O_RDONLY)
            try:
                os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
            finally:
                os.close(fd)
    return ok


def build(torch, device: str, width: int, depth: int, seed: int):
    torch.manual_seed(seed)
    layers = []
    for _ in range(depth):
        layers += [torch.nn.Linear(width, width), torch.nn.GELU()]
    model = torch.nn.Sequential(*layers).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    return model, opt


def train_step_on(torch, model, opt, x, y):
    loss = torch.nn.functional.mse_loss(model(x), y)
    loss.backward()
    opt.step()
    opt.zero_grad(set_to_none=True)
    return loss


def run(ctx) -> dict:
    torch = ctx.torch
    import torch.distributed as dist
    import torch.distributed.checkpoint as dcp
    from torch.distributed.checkpoint.state_dict import get_state_dict, set_state_dict
    import hwlab

    dev = ctx.device
    if ctx.is_gpu:
        width, depth = (1024, 8) if ctx.quick else (3072, 10)     # ~8.4 M / 94 M params -> 0.10 / 1.13 GB state
        batch = 512 if ctx.quick else 2048
    else:
        torch.set_num_threads(max(1, min(8, torch.get_num_threads())))
        width, depth = (1024, 4) if ctx.quick else (1024, 16)     # 4.2 M / 16.8 M params -> 50 / 200 MB state
        batch = 256
    reps = ctx.reps(5)
    steps_window = 5 if ctx.quick else 10

    tmp_root = Path(tempfile.mkdtemp(prefix="ch14-l2-"))
    store = dist.FileStore(str(tmp_root / "pgstore"), 1)
    dist.init_process_group("gloo", store=store, rank=0, world_size=1)   # async_save needs a CPU backend

    model, opt = build(torch, dev, width, depth, seed=0)
    g = torch.Generator(device="cpu").manual_seed(1)
    x = torch.randn(batch, width, generator=g).to(dev)
    y = torch.randn(batch, width, generator=g).to(dev)
    x_eval = torch.randn(batch, width, generator=g).to(dev)

    def train_step():
        loss = torch.nn.functional.mse_loss(model(x), y)
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)
        return loss

    def timed_step() -> float:
        ctx.sync()
        t0 = time.perf_counter()
        train_step()
        ctx.sync()
        return time.perf_counter() - t0

    for _ in range(5):                                            # creates Adam state, warms kernels
        train_step()
    ctx.sync()
    msd, osd = get_state_dict(model, opt)
    state = {"model": msd, "optim": osd}
    state_bytes = sum(t.numel() * t.element_size() for t in _tensors(state))
    n_params = sum(p.numel() for p in model.parameters())
    ctx.log(f"model {n_params / 1e6:.1f} M params, checkpointed state {state_bytes / 1e9:.3f} GB on {dev}")

    # --- synchronous save
    rows = []
    for i in range(1 + reps):
        d = tmp_root / f"sync_{i}"
        ctx.sync()
        t0 = time.perf_counter()
        dcp.save(state, checkpoint_id=str(d))
        t1 = time.perf_counter()
        if i == 0:   # the values the restore test must reproduce, recorded right at save time
            with torch.no_grad():
                rec_eval = float(torch.nn.functional.mse_loss(model(x_eval), y))
            rec_step = float(train_step())       # loss of the first step taken from the saved state
        rows.append({"api": "save", "rep": i, "warmup": i == 0, "blocking_s": t1 - t0, "completion_s": t1 - t0,
                     "bytes_on_disk": _dir_bytes(d)})
        if i:
            shutil.rmtree(d)
    keep = tmp_root / "sync_0"                                     # the warm-up save is kept for the restore tests

    def make_writer(d: Path, cached: bool):
        writer = dcp.FileSystemWriter(str(d), cache_staged_state_dict=cached)
        if cached and not getattr(writer, "cache_staged_state_dict", False):
            # torch 2.5.1: FileSystemWriter.__init__ never reaches BlockingAsyncStager.__init__, so the argument is
            # silently dropped (finding recorded in the notes). Set the stager's attributes directly.
            writer.cache_staged_state_dict, writer.state_dict_cache = True, None
            dropped_flag.append(True)
        return writer

    dropped_flag: list = []

    def one_async(d: Path, writer, step_during: bool = True) -> dict:
        """One async_save; captures what DCP's stager returned (bytes, pinned bytes, aliasing of live tensors)."""
        msd, osd = get_state_dict(model, opt)
        st = {"model": msd, "optim": osd}
        staged: list = []
        orig_stage = type(writer).stage.__get__(writer)
        writer.stage = lambda sd, _o=orig_stage: staged.append(_o(sd)) or staged[-1]   # inspect the staged copy
        ctx.sync()
        t0 = time.perf_counter()
        fut = dcp.async_save(st, checkpoint_id=str(d), storage_writer=writer)
        t1 = time.perf_counter()
        during = []
        while step_during and not fut.done():
            during.append(timed_step())
        fut.result()
        t2 = time.perf_counter()
        staged_t = list(_tensors(staged))
        live = {t.data_ptr() for t in _tensors(st)}
        out = {"blocking_s": t1 - t0, "completion_s": t2 - t0, "bytes_on_disk": _dir_bytes(d), "during": during,
               "staged_bytes": sum(t.numel() * t.element_size() for t in staged_t),
               "staged_pinned_bytes": sum(t.numel() * t.element_size() for t in staged_t if t.is_pinned()),
               "staged_aliasing_live_bytes": sum(t.numel() * t.element_size() for t in staged_t if t.data_ptr() in live)}
        return out

    # --- async save (default pageable staging, and cache_staged_state_dict=True: pinned, reused buffers),
    #     with step time before / during / after the background persist
    series = [("async_save", False)] + ([("async_save+cached_pinned", True)] if ctx.is_gpu else [])
    for api, cached in series:   # pinned host memory needs CUDA: the cached series is GPU-only
        writer = make_writer(tmp_root / f"{api}_0", cached)    # one writer per series: the pinned cache is per writer
        for i in range(1 + reps):
            d = tmp_root / f"{api}_{i}"
            before = [timed_step() for _ in range(steps_window)]
            r = one_async(d, writer)
            after = [timed_step() for _ in range(steps_window)]
            during = r.pop("during")
            rows.append({"api": api, "rep": i, "warmup": i == 0, **r,
                         "step_before_p50_s": statistics.median(before),
                         "step_during_p50_s": statistics.median(during) if during else None,
                         "steps_during": len(during), "step_after_p50_s": statistics.median(after)})
            shutil.rmtree(d)

    # --- consistency: is the checkpoint the state at the call, even though training continues during the persist?
    ref_sd = dict(zip(("model", "optim"), get_state_dict(model, opt)))
    # The reference copy lives in host memory: a third full copy of the state on the GPU (live model, reference,
    # restore target) does not fit a shared 8 GB laptop GPU, and the comparison does not need to run on the device.
    snap_ref = {k: t.detach().to("cpu", copy=True) for k, t in _flat(ref_sd).items() if hasattr(t, "shape")}
    d = tmp_root / "consistency"
    cons_run = one_async(d, make_writer(d, False))
    if ctx.is_gpu:
        torch.cuda.empty_cache()
    m3, o3 = build(torch, dev, width, depth, seed=5)
    train_step_on(torch, m3, o3, x, y)
    s3 = dict(zip(("model", "optim"), get_state_dict(m3, o3)))
    dcp.load(s3, checkpoint_id=str(d))
    loaded = {k: t for k, t in _flat(s3).items() if hasattr(t, "shape")}
    diff = [k for k, t in loaded.items() if not torch.equal(snap_ref[k], t.detach().cpu())]
    diff_data = [k for k in diff if loaded[k].numel() > 1]
    consistency = {"tensors_compared": len(loaded), "tensors_differing_from_call_time_state": len(diff),
                   "data_tensors_differing": len(diff_data), "scalar_tensors_differing": len(diff) - len(diff_data),
                   "differing_examples": diff[:4], "steps_during": len(cons_run["during"])}
    ctx.log(f"consistency: {len(diff)} of {len(loaded)} tensors in the async checkpoint differ from the call-time state "
            f"({len(diff_data)} data tensors, {len(diff) - len(diff_data)} scalars, e.g. {diff[:2]})")
    del snap_ref, ref_sd, m3, o3, s3, loaded
    shutil.rmtree(d)

    # --- snapshot path alone: copy the whole state into pinned (GPU) / plain (CPU) host buffers
    host = [torch.empty(t.shape, dtype=t.dtype, pin_memory=ctx.is_gpu) for t in _tensors(state)]

    def snapshot():
        for h, t in zip(host, _tensors(state)):
            h.copy_(t, non_blocking=ctx.is_gpu)
        ctx.sync()
    snap = ctx.bench(snapshot, warmup=1, reps=reps)
    del host
    snap_gbs = state_bytes / snap["median"] / 1e9
    ctx.log(f"snapshot copy p50 {snap['median']:.3f} s -> {snap_gbs:.2f} GB/s")

    for r in rows:
        ctx.log(f"{r['api']:25} rep {r['rep']} blocking {r['blocking_s']:.3f} s completion {r['completion_s']:.3f} s"
                + (f" steps during {r['steps_during']}" if "steps_during" in r else ""))

    # --- restore throughput: dcp.load into the live state, page cache evicted first
    load_rows = []
    for i in range(1 + reps):
        fsync_dir_tree(keep)
        evicted = evict_page_cache(keep)
        msd, osd = get_state_dict(model, opt)
        st = {"model": msd, "optim": osd}
        ctx.sync()
        t0 = time.perf_counter()
        dcp.load(st, checkpoint_id=str(keep))
        ctx.sync()
        load_rows.append({"rep": i, "warmup": i == 0, "load_s": time.perf_counter() - t0, "page_cache_evicted": evicted})

    # free the live training state before the restore test builds fresh models (keeps VRAM under ~3 x state)
    model = opt = state = msd = osd = st = None
    if ctx.is_gpu:
        torch.cuda.empty_cache()
    restore = restore_test(ctx, keep, tmp_root, width, depth, dcp, get_state_dict, set_state_dict, x, y, x_eval,
                           rec_eval, rec_step)
    dist.destroy_process_group()
    shutil.rmtree(tmp_root, ignore_errors=True)

    timed = [r for r in rows if not r["warmup"]]
    by_api = {api: [r for r in timed if r["api"] == api] for api in ("save", "async_save", "async_save+cached_pinned")}
    loads = [r["load_s"] for r in load_rows if not r["warmup"]]

    def stat(vals):
        vals = [v for v in vals if v is not None]
        if not vals:
            return {k: float("nan") for k in ("median", "p95", "min", "max", "iqr")} | {"n": 0}
        s = hwlab.summarize(vals)
        return {k: s[k] for k in ("median", "p95", "min", "max", "iqr", "n")}

    summary = {"save_blocking_s": stat([r["blocking_s"] for r in by_api["save"]]),
               "load_s": stat(loads), "snapshot_s": {k: snap[k] for k in ("median", "p95", "min", "max", "iqr", "n")}}
    for api, key in (("async_save", "async"), ("async_save+cached_pinned", "cached")):
        rs = by_api[api]
        summary.update({f"{key}_blocking_s": stat([r["blocking_s"] for r in rs]),
                        f"{key}_completion_s": stat([r["completion_s"] for r in rs]),
                        f"{key}_step_before_s": stat([r["step_before_p50_s"] for r in rs]),
                        f"{key}_step_during_s": stat([r["step_during_p50_s"] for r in rs]),
                        f"{key}_step_after_s": stat([r["step_after_p50_s"] for r in rs]),
                        f"{key}_staged_bytes": stat([r["staged_bytes"] for r in rs]),
                        f"{key}_staged_pinned_bytes": stat([r["staged_pinned_bytes"] for r in rs]),
                        f"{key}_aliasing_live_bytes": stat([r["staged_aliasing_live_bytes"] for r in rs])})
    for k in ("step_before_s", "step_during_s", "step_after_s"):    # the default async_save
        summary[k] = summary[f"async_{k}"]
    write_gbs = state_bytes / summary["save_blocking_s"]["median"] / 1e9
    read_gbs = state_bytes / summary["load_s"]["median"] / 1e9
    model_cmp = l1_comparison(state_bytes, snap_gbs, write_gbs, summary)

    def interference(key):
        d, b0 = summary[f"{key}_step_during_s"], summary[f"{key}_step_before_s"]
        return d["median"] / b0["median"] - 1.0 if d["n"] else None
    metrics = {
        "n_params": n_params, "state_bytes": state_bytes, "state_gb": state_bytes / 1e9,
        "snapshot_GBps": snap_gbs, "save_write_GBps": write_gbs, "restore_read_GBps": read_gbs,
        "save_blocking_p50_s": summary["save_blocking_s"]["median"],
        "async_blocking_p50_s": summary["async_blocking_s"]["median"],
        "async_completion_p50_s": summary["async_completion_s"]["median"],
        "cached_blocking_p50_s": summary["cached_blocking_s"]["median"],
        "cached_completion_p50_s": summary["cached_completion_s"]["median"],
        "interference_frac": interference("async"), "interference_frac_cached": interference("cached"),
        "async_staged_gb": summary["async_staged_bytes"]["max"] / 1e9,
        "async_staged_pinned_gb": summary["async_staged_pinned_bytes"]["max"] / 1e9,
        "cached_staged_pinned_gb": summary["cached_staged_pinned_bytes"]["max"] / 1e9,
        "async_aliasing_live_gb": summary["async_aliasing_live_bytes"]["max"] / 1e9,
        "consistency": consistency,
        "torch_251_cache_staged_flag_dropped": bool(dropped_flag),
        "torch_version": torch.__version__, "checkpoint_api": "torch.distributed.checkpoint.save / async_save / load",
        "target_filesystem": _fs_of(tempfile.gettempdir()), "repetitions": reps,
    }
    probes = {"fio_on_path": bool(shutil.which("fio")), "nvme_devices": sorted(p.name for p in Path("/dev").glob("nvme*"))}
    not_runnable_parts = [
        {"part": "L2 fio NVMe acceptance (randread 4k QD32, seqwrite 1M QD8, >= 5 runs)",
         "reason": f"fio on PATH: {probes['fio_on_path']}; NVMe block devices visible: {probes['nvme_devices'] or 'none'} "
                   "(Docker Desktop/WSL2 exposes only a virtual disk)",
         "needs": ["Linux host with local NVMe you may wipe (or a scratch file on it)", "fio", "root for raw-device reads"]},
        {"part": "L3 shared-PFS checkpoint (aggregate write, commit latency, restore read, time to resume)",
         "reason": "single host, no parallel file system",
         "needs": ["2+ GPU nodes", "Lustre-class PFS or object store", "maintenance window"]},
    ]
    notes = [
        f"State = model.state_dict() + Adam state via torch.distributed.checkpoint.state_dict.get_state_dict "
        f"(FP32: 4 B weight + 8 B Adam m, v = 12 B/param; the lab's 14 B/param adds a BF16 copy).",
        f"One warm-up then {reps} timed repetitions per API; the warm-up row is kept in the table and excluded from "
        "the summary. dcp.save uses FileSystemWriter(sync_files=True): completion includes fsync.",
        "async_save: blocking = call -> return (the staging copy), completion = call -> future resolved. Training "
        "steps run back-to-back while the future is pending ('during').",
        "Peak host staging memory = the bytes of the state dict DCP's stager returned (FileSystemWriter.stage is "
        "wrapped to inspect it), split into pinned (page-locked) and pageable, plus the bytes that still alias the "
        "live tensors (staged by reference). Process RSS is not used: under WSL2 pinned pages need not appear in it.",
        "async_save+cached_pinned = FileSystemWriter(cache_staged_state_dict=True), one writer reused for the whole "
        "series: DCP stages into pinned host buffers it keeps between saves (memory for speed); the default stages "
        "into fresh pageable copies. Finding: in torch 2.5.1 the constructor argument is silently dropped "
        "(FileSystemWriter.__init__ does not call BlockingAsyncStager.__init__); the experiment sets the stager "
        "attributes directly when it detects this.",
        "Consistency test: the state is cloned at the async_save call, training continues during the persist, then "
        "the checkpoint is loaded and compared tensor by tensor with the clone.",
        f"Restore read: files fsync'd, then evicted with posix_fadvise(DONTNEED); WSL2's virtual disk may still be "
        f"cached by the Windows host, so read GB/s is an upper bound for the physical drive. Target: "
        f"{metrics['target_filesystem']}.",
        f"Lab model source: {restore['validator_source']}.",
        "Not runnable here: " + "; ".join(f"{p['part']} ({p['reason']})" for p in not_runnable_parts) + ".",
    ]
    if not ctx.is_gpu:
        notes.append("CPU fallback: the model lives in host memory, so 'snapshot' is a host-to-host copy, not PCIe D2H.")
    return {"metrics": metrics, "summary": summary, "l1_model": model_cmp, "restore_test": restore,
            "not_runnable_parts": not_runnable_parts, "probes": probes,
            "tables": {"saves": rows, "loads": load_rows}, "notes": notes}


def restore_test(ctx, keep: Path, tmp_root: Path, width, depth, dcp, get_state_dict, set_state_dict, x, y, x_eval,
                 rec_eval: float, rec_step: float) -> dict:
    """Manifest + COMMIT, corrupt a scratch copy, validate both, restore from the intact one, compare losses
    with the values recorded at save time."""
    torch = ctx.torch
    from torch.distributed.checkpoint.api import CheckpointException
    F = torch.nn.functional
    log = [f"recorded at save ({keep.name}): eval loss {rec_eval!r}; first-step loss {rec_step!r}; "
           f"tolerance rel {LOSS_RTOL:g} (FP32, same kernels and batch), stated before running"]
    write_manifest(keep, step=1)
    log.append(f"wrote manifest.json ({len(json.loads((keep / 'manifest.json').read_text())['shards'])} files) + COMMIT")
    codes_ok, src = validate(keep)
    log.append(f"validator on intact checkpoint: {codes_ok or 'valid'}")

    corrupt = tmp_root / "corrupt_copy"
    shutil.copytree(keep, corrupt)
    victim = max((p for p in corrupt.iterdir() if p.suffix == ".distcp"), key=lambda p: p.stat().st_size)
    with victim.open("r+b") as f:
        f.seek(victim.stat().st_size // 2)
        f.write(os.urandom(4096))
    log.append(f"corrupted 4 KiB in the middle of the scratch copy {corrupt.name}/{victim.name} (original untouched)")
    codes_bad, _ = validate(corrupt)
    log.append(f"validator on corrupted copy: {codes_bad or 'valid'} -> rejected" if codes_bad else
               "validator on corrupted copy: valid (NOT rejected)")

    def fresh(seed):
        mdl, op = build(torch, ctx.device, width, depth, seed=seed)
        F.mse_loss(mdl(x), y).backward()          # a fresh Adam has no state; one step creates the load targets
        op.step()
        op.zero_grad(set_to_none=True)
        return mdl, op

    def load_into(mdl, op, ckpt):
        msd, osd = get_state_dict(mdl, op)
        st = {"model": msd, "optim": osd}
        dcp.load(st, checkpoint_id=str(ckpt))
        set_state_dict(mdl, op, model_state_dict=st["model"], optim_state_dict=st["optim"])

    mdl, op = fresh(123)
    load_into(mdl, op, keep)
    # what DCP itself does with the corrupted copy (it stores no data checksums)
    try:
        m2, o2 = fresh(7)
        load_into(m2, o2, corrupt)
        good, bad = get_state_dict(mdl, op), get_state_dict(m2, o2)
        differ = [k for part in (0, 1) for k, t in _flat(bad[part]).items()
                  if hasattr(t, "shape") and not torch.equal(t, _flat(good[part])[k])]
        with torch.no_grad():
            l_bad = float(F.mse_loss(m2(x_eval), y))
        dcp_loaded_corrupt = True
        log.append(f"dcp.load accepted the corrupted copy without error: {len(differ)} tensor(s) silently differ from "
                   f"the intact copy ({', '.join(differ[:3])}); eval loss {l_bad!r}"
                   + (" - unchanged, because the damage is in optimizer state and only surfaces steps later"
                      if l_bad == rec_eval else ""))
        del m2, o2, bad, good
    except (Exception, CheckpointException) as exc:  # noqa: BLE001 - recording what DCP does is the point
        # CheckpointException derives from BaseException in torch 2.5, so `except Exception` misses it
        dcp_loaded_corrupt, l_bad, differ = False, None, []
        last = [ln.strip() for ln in str(exc).splitlines() if ln.strip()][-1:] or [""]
        log.append(f"dcp.load refused the corrupted copy: {type(exc).__name__} ({last[0][:160]}) - here the damage hit "
                   "the zip/pickle framing; damage inside tensor bytes would load silently")

    with torch.no_grad():
        l_eval = float(F.mse_loss(mdl(x_eval), y))
    loss = F.mse_loss(mdl(x), y)
    loss.backward()
    op.step()
    l_step = float(loss)
    rel = abs(l_eval - rec_eval) / max(abs(rec_eval), 1e-30)
    rel_step = abs(l_step - rec_step) / max(abs(rec_step), 1e-30)
    log.append(f"restored from the intact copy into a fresh model (seed 123): eval loss {l_eval!r} (rel diff {rel:.1e})")
    log.append(f"first step after restore: loss {l_step!r} vs recorded {rec_step!r} (rel diff {rel_step:.1e}) -> "
               f"{'PASS' if max(rel, rel_step) <= LOSS_RTOL else 'FAIL'}")
    for line in log:
        ctx.log("restore-test: " + line)
    del mdl, op
    return {"validator_source": src, "intact_codes": codes_ok, "corrupt_codes": codes_bad, "corrupted_file": victim.name,
            "dcp_loaded_corrupt_copy": dcp_loaded_corrupt, "loss_on_corrupt_copy": l_bad, "tensors_differing": differ,
            "recorded_eval_loss": rec_eval, "recorded_first_step_loss": rec_step,
            "restored_eval_loss": l_eval, "restored_first_step_loss": l_step,
            "rel_diff": rel, "first_step_rel_diff": rel_step, "tolerance": LOSS_RTOL, "log": log}


def l1_comparison(state_bytes: float, snap_gbs: float, write_gbs: float, summary: dict) -> dict:
    """Lab Part A async_pfs timings with this host's measured rates plugged in."""
    mod, src = _load_lab_module()
    cfg = {"workload": {"params": state_bytes / 12, "ckpt_bytes_per_param": 12, "gpus": 1, "nodes": 1, "step_time_s": 1},
           "storage": {"pfs_write_GBps": write_gbs, "pfs_read_GBps": write_gbs, "pfs_efficiency": 1.0, "commit_overhead_s": 0.0},
           "host": {"d2h_GBps_per_gpu": snap_gbs, "snapshot_fixed_s": 0.0, "nvme_write_GBps_per_node": write_gbs,
                    "nvme_read_GBps_per_node": write_gbs},
           "async": {"interference_frac": 0.03, "pfs_every_k": 1}}
    try:
        t = mod.strategy_timings(cfg, "async_pfs") if mod is not None else None
    except NotImplementedError:
        t = None
    if t is None:  # same formulas as lab Part A (Section 14.7), used only if the lab module is unavailable
        snap = state_bytes / (snap_gbs * 1e9)
        t = {"blocking": snap, "L_soft": snap + state_bytes / (write_gbs * 1e9)}
        src = "inline async_pfs formulas"
    return {"source": src, "pred_async_blocking_s": t["blocking"], "pred_async_completion_s": t["L_soft"],
            "meas_async_blocking_s": summary["async_blocking_s"]["median"],
            "meas_async_completion_s": summary["async_completion_s"]["median"],
            "pred_sync_blocking_s": state_bytes / (write_gbs * 1e9),
            "meas_sync_blocking_s": summary["save_blocking_s"]["median"]}


def _tensors(obj):
    if hasattr(obj, "numel") and hasattr(obj, "element_size"):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _tensors(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _tensors(v)


def _flat(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flat(v, key + "."))
        else:
            out[key] = v
    return out


def _dir_bytes(d: Path) -> int:
    return sum(p.stat().st_size for p in Path(d).rglob("*") if p.is_file())


def _fs_of(path: str) -> str:
    best = ("?", "?", "")
    try:
        for line in Path("/proc/mounts").read_text().splitlines():
            dev, mnt, fs, opts = line.split()[:4]
            if path.startswith(mnt) and len(mnt) >= len(best[2]):
                best = (fs, opts, mnt)
    except OSError:
        pass
    return f"{path} on {best[2]} ({best[0]}; {best[1][:80]})"


def link_ceiling_gbs(env: dict) -> float | None:
    g = (env.get("gpus") or [{}])[0]
    try:
        return PCIE_GBPS_PER_LANE[int(g["pcie.link.gen.max"])] * int(g["pcie.link.width.max"])
    except (KeyError, ValueError):
        return None


def check(result: dict, env: dict) -> list[str]:
    m, s, r = result["metrics"], result["summary"], result["restore_test"]
    fails = []
    gpu = env["device"] == "cuda"
    if not env.get("quick") and gpu and m["state_bytes"] < 1e9:
        fails.append(f"checkpointed state {m['state_gb']:.2f} GB < 1 GB (exercise 14.19 asks for >= 1 GB)")
    if not s["async_blocking_s"]["median"] < s["save_blocking_s"]["median"]:
        fails.append("async_save blocked as long as save: staging is not overlapping the write; check that the "
                     "future is not resolved before returning (DCP version?)")
    if not s["async_completion_s"]["median"] >= s["async_blocking_s"]["median"]:
        fails.append("async completion < blocking: the timer around future.result() is wrong")
    # async blocking cannot be faster than copying the state once (5 % allowance for timer noise) - GPU only:
    # for host-resident tensors DCP may stage by reference (see the aliasing metric)
    if gpu and s["async_blocking_s"]["median"] < 0.95 * s["snapshot_s"]["min"]:
        fails.append("async_save returned faster than a single copy of the state: it did not stage the state; a "
                     "later in-place update could corrupt the checkpoint")
    if "CHECKSUM_MISMATCH" not in (r["corrupt_codes"] or []):
        fails.append(f"validator did not reject the corrupted copy ({r['corrupt_codes']}): check the manifest hashes")
    if r["intact_codes"]:
        fails.append(f"validator rejected the intact checkpoint: {r['intact_codes']}")
    if r["rel_diff"] > r["tolerance"] or r["first_step_rel_diff"] > r["tolerance"]:
        fails.append(f"restored loss differs by {max(r['rel_diff'], r['first_step_rel_diff']):.2e} > {r['tolerance']:g}: "
                     "the load did not restore every tensor (check optimizer state keys)")
    if s["step_during_s"]["n"] and s["step_during_s"]["median"] < 0.8 * s["step_before_s"]["median"]:
        fails.append("steps got > 20 % faster during the persist: timing is not synchronised")
    for name in ("save_write_GBps", "restore_read_GBps", "snapshot_GBps"):
        if m[name] <= 0:
            fails.append(f"{name} non-positive")
    cons = m["consistency"]
    if gpu and m["async_aliasing_live_gb"] * 1e9 > 0.01 * m["state_bytes"]:
        fails.append("DCP staged GPU-resident state by reference: the background write could see in-place updates")
    if gpu and cons["data_tensors_differing"]:
        fails.append("GPU-resident data tensors in the async checkpoint differ from the state at the call (torn "
                     "checkpoint): staging did not snapshot the GPU state")
    if (not cons["tensors_differing_from_call_time_state"] and cons["steps_during"] > 0
            and m["async_aliasing_live_gb"] * 1e9 > 0.5 * m["state_bytes"]):
        fails.append("state was staged by reference and training ran during the persist, yet the checkpoint matches "
                     "the call-time state: the consistency test is not detecting anything; check it")
    if gpu and s["cached_blocking_s"]["median"] > 1.5 * s["async_blocking_s"]["median"]:
        fails.append("cached pinned staging blocked > 1.5 x longer than pageable staging: pinned buffers are being "
                     "re-allocated on every save")
    if gpu:
        ceiling = link_ceiling_gbs(env)
        if ceiling and m["snapshot_GBps"] > 1.05 * ceiling:
            fails.append(f"D2H snapshot {m['snapshot_GBps']:.1f} GB/s exceeds the PCIe link {ceiling:.1f} GB/s: check "
                         "the byte count")
        if ceiling and s["async_blocking_s"]["median"] < m["state_bytes"] / (ceiling * 1e9):
            fails.append("async_save blocked for less than the PCIe minimum D2H time: staging cannot have copied the state")
    return fails


def report(result: dict, env: dict) -> str:
    m, s, c, r = result["metrics"], result["summary"], result["l1_model"], result["restore_test"]
    gpu = env["device"] == "cuda"

    def row(label, st, scale=1.0, unit="s", fmt="{:.3f}"):
        f = lambda v: fmt.format(v * scale)  # noqa: E731
        if not st["n"]:
            return f"| {label} | n/a | n/a | n/a | 0 |"
        return f"| {label} | {f(st['median'])} | {f(st['p95'])} | {f(st['min'])} - {f(st['max'])} | {st['n']} |"

    lines = [f"Checkpointed state: **{m['state_gb']:.3f} GB** ({m['n_params'] / 1e6:.1f} M params, FP32 weights + Adam) "
             f"on {'the GPU' if gpu else 'the CPU'}; target {m['target_filesystem']}.", "",
             "## Blocking vs completion (timed repetitions)", "",
             "| Metric | Median | p95 | Min - max | n |", "|---|---|---|---|---|",
             row("save: blocking = completion (s)", s["save_blocking_s"]),
             row("async_save: blocking (s)", s["async_blocking_s"]),
             row("async_save: completion (s)", s["async_completion_s"]),
             row("async_save: step time before (ms)", s["async_step_before_s"], 1e3, fmt="{:.2f}"),
             row("async_save: step time during persist (ms)", s["async_step_during_s"], 1e3, fmt="{:.2f}"),
             row("async_save: step time after (ms)", s["async_step_after_s"], 1e3, fmt="{:.2f}"),
             row("async_save: staged host bytes (MB)", s["async_staged_bytes"], 1e-6, fmt="{:.0f}"),
             row("async_save: of which pinned (MB)", s["async_staged_pinned_bytes"], 1e-6, fmt="{:.0f}"),
             row("async_save: still aliasing live state (MB)", s["async_aliasing_live_bytes"], 1e-6, fmt="{:.0f}"),
             row("cached pinned: blocking (s)", s["cached_blocking_s"]),
             row("cached pinned: completion (s)", s["cached_completion_s"]),
             row("cached pinned: step time during persist (ms)", s["cached_step_during_s"], 1e3, fmt="{:.2f}"),
             row("cached pinned: pinned host bytes (MB)", s["cached_staged_pinned_bytes"], 1e-6, fmt="{:.0f}"),
             row(f"{'D2H pinned snapshot' if gpu else 'host snapshot copy'} (s)", s["snapshot_s"]),
             row("dcp.load after page-cache eviction (s)", s["load_s"]),
             "", "| Throughput | GB/s |", "|---|---|",
             f"| {'D2H snapshot (pinned)' if gpu else 'host copy'} | {m['snapshot_GBps']:.2f} |",
             f"| save (write + fsync) | {m['save_write_GBps']:.2f} |",
             f"| restore (dcp.load) | {m['restore_read_GBps']:.2f} |"]
    cons = m["consistency"]
    lines += ["", f"**Consistency:** {cons['tensors_differing_from_call_time_state']} of {cons['tensors_compared']} "
              f"tensors in an async checkpoint differ from the state at the call ({cons['data_tensors_differing']} data "
              f"tensors, {cons['scalar_tensors_differing']} scalars, e.g. `{', '.join(cons['differing_examples'][:2])}`; "
              f"{cons['steps_during']} training steps ran during the persist)."]
    if gpu and cons["scalar_tensors_differing"] and not cons["data_tensors_differing"]:
        lines += ["", "The weights and Adam moments were snapshotted, but Adam's `step` counters are CPU scalar tensors "
                  "(non-fused, non-capturable Adam) and DCP stages host tensors by reference: the checkpoint records a "
                  "later step count than its moments, which skews bias correction on resume. Copy them (or use "
                  "`fused=True`/`capturable=True`, which keeps `step` on the GPU) before relying on async_save."]
    if m["async_aliasing_live_gb"] * 1e9 > 0.5 * m["state_bytes"]:
        lines += ["", f"**Staging by reference:** {m['async_aliasing_live_gb'] * 1e3:.0f} MB of the staged state still "
                  "shares storage with the live tensors. For host-resident state DCP's default async_save does not "
                  "copy, so optimizer steps taken during the persist can land in the checkpoint (a torn checkpoint); "
                  "the consistency line shows whether they did. Snapshot explicitly before async_save when the state "
                  "lives in host memory."]
    if m["interference_frac"] is not None:
        cached = (f"; {m['interference_frac_cached'] * 100:+.0f} % with cached pinned staging"
                  if m["interference_frac_cached"] is not None else "")
        lines += ["", f"Interference: steps were **{m['interference_frac'] * 100:+.0f} %** slower while the persist ran"
                  f"{cached} (the lab assumes +3 %, `interference_frac`)."]
    if gpu and link_ceiling_gbs(env):
        lines += [f"PCIe ceiling for the snapshot: {link_ceiling_gbs(env):.1f} GB/s `[MODELED]` from the negotiated link."]
    lines += ["", f"## Lab Part A model with this host's measured rates (`async_pfs`, {c['source']})", "",
              "| Quantity | Predicted | Measured |", "|---|---|---|",
              f"| sync save blocking (s) | {c['pred_sync_blocking_s']:.3f} | {c['meas_sync_blocking_s']:.3f} |",
              f"| async blocking = snapshot (s) | {c['pred_async_blocking_s']:.3f} | {c['meas_async_blocking_s']:.3f} |",
              f"| async completion = snapshot + persist (s) | {c['pred_async_completion_s']:.3f} | {c['meas_async_completion_s']:.3f} |",
              "", "Blocking above the predicted snapshot time is DCP's planning, allocation of staging buffers and "
              "metadata work: the lab's `snapshot_fixed_s`.",
              "", "## Restore test", "", "```text", *r["log"], "```", "",
              "## What to conclude", "",
              "- async_save moves the write off the critical path; what remains on it is the snapshot (bounded by the "
              "D2H link) plus fixed DCP overhead. Size `snapshot_fixed_s` from the gap above, not from a guess.",
              "- The persist is not free: steps during it run slower (CPU/PCIe/page-cache contention). That is the "
              "lab's interference term, and here it is measured.",
              "- DCP stores no data checksums. Only the manifest validator caught the corrupted copy: verify before "
              "you load, and pick the latest *valid* checkpoint, not the `latest` pointer."]
    if gpu:
        lines += ["", "_Laptop RTX 4060 (PCIe Gen4 x8) writing to a Docker Desktop/WSL2 virtual disk, not an HX8 node "
                  "with 8 x U.2 NVMe and a PFS. Compare the shape (blocking << completion; interference > 0) with "
                  "Chapter 14, not the absolute GB/s._"]
    else:
        lines += ["", "_CPU fallback: no GPU was used; the snapshot is a host-memory copy. D2H/PCIe invariants were "
                  "skipped._"]
    return "\n".join(lines)
