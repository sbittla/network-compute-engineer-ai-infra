"""Ch 17 L2: the GPU as a schedulable resource: discovery, what a scheduler would see, and what sharing costs.

The chapter's L2 extension installs kind/k3s with the GPU Operator (or a single-node Slurm with
``gres/gpu``) and reproduces planted pending causes. This harness runs each lab in an unprivileged
container with no network, no kubelet and no slurmd, so that part is probed and recorded as not
runnable. Three things do apply to one GPU host, and the experiment measures them:

1. **Discovery.** It reads what a device plugin / GPU Feature Discovery would read (``nvidia-smi -L``,
   UUID, memory, compute capability, MIG mode, compute mode, the ``/dev/nvidia*`` device nodes) and
   derives the node's ``nvidia.com/gpu`` capacity, the ``nvidia.com/gpu.product`` label, and the
   ``gres.conf`` line a Slurm admin would write. It records what is missing on this host (WSL2 exposes
   ``/dev/dxg``, not ``/dev/nvidia0``).
2. **The lab's diagnoser on this real node.** The node object built from that discovery goes through
   ``diagnose_pending`` twice: as found (hardware present, no device plugin advertising it), then as it
   would be with a plugin running, for three jobs (1 GPU, 2 GPUs, an H100 node selector).
3. **Why a GPU is allocated whole.** Two independent processes ("jobs") run the same GEMM loop on the
   one GPU, alone and then together under the driver's default time-slicing, interleaved over >= 5
   repetitions. It measures per-job throughput, the slowdown, aggregate throughput, and whether one
   job's allocation is visible in the other's free memory (no isolation). This is the evidence behind
   integer ``nvidia.com/gpu`` requests, and behind MIG or MPS when sharing is intended.

CPU fallback: discovery and the diagnoser run unchanged (they report no GPU). The sharing test runs
two CPU processes pinned to the same two cores, the CPU analogue of oversubscribing one device. The
GPU-memory isolation check is skipped.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch17-l2",
    "title": "Lab 17 L2: the GPU as a schedulable resource (discovery, diagnoser, time-slicing cost)",
    "evidence": "MEASURED",
    "cpu_fallback": ("discovery and the pending-job diagnoser on this host (no GPU found), and the sharing test with two "
                     "CPU processes pinned to the same two cores"),
}

PKG = Path(__file__).resolve().parents[2]

WORKER = r"""
import json, sys, time, os
import torch
dev, n, threads, cpus = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
if cpus != "-":
    os.sched_setaffinity(0, {int(c) for c in cpus.split(",")})
torch.set_num_threads(threads)
dt = torch.float16 if dev == "cuda" else torch.float32
a = torch.randn(n, n, device=dev, dtype=dt); b = torch.randn(n, n, device=dev, dtype=dt); c = torch.empty_like(a)
sync = torch.cuda.synchronize if dev == "cuda" else (lambda: None)
for _ in range(5): torch.matmul(a, b, out=c)
sync()
print(json.dumps({"ready": True}), flush=True)
hold = []
for line in sys.stdin:
    cmd = line.split()
    if cmd[0] == "run":
        secs, it, t0 = float(cmd[1]), 0, time.perf_counter()
        while time.perf_counter() - t0 < secs:
            for _ in range(10): torch.matmul(a, b, out=c)
            sync(); it += 10
        el = time.perf_counter() - t0
        print(json.dumps({"tflops": 2 * n ** 3 * it / el / 1e12, "iters": it, "s": el}), flush=True)
    elif cmd[0] == "mem":
        f, t = torch.cuda.mem_get_info() if dev == "cuda" else (0, 0)
        print(json.dumps({"free": f, "total": t}), flush=True)
    elif cmd[0] == "alloc":
        hold.append(torch.empty(int(cmd[1]), dtype=torch.uint8, device=dev)); sync()
        print(json.dumps({"held": sum(h.numel() for h in hold)}), flush=True)
    elif cmd[0] == "quit":
        break
"""


def sh(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip("\n")
    except FileNotFoundError:
        return 127, f"{cmd[0]}: command not found"
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)


def load_l1(name: str):
    """The L1 module: the reference solution if present, else the learner's starter (student release)."""
    for d in (PKG / "solutions" / "lab", PKG / "lab" / "starter"):
        p = d / f"{name}.py"
        if p.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            try:
                spec.loader.exec_module(mod)
                return mod, p.relative_to(PKG).as_posix()
            except Exception:  # noqa: BLE001
                continue
    return None, None


# --------------------------------------------------------------------------------------------- discovery
def discover() -> dict:
    rc, listing = sh(["nvidia-smi", "-L"])
    gpus = re.findall(r"GPU (\d+): (.+?) \(UUID: (GPU-[0-9a-f-]+)\)", listing) if rc == 0 else []
    rc, q = sh(["nvidia-smi", "--query-gpu=name,memory.total,compute_cap,mig.mode.current,compute_mode",
                "--format=csv,noheader,nounits"])
    rows = [[v.strip() for v in ln.split(",")] for ln in q.splitlines()] if rc == 0 else []
    dev_nodes = sorted(str(p) for p in Path("/dev").glob("nvidia*")) + (["/dev/dxg"] if Path("/dev/dxg").exists() else [])
    sched = {t: bool(shutil.which(t)) for t in ("kubectl", "kubelet", "k3s", "kind", "sinfo", "scontrol", "slurmd")}
    in_k8s = Path("/var/run/secrets/kubernetes.io").exists()
    gres_conf = Path("/etc/slurm/gres.conf").exists()
    out = {"gpus": [], "device_nodes": dev_nodes, "scheduler_tools": sched, "in_kubernetes_pod": in_k8s,
           "slurm_gres_conf": gres_conf}
    for (idx, name, uuid), r in zip(gpus, rows):
        out["gpus"].append({"index": int(idx), "name": name, "uuid": uuid, "memory_mib": int(float(r[1])),
                            "compute_cap": r[2], "mig_mode": r[3], "compute_mode": r[4]})
    if out["gpus"]:
        g = out["gpus"][0]
        major, minor = g["compute_cap"].split(".")
        product = re.sub(r"\s+", "-", g["name"].strip())
        out["advertised"] = {
            "capacity": {"nvidia.com/gpu": len(out["gpus"])},
            "labels": {"nvidia.com/gpu.product": product, "nvidia.com/gpu.count": str(len(out["gpus"])),
                       "nvidia.com/gpu.memory": str(g["memory_mib"]), "nvidia.com/gpu.compute.major": major,
                       "nvidia.com/gpu.compute.minor": minor,
                       "nvidia.com/mig.capable": "false" if g["mig_mode"] in ("[N/A]", "N/A") else "true"},
            "gres_conf": (f"NodeName=<this-node> Name=gpu Type={product.lower().replace('nvidia-', '')} "
                          f"File=/dev/nvidia{g['index']}"),
            "gres_file_exists": Path(f"/dev/nvidia{g['index']}").exists(),
        }
    return out


def diagnose(disc: dict) -> list[dict]:
    mod, src = load_l1("orion_sched")
    phys = len(disc["gpus"])
    product = disc.get("advertised", {}).get("labels", {}).get("nvidia.com/gpu.product", "none")
    node = {"name": "this-host", "schedulable": True, "physical_gpus": phys, "conditions": {"Ready": True},
            "labels": {"nvidia.com/gpu.product": product}, "taints": [], "allocated": {"nvidia.com/gpu": 0}}
    jobs = {
        "1 GPU": {"gpus_per_node": 1, "nodes": 1, "node_selector": {}, "tolerations": []},
        "2 GPUs": {"gpus_per_node": 2, "nodes": 1, "node_selector": {}, "tolerations": []},
        "1 GPU, selector H100": {"gpus_per_node": 1, "nodes": 1, "tolerations": [],
                                 "node_selector": {"nvidia.com/gpu.product": "NVIDIA-H100-80GB-HBM3"}},
    }
    rows = []
    for state, alloc in (("as found (no device plugin running)", 0), ("with a device plugin advertising", phys)):
        n = {**node, "allocatable": {"nvidia.com/gpu": alloc}, "capacity": {"nvidia.com/gpu": alloc}}
        for jname, job in jobs.items():
            if state.startswith("as found") and jname != "1 GPU":
                continue
            case = {"case_id": f"L2-{len(rows) + 1}", "job": {**job, "resource": "nvidia.com/gpu", "name": jname,
                                                               "tenant": "lab"}, "nodes": [n], "quota": None}
            try:
                causes = mod.diagnose_pending(case) if mod else ["module not found"]
            except Exception as exc:  # noqa: BLE001 - starter TODO
                causes = [f"not implemented ({type(exc).__name__})"]
            rows.append({"node_state": state, "job": jname, "physical_gpus": phys, "allocatable": alloc,
                         "diagnosis": causes, "module": src})
    return rows


# --------------------------------------------------------------------------------------------- sharing
class Job:
    def __init__(self, dev: str, n: int, threads: int, cpus: str):
        import tempfile  # noqa: PLC0415
        for attempt in range(2):  # one retry: CUDA context creation can fail transiently on a busy shared GPU
            self.err = tempfile.TemporaryFile(mode="w+")
            self.p = subprocess.Popen([sys.executable, "-c", WORKER, dev, str(n), str(threads), cpus],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err, text=True)
            try:
                self.recv()
                return
            except RuntimeError:
                if attempt:
                    raise
                time.sleep(3)

    def send(self, line: str) -> None:
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def recv(self) -> dict:
        line = self.p.stdout.readline()
        if not line:
            self.p.wait(timeout=10)
            self.err.seek(0)
            raise RuntimeError(f"worker process exited ({self.p.returncode}): {self.err.read()[-800:]}")
        return json.loads(line)

    def close(self) -> None:
        try:
            self.send("quit")
            self.p.wait(timeout=20)
        except Exception:  # noqa: BLE001
            self.p.kill()


def smi_used_mib() -> float | None:
    rc, out = sh(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"])
    try:
        return float(out.splitlines()[0])
    except (ValueError, IndexError):
        return None


def sharing(ctx) -> dict:
    gpu = ctx.is_gpu
    secs = 1.0 if ctx.quick else 2.0
    reps = ctx.reps(8)
    if gpu:
        dev, n, threads, cpus = "cuda", 2048, 1, "-"
    else:
        avail = sorted(os.sched_getaffinity(0))
        dev, n, threads, cpus = "cpu", 768, 2, ",".join(map(str, avail[:2]))
    a, b = Job(dev, n, threads, cpus), Job(dev, n, threads, cpus)
    solo, pair_a, pair_b, pair_sum = [], [], [], []
    mem = {}
    try:
        for _ in range(reps):  # interleave solo and pair so drift (thermals, other tenants) hits both alike
            a.send(f"run {secs}")
            solo.append(a.recv()["tflops"])
            a.send(f"run {secs}")
            b.send(f"run {secs}")
            ra, rb = a.recv()["tflops"], b.recv()["tflops"]
            pair_a.append(ra)
            pair_b.append(rb)
            pair_sum.append(ra + rb)
        if gpu:
            a.send("mem")
            before = a.recv()
            smi_before = smi_used_mib()
            b.send(f"alloc {1 << 30}")
            b.recv()
            a.send("mem")
            after = a.recv()
            smi_after = smi_used_mib()
            mem = {"smi_used_before_mib": smi_before, "smi_used_after_mib": smi_after,"a_free_before_gib": before["free"] / 2 ** 30, "a_free_after_b_alloc_gib": after["free"] / 2 ** 30,
                   "b_alloc_gib": 1.0, "total_gib": before["total"] / 2 ** 30,
                   "drop_seen_by_a_gib": (before["free"] - after["free"]) / 2 ** 30}
    finally:
        a.close()
        b.close()
    per_job = pair_a + pair_b
    med = statistics.median
    return {"device": dev, "n": n, "seconds_per_rep": secs, "reps": reps, "cpus": cpus,
            "solo": solo, "pair_a": pair_a, "pair_b": pair_b, "pair_sum": pair_sum,
            "solo_median": med(solo), "pair_per_job_median": med(per_job), "pair_sum_median": med(pair_sum),
            "slowdown": med(solo) / med(per_job), "aggregate_vs_solo": med(pair_sum) / med(solo),
            "fairness_a_over_b": med(pair_a) / med(pair_b), "memory": mem}


def run(ctx) -> dict:
    disc = discover()
    diag = diagnose(disc)
    sh_res = sharing(ctx)
    unit = "TFLOP/s" if ctx.is_gpu else "TFLOP/s (CPU)"
    ctx.log(f"sharing on {sh_res['device']}: solo {sh_res['solo_median']:.3f} {unit}, per job when shared "
            f"{sh_res['pair_per_job_median']:.3f}, slowdown {sh_res['slowdown']:.2f}x, aggregate {sh_res['aggregate_vs_solo']:.2f}x")
    metrics = {
        "physical_gpus": len(disc["gpus"]),
        "advertised_nvidia_com_gpu": disc.get("advertised", {}).get("capacity", {}).get("nvidia.com/gpu", 0),
        "gpu_product_label": disc.get("advertised", {}).get("labels", {}).get("nvidia.com/gpu.product"),
        "mig_capable": disc.get("advertised", {}).get("labels", {}).get("nvidia.com/mig.capable"),
        "nvidia_device_nodes": [d for d in disc["device_nodes"] if "nvidia" in d],
        "solo_tflops_median": round(sh_res["solo_median"], 4), "shared_per_job_tflops_median": round(sh_res["pair_per_job_median"], 4),
        "shared_slowdown": round(sh_res["slowdown"], 3), "shared_aggregate_vs_solo": round(sh_res["aggregate_vs_solo"], 3),
        "shared_fairness_a_over_b": round(sh_res["fairness_a_over_b"], 3),
        "diagnosis_as_found": diag[0]["diagnosis"] if diag else None,
    }
    if sh_res["memory"]:
        metrics["memory_drop_seen_by_other_job_gib"] = round(sh_res["memory"]["drop_seen_by_a_gib"], 3)
    not_runnable = [{
        "part": "kind/k3s + GPU Operator (or single-node Slurm with gres/gpu): allocatable snapshot, taint/quota/selector "
                "events reproduced on a lab node",
        "needs": ["a Linux GPU host where you can run a kubelet or slurmd (root)", "the NVIDIA device plugin / GPU Operator",
                  "/dev/nvidia* device nodes (WSL2 exposes /dev/dxg)", "network for the control plane"],
        "probe": {k: disc[k] for k in ("scheduler_tools", "in_kubernetes_pod", "slurm_gres_conf", "device_nodes")}},
        {"part": "L3: 2-node all_reduce_perf under two placements, gang time-to-start",
         "needs": [">= 2 multi-GPU nodes with RDMA NICs", "Slurm or Kubernetes with gang scheduling"],
         "probe": f"{len(disc['gpus'])} GPU(s), one host"}]
    notes = [
        f"Sharing test: two independent worker processes, each a GEMM loop ({sh_res['n']}^3, "
        f"{'FP16 on the GPU' if ctx.is_gpu else 'FP32 on CPUs ' + sh_res['cpus']}), {sh_res['seconds_per_rep']} s per "
        f"measurement; solo and shared measurements interleaved, {sh_res['reps']} repetitions each; after 5 warm-up GEMMs.",
        "Labels follow GPU Feature Discovery's naming (nvidia.com/gpu.product = the product name with spaces as '-').",
    ]
    return {"metrics": metrics, "tables": {"discovery": [disc], "diagnoser": diag, "sharing": [sh_res]},
            "notes": notes, "not_runnable_parts": not_runnable}


def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    s = t["sharing"][0]
    fails = []
    if s["reps"] < 5:
        fails.append("fewer than 5 sharing repetitions")
    if s["pair_per_job_median"] > 0.8 * s["solo_median"]:
        fails.append(f"a job sharing the device kept {s['pair_per_job_median'] / s['solo_median'] * 100:.0f} % of its solo "
                     "throughput: either the solo job did not saturate the device or the jobs did not overlap")
    if s["aggregate_vs_solo"] > 1.2:
        fails.append(f"two shared jobs together did {s['aggregate_vs_solo']:.2f}x one job: the solo run is not saturating "
                     "the device (raise the GEMM size)")
    if not 0.6 <= s["fairness_a_over_b"] <= 1.67:
        fails.append(f"time-slicing split throughput {s['fairness_a_over_b']:.2f}:1 between identical jobs")
    diag = t["diagnoser"]
    if diag and all(not d["diagnosis"][0].startswith(("not implemented", "module")) for d in diag):
        found = diag[0]
        if found["physical_gpus"] > 0 and "DEVICE_PLUGIN_NOT_ADVERTISING" not in found["diagnosis"]:
            fails.append("a node with physical GPUs and allocatable 0 must diagnose DEVICE_PLUGIN_NOT_ADVERTISING")
        sel = [d for d in diag if "selector" in d["job"]]
        if sel and found["physical_gpus"] > 0 and m["gpu_product_label"] != "NVIDIA-H100-80GB-HBM3" \
                and "SELECTOR_MISMATCH" not in sel[0]["diagnosis"]:
            fails.append("an H100 node selector on a non-H100 node must diagnose SELECTOR_MISMATCH")
    if env["device"] == "cuda":
        if m["physical_gpus"] < 1:
            fails.append("CUDA is available but nvidia-smi -L lists no GPU: check the discovery parser")
        mem = s["memory"]
        if mem and mem["drop_seen_by_a_gib"] > 1.5:
            fails.append(f"job A's free memory fell by {mem['drop_seen_by_a_gib']:.2f} GiB for a 1 GiB allocation by job B: "
                         "another tenant allocated during the test; rerun")
    return fails


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    d, s = t["discovery"][0], t["sharing"][0]
    gpu = env["device"] == "cuda"
    lines = ["## Discovery: what a device plugin would see", ""]
    if d["gpus"]:
        g = d["gpus"][0]
        adv = d["advertised"]
        lines += ["| Field | Value |", "|---|---|",
                  f"| Physical GPUs (nvidia-smi -L) | {len(d['gpus'])} |", f"| UUID | `{g['uuid']}` |",
                  f"| Memory | {g['memory_mib']} MiB |", f"| Compute capability | {g['compute_cap']} |",
                  f"| MIG mode | {g['mig_mode']} |", f"| Compute mode | {g['compute_mode']} |",
                  f"| Device nodes | {', '.join(d['device_nodes']) or 'none'} |",
                  f"| Would advertise | `nvidia.com/gpu: {adv['capacity']['nvidia.com/gpu']}` |"]
        for k, v in adv["labels"].items():
            lines.append(f"| label `{k}` | `{v}` |")
        lines += [f"| Slurm gres.conf | `{adv['gres_conf']}` (device file {'present' if adv['gres_file_exists'] else 'ABSENT here'}) |"]
    else:
        lines.append(f"No GPU found (nvidia-smi absent or no devices). Device nodes: {d['device_nodes'] or 'none'}.")
    lines += ["", f"Scheduler components present: {', '.join(k for k, v in d['scheduler_tools'].items() if v) or 'none'}.", "",
              "## The lab's diagnoser on this node", "", "| Node state | Job | Physical GPUs | Allocatable | Diagnosis |",
              "|---|---|---|---|---|"]
    for r in t["diagnoser"]:
        lines.append(f"| {r['node_state']} | {r['job']} | {r['physical_gpus']} | {r['allocatable']} | {', '.join(r['diagnosis'])} |")
    unit = "TFLOP/s" if gpu else "TFLOP/s (CPU)"
    lines += ["", "The 2-GPU job on a 1-GPU node comes back NONE_FOUND: the diagnoser explains pending-*despite*-free-GPUs "
              "cases, and this one is plain insufficient capacity (Kubernetes: `Insufficient nvidia.com/gpu`).", "",
              f"## Sharing one {'GPU' if gpu else 'set of two CPU cores'} between two jobs `[MEASURED]`", "",
              f"| Measurement | Median {unit} | Min | Max | n |", "|---|---|---|---|---|"]
    for name, xs in (("job alone", s["solo"]), ("job A, shared", s["pair_a"]), ("job B, shared", s["pair_b"]),
                     ("A + B, shared", s["pair_sum"])):
        lines.append(f"| {name} | {statistics.median(xs):.3f} | {min(xs):.3f} | {max(xs):.3f} | {len(xs)} |")
    lines += ["", f"Slowdown per job **{m['shared_slowdown']:.2f}x**; aggregate **{m['shared_aggregate_vs_solo']:.2f}x** of one "
              f"job alone; split A:B {m['shared_fairness_a_over_b']:.2f}."]
    mem_line = ""
    if s["memory"]:
        mem = s["memory"]
        lines.append(f"When job B allocated 1 GiB, job A's free memory (cudaMemGetInfo) dropped by "
                     f"**{mem['drop_seen_by_a_gib']:.2f} GiB** ({mem['a_free_before_gib']:.2f} -> "
                     f"{mem['a_free_after_b_alloc_gib']:.2f} GiB of {mem['total_gib']:.2f}); nvidia-smi memory.used went "
                     f"{mem['smi_used_before_mib']} -> {mem['smi_used_after_mib']} MiB.")
        if mem["drop_seen_by_a_gib"] >= 0.9:
            mem_line = ("Memory is not isolated either: job B's allocation came straight out of job A's free memory, so one "
                        "job can push the other out of memory.")
        else:
            smi_delta = ((mem["smi_used_after_mib"] or 0) - (mem["smi_used_before_mib"] or 0)) / 1024
            mem_line = (f"The device-wide view (nvidia-smi) shows job B's allocation ({smi_delta:.2f} GiB more in use), but job "
                        "A's own free-memory query did not move: under WSL2 the Windows (WDDM) driver virtualises and pages GPU "
                        "memory per process, so a job cannot see its neighbour coming. On bare-metal Linux the drop is visible "
                        "in both views; either way nothing stops one job pushing the other out of memory.")
    first = t["diagnoser"][0]["diagnosis"] if t["diagnoser"] else ["n/a"]
    lines += ["", "What to conclude:", "",
              ("- A GPU that is not advertised does not exist to the scheduler: with the hardware present and no device plugin, "
               f"the diagnoser says {', '.join(first)}, the same evidence as an allocatable of 0 on a real node.") if gpu else
              (f"- With no GPU at all the node has nothing to advertise and the diagnoser says {', '.join(first)}: a pending GPU "
               "job here is plain missing capacity, not a misconfiguration."),
              f"- Two jobs on one device under time-slicing each ran {m['shared_slowdown']:.2f}x slower and together did "
              f"{m['shared_aggregate_vs_solo']:.2f}x the work of one job alone: sharing buys nothing for throughput-bound "
              f"jobs, stretches each one's step time{' by more than 2x, because context switching costs extra' if m['shared_slowdown'] > 2 else ''}, "
              f"and is invisible to the scheduler. {mem_line} That is why `nvidia.com/gpu` is an integer resource, and why sharing is an "
              f"explicit choice (time-slicing replicas, MPS, or MIG on parts that support it; this one reports MIG "
              f"{m['mig_capable'] == 'true' and 'capable' or 'not supported'}).",
              ("- Labels come from the hardware: a job pinned to an H100 product label will never land here, and the diagnoser "
               "says why (SELECTOR_MISMATCH).") if gpu else "- Labels come from the hardware: with no GPU there are none to match.",
              "- This is one laptop host, not an 8-GPU HX8 node: socket-aware placement, rails and gang scheduling need "
              "the L3 multi-node setup."]
    if not gpu:
        lines += ["", "_CPU fallback: no GPU was found, so discovery shows an empty node; the sharing test used two CPU "
                  "processes on the same two cores, and the GPU-memory isolation check was skipped._"]
    lines += ["", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}.")
    return "\n".join(lines)
