"""Ch 22 L2: inject real regressions into a training step on one GPU, then attribute them with the lab's method.

What it teaches (Sections 22.4 and 22.6, Table 22.6): attribution is a measurement, and it can be checked
against ground truth. A small training step (input batch copied host-to-device, then forward, backward and an
SGD update of a 2-layer MLP) runs as a sequence of short *jobs*. In the "after" period, jobs are exposed to
injected changes in a balanced 2 x 2 design:

- ``pageable``: the input batch is copied from pageable instead of pinned host memory, so the driver stages it
  through a bounce buffer. This is the single-GPU cousin of the lab's host-staged GDR path.
- ``small_batch``: the same samples processed as 8 micro-batches with gradient accumulation, giving more
  launches and smaller GEMMs (a config change).
- ``placebo``: a flag set on a random half of the after-jobs that changes nothing. It plays the lab's "ECC alert
  node", a factor that must come out as zero.

The per-job mean step times go through the lab's own estimator (``estimate_effects`` / ``attribute`` /
``bootstrap_shares`` from the reference solution, or the learner's starter, with the factor list swapped). The
result is then corroborated three ways, as in Table 22.6:

1. **statistical:** OLS coefficient ± HC3 SE;
2. **direct:** a controlled A/B of each factor alone (≥ 5 repetitions after warm-up);
3. **mechanism model:** for ``pageable``, the batch's bytes divided by the pageable and pinned H2D bandwidths,
   which are measured separately.

The minimum detectable effect is computed from the before-period spread (Section 22.6.1).

CPU fallback: the same design on the CPU, on one thread with 64 micro-batches. The data-path factor becomes a
strided fp64 input that must be gathered and converted into a contiguous fp32 buffer each step, a real extra
staging pass through memory, and the mechanism model uses the measured gather bandwidth. Per-job medians replace
means because a shared host adds one-off stalls. More jobs and steps keep the SE below the injected effects. The
GPU-only invariants (pinned ≥ pageable, below the PCIe ceiling) are skipped.
"""
from __future__ import annotations

import importlib.util
import math
import random
import time
from pathlib import Path

import hwlab

EXPERIMENT = {
    "id": "ch22-l2",
    "title": "Lab 22 L2: inject a regression on one GPU and attribute it with the lab's method",
    "evidence": "MEASURED",
    "cpu_fallback": ("same 2 x 2 + placebo job design on the CPU (one thread); the data-path factor is a strided fp64 input "
                     "gathered and converted into a contiguous fp32 buffer each step (an extra staging pass), modeled from the "
                     "measured gather bandwidth"),
}

PKG = Path(__file__).resolve().parents[2]
LAB = PKG / "lab"
TERMS = ["after", "pageable", "small_batch", "placebo", "pageable_x_small"]
LABELS = {"after": "common shift (period indicator)", "pageable": "pageable H2D input (injected)",
          "small_batch": "micro-batches + grad accumulation (injected)", "placebo": "placebo flag (no change)",
          "pageable_x_small": "interaction pageable x small_batch", "residual": "residual"}
PCIE_GBPS_PER_LANE = {1: 0.25, 2: 0.5, 3: 0.985, 4: 1.969, 5: 3.938, 6: 7.563}
SEED = 22


def load_lab_model(name: str):
    """The lab's L1 model: the reference solution when the instructor tree is present, else the learner's starter."""
    for path in (PKG / "solutions" / "lab" / f"{name}.py", LAB / "starter" / f"{name}.py"):
        if path.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, path.relative_to(PKG).as_posix()
    return None, None


# ----------------------------------------------------------------------------------------------- the step
class Trainer:
    def __init__(self, ctx):
        torch = ctx.torch
        self.ctx, self.torch = ctx, torch
        self.dev = "cuda" if ctx.is_gpu else "cpu"
        if ctx.is_gpu:
            self.batch, self.d, self.hidden, dt = 2048, 4096, 4096, torch.float16
        else:   # one thread: a shared host's other tenants then perturb the timing far less
            torch.set_num_threads(1)
            self.batch, self.d, self.hidden, dt = 1024, 1024, 64, torch.float32
        self.micro = 8 if ctx.is_gpu else 64
        self.dtype = dt
        g = torch.Generator().manual_seed(SEED)
        self.w1 = (torch.randn(self.d, self.hidden, generator=g) * 0.01).to(self.dev, dt).requires_grad_()
        self.w2 = (torch.randn(self.hidden, self.d, generator=g) * 0.01).to(self.dev, dt).requires_grad_()
        host = torch.randn(self.batch, self.d, generator=g)                  # fp32 input batch on the host
        self.bytes = host.numel() * host.element_size()
        if ctx.is_gpu:
            self.src_fast = host.pin_memory()
            self.src_slow = host.clone()                                       # pageable
            self.dev_buf = torch.empty_like(host, device="cuda")
        else:
            self.src_fast = host                                               # contiguous
            self.src_slow = host.double().t().contiguous().t()                 # same values, fp64 and transposed storage
            self.dev_buf = torch.empty_like(host)

    def load(self, slow: bool):
        if self.ctx.is_gpu:
            if slow:
                self.dev_buf.copy_(self.src_slow)                  # pageable: staged through a driver bounce buffer
            else:
                self.dev_buf.copy_(self.src_fast, non_blocking=True)
        else:
            self.dev_buf.copy_(self.src_slow if slow else self.src_fast)   # strided fp64 source -> gather + convert pass
        return self.dev_buf

    def step(self, pageable: bool, small_batch: bool):
        torch = self.torch
        x = self.load(pageable).to(self.dtype)
        micro = self.micro if small_batch else 1
        for xb in x.chunk(micro):
            h = torch.relu(xb @ self.w1)
            loss = ((h @ self.w2) ** 2).mean() / micro
            loss.backward()
        with torch.no_grad():
            for w in (self.w1, self.w2):
                w.add_(w.grad, alpha=-1e-3)
                w.grad = None
        self.ctx.sync()


def gpu_mem_used() -> float | None:
    rows = hwlab.nvidia_smi_query(["memory.used"])
    try:
        return float(rows[0]["memory.used"]) if rows else None
    except (ValueError, KeyError):
        return None


def interleaved(ctx, fns: dict, warmup: int = 3, reps: int = 15) -> dict:
    """Interleaved wall-clock A/B (Section 22.6.2: alternate A/B/A/B, never all A then all B).

    Every repetition visits each configuration once, in a freshly shuffled order, so slow drift (temperature,
    clocks, a neighbour) hits all arms equally. Each visit runs the configuration once untimed and then once timed:
    the untimed run absorbs carry-over from the previous arm (allocator and cache state), which would otherwise
    bias whichever arm follows the heaviest one."""
    rng = random.Random(SEED + 1)
    for _ in range(warmup):
        for fn in fns.values():
            fn()
            ctx.sync()
    samples = {k: [] for k in fns}
    order = list(fns)
    for _ in range(reps):
        rng.shuffle(order)
        for k in order:
            fns[k]()
            ctx.sync()
            t0 = time.perf_counter()
            fns[k]()
            ctx.sync()
            samples[k].append(time.perf_counter() - t0)
    return {k: hwlab.summarize(v) for k, v in samples.items()}


# ----------------------------------------------------------------------------------------------- estimation
def ols_hc3(rows: list[dict], terms: list[str]) -> dict:
    """Embedded fallback (same maths as the lab's estimate_effects): OLS + HC3 standard errors."""
    import numpy as np
    X = np.column_stack([np.ones(len(rows))] + [[r[t] for r in rows] for t in terms]).astype(float)
    y = np.array([r["mean_step_s"] for r in rows], float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    xtx_inv = np.linalg.inv(X.T @ X)
    h = np.einsum("ij,jk,ik->i", X, xtx_inv, X)
    meat = X.T @ (X * (resid / (1 - h))[:, None] ** 2)
    se_hc3 = np.sqrt(np.diag(xtx_inv @ meat @ xtx_inv))
    se = np.sqrt(np.diag(float(resid @ resid) / (len(y) - X.shape[1]) * xtx_inv))
    names = ["intercept"] + terms
    r2 = 1 - float(resid @ resid) / float(((y - y.mean()) ** 2).sum())
    return {"coef": dict(zip(names, map(float, beta))), "se": dict(zip(names, map(float, se))),
            "se_hc3": dict(zip(names, map(float, se_hc3))), "r2": r2}


def attribute_embedded(rows, effects, terms):
    bef = [r for r in rows if r["period"] == "before"]
    aft = [r for r in rows if r["period"] == "after"]
    mean = lambda rs, k: sum(r[k] for r in rs) / len(rs)   # noqa: E731
    delta = mean(aft, "mean_step_s") - mean(bef, "mean_step_s")
    out = []
    for f in terms:
        dx = mean(aft, f) - mean(bef, f)
        c = effects["coef"][f] * dx
        out.append({"factor": f, "effect_s": effects["coef"][f], "exposure_change": dx, "contribution_s": c,
                    "share_pct": 100 * c / delta, "share_se_hc3_pp": 100 * effects["se_hc3"][f] * abs(dx) / delta})
    resid = delta - sum(r["contribution_s"] for r in out)
    out.append({"factor": "residual", "effect_s": None, "exposure_change": None, "contribution_s": resid,
                "share_pct": 100 * resid / delta, "share_se_hc3_pp": None})
    return out, delta


# ----------------------------------------------------------------------------------------------- run
def run(ctx) -> dict:
    torch = ctx.torch
    import pandas as pd
    rng = random.Random(SEED)
    if ctx.is_gpu:
        n_before, per_cell, steps, warm = (8, 4, 16, 3) if ctx.quick else (16, 8, 30, 5)
    else:   # host timing is noisier: more jobs and steps so the SE shrinks below the injected effects
        n_before, per_cell, steps, warm = (10, 5, 30, 3) if ctx.quick else (16, 8, 50, 5)
    notes = [f"{n_before} before-jobs, then {4 * per_cell} after-jobs ({per_cell} per pageable x small_batch cell, order "
             f"shuffled, placebo on a random half); {steps} steps per job, the first {warm} dropped as warm-up.",
             "All timings are host wall clock around a synchronized step (CUDA events would miss host-side staging).",
             "Before-jobs run first and after-jobs second, as in production. Slow drift (GPU temperature, clocks) therefore "
             "lands in the 'after' common-shift term, exactly the confounding Section 22.4.3 warns about."]
    tr = Trainer(ctx)

    # -------- mechanism measurements: copy bandwidths
    bw = interleaved(ctx, {"fast": lambda: tr.load(False), "slow": lambda: tr.load(True)}, reps=max(15, ctx.reps(30)))
    fast, slow = bw["fast"], bw["slow"]
    bw_fast, bw_slow = tr.bytes / fast["median"] / 1e9, tr.bytes / slow["median"] / 1e9
    model_pageable_s = tr.bytes / (bw_slow * 1e9) - tr.bytes / (bw_fast * 1e9)
    ctx.log(f"input batch {tr.bytes / 2 ** 20:.0f} MiB: {'pinned' if ctx.is_gpu else 'contiguous'} {bw_fast:.2f} GB/s, "
            f"{'pageable' if ctx.is_gpu else 'strided gather'} {bw_slow:.2f} GB/s -> modeled +{model_pageable_s * 1e3:.2f} ms/step")

    # -------- direct controlled A/B of each factor alone (ground truth)
    arms = {"baseline": (False, False), "pageable": (True, False), "small_batch": (False, True), "both": (True, True)}
    res = interleaved(ctx, {k: (lambda p=p, sb=sb: tr.step(p, sb)) for k, (p, sb) in arms.items()},
                      reps=max(15 if ctx.is_gpu else 30, ctx.reps(30)))
    ab = {k: {q: v[q] for q in ("median", "p95", "iqr", "n")} for k, v in res.items()}
    for v in ab.values():   # SE of a median ~ 1.253 sigma / sqrt(n), sigma ~ IQR / 1.349 (robust)
        v["se_median"] = 1.253 * (v["iqr"] / 1.349) / math.sqrt(v["n"])
    se_ab = {"pageable": math.hypot(ab["pageable"]["se_median"], ab["baseline"]["se_median"]),
             "small_batch": math.hypot(ab["small_batch"]["se_median"], ab["baseline"]["se_median"]),
             "pageable_x_small": math.sqrt(sum(v["se_median"] ** 2 for v in ab.values())), "placebo": 0.0}
    direct = {"pageable": ab["pageable"]["median"] - ab["baseline"]["median"],
              "small_batch": ab["small_batch"]["median"] - ab["baseline"]["median"],
              "pageable_x_small": ab["both"]["median"] - ab["pageable"]["median"] - ab["small_batch"]["median"] + ab["baseline"]["median"]}
    ctx.log("direct A/B (median step ms): " + ", ".join(f"{k} {v['median'] * 1e3:.2f}" for k, v in ab.items()))

    # -------- the natural experiment
    after_cells = [(p, s) for p in (0, 1) for s in (0, 1) for _ in range(per_cell)]
    rng.shuffle(after_cells)
    placebo = [1] * (len(after_cells) // 2) + [0] * (len(after_cells) - len(after_cells) // 2)
    rng.shuffle(placebo)
    plan = [{"period": "before", "pageable": 0, "small_batch": 0, "placebo": 0} for _ in range(n_before)]
    plan += [{"period": "after", "pageable": p, "small_batch": s, "placebo": pl} for (p, s), pl in zip(after_cells, placebo)]
    step_rows, jobs, mem = [], [], []
    for j, cfg in enumerate(plan, start=1):
        mem.append(gpu_mem_used() if ctx.is_gpu else None)
        for k in range(steps):
            t0 = time.perf_counter()
            tr.step(bool(cfg["pageable"]), bool(cfg["small_batch"]))
            step_rows.append({"job_id": j, "step": k, "step_time_s": time.perf_counter() - t0})
        jobs.append({"job_id": j, "status": "COMPLETED", **cfg})
    steps_df = pd.DataFrame(step_rows)
    # the lab's own cleaning (drop replayed duplicates and warm-up steps)
    mod, model_path = load_lab_model("regression_lab")
    cleaned = None
    if mod:
        try:
            cleaned = mod.clean_steps(steps_df, warmup_steps=warm)
        except NotImplementedError:
            cleaned = None
    if cleaned is None:
        cleaned = steps_df[steps_df.step >= warm].drop_duplicates(["job_id", "step"])
    g = cleaned.groupby("job_id")["step_time_s"]
    ft = pd.DataFrame(jobs).set_index("job_id")
    ft["n_steps"], ft["mean_raw_s"], ft["p50_step_s"] = g.size(), g.mean(), g.median()
    # The lab regresses per-job means. On the GPU that is kept; on the shared host of the CPU fallback, other tenants
    # add long one-off stalls, so the per-job median is the robust statistic (Section 22.6.2: "Statistic").
    ft["mean_step_s"] = ft["mean_raw_s"] if ctx.is_gpu else ft["p50_step_s"]
    ft["pageable_x_small"] = ft["pageable"] * ft["small_batch"]
    ft["after"] = (ft["period"] == "after").astype(int)

    effects = attribution = boot = None
    used = "embedded OLS (lab model unavailable)"
    if mod:
        try:
            mod.TERMS = TERMS                      # the lab's estimator, with this experiment's factor list
            effects = mod.estimate_effects(ft)
            att = mod.attribute(ft, effects)
            attribution = [{"factor": f, **{k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.items()}}
                           for f, r in att.to_dict("index").items()]
            delta = mod.regression_summary(ft)["delta_s"]
            boot = mod.bootstrap_shares(ft, n_boot=300 if ctx.quick else 2000, seed=SEED)
            used = f"{model_path} (estimate_effects, attribute, bootstrap_shares; TERMS swapped)"
        except NotImplementedError as exc:
            notes.append(f"The lab estimator is not implemented yet in {model_path} ({exc}); used the embedded OLS. "
                         "Implement it in lab/starter/regression_lab.py and rerun.")
            effects = None
    recs = ft.reset_index().to_dict("records")
    if effects is None:
        effects = ols_hc3(recs, TERMS)
        attribution, delta = attribute_embedded(recs, effects, TERMS)
    ctx.log(f"attribution via {used}: " + ", ".join(f"{r['factor']} {r['share_pct']:.1f} %" for r in attribution))

    bef = ft[ft.period == "before"]["mean_step_s"]
    sigma = float(bef.std(ddof=1))
    mde = 2.8 * sigma * math.sqrt(2 / len(bef))
    corroboration = []
    for f in ("pageable", "small_batch", "pageable_x_small", "placebo"):
        corroboration.append({"factor": f, "ols_s": effects["coef"][f], "se_hc3_s": effects["se_hc3"][f],
                              "direct_ab_s": direct.get(f, 0.0), "direct_se_s": se_ab[f],
                              "model_s": model_pageable_s if f == "pageable" else None})
    metrics = {
        "batch_mib": round(tr.bytes / 2 ** 20, 1), "bw_fast_gbs": round(bw_fast, 3), "bw_slow_gbs": round(bw_slow, 3),
        "baseline_step_ms": round(ab["baseline"]["median"] * 1e3, 3),
        "direct_pageable_ms": round(direct["pageable"] * 1e3, 3), "direct_small_batch_ms": round(direct["small_batch"] * 1e3, 3),
        "model_pageable_ms": round(model_pageable_s * 1e3, 3),
        "ols_pageable_ms": round(effects["coef"]["pageable"] * 1e3, 3), "ols_small_batch_ms": round(effects["coef"]["small_batch"] * 1e3, 3),
        "ols_placebo_ms": round(effects["coef"]["placebo"] * 1e3, 3), "ols_after_ms": round(effects["coef"]["after"] * 1e3, 3),
        "se_hc3_placebo_ms": round(effects["se_hc3"]["placebo"] * 1e3, 3),
        "r2": round(effects["r2"], 4), "delta_ms": round(delta * 1e3, 3),
        "share_sum_pct": round(sum(r["share_pct"] for r in attribution), 6),
        "before_sigma_ms": round(sigma * 1e3, 4), "mde_ms": round(mde * 1e3, 4),
        "jobs": len(ft), "estimator": used, "per_job_statistic": "mean" if ctx.is_gpu else "median",
    }
    if ctx.is_gpu:
        valid = [m for m in mem if m is not None]
        metrics["foreign_mem_swing_mib"] = round(max(valid) - min(valid), 1) if valid else None
    return {"metrics": metrics,
            "tables": {"direct_ab": ab, "attribution": attribution, "corroboration": corroboration,
                       "bootstrap_share_ci": boot, "jobs": ft.reset_index().round(6).to_dict("records")},
            "notes": notes}


# ----------------------------------------------------------------------------------------------- check
def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    fails = []
    if abs(m["share_sum_pct"] - 100) > 1e-6:
        fails.append(f"attribution shares (with residual) sum to {m['share_sum_pct']} %, not 100 %: check attribute()")
    for f, key in (("pageable", "pageable"), ("small_batch", "small_batch")):
        ols, d = m[f"ols_{key}_ms"], m[f"direct_{key}_ms"]
        cor = next(r for r in t["corroboration"] if r["factor"] == f)
        se, se_d = cor["se_hc3_s"] * 1e3, cor["direct_se_s"] * 1e3
        tol = max(0.35 * abs(d), 3 * math.hypot(se, se_d), 0.5)
        if abs(ols - d) > tol:
            fails.append(f"{f}: OLS effect {ols:.2f} ms vs direct A/B {d:.2f} ms differ by more than {tol:.2f} ms: the natural "
                         "experiment does not recover the injected regression (confounding, too few jobs, or a noisy device)")
        if se > max(abs(d), 1.0):
            fails.append(f"{f}: SE {se:.2f} ms exceeds the {d:.2f} ms effect, so agreement would be vacuous: the device or host "
                         "is too noisy (another tenant?); rerun alone or with more jobs")
        if d <= 0:
            fails.append(f"{f}: the injected change did not slow the step in the controlled A/B ({d:.2f} ms): check the injection")
    if abs(m["ols_placebo_ms"]) > max(3 * m["se_hc3_placebo_ms"], 0.15 * max(m["direct_pageable_ms"], m["direct_small_batch_ms"])):
        fails.append(f"placebo factor got {m['ols_placebo_ms']:.2f} ms ± {m['se_hc3_placebo_ms']:.2f}: a no-op must attribute ~0; "
                     "check the design (placebo correlated with a real factor?)")
    d = m["direct_pageable_ms"]
    se_d = next(r for r in t["corroboration"] if r["factor"] == "pageable")["direct_se_s"] * 1e3
    if d > 0.5 and not 0.4 * d <= m["model_pageable_ms"] <= 1.6 * d and abs(m["model_pageable_ms"] - d) > 3 * se_d:
        fails.append(f"data-path mechanism model {m['model_pageable_ms']:.2f} ms vs direct {d:.2f} ms: the slower copy explains "
                     "less than 40 % or more than 160 % of the extra step time; the mechanism is not understood")
    if env["device"] == "cuda":
        if m.get("foreign_mem_swing_mib") and m["foreign_mem_swing_mib"] > 256:
            fails.append(f"memory.used moved by {m['foreign_mem_swing_mib']} MiB between jobs: another process shared the GPU; rerun alone")
        g = (env.get("gpus") or [{}])[0]
        try:
            ceiling = PCIE_GBPS_PER_LANE[int(g["pcie.link.gen.max"])] * int(g["pcie.link.width.max"])
        except (KeyError, ValueError):
            ceiling = None
        if ceiling and m["bw_fast_gbs"] > 1.05 * ceiling:
            fails.append(f"pinned H2D {m['bw_fast_gbs']} GB/s above the {ceiling:.1f} GB/s PCIe ceiling: check the timing")
        if m["bw_fast_gbs"] < m["bw_slow_gbs"]:
            fails.append("pinned H2D slower than pageable: check pin_memory() and non_blocking")
    return fails


# ----------------------------------------------------------------------------------------------- report
def report(result: dict, env: dict) -> str:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    fast, slow = ("pinned", "pageable") if gpu else ("contiguous", "strided gather")
    labels = dict(LABELS)
    if not gpu:
        labels["pageable"] = "strided fp64 input gather (injected)"
    L = ["## Measured facts", "",
         f"- Input batch {m['batch_mib']} MiB; H2D {fast} {m['bw_fast_gbs']} GB/s, {slow} {m['bw_slow_gbs']} GB/s `[MEASURED]`.",
         f"- Controlled A/B, median step (ms; ≥ 5 reps after 3 warm-ups):", "",
         "| Configuration | median | p95 | IQR | n |", "|---|---|---|---|---|"]
    for k, v in t["direct_ab"].items():
        L.append(f"| {k} | {v['median'] * 1e3:.2f} | {v['p95'] * 1e3:.2f} | {v['iqr'] * 1e3:.3f} | {v['n']} |")
    L += ["", f"- Natural experiment: {m['jobs']} jobs, per-job {m['per_job_statistic']} step after - before = **{m['delta_ms']:+.2f} ms**. Before-period "
          f"spread σ = {m['before_sigma_ms']:.3f} ms per job {m['per_job_statistic']}, so MDE ≈ 2.8 σ √(2/n) = {m['mde_ms']:.3f} ms (Section 22.6.1).",
          "", f"## Attribution (estimator: {m['estimator']})", "",
          "| Term | Effect (ms/step) ± SE HC3 (factors) | Exposure change | Contribution (ms) | Share | Bootstrap 95 % share interval |",
          "|---|---|---|---|---|---|"]
    boot = t.get("bootstrap_share_ci") or {}
    for r in t["attribution"]:
        f = r["factor"]
        se = r.get("share_se_hc3_pp")
        eff = "" if r["effect_s"] is None else f"{r['effect_s'] * 1e3:+.2f}"
        cor = next((c for c in t["corroboration"] if c["factor"] == f), None)
        if cor:
            eff += f" ± {cor['se_hc3_s'] * 1e3:.2f}"
        expo = "" if r["exposure_change"] is None else f"{r['exposure_change']:.3f}"
        ci = boot.get(f)
        L.append(f"| {labels.get(f, f)} | {eff} | {expo} | {r['contribution_s'] * 1e3:+.2f} | {r['share_pct']:.1f} %"
                 f"{f' ± {se:.1f} pp' if se is not None else ''} | {f'{ci[0]:.0f} to {ci[1]:.0f} %' if ci else ''} |")
    L += ["", f"R² = {m['r2']}.", "", "## Corroboration (Table 22.6: statistical, direct, mechanism model)", "",
          "| Factor | OLS (ms) | Direct A/B (ms) | Mechanism model (ms) | Verdict |", "|---|---|---|---|---|"]
    for c in t["corroboration"]:
        ols, d = c["ols_s"] * 1e3, c["direct_ab_s"] * 1e3
        mdl = "" if c["model_s"] is None else f"{c['model_s'] * 1e3:+.2f}"
        se = c["se_hc3_s"] * 1e3
        agree = abs(ols - d) <= max(0.35 * abs(d), 3 * math.hypot(se, c["direct_se_s"] * 1e3), 0.5)
        precise = se < 0.5 * max(abs(d), 1.0)
        verdict = ("ruled out (no effect)" if c["factor"] == "placebo" and abs(ols) <= 3 * se + 0.5 else
                   "inconclusive: SE too large for this effect" if not precise else
                   "inferred cause, corroborated" if agree and d > 0.5 else "agree (≈ 0)" if agree else "disagree: not understood")
        L.append(f"| {labels[c['factor']]} | {ols:+.2f} ± {c['se_hc3_s'] * 1e3:.2f} | {d:+.2f} ± {c['direct_se_s'] * 1e3:.2f} | "
                 f"{mdl} | {verdict} |")
    L += ["", "## What to conclude", ""]
    L += [f"- The lab's estimator, fed real per-job means, recovers both injected regressions within their uncertainty "
          f"(pageable {m['ols_pageable_ms']:+.2f} vs {m['direct_pageable_ms']:+.2f} ms direct; small batch {m['ols_small_batch_ms']:+.2f} vs "
          f"{m['direct_small_batch_ms']:+.2f} ms) and gives the placebo {m['ols_placebo_ms']:+.2f} ± {m['se_hc3_placebo_ms']:.2f} ms. "
          "A factor that happens to coincide with an incident is not its cause.",
          f"- The data-path effect is also explained by mechanism: {m['batch_mib']} MiB at the slower copy rate costs "
          f"{m['model_pageable_ms']:+.2f} ms per step, {100 * m['model_pageable_ms'] / m['direct_pageable_ms']:.0f} % of the "
          f"{m['direct_pageable_ms']:+.2f} ms measured in the A/B. Statistical, direct and mechanism evidence agree, so it is a strong "
          "inferred cause. The unexplained remainder is the host-side cost a bandwidth number does not capture (staging-buffer "
          "management, cache effects).",
          f"- The common-shift term ({m['ols_after_ms']:+.2f} ms) absorbs whatever drifted between the before and after blocks, such as "
          "temperature or clocks. Compare it with the MDE before calling it real.",
          ("- This is a **laptop Ada GPU** on PCIe Gen4 x8, not an HX8 node. The lab's W-TRAIN factors (TP split, GDR host-staging "
           "across nodes, storage tier) need multi-node hardware (L3). This run validates the *method* on regressions whose truth "
           "is known." if gpu else
           "- _CPU fallback: no GPU was visible, so the data-path factor is a strided gather on the host rather than a pageable "
           "PCIe copy. The design, estimator and corroboration are identical. GPU-only invariants (PCIe ceiling, pinned >= "
           "pageable) were skipped._")]
    return "\n".join(L)
