"""Capstone G L2: read-only health on a real host, plus a measured checkpoint/resume drill gated by the L1 code.

What it teaches (starter-kit README section 8; manuscript Ch 23 fault tolerance): the incident
workbench's parsers and gates have to survive real data. The experiment has three parts.
  1. **Read-only evidence.** It runs the L2 command list (nvidia-smi inventory, ECC, row remapping,
     kernel log, rdma, ethtool, lldpctl, chronyc, dcgmi), records what exists and what does not, converts
     what exists into the ``events.jsonl`` schema, and feeds it through the L1 ``normalize_events``
     and ``health_scores``. A healthy host must score nothing. It also records where the real formats
     differ from the synthetic ones (the manifest's ``log_format_differences``).
  2. **Resume validation on a real training run.** A small MLP trains on the GPU with a
     deterministic, index-addressed data loader. It logs step, loss, grad_norm and sample_idx, and it
     checkpoints model, optimizer and data cursor. The replay noise is measured first by restoring
     the same checkpoint twice; the tolerance is then set from it, as ``validate_resume``'s docstring
     prescribes. Three resumes are gated by the L1 ``validate_resume``: a correct one, one with the
     data loader not restored, and one with the optimizer state not restored.
  3. **Checkpoint commit protocol.** Sharded checkpoints are written with the metadata (shard list and
     SHA-256) last. One save is SIGKILLed mid-write, and one committed checkpoint has a shard
     corrupted on purpose. The directory is scanned into the ``checkpoints.json`` catalog form, and
     the L1 ``select_checkpoint`` must pick the newest restorable one and give the right reason for
     each rejection. Save and restore throughput are measured.

Not runnable here: DCGM, ECC counters (not supported on this GPU), the kernel log (Xid/AER; dmesg is
not readable in the container), RDMA link state and NIC counters, LLDP, chrony offset, and the L3
multi-node drill (rank kill with NCCL watchdog, link flap, drain and restart). Each is probed.

CPU fallback: parts 2 and 3 run on the CPU, and part 1 records that no GPU is visible. The GPU-only
invariants are skipped.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

EXPERIMENT = {
    "id": "capstone-g-l2",
    "title": "Capstone G L2: real read-only health evidence and a validated checkpoint/resume drill",
    "evidence": "MEASURED",
    "cpu_fallback": ("the resume-validation and checkpoint-commit drills run on the CPU and are gated by the same L1 "
                     "validate_resume/select_checkpoint; the read-only GPU health part records that no GPU is visible"),
}

PKG = Path(__file__).resolve().parents[2]
WORK = Path("/tmp/ftops-l2")


def load_l1(name: str):
    for p in (PKG / "instructor" / "reference" / f"{name}.py", PKG / "starter-kit" / "starter" / f"{name}.py"):
        if p.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, p.relative_to(PKG).as_posix()
    return None, None


def sh(cmd: list[str]) -> tuple[int, str]:
    if not shutil.which(cmd[0]):
        return 127, f"{cmd[0]}: not installed"
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 127, str(e)


def utc_ms() -> str:
    t = time.time()
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + f".{int(t % 1 * 1000):03d}Z"


# ---------------------------------------------------------------------------------- part 1: read-only evidence
COMMANDS = {
    "nvidia-smi inventory": ["nvidia-smi", "--query-gpu=index,uuid,pci.bus_id", "--format=csv,noheader"],
    "nvidia-smi -q -d ECC": ["nvidia-smi", "-q", "-d", "ECC"],
    "nvidia-smi -q -d ROW_REMAPPER": ["nvidia-smi", "-q", "-d", "ROW_REMAPPER"],
    "journalctl -k": ["journalctl", "-k", "--no-pager", "-n", "50"],
    "dmesg": ["dmesg"],
    "rdma link show": ["rdma", "link", "show"],
    "ethtool -S": ["ethtool", "-S", "lo"],
    "lldpctl": ["lldpctl"],
    "chronyc tracking": ["chronyc", "tracking"],
    "dcgmi discovery -l": ["dcgmi", "discovery", "-l"],
}


def read_only(ctx) -> dict:
    out, full = {}, {}
    for name, cmd in COMMANDS.items():
        rc, txt = sh(cmd)
        full[name] = txt if rc == 0 else ""
        out[name] = {"rc": rc, "available": rc == 0 and bool(txt), "excerpt": txt[:400]}
    host = os.uname().nodename
    gpus = []
    if out["nvidia-smi inventory"]["available"]:
        for line in out["nvidia-smi inventory"]["excerpt"].splitlines():
            i, uuid, bdf = [v.strip() for v in line.split(",")]
            gpus.append({"index": int(i), "uuid": uuid, "bus_id": bdf})
    rr, ecc = full["nvidia-smi -q -d ROW_REMAPPER"], full["nvidia-smi -q -d ECC"]
    events = []
    pending = re.search(r"Pending\s*:\s*(\w+)", rr)
    failure = re.search(r"Remapping Failure Occurred\s*:\s*(\w+)", rr)
    dbe = re.search(r"DRAM Uncorrectable\s*:\s*(\S+)", ecc)
    for g in gpus[:1]:
        if pending:
            events.append({"host_ts": utc_ms(), "host": host, "source": "dcgm", "gpu_uuid": g["uuid"],
                           "field": "DCGM_FI_DEV_ROW_REMAP_PENDING", "value": 0 if pending.group(1).lower() == "no" else 1})
        if failure:
            events.append({"host_ts": utc_ms(), "host": host, "source": "dcgm", "gpu_uuid": g["uuid"],
                           "field": "DCGM_FI_DEV_ROW_REMAP_FAILURE", "value": 0 if failure.group(1).lower() == "no" else 1})
        if dbe and dbe.group(1) not in ("N/A",):
            events.append({"host_ts": utc_ms(), "host": host, "source": "dcgm", "gpu_uuid": g["uuid"],
                           "field": "DCGM_FI_DEV_ECC_DBE_VOL_TOTAL", "value": int(dbe.group(1))})
    diffs = []
    if gpus:
        b = gpus[0]["bus_id"]
        diffs.append(f"nvidia-smi pci.bus_id is '{b}' (8-hex-digit PCI domain); the kernel Xid line prints 'PCI:{b[4:-2]}' "
                     f"(4-digit domain, no function) and the synthetic inventory uses '{b[4:].lower()}': normalise the domain width "
                     "and the function suffix in the adapter")
    diffs.append("no DCGM here: field values come from nvidia-smi text and are renamed to DCGM_FI_* by the adapter; "
                 "nvidia-smi reports 'Yes/No' for remap pending/failure, DCGM reports counts")
    if dbe and dbe.group(1) == "N/A":
        diffs.append("ECC counters are 'N/A' on this GPU (GeForce, no ECC): the adapter must emit nothing, not 0. "
                     "A 0 would read as 'checked and clean'")
    diffs.append("host_ts here is the container's clock with no chrony offset available; the synthetic data carries "
                 "per-host offsets from clock_offsets.csv")
    ftops, src = load_l1("ftops")
    l1 = {"available": False}
    if ftops is not None:
        try:
            maps = {"uuid": {g["uuid"]: (host, g["index"]) for g in gpus},
                    "gpu_bdf": {(host, g["bus_id"][4:].lower()): g["index"] for g in gpus}, "nic_bdf": {}, "port": {}, "rank": {}}
            norm = ftops.normalize_events(events, {host: 0.0}, maps) if events else None
            scores = ftops.health_scores(norm) if norm is not None else {}
            l1 = {"available": True, "source": src, "normalized_rows": 0 if norm is None else len(norm),
                  "kinds": sorted(norm["kind"].unique()) if norm is not None else [], "scores": scores}
            if gpus:   # positive control (synthetic, labelled): the same adapter path with a pending remap must be flagged
                ctrl = [dict(e) for e in events if e["field"] == "DCGM_FI_DEV_ROW_REMAP_PENDING"]
                for e in ctrl:
                    e["value"] = 1
                l1["positive_control_scores"] = ftops.health_scores(ftops.normalize_events(ctrl, {host: 0.0}, maps)) if ctrl else {}
        except NotImplementedError as e:
            l1 = {"available": False, "why": f"starter ftops.py not implemented yet ({e})"}
    return {"commands": out, "gpus": gpus, "events": events, "format_differences": diffs, "l1": l1,
            "ecc_dram_uncorrectable": dbe.group(1) if dbe else None}


# ---------------------------------------------------------------------------------- part 2: resume validation
class Job:
    """A tiny deterministic training job: sample i is generated from seed i, so data order is the data cursor."""

    def __init__(self, ctx, width: int, batch: int, seed: int = 0):
        torch = ctx.torch
        self.ctx, self.t, self.width, self.batch = ctx, torch, width, batch
        torch.manual_seed(seed)
        self.model = torch.nn.Sequential(torch.nn.Linear(width, width), torch.nn.GELU(), torch.nn.Linear(width, width),
                                         torch.nn.GELU(), torch.nn.Linear(width, 1)).to(ctx.device)
        self.opt = torch.optim.Adam(self.model.parameters(), lr=3e-4)
        self.cursor = 0

    def data(self, idx: int):
        g = self.t.Generator().manual_seed(1_000_003 + idx)
        x = self.t.randn(self.batch, self.width, generator=g)
        y = x[:, :8].sum(1, keepdim=True).sin()
        return x.to(self.ctx.device), y.to(self.ctx.device)

    def step(self, step: int) -> dict:
        x, y = self.data(self.cursor)
        loss = (self.model(x) - y).pow(2).mean()
        self.opt.zero_grad(set_to_none=True)
        loss.backward()
        gn = self.t.nn.utils.clip_grad_norm_(self.model.parameters(), 1e9)
        self.opt.step()
        row = {"step": step, "loss": float(loss.item()), "grad_norm": float(gn.item()), "sample_idx": self.cursor * self.batch}
        self.cursor += 1
        return row

    def state(self) -> dict:
        return {"model": {k: v.detach().cpu().clone() for k, v in self.model.state_dict().items()},
                "opt": self.opt.state_dict(), "cursor": self.cursor}

    def load(self, s: dict, *, data=True, optimizer=True):
        self.model.load_state_dict(s["model"])
        if optimizer:
            self.opt.load_state_dict(s["opt"])
        self.cursor = s["cursor"] if data else 0


def resume_drill(ctx) -> dict:
    import copy
    import pandas as pd
    width, batch = (1024, 256) if ctx.is_gpu else (256, 128)
    n_pre, ck_at = (60, 30) if ctx.quick else (200, 100)
    base = 100_000                                        # step numbering offset, like the synthetic logs
    job = Job(ctx, width, batch)
    pre, ckpt = [], None
    for s in range(1, n_pre + 1):
        pre.append(job.step(base + s))
        if s == ck_at:
            ckpt = copy.deepcopy(job.state())
    extra = 10                                            # resumed runs go past the last pre-fault step

    def resume(**kw):
        j = Job(ctx, width, batch, seed=123)              # fresh process-equivalent: different init, then restore
        j.load(copy.deepcopy(ckpt), **kw)
        return pd.DataFrame([j.step(base + s) for s in range(ck_at + 1, n_pre + extra + 1)])

    r1, r2 = resume(), resume()
    m = r1.merge(r2, on="step")
    replay = float(((m["loss_x"] - m["loss_y"]).abs() / m["loss_x"]).max())
    replay_g = float(((m["grad_norm_x"] - m["grad_norm_y"]).abs() / m["grad_norm_x"]).max())
    tol = max(10 * max(replay, replay_g), 1e-5)
    pre_df = pd.DataFrame(pre)
    cases = {"validated (model + optimizer + data cursor)": r1, "data loader not restored": resume(data=False),
             "optimizer state not restored": resume(optimizer=False)}
    ftops, src = load_l1("ftops")
    out = {"n_pre": n_pre, "restored_step": base + ck_at, "replay_noise_loss": replay, "replay_noise_grad": replay_g, "tol": tol,
           "width": width, "batch": batch, "cases": {}}
    for name, df in cases.items():
        res = None
        if ftops is not None:
            try:
                res = ftops.validate_resume(pre_df, df, base + ck_at, tol=tol)
                res = {k: (bool(v) if isinstance(v, bool) or type(v).__name__ == "bool_" else float(v)) for k, v in res.items()}
            except NotImplementedError:
                res = None
        out["cases"][name] = res
    out["source"] = src
    out["loss_log_head"] = pre[:3]
    return out


# ---------------------------------------------------------------------------------- part 3: commit protocol
WRITER = r"""
import hashlib, json, os, sys, time
d, step, shards, mib, slow = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
os.makedirs(d, exist_ok=True)
sums = {}
blk = os.urandom(1 << 20)
for i in range(shards):
    p = os.path.join(d, f"shard_{i:02d}.bin")
    h = hashlib.sha256()
    with open(p, "wb") as f:
        for _ in range(mib):
            f.write(blk); h.update(blk)
        f.flush(); os.fsync(f.fileno())
    sums[f"shard_{i:02d}.bin"] = h.hexdigest()
    open(os.path.join(d, f".shard_{i:02d}.done"), "w").close()
    time.sleep(slow)
tmp = os.path.join(d, "metadata.json.tmp")
with open(tmp, "w") as f:
    json.dump({"step": step, "shards": sums, "committed_utc": time.time()}, f); f.flush(); os.fsync(f.fileno())
os.replace(tmp, os.path.join(d, "metadata.json"))   # the commit point
"""


def scan_catalog(root: Path, shards: int) -> list[dict]:
    """The checkpoints.json catalog form, built from what is actually on disk."""
    cat = []
    for d in sorted(root.glob("step_*")):
        step = int(d.name.split("_")[1])
        meta = d / "metadata.json"
        committed = meta.is_file()
        sums = json.loads(meta.read_text())["shards"] if committed else {}
        names = [f"shard_{i:02d}.bin" for i in range(shards)]
        missing = [i for i, n in enumerate(names) if not (d / n).is_file()]
        bad = []
        if committed:
            for i, n in enumerate(names):
                if (d / n).is_file() and hashlib.sha256((d / n).read_bytes()).hexdigest() != sums.get(n):
                    bad.append(i)
        cat.append({"step": step, "kind": "sharded", "expected_shards": shards, "metadata_committed": committed,
                    "missing_shards": missing if committed else [i for i in missing], "checksum_failures": bad})
    return cat


def commit_drill(ctx) -> dict:
    shards, mib = 4, (8 if ctx.quick else 32)
    root = WORK / "ckpts"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    writes = []
    for step in (1000, 2000, 3000):
        t0 = time.perf_counter()
        subprocess.run([sys.executable, "-c", WRITER, str(root / f"step_{step}"), str(step), str(shards), str(mib), "0"], check=True)
        writes.append({"step": step, "s": time.perf_counter() - t0, "bytes": shards * mib * 2 ** 20})
    # corrupt one shard of step 3000 (a committed checkpoint whose data rotted)
    victim = root / "step_3000" / "shard_02.bin"
    with open(victim, "r+b") as f:
        f.seek(12345)
        b = f.read(1)
        f.seek(12345)
        f.write(bytes([b[0] ^ 0xFF]))
    # kill a save mid-write: step 4000, SIGKILL after the first shard is durable
    p = subprocess.Popen([sys.executable, "-c", WRITER, str(root / "step_4000"), "4000", str(shards), str(mib), "0.5"])
    t0 = time.time()
    while not (root / "step_4000" / ".shard_00.done").exists():
        if p.poll() is not None or time.time() - t0 > 60:
            break
        time.sleep(0.01)
    p.send_signal(signal.SIGKILL)
    p.wait()
    # restore throughput: read every shard of the newest good checkpoint (cache dropped)
    good = root / "step_2000"
    t0 = time.perf_counter()
    nbytes = 0
    for f in sorted(good.glob("shard_*.bin")):
        fd = os.open(f, os.O_RDONLY)
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        while chunk := os.read(fd, 1 << 20):
            nbytes += len(chunk)
        os.close(fd)
    read_s = time.perf_counter() - t0
    cat = scan_catalog(root, shards)
    ftops, src = load_l1("ftops")
    sel = None
    if ftops is not None:
        try:
            sel = ftops.select_checkpoint(cat)
            sel = {"step": sel["step"], "rejected": {str(k): v for k, v in sel["rejected"].items()}}
        except NotImplementedError:
            sel = None
    shutil.rmtree(WORK, ignore_errors=True)
    return {"catalog": cat, "selected": sel, "source": src, "writes": writes,
            "write_GBps": [w["bytes"] / w["s"] / 1e9 for w in writes], "read_GBps": nbytes / read_s / 1e9,
            "shards": shards, "shard_mib": mib, "killed_step": 4000, "corrupted": "step_3000/shard_02.bin"}


def run(ctx) -> dict:
    torch = ctx.torch
    if not ctx.is_gpu:
        torch.set_num_threads(min(8, os.cpu_count() or 1))
    else:
        torch.backends.cudnn.deterministic = True
    ro = read_only(ctx)
    rd = resume_drill(ctx)
    cd = commit_drill(ctx)
    ctx.log(f"read-only: {sum(c['available'] for c in ro['commands'].values())}/{len(ro['commands'])} commands available; "
            f"replay noise {rd['replay_noise_loss']:.2e} -> tol {rd['tol']:.1e}; selected checkpoint {cd['selected'] and cd['selected']['step']}")
    cmds = ro["commands"]
    nr = [{"part": n, "probe": f"rc={cmds[n]['rc']}: {cmds[n]['excerpt'][:80]}", "needs": [need]}
          for n, need in (("dcgmi discovery -l", "DCGM on a data-center GPU host"), ("journalctl -k", "host kernel log (root, not a container)"),
                          ("dmesg", "host kernel log (root)"), ("rdma link show", "RDMA NIC + iproute2 rdma"),
                          ("ethtool -S", "a real NIC netdev and ethtool"), ("lldpctl", "lldpd on a host cabled to a switch"),
                          ("chronyc tracking", "chrony on the host")) if not cmds[n]["available"]]
    nr.append({"part": "L3 drill: kill a rank, NCCL watchdog timing, link flap, drain + restart on >= 2 RDMA nodes",
               "probe": f"GPUs={torch.cuda.device_count() if ctx.is_gpu else 0}, RDMA devices="
                        f"{sorted(os.listdir('/sys/class/infiniband')) if Path('/sys/class/infiniband').is_dir() else 'none'}",
               "needs": [">= 2 GPU nodes with RDMA NICs", "lab scheduler", "shared storage"]})
    ok = rd["cases"].get("validated (model + optimizer + data cursor)") or {}
    return {"metrics": {"commands_available": sum(c["available"] for c in cmds.values()),
                        "replay_noise_rel": rd["replay_noise_loss"], "resume_tol": rd["tol"],
                        "validated_resume_ok": ok.get("ok"), "selected_checkpoint": cd["selected"] and cd["selected"]["step"],
                        "ckpt_write_GBps_median": round(sorted(cd["write_GBps"])[1], 3), "ckpt_read_GBps": round(cd["read_GBps"], 3)},
            "read_only": ro, "resume": rd, "commit": cd, "not_runnable_parts": nr,
            "notes": ["Resume drill: one process, three restores of the same in-memory checkpoint into freshly initialised "
                      "models (different init seed), so a missing restore cannot hide behind identical initial weights.",
                      "Commit protocol: shards first (each fsynced), metadata with SHA-256 per shard last, renamed into place; "
                      "the rename is the commit point. The kill lands after shard 0 is durable.",
                      "Throughput: write = subprocess wall time for shards + metadata (incl. interpreter start); read = all shards of "
                      "one checkpoint with the page cache dropped per file."]}


def check(result: dict, env: dict) -> list[str]:
    fails = []
    ro, rd, cd = result["read_only"], result["resume"], result["commit"]
    if ro["l1"].get("available") and ro["l1"]["scores"]:
        fails.append(f"the L1 health scores flag this healthy host: {ro['l1']['scores']} (an adapter is emitting a fault "
                     "value for a field that is clean or N/A)")
    if env["device"] == "cuda":
        if ro["l1"].get("available") and "positive_control_scores" in ro["l1"] and not ro["l1"]["positive_control_scores"]:
            fails.append("positive control: a pending row remap went through the adapter and was NOT flagged; the "
                         "'healthy' verdict above is then meaningless (check the uuid map in the adapter)")
        if not ro["gpus"]:
            fails.append("nvidia-smi inventory is empty on a GPU run")
        if any(e["field"].startswith("DCGM_FI_DEV_ECC") for e in ro["events"]) and ro["ecc_dram_uncorrectable"] == "N/A":
            fails.append("an ECC event was emitted although nvidia-smi reports ECC as N/A")
    cases = rd["cases"]
    good = cases.get("validated (model + optimizer + data cursor)")
    bad_data = cases.get("data loader not restored")
    bad_opt = cases.get("optimizer state not restored")
    if good is not None:
        if not good["ok"]:
            fails.append(f"the correct resume failed validate_resume (max_rel_dev {good['max_rel_dev']:.2e}, tol {rd['tol']:.1e}): "
                         "replay is not deterministic or the checkpoint misses state")
        if bad_data["ok"] or bad_data["sample_idx_ok"]:
            fails.append("validate_resume accepted a resume whose data loader restarted from sample 0")
        if bad_opt["ok"]:
            fails.append("validate_resume accepted a resume without optimizer state: the tolerance is too loose to see it")
    if rd["tol"] > 1e-3:
        fails.append(f"replay noise sets the tolerance to {rd['tol']:.1e}, looser than the synthetic 1e-3: the job is not "
                     "deterministic enough to validate a resume (check nondeterministic kernels)")
    cat = {c["step"]: c for c in cd["catalog"]}
    if cat.get(cd["killed_step"], {}).get("metadata_committed"):
        fails.append("the killed save shows a committed metadata file: the commit point is not last")
    if not cat.get(3000, {}).get("checksum_failures"):
        fails.append("the corrupted shard was not detected by the checksum scan")
    sel = cd["selected"]
    if sel is not None:
        if sel["step"] != 2000:
            fails.append(f"select_checkpoint chose step {sel['step']}; the newest restorable checkpoint is 2000")
        rej = sel["rejected"]
        if not any("metadata" in r for r in rej.get("4000", [])):
            fails.append("step 4000 (killed mid-save) must be rejected for uncommitted metadata")
        if not any("checksum" in r for r in rej.get("3000", [])):
            fails.append("step 3000 (corrupted shard) must be rejected for a checksum failure")
    if cd["read_GBps"] <= 0 or min(cd["write_GBps"]) <= 0:
        fails.append("non-positive checkpoint throughput")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    ro, rd, cd = result["read_only"], result["resume"], result["commit"]
    L = ["## 1. Read-only evidence on this host", "", "| Command | available | first output |", "|---|---|---|"]
    for n, c in ro["commands"].items():
        first = c["excerpt"].strip().splitlines()[0][:70].replace("|", "/") if c["excerpt"].strip() else ""
        L.append(f"| `{n}` | {c['available']} | {first} |")
    l1 = ro["l1"]
    L += ["", f"Events produced by the adapters: {len(ro['events'])} ({', '.join(sorted({e['field'] for e in ro['events']})) or 'none'})."]
    if l1.get("available"):
        L.append(f"L1 `normalize_events` -> {l1['normalized_rows']} rows ({', '.join(l1['kinds']) or '-'}); `health_scores` -> "
                 f"{l1['scores'] or 'nothing flagged'} (`{l1['source']}`).")
        if "positive_control_scores" in l1:
            L.append(f"Positive control (synthetic: the same event with ROW_REMAP_PENDING=1): {l1['positive_control_scores']}. "
                     "The healthy verdict comes from a path that can flag.")
    L += ["", "Format differences against the synthetic bundle (`log_format_differences`):", ""]
    L += [f"- {d}" for d in ro["format_differences"]]
    L += ["", "## 2. Resume validation on a real training run (L1 `validate_resume`)", "",
          f"MLP width {rd['width']}, batch {rd['batch']}, {rd['n_pre']} pre-fault steps, checkpoint at step {rd['restored_step']}. "
          f"Replay noise (same checkpoint restored twice): loss {rd['replay_noise_loss']:.1e}, grad_norm {rd['replay_noise_grad']:.1e} "
          f"(relative) -> tolerance **{rd['tol']:.0e}** (10x the observed maximum, floor 1e-5).", "",
          "| Resume | first_step_ok | sample_idx_ok | continuity_ok | progressed | max rel dev | ok |", "|---|---|---|---|---|---|---|"]
    for n, r in rd["cases"].items():
        if r:
            L.append(f"| {n} | {r['first_step_ok']} | {r['sample_idx_ok']} | {r['continuity_ok']} | {r['progressed']} | "
                     f"{r['max_rel_dev']:.1e} | **{r['ok']}** |")
    L += ["", "## 3. Checkpoint commit protocol (L1 `select_checkpoint`)", "",
          f"{cd['shards']} shards x {cd['shard_mib']} MiB per checkpoint; metadata with SHA-256 written last. Step 3000 had "
          f"`{cd['corrupted'].split('/')[-1]}` corrupted after commit; step {cd['killed_step']} was SIGKILLed after its first shard.", "",
          "| Step | metadata committed | missing shards | checksum failures |", "|---|---|---|---|"]
    for c in cd["catalog"]:
        L.append(f"| {c['step']} | {c['metadata_committed']} | {c['missing_shards'] or '-'} | {c['checksum_failures'] or '-'} |")
    if cd["selected"]:
        L += ["", f"Selected: **step {cd['selected']['step']}**; rejected: " +
              "; ".join(f"{k}: {', '.join(v)}" for k, v in cd["selected"]["rejected"].items()) + "."]
    w = sorted(cd["write_GBps"])
    L += ["", f"Checkpoint write {w[1]:.2f} GB/s median of 3 (range {w[0]:.2f}-{w[-1]:.2f}), restore read {cd['read_GBps']:.2f} GB/s "
          "on the container's overlay file system `[MEASURED]`."]
    L += ["", "## Not runnable here", ""]
    for p in result["not_runnable_parts"]:
        L.append(f"- **{p['part']}**. Probe: {p['probe']}. Needs: {', '.join(p['needs'])}.")
    L += ["", "## What to conclude", "",
          "- Measure the replay noise and derive the tolerance from it. Then the resume check is strict enough to catch a data "
          "loader that restarted from sample 0, *and* a resume that dropped the optimizer state. Loss alone looks plausible in both.",
          "- A checkpoint is restorable only if its commit record exists and every shard matches its checksum. Reading "
          "'the newest directory' would have restored a half-written or corrupted checkpoint.",
          "- Real tools disagree with the synthetic formats (PCI domain width, N/A versus 0, Yes/No versus counts). The adapter "
          "is where these differences are handled. Emitting 0 for N/A would hide a missing signal."]
    if gpu:
        L.append("- This is a **laptop Ada GPU in a container**: no DCGM, ECC, kernel log or RDMA. The read-only part shows how "
                 "much of the L2 command list depends on host access a container does not have.")
    else:
        L.append("- _CPU fallback: no GPU was used. The GPU inventory and ECC-adapter invariants were skipped. Parts 2 and 3 ran on the CPU._")
    return "\n".join(L)
