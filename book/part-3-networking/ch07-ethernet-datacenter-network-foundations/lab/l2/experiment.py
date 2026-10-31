"""Ch 7 L2: probe for the container-fabric lab, then reproduce Section 7.6's ECMP statistics at scale.

The chapter's L2 extension builds a 2-spine x 4-leaf eBGP fabric with containerlab + FRR and times
reconvergence after a link failure. That needs a Linux host with containerlab, the Docker socket and
CAP_NET_ADMIN; the L2 harness runs each lab in an unprivileged container with ``--network none``. The
experiment probes for each prerequisite, records the fabric part as not runnable, and runs what does
apply on this host.

What runs (Section 7.6, "ECMP: how traffic is actually spread"): a vectorised Monte Carlo of per-flow
ECMP hashing for low-entropy RoCEv2 flows (fixed UDP destination port 4791; only the source port, one
per queue pair, varies). Real 5-tuples go through a real integer hash (a murmur3-style 64-bit
finaliser, the kind of mixing switch ASICs use) on the GPU, or on the CPU in the fallback. It
reproduces the manuscript's figures: P(8 flows land on 8 distinct links), the expected links used, the
most-loaded-link distribution (8 on 8 and 32 on 32), hash polarisation when two tiers use the same hash
function and seed, and how many flows keep their member after a link failure with modulo versus
resilient hashing. Every result is ``[SIMULATED]`` (hashing only: no queues, no congestion control),
and ``check()`` holds each one against its closed-form value. Trials per second is ``[MEASURED]``.

CPU fallback: the same Monte Carlo on the CPU with fewer trials; the invariants are identical.
"""
from __future__ import annotations

import math
import os
import shutil
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch07-l2",
    "title": "Lab 7 L2: container-fabric probe and an ECMP hashing Monte Carlo for low-entropy RoCE flows",
    "evidence": "SIMULATED",
    "gpu_optional": True,
    "cpu_fallback": "the same ECMP Monte Carlo on the CPU with fewer trials (the GPU only makes it faster)",
}

ROCE_DPORT = 4791
M64 = (1 << 64) - 1
# Section 7.6, 200,000 trials, seed 1: most-loaded link for 8 flows on 8 links [SIMULATED in the manuscript]
MANUSCRIPT_MAXLOAD_8x8 = {2: 0.499, 3: 0.409, "4+": 0.089}


def probe_fabric_lab() -> dict:
    status = Path("/proc/self/status").read_text() if Path("/proc/self/status").exists() else ""
    cap_eff = next((int(ln.split()[1], 16) for ln in status.splitlines() if ln.startswith("CapEff:")), 0)
    nets = sorted(p.name for p in Path("/sys/class/net").iterdir()) if Path("/sys/class/net").is_dir() else []
    return {
        "containerlab": shutil.which("containerlab"), "docker_cli": shutil.which("docker"),
        "docker_socket": Path("/var/run/docker.sock").exists(), "vtysh_frr": shutil.which("vtysh"),
        "cap_net_admin": bool(cap_eff & (1 << 12)), "euid": os.geteuid(), "netdevs": nets,
        "lo_mtu": (Path("/sys/class/net/lo/mtu").read_text().strip() if Path("/sys/class/net/lo/mtu").exists() else None),
        "fib_multipath_hash_policy": (Path("/proc/sys/net/ipv4/fib_multipath_hash_policy").read_text().strip()
                                      if Path("/proc/sys/net/ipv4/fib_multipath_hash_policy").exists() else None),
    }


def fmix64(torch, x):
    """murmur3 64-bit finaliser on int64 tensors (wrapping arithmetic; logical shifts emulated with masks)."""
    def shr(v, k):
        return (v >> k) & ((1 << (64 - k)) - 1)
    c1 = torch.tensor(0xFF51AFD7ED558CCD - (1 << 64), dtype=torch.int64, device=x.device)
    c2 = torch.tensor(0xC4CEB9FE1A85EC53 - (1 << 64), dtype=torch.int64, device=x.device)
    x = x ^ shr(x, 33)
    x = x * c1
    x = x ^ shr(x, 33)
    x = x * c2
    return x ^ shr(x, 33)


def five_tuple_hash(torch, src_ip, dst_ip, sport, seed: int):
    """Hash of (src IP, dst IP, proto 17, UDP sport, UDP dport 4791) with a per-switch seed; non-negative int64."""
    key = (src_ip * 0x100000001B3) ^ (dst_ip << 7) ^ (sport << 20) ^ (17 << 40) ^ (ROCE_DPORT << 44)
    h = fmix64(torch, key ^ fmix64(torch, torch.full_like(key, seed)))
    return h & ((1 << 62) - 1)


def flows(torch, trials: int, nflows: int, gen):
    """``trials`` independent draws of ``nflows`` RoCE flows between NIC pairs: random IPs and QP source ports."""
    dev = gen.device
    src_ip = torch.randint(0, 1 << 24, (trials, nflows), device=dev, generator=gen) + (10 << 24)
    dst_ip = torch.randint(0, 1 << 24, (trials, nflows), device=dev, generator=gen) + (10 << 24)
    sport = torch.randint(49152, 65536, (trials, nflows), device=dev, generator=gen)
    return src_ip, dst_ip, sport


def ecmp_trial_stats(torch, trials: int, nflows: int, nlinks: int, gen, seed: int = 0x5EED) -> dict:
    s, d, p = flows(torch, trials, nflows, gen)
    member = five_tuple_hash(torch, s, d, p, seed) % nlinks
    counts = torch.zeros(trials, nlinks, dtype=torch.int64, device=member.device)
    counts.scatter_add_(1, member, torch.ones_like(member))
    maxload = counts.max(dim=1).values
    used = (counts > 0).sum(dim=1).double()
    dist = {k: (maxload == k).double().mean().item() for k in range(1, nflows + 1)}
    return {"p_all_distinct": (maxload == 1).double().mean().item(), "links_used_mean": used.mean().item(),
            "maxload_dist": dist, "trials": trials, "flows": nflows, "links": nlinks}


def polarization(torch, nflows: int, gen, same_seed: bool) -> dict:
    """Leaf picks uplink h mod 32 (uplink i -> spine i mod 4); spine-1 picks among 8 links with h' mod 8."""
    s, d, p = flows(torch, 1, nflows, gen)
    h_leaf = five_tuple_hash(torch, s, d, p, 0x11)[0]
    at_spine1 = (h_leaf % 32) % 4 == 0
    h_spine = h_leaf if same_seed else five_tuple_hash(torch, s, d, p, 0x22)[0]
    links = torch.unique(h_spine[at_spine1] % 8)
    return {"flows_at_spine1": int(at_spine1.sum().item()), "spine1_links_used": int(links.numel())}


def rehash_on_failure(torch, nflows: int, gen) -> dict:
    """Fraction of flows that keep their ECMP member when one of 32 members fails."""
    s, d, p = flows(torch, 1, nflows, gen)
    h = five_tuple_hash(torch, s, d, p, 0x33)[0]
    before = h % 32
    failed = 5
    modulo_after = torch.where(h % 31 >= failed, h % 31 + 1, h % 31)  # surviving members renumbered around the hole
    # resilient: a 32-bucket table; only the failed member's buckets are reassigned (round-robin to survivors)
    survivors = torch.tensor([m for m in range(32) if m != failed], device=h.device)
    resilient_after = torch.where(before == failed, survivors[h % 31], before)
    keep_mod = ((modulo_after == before) & (before != failed)).double().mean().item()
    keep_res = ((resilient_after == before) & (before != failed)).double().mean().item()
    on_failed = (before == failed).double().mean().item()
    return {"modulo_keep_fraction": keep_mod, "resilient_keep_fraction": keep_res, "on_failed_member": on_failed,
            "resilient_keep_of_survivors": keep_res / (1 - on_failed)}


def run(ctx) -> dict:
    torch = ctx.torch
    dev = "cuda" if ctx.is_gpu else "cpu"
    gen = torch.Generator(device=dev)
    gen.manual_seed(1)
    trials = (200_000 if ctx.quick else 2_000_000) if ctx.is_gpu else (100_000 if ctx.quick else 400_000)
    probe = probe_fabric_lab()

    def eight():
        return ecmp_trial_stats(torch, trials, 8, 8, gen)

    t = ctx.bench(eight, warmup=1, reps=ctx.reps(5))
    r88 = eight()
    r3232 = ecmp_trial_stats(torch, max(trials // 8, 20_000), 32, 32, gen)
    pol_same = polarization(torch, 400_000, gen, same_seed=True)
    pol_seeded = polarization(torch, 400_000, gen, same_seed=False)
    rh = rehash_on_failure(torch, 400_000, gen)

    analytic = {
        "p_all_distinct_8x8": math.factorial(8) / 8 ** 8,
        "links_used_8x8": 8 * (1 - (7 / 8) ** 8),
        "links_used_32x32": 32 * (1 - (31 / 32) ** 32),
        "modulo_keep_32": 1 / 32,  # h mod 32 == renumbered h mod 31 for about 1/32 of flows
        "resilient_keep_of_survivors": 1.0,
    }
    d88 = r88["maxload_dist"]
    sim_88 = {2: d88[2], 3: d88[3], "4+": sum(v for k, v in d88.items() if k >= 4)}
    d32 = r3232["maxload_dist"]
    metrics = {
        "trials_8x8": trials, "trials_per_s": round(trials / t["median"], 0), "trial_batch_s_median": round(t["median"], 4),
        "p_all_distinct_8x8": r88["p_all_distinct"], "links_used_8x8": round(r88["links_used_mean"], 4),
        "maxload_8x8_2": round(sim_88[2], 4), "maxload_8x8_3": round(sim_88[3], 4), "maxload_8x8_4plus": round(sim_88["4+"], 4),
        "links_used_32x32": round(r3232["links_used_mean"], 3),
        "p_link_ge3_32x32": round(sum(v for k, v in d32.items() if k >= 3), 4),
        "polarized_spine1_links_used": pol_same["spine1_links_used"],
        "seeded_spine1_links_used": pol_seeded["spine1_links_used"],
        "modulo_keep_fraction": round(rh["modulo_keep_fraction"], 4),
        "resilient_keep_of_survivors": round(rh["resilient_keep_of_survivors"], 4),
        "fabric_lab_runnable": False,
    }
    tables = {
        "ecmp_8x8": [{"most_loaded_link_flows": k, "simulated": round(sim_88[k], 4),
                      "manuscript_simulated": MANUSCRIPT_MAXLOAD_8x8[k]} for k in (2, 3, "4+")],
        "analytic": [{"quantity": k, "closed_form": round(v, 5), "simulated": round(
            {"p_all_distinct_8x8": r88["p_all_distinct"], "links_used_8x8": r88["links_used_mean"],
             "links_used_32x32": r3232["links_used_mean"], "modulo_keep_32": rh["modulo_keep_fraction"],
             "resilient_keep_of_survivors": rh["resilient_keep_of_survivors"]}[k], 5)} for k, v in analytic.items()],
        "probe": [probe],
    }
    ctx.log(f"8 flows/8 links: P(distinct)={r88['p_all_distinct'] * 100:.3f} %, links used {r88['links_used_mean']:.3f}; "
            f"polarised spine-1 uses {pol_same['spine1_links_used']}/8 links, seeded {pol_seeded['spine1_links_used']}/8; "
            f"{trials / t['median']:.3g} trials/s on {dev}")
    not_runnable = [{
        "part": "containerlab 2-spine x 4-leaf eBGP fabric (FRR): ECMP next-hop counts, BFD, reconvergence loss window",
        "needs": ["a Linux host with containerlab and FRR images", "the Docker socket", "root / CAP_NET_ADMIN",
                  "network namespaces the lab may create (the harness runs with --network none)"],
        "probe": probe,
    }]
    notes = [
        "[SIMULATED] ECMP hashing only: flows are independent, constant-rate and never adapt; there are no queues, ECN or PFC.",
        "Flows: random 10.x.y.z source/destination NICs, UDP source port per queue pair in 49152-65535, destination port 4791.",
        f"Timing [MEASURED]: {t['n']} repetitions of the {trials}-trial 8x8 batch after 1 warm-up; median "
        f"{t['median'] * 1e3:.1f} ms, p95 {t['p95'] * 1e3:.1f} ms.",
    ]
    return {"metrics": metrics, "tables": tables, "notes": notes, "not_runnable_parts": not_runnable}


def check(result: dict, env: dict) -> list[str]:
    m = result["metrics"]
    fails = []
    n = m["trials_8x8"]
    p0 = math.factorial(8) / 8 ** 8
    se = math.sqrt(p0 * (1 - p0) / n)
    if abs(m["p_all_distinct_8x8"] - p0) > max(4 * se, 1e-4):
        fails.append(f"P(8 flows on 8 distinct links) {m['p_all_distinct_8x8']:.5f} vs closed form {p0:.5f}: the hash is "
                     "not uniform (check the masking in fmix64) or the trial count is wrong")
    if abs(m["links_used_8x8"] - 8 * (1 - (7 / 8) ** 8)) > 0.01:
        fails.append(f"expected links used {m['links_used_8x8']} vs 5.251: check the per-trial bincount")
    if abs(m["links_used_32x32"] - 32 * (1 - (31 / 32) ** 32)) > 0.05:
        fails.append(f"32x32 links used {m['links_used_32x32']} vs 20.39 closed form")
    for k, key in ((2, "maxload_8x8_2"), (3, "maxload_8x8_3"), ("4+", "maxload_8x8_4plus")):
        if abs(m[key] - MANUSCRIPT_MAXLOAD_8x8[k]) > 0.01:
            fails.append(f"most-loaded-link share for {k} flows {m[key]:.3f} disagrees with the manuscript's "
                         f"{MANUSCRIPT_MAXLOAD_8x8[k]} by > 1 point")
    if not 0.95 <= m["p_link_ge3_32x32"] <= 0.99:
        fails.append(f"P(a link with >= 3 of 32 flows) {m['p_link_ge3_32x32']} outside the manuscript's ~97 %")
    if m["polarized_spine1_links_used"] != 2:
        fails.append(f"same-hash polarisation should leave spine-1 using exactly 2 of 8 links (h mod 8 in {{0, 4}}), got "
                     f"{m['polarized_spine1_links_used']}")
    if m["seeded_spine1_links_used"] != 8:
        fails.append("with a different seed at the spine all 8 links should be used")
    if abs(m["modulo_keep_fraction"] - 1 / 32) > 0.01:
        fails.append(f"modulo rehash kept {m['modulo_keep_fraction']:.3f} of flows, expected ~1/32")
    if m["resilient_keep_of_survivors"] < 0.9999:
        fails.append("resilient hashing must keep every flow whose member survived")
    if m["fabric_lab_runnable"]:
        fails.append("fabric part marked runnable without a containerlab run")
    return fails


def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    lines = ["## Section 7.6 reproduced: 8 RoCE flows hashed onto 8 equal-cost links `[SIMULATED]`", "",
             f"{m['trials_8x8']:,} trials. P(all eight on distinct links) **{m['p_all_distinct_8x8'] * 100:.3f} %**; expected "
             f"links used **{m['links_used_8x8']:.3f} of 8**.", "",
             "| Most-loaded link carries | This run | Manuscript (200,000 trials) |", "|---|---|---|"]
    for r in t["ecmp_8x8"]:
        lines.append(f"| {r['most_loaded_link_flows']} flows | {r['simulated'] * 100:.1f} % | {r['manuscript_simulated'] * 100:.1f} % |")
    lines += ["", "## Simulation against closed form", "", "| Quantity | Closed form `[MODELED]` | Simulated |", "|---|---|---|"]
    for r in t["analytic"]:
        lines.append(f"| {r['quantity']} | {r['closed_form']} | {r['simulated']} |")
    lines += ["", f"32 flows on 32 links: a link with >= 3 flows in **{m['p_link_ge3_32x32'] * 100:.1f} %** of trials.",
              f"Polarisation: with the leaf's hash reused at the spine, spine-1 used **{m['polarized_spine1_links_used']} of 8** "
              f"links toward the destination leaf; with its own seed it used {m['seeded_spine1_links_used']} of 8.",
              f"Link failure (32 -> 31 members): modulo rehash kept **{m['modulo_keep_fraction'] * 100:.1f} %** of flows on "
              f"their member; resilient hashing kept {m['resilient_keep_of_survivors'] * 100:.1f} % of the flows whose member "
              "survived.", "",
              f"Monte Carlo speed `[MEASURED]` on {'the GPU' if env['device'] == 'cuda' else 'the CPU'}: "
              f"{m['trials_per_s']:,.0f} trials/s.", "",
              "What to conclude: ECMP balances *flows*, not bytes. With the handful of flows an AI collective presents, "
              "collisions are the norm (some link carries two or more flows in over 99 % of trials), polarisation silently "
              "idles links, and a plain modulo rehash moves almost every flow when one member fails. None of this needs a "
              "fault to happen; it is why the book keeps collectives on rails, adds QPs, and asks for resilient hashing.",
              "", "## Not runnable on this host", ""]
    for p in result.get("not_runnable_parts", []):
        pr = p["probe"]
        lines.append(f"- **{p['part']}**: needs {', '.join(p['needs'])}. Probe: containerlab "
                     f"{'found' if pr['containerlab'] else 'absent'}, Docker socket {'present' if pr['docker_socket'] else 'absent'}, "
                     f"CAP_NET_ADMIN {'yes' if pr['cap_net_admin'] else 'no'}, interfaces {pr['netdevs']}.")
    return "\n".join(lines)
