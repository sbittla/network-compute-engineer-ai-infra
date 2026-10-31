"""Capstone F L2: a safe, contained fault-injection drill on one GPU: kill, detect, recover, measure.

What it teaches (starter-kit README section 8; manuscript Ch 23 reliability engineering): a game day
is a measurement. You inject one fault with a written abort condition and a rollback, then measure
time to detect, time to resume and the work lost, and compare them with what the simulator
predicted. Here the "job" is a real training process on the GPU (a small MLP with Adam). It writes a
heartbeat every step and an atomic checkpoint every K steps (temporary file plus rename, so a
checkpoint is durable only once its write completes, as in ``sim/cluster_sim.py``). The injection is
``SIGKILL`` of that process, at a seeded random moment. That is the node-loss fault reduced to the one
blast radius that is safe on a shared laptop: one process inside a disposable container. A monitor
applies the L1 rule form (``metric op threshold for for_s``, the reference ``JobStalled`` rule
scaled to this job's step time) to the heartbeat's progress age, fires the alert, and "requeues" the
job, which restarts and reloads the last durable checkpoint. Each repetition records detect_s,
resume_s (with its parts: process launch, CUDA init, checkpoint load) and steps_lost. The prediction
uses the simulator's own recovery model: detect = threshold + for_s, restart = launch + checkpoint
bytes / read bandwidth, steps lost uniform in [0, K).

Not runnable here: a backend link down (``ip link set dev <rail> down``), node power-off through the
BMC, the storage slowdown (``tc qdisc ... netem``), a scheduler outage (``systemctl stop
slurmctld``), and the multi-node DDP job with an NCCL timeout. Each needs hardware or privileges
this host does not have, and each is probed.

CPU fallback: the same drill with the training process on the CPU (a smaller MLP). The GPU-only
check (the CUDA-init share of the restart) is skipped.
"""
from __future__ import annotations

import json
import os
import random
import shutil
import signal
import statistics
import subprocess
import sys
import time
from pathlib import Path

EXPERIMENT = {
    "id": "capstone-f-l2",
    "title": "Capstone F L2: contained kill-detect-recover drill with measured detect, resume and steps lost",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same SIGKILL/heartbeat/requeue drill with the training process on the CPU; detect_s, resume_s "
                     "and steps_lost are CPU measurements; the multi-node faults are recorded as not runnable"),
}

PKG = Path(__file__).resolve().parents[2]
WORK = Path("/tmp/gameday-l2")

WORKER = r"""
import json, os, sys, time
T0 = time.time()
import torch
dev, ckdir, hb, total, every, seed, width = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7])
if dev == "cpu":
    torch.set_num_threads(4)
def beat(**kw):
    tmp = hb + ".tmp"
    with open(tmp, "w") as f:
        json.dump(dict(pid=os.getpid(), t=time.time(), **kw), f)
    os.replace(tmp, hb)
torch.manual_seed(seed)
layers = []
for _ in range(4):
    layers += [torch.nn.Linear(width, width), torch.nn.GELU()]
model = torch.nn.Sequential(*layers).to(dev)
opt = torch.optim.Adam(model.parameters(), lr=1e-4)
if dev == "cuda":
    torch.zeros(1, device="cuda"); torch.cuda.synchronize()
T_INIT = time.time()
step, ck = 0, os.path.join(ckdir, "ckpt.pt")
if os.path.exists(ck):
    s = torch.load(ck, map_location="cpu", weights_only=False)
    model.load_state_dict(s["model"]); opt.load_state_dict(s["opt"]); step = s["step"]
    torch.set_rng_state(s["rng"])
T_LOAD = time.time()
durable = restored = step
beat(step=step, durable_step=durable, phase="ready", t_start=T0, t_init=T_INIT, t_load=T_LOAD, restored=restored)
g = torch.Generator().manual_seed(seed + 1)
while step < total:
    x = torch.randn(512, width, generator=g).to(dev)
    loss = model(x).pow(2).mean()
    opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    lv = loss.item()
    step += 1
    if step % every == 0:
        tmp = ck + ".tmp"
        torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "step": step, "rng": torch.get_rng_state()}, tmp)
        os.replace(tmp, ck)                     # durable only now
        durable = step
    beat(step=step, durable_step=durable, phase="train", loss=lv, t_start=T0, t_init=T_INIT, t_load=T_LOAD, restored=restored)
"""


def read_hb(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def l1_rule() -> dict:
    """The L1 JobStalled rule (reference alert_rules) if available: its form is reused, its numbers scaled."""
    import importlib.util
    for p in (PKG / "instructor" / "reference" / "gameday.py", PKG / "starter-kit" / "starter" / "gameday.py"):
        if p.is_file():
            try:
                sys.path.insert(0, str(PKG / "starter-kit"))
                spec = importlib.util.spec_from_file_location("l1_gameday", p)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for r in mod.alert_rules():
                    if r["metric"] == "sim_job_progress_age_seconds":
                        return {**r, "source": p.relative_to(PKG).as_posix()}
            except Exception as e:  # noqa: BLE001 - a learner starter may be incomplete
                return {"source": p.relative_to(PKG).as_posix(), "error": f"{type(e).__name__}: {e}"}
    return {}


def one_drill(ctx, rep: int, rng: random.Random, cfg: dict) -> dict:
    shutil.rmtree(WORK, ignore_errors=True)
    (WORK / "ck").mkdir(parents=True)
    hb = WORK / "hb.json"
    cmd = [sys.executable, "-c", WORKER, ctx.device, str(WORK / "ck"), str(hb), str(cfg["total"]), str(cfg["every"]),
           str(cfg["seed"]), str(cfg["width"])]
    t_launch = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    # wait for one durable checkpoint plus some steps, then a seeded random extra delay
    while True:
        h = read_hb(hb)
        if h and h.get("durable_step", 0) >= cfg["every"]:
            break
        if p.poll() is not None:
            raise RuntimeError("worker exited before its first checkpoint: " + p.stderr.read()[-2000:])
        time.sleep(0.01)
    first = h
    step_time = (first["t"] - first["t_load"]) / max(1, first["step"])
    time.sleep(rng.uniform(0.0, 2.0 * cfg["every"] * step_time))
    before = read_hb(hb)
    t_kill = time.time()
    os.kill(p.pid, signal.SIGKILL)                     # the injection
    p.wait()
    last_step = before["step"]                         # last heartbeat before the kill
    # detection: progress age > threshold, held for for_s, polled every poll_s
    thr, hold, poll = cfg["threshold_s"], cfg["for_s"], cfg["poll_s"]
    breach_since, t_alert = None, None
    while t_alert is None:
        h = read_hb(hb) or before
        age = time.time() - h["t"]
        if age > thr:
            breach_since = breach_since or time.time()
            if time.time() - breach_since >= hold:
                t_alert = time.time()
        else:
            breach_since = None
        time.sleep(poll)
    final = read_hb(hb)
    last_step = max(last_step, final["step"])
    durable = final["durable_step"]
    # rollback / recovery: requeue immediately on the alert
    t_requeue = time.time()
    p2 = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    resumed = None
    while resumed is None:
        h = read_hb(hb)
        if h and h.get("pid") == p2.pid and h["step"] > h["restored"]:
            resumed = h                                  # first new step completed by the restarted job
        if p2.poll() is not None and resumed is None:
            raise RuntimeError("restarted worker exited before resuming: " + p2.stderr.read()[-2000:])
        if time.time() - t_requeue > 120:                # abort condition
            p2.kill()
            raise RuntimeError("abort: the requeued job did not resume within 120 s")
        time.sleep(0.005)
    ready = resumed
    p2.wait(timeout=120)
    if p2.returncode != 0:
        raise RuntimeError("restarted worker failed: " + p2.stderr.read()[-2000:])
    ck_bytes = (WORK / "ck" / "ckpt.pt").stat().st_size
    return {"rep": rep, "step_time_s": step_time, "last_step_before_kill": last_step, "durable_step": durable,
            "restored_step": ready["restored"], "steps_lost": last_step - ready["restored"],
            "detect_s": t_alert - t_kill, "silence_to_alert_s": t_alert - final["t"], "age_at_kill_s": t_kill - final["t"], "resume_s": resumed["t"] - t_kill, "requeue_to_resume_s": resumed["t"] - t_requeue,
            "launch_s": ready["t_start"] - t_requeue, "init_s": ready["t_init"] - ready["t_start"],
            "load_s": ready["t_load"] - ready["t_init"], "first_step_s": resumed["t"] - ready["t_load"],
            "ckpt_bytes": ck_bytes, "launch_to_first_ckpt_s": first["t"] - t_launch}


def read_bw() -> float:
    """Sequential read bandwidth of the checkpoint file system (page cache dropped for the file)."""
    path = WORK / "bw.bin"
    WORK.mkdir(parents=True, exist_ok=True)
    blk = os.urandom(1 << 20)
    with open(path, "wb") as f:
        for _ in range(64):
            f.write(blk)
        f.flush()
        os.fsync(f.fileno())
    fd = os.open(path, os.O_RDONLY)
    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    t0 = time.perf_counter()
    while os.read(fd, 1 << 20):
        pass
    dt = time.perf_counter() - t0
    os.close(fd)
    path.unlink()
    return 64 * 2 ** 20 / dt


def probes() -> dict:
    w = shutil.which
    return {"ip": bool(w("ip")), "tc": bool(w("tc")), "ipmitool": bool(w("ipmitool")), "scontrol": bool(w("scontrol")),
            "systemctl": bool(w("systemctl")), "kubectl": bool(w("kubectl")), "uid": os.getuid(),
            "rdma_devices": sorted(os.listdir("/sys/class/infiniband")) if Path("/sys/class/infiniband").is_dir() else [],
            "net_interfaces": sorted(os.listdir("/sys/class/net")) if Path("/sys/class/net").is_dir() else []}


def run(ctx) -> dict:
    reps = 3 if ctx.quick else 5
    # total: the kill lands within ~3 checkpoint intervals, so the resumed job finishes by itself shortly after
    cfg = {"every": 25, "seed": 7, "width": 1024 if ctx.is_gpu else 512, "total": 4 * 25 + 10,
           "threshold_s": 0.5, "for_s": 0.25, "poll_s": 0.05}
    rule = l1_rule()
    rng = random.Random(2026)
    drills = []
    for rep in range(reps):
        d = one_drill(ctx, rep, rng, cfg)
        drills.append(d)
        ctx.log(f"rep {rep}: killed at step {d['last_step_before_kill']}, restored {d['restored_step']} "
                f"(lost {d['steps_lost']}), detect {d['detect_s']:.2f} s, resume {d['resume_s']:.2f} s "
                f"(launch {d['launch_s']:.2f} + init {d['init_s']:.2f} + load {d['load_s'] * 1e3:.0f} ms)")
    bw = read_bw()
    shutil.rmtree(WORK, ignore_errors=True)
    med = lambda k: statistics.median(d[k] for d in drills)  # noqa: E731
    pred = {"detect_s": cfg["threshold_s"] + cfg["for_s"], "detect_s_max": cfg["threshold_s"] + cfg["for_s"] + 2 * cfg["poll_s"] + med("step_time_s"),
            "load_s": med("ckpt_bytes") / bw, "steps_lost_mean": (cfg["every"] - 1) / 2, "steps_lost_max": cfg["every"] - 1}
    pred["resume_s"] = pred["detect_s"] + med("launch_s") + med("init_s") + pred["load_s"]
    pr = probes()
    nr = [{"part": "backend link down / up (ip link set dev <rail_iface> down)",
           "probe": f"interfaces={pr['net_interfaces']}, RDMA={pr['rdma_devices'] or 'none'}, uid={pr['uid']} (not root)",
           "needs": ["dedicated lab node with a rail interface", "root", "a multi-node job using it"]},
          {"part": "node loss via BMC (ipmitool chassis power off / Redfish reset)", "probe": f"ipmitool={pr['ipmitool']}",
           "needs": ["lab BMC", "written authorisation"]},
          {"part": "storage slowdown (tc qdisc add ... netem delay 20ms rate 1gbit)", "probe": f"tc={pr['tc']}, uid={pr['uid']}",
           "needs": ["root (CAP_NET_ADMIN) on a lab client", "network storage"]},
          {"part": "scheduler outage (systemctl stop slurmctld) and drain/requeue", "probe": f"scontrol={pr['scontrol']}, kubectl={pr['kubectl']}",
           "needs": ["lab Slurm or Kubernetes"]},
          {"part": "multi-node DDP with NCCL/process-group timeout", "probe": f"GPUs={ctx.torch.cuda.device_count() if ctx.is_gpu else 0}",
           "needs": [">= 2 GPU nodes with RDMA"]}]
    return {"metrics": {"detect_s_median": round(med("detect_s"), 3), "resume_s_median": round(med("resume_s"), 3),
                        "steps_lost_median": med("steps_lost"), "init_s_median": round(med("init_s"), 3),
                        "ckpt_mb": round(med("ckpt_bytes") / 1e6, 1)},
            "drills": drills, "config": cfg, "rule_l1": rule, "prediction": pred, "read_bw_Bps": bw, "probes": pr,
            "not_runnable_parts": nr,
            "notes": ["Abort condition: the drill stops if the worker exits on its own or does not resume within 120 s. "
                      "Rollback: requeue from the last durable checkpoint, verified by the restored step in the new process's heartbeat.",
                      "Blast radius: one child process in a disposable container (--network none); nothing outside it is touched.",
                      f"Repetitions: {reps} drills, each with a seeded random kill time; medians reported.",
                      "Times are wall clock (time.time) shared by the monitor and the worker heartbeats."]}


def check(result: dict, env: dict) -> list[str]:
    fails = []
    cfg, pred = result["config"], result["prediction"]
    for d in result["drills"]:
        r = d["rep"]
        if d["restored_step"] != d["durable_step"]:
            fails.append(f"rep {r}: restored step {d['restored_step']} != last durable checkpoint {d['durable_step']}: "
                         "the restart loaded something other than the last committed checkpoint")
        if d["restored_step"] % cfg["every"]:
            fails.append(f"rep {r}: restored step {d['restored_step']} is not a checkpoint step (multiple of {cfg['every']})")
        if not (0 <= d["steps_lost"] < cfg["every"]):
            fails.append(f"rep {r}: {d['steps_lost']} steps lost, outside [0, {cfg['every']}): with a checkpoint every "
                         f"{cfg['every']} steps the loss is bounded by the interval; check durable-only-after-rename")
        # The rule measures silence since the last heartbeat, so the alert can never precede threshold + hold after it.
        # (detect_s from the kill can be shorter: a step or checkpoint write may already have been in progress.)
        if d["silence_to_alert_s"] < cfg["threshold_s"] + cfg["for_s"] - 0.01:
            fails.append(f"rep {r}: alert {d['silence_to_alert_s']:.2f} s after the last heartbeat, before threshold + for "
                         f"= {cfg['threshold_s'] + cfg['for_s']} s: the rule evaluation is wrong")
        if d["silence_to_alert_s"] > pred["detect_s_max"] + 0.5:
            fails.append(f"rep {r}: alert {d['silence_to_alert_s']:.2f} s after the last heartbeat, far above threshold + for + poll "
                         f"= {pred['detect_s_max']:.2f} s: the monitor is starved (check host load)")
        if d["resume_s"] <= d["detect_s"]:
            fails.append(f"rep {r}: resumed before the alert fired: the timestamps are inconsistent")
        parts = d["launch_s"] + d["init_s"] + d["load_s"] + d["first_step_s"]
        if abs(parts - d["requeue_to_resume_s"]) > 0.05:
            fails.append(f"rep {r}: restart parts sum to {parts:.3f} s but requeue->resume is {d['requeue_to_resume_s']:.3f} s")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    cfg, pred, dr = result["config"], result["prediction"], result["drills"]
    rule = result["rule_l1"]
    L = ["## The drill", "",
         f"Job: a {cfg['width']}-wide 4-layer MLP with Adam on the {'GPU' if gpu else 'CPU'}, a heartbeat every step, an atomic checkpoint "
         f"every {cfg['every']} steps (~{statistics.median(d['ckpt_bytes'] for d in dr) / 1e6:.0f} MB). Injection: SIGKILL at a seeded random "
         f"time after the first checkpoint. Alert rule: progress age > {cfg['threshold_s']} s for {cfg['for_s']} s, polled every "
         f"{cfg['poll_s'] * 1e3:.0f} ms."]
    if rule.get("name"):
        L.append(f"Same form as the L1 rule `{rule['name']}` in `{rule['source']}` ({rule['metric']} {rule['op']} {rule['threshold']} for "
                 f"{rule['for_s']} s), with the threshold scaled from an ORION step (~17 s plus checkpoint stall) to this job's "
                 f"~{statistics.median(d['step_time_s'] for d in dr) * 1e3:.1f} ms mean step (including the first, warm-up step).")
    L += ["", "| Rep | killed at step | restored | steps lost | heartbeat age at kill (s) | detect (s) | resume (s) | launch (s) | init (s) | ckpt load (ms) | first step (ms) |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in dr:
        L.append(f"| {d['rep']} | {d['last_step_before_kill']} | {d['restored_step']} | {d['steps_lost']} | {d['age_at_kill_s']:.3f} | "
                 f"{d['detect_s']:.3f} | {d['resume_s']:.3f} | "
                 f"{d['launch_s']:.3f} | {d['init_s']:.3f} | {d['load_s'] * 1e3:.0f} | {d['first_step_s'] * 1e3:.0f} |")
    m = result["metrics"]
    L += ["", "## Measured vs the simulator's recovery model", "", "| Quantity | predicted | measured median | min-max |", "|---|---|---|---|"]
    rng = lambda k: f"{min(d[k] for d in dr):.3f}-{max(d[k] for d in dr):.3f}"  # noqa: E731
    L += [f"| detect_s | {pred['detect_s']:.3f} (+ up to one poll and one step) | {m['detect_s_median']:.3f} | {rng('detect_s')} |",
          f"| checkpoint load (s) | {pred['load_s']:.3f} (bytes / {result['read_bw_Bps'] / 1e9:.2f} GB/s read) | "
          f"{statistics.median(d['load_s'] for d in dr):.3f} | {rng('load_s')} |",
          f"| resume_s (kill -> first new step) | {pred['resume_s']:.3f} | {m['resume_s_median']:.3f} | {rng('resume_s')} |",
          f"| steps lost | {pred['steps_lost_mean']:.1f} mean, max {pred['steps_lost_max']} | {m['steps_lost_median']} | "
          f"{min(d['steps_lost'] for d in dr)}-{max(d['steps_lost'] for d in dr)} |"]
    L += ["", "## Not runnable here", ""]
    for p in result["not_runnable_parts"]:
        L.append(f"- **{p['part']}**. Probe: {p['probe']}. Needs: {', '.join(p['needs'])}.")
    init_share = m["init_s_median"] / m["resume_s_median"] if m["resume_s_median"] else 0
    L += ["", "## What to conclude", "",
          f"- Recovery time is dominated by restart, not by loading the checkpoint: process launch plus framework"
          f"{' and CUDA context' if gpu else ''} initialisation take {init_share * 100:.0f} % of resume_s here. A simulator that models "
          "restart as checkpoint bytes / bandwidth alone underestimates RTO. Measure launch_s on the real stack.",
          "- Steps lost are bounded by the checkpoint interval only because a checkpoint counts once its rename commits. Kill "
          "during a save and the previous checkpoint is the one restored. The restored-step column shows it.",
          "- Detection is threshold + hold + one poll *after the last heartbeat*. Measured from the kill it can be shorter: when the "
          "kill lands during a checkpoint write, the job has already been silent for a while (see the heartbeat-age column).",
          "- Tighter thresholds detect faster but page on every checkpoint stall. "
          "The L1 rule's 120 s / 60 s exist because ORION's checkpoint stall is ~20 s."]
    if gpu:
        L.append("- This is a **laptop Ada GPU in a container, not ORION**: the absolute seconds are not transferable, the decomposition is.")
    else:
        L.append("- _CPU fallback: no GPU was used. The job ran on the CPU, so there is no CUDA-init term in the restart._")
    return "\n".join(L)
