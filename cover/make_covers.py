"""Covers for "AI Infrastructure Engineering", First Edition (the concise print build): KDP paperback wrap,
hardcover (case laminate) wrap, and a front-only image for the ebook and store listing.

    python cover/make_covers.py [interior page count]     (default: count build/concise/*.pdf)

Outputs go to build/cover/.

Paperback (7 x 10 in, black-and-white interior on white paper):
    width  = 0.125 bleed + 7 back + spine + 7 front + 0.125 bleed,  height = 10.25
    spine  = pages x 0.002252 in
Hardcover (case laminate, 7 x 10 in):
    width  = 0.591 wrap + 7 back + 0.197 hinge + spine + 0.197 hinge + 7 front + 0.591 wrap,
    height = 11.443;  spine = pages x 0.002252 + 0.189 in
Check both against the template KDP's cover calculator gives for your final page count before you
upload: KDP's numbers win. The back cover leaves the bottom-right corner empty for the barcode.

Renders with Chromium through Playwright: set CHROME to a chrome.exe, or it uses Puppeteer's (mmdc's).
Fonts (Poppins) come from Google Fonts, so the render needs network access.
"""
import asyncio
import glob
import math
import os
import random
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "cover"


def interior_pages() -> int:
    if len(sys.argv) > 1:
        return int(sys.argv[1])
    interior = ROOT / "build" / "concise" / "AI_Infrastructure_Engineering_Concise_Edition.pdf"
    if interior.exists():
        import fitz  # PyMuPDF
        return fitz.open(interior).page_count
    return 400


PAGES = interior_pages()
PAGES += PAGES % 2
TRIM_W, TRIM_H = 7.0, 10.0
EBOOK_W = 6.25                     # 1600 x 2560 px, KDP's recommended 1.6:1
BASE = "AI_Infrastructure_Engineering"

# What the book is, in numbers the repo computes: 24 chapters; 24 chapter labs + 8 capstone kits;
# exercise folders under book/*/*/exercises; ORION = 32 nodes x 8 GPUs (docs/REFERENCE_CLUSTER.md).
CHAPTERS, LABS, CAPSTONES = 24, 32, 8
EXERCISES = len(glob.glob(str(ROOT / "book" / "*" / "*" / "exercises" / "*" / "README.md")))
ORION_GPUS = 256

NAVY, NAVY2, INK = "#0B1530", "#1A2A55", "#070D1F"
GREEN, GREEN_D = "#14B886", "#0E7C5E"
CYAN, CYAN2, VIOLET = "#35C9FF", "#8FE3FF", "#7C6BFF"
AMBER = "#FFB547"
PALE, MUTED, STEEL = "#D6E4F5", "#9FB3CF", "#A9B8D6"

FORMATS = {
    "paperback": dict(wrap=0.125, hinge=0.0, spine=PAGES * 0.002252, height=TRIM_H + 0.25),
    "hardcover": dict(wrap=0.591, hinge=0.197, spine=PAGES * 0.002252 + 0.189, height=11.443),
}
LOOP_IN, LOOP_RIGHT, LOOP_BOTTOM = 3.35, 0.12, 1.2


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def background(w, h, ex, ey, top, seed=11):
    """The whole wrap in 1/100 in. A GPU-cluster fabric: a lattice of nodes whose links carry more
    traffic the closer they run to one bottleneck at (ex, ey), the center of the front cover's loop.
    Rings mark the layers a diagnosis crosses; packets ride the busy links; a step-time trace across
    the top shows a straggler spike above the bottleneck and the recovery after the fix."""
    r = random.Random(seed)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" preserveAspectRatio="none">',
         '<defs>',
         f'<radialGradient id="heat" cx="{ex:.0f}" cy="{ey:.0f}" r="440" gradientUnits="userSpaceOnUse">'
         f'<stop offset="0" stop-color="{CYAN}" stop-opacity=".30"/><stop offset=".4" stop-color="{VIOLET}" stop-opacity=".14"/>'
         f'<stop offset="1" stop-color="{NAVY}" stop-opacity="0"/></radialGradient>',
         f'<radialGradient id="cool" cx="{w * .2:.0f}" cy="{h * .25:.0f}" r="{w * .35:.0f}" gradientUnits="userSpaceOnUse">'
         f'<stop offset="0" stop-color="#1F3A78" stop-opacity=".35"/><stop offset="1" stop-color="{NAVY}" stop-opacity="0"/></radialGradient>',
         '<pattern id="grid" width="25" height="25" patternUnits="userSpaceOnUse">'
         '<path d="M25 0H0V25" fill="none" stroke="#8FA6C8" stroke-opacity=".045" stroke-width=".6"/></pattern>',
         '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2"/></filter>',
         '</defs>',
         f'<rect width="{w:.0f}" height="{h:.0f}" fill="url(#cool)"/>',
         f'<rect width="{w:.0f}" height="{h:.0f}" fill="url(#grid)"/>',
         f'<rect width="{w:.0f}" height="{h:.0f}" fill="url(#heat)"/>']

    # Layer rings around the bottleneck: compute, network, storage, orchestration.
    for i, rad in enumerate((175, 240, 315, 405, 510, 630)):
        op = .45 * (1 - i / 6.5)
        dash = "" if i == 0 else f' stroke-dasharray="{2 + i} {5 + i * 2}"'
        s.append(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{rad}" fill="none" stroke="{CYAN}" '
                 f'stroke-opacity="{op:.2f}" stroke-width="{1.4 - i * .15:.2f}"{dash}/>')

    # Fabric: jittered lattice, each node linked to its nearest neighbours.
    step = 62
    pts = []
    for gy in range(-1, int(h / step) + 2):
        for gx in range(-1, int(w / step) + 2):
            x = gx * step + (step / 2 if gy % 2 else 0) + r.uniform(-18, 18)
            y = gy * step + r.uniform(-18, 18)
            if r.random() < .8:
                pts.append((x, y))

    def heat(x, y):
        return max(0.0, 1 - math.hypot(x - ex, y - ey) / 480)

    seen = set()
    for i, (x, y) in enumerate(pts):
        near = sorted(range(len(pts)), key=lambda j: (pts[j][0] - x) ** 2 + (pts[j][1] - y) ** 2)[1:4]
        for j in near:
            if (j, i) in seen:
                continue
            seen.add((i, j))
            x2, y2 = pts[j]
            t = max(heat(x, y), heat(x2, y2))
            col = mix("#8FA6C8", CYAN, min(1, t * 1.4))
            op = .10 + .40 * t
            s.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{col}" '
                     f'stroke-opacity="{op:.2f}" stroke-width="{.8 + .6 * t:.2f}"/>')
            if t > .35 and r.random() < .55:
                # A packet in flight on a busy link.
                k = r.uniform(.2, .8)
                px, py = x + (x2 - x) * k, y + (y2 - y) * k
                s.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{1.6 + 1.6 * t:.1f}" fill="{CYAN2}" fill-opacity="{.35 + .45 * t:.2f}"/>')
    for x, y in pts:
        t = heat(x, y)
        if t > .25:
            col, rad, op = mix(CYAN2, CYAN, t), 2 + 2.6 * t, .28 + .45 * t
            s.append(f'<rect x="{x - rad - 3:.1f}" y="{y - rad - 3:.1f}" width="{2 * rad + 6:.1f}" height="{2 * rad + 6:.1f}" '
                     f'rx="2" fill="{col}" fill-opacity="{op * .45:.2f}" filter="url(#glow)"/>')
            s.append(f'<rect x="{x - rad:.1f}" y="{y - rad:.1f}" width="{2 * rad:.1f}" height="{2 * rad:.1f}" rx="1.2" '
                     f'fill="{col}" fill-opacity="{op:.2f}"/>')
        elif r.random() < .06:
            s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="2.6" fill="{GREEN}" fill-opacity=".55"/>')
        else:
            s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r.choice([1.8, 2.2, 2.8]):.1f}" fill="#8FA6C8" fill-opacity=".2"/>')

    # Telemetry: training step time across the top margin, steady, a straggler spike over the bottleneck,
    # then back to baseline after the safe change.
    base = top * 100 + 46
    d = []
    for k in range(0, int(w) + 1, 4):
        noise = math.sin(k * .19) * 2.0 + math.sin(k * .061) * 2.6 + r.uniform(-1.4, 1.4)
        spike = 32 * math.exp(-((k - ex) / 30) ** 2) + 10 * math.exp(-((k - ex - 55) / 40) ** 2)
        d.append(f"{'M' if k == 0 else 'L'}{k},{base - noise - spike:.1f}")
    s.append(f'<path d="{"".join(d)}" fill="none" stroke="{GREEN}" stroke-opacity=".28" stroke-width="1.1"/>')
    s.append(f'<path d="{"".join(d)}" fill="none" stroke="{AMBER}" stroke-opacity=".6" stroke-width="1.3" '
             f'clip-path="inset(0 {w - ex - 140:.0f} 0 {ex - 70:.0f})"/>')
    s.append(f'<line x1="0" y1="{base - 22}" x2="{w:.0f}" y2="{base - 22}" stroke="{AMBER}" stroke-opacity=".18" '
             f'stroke-width=".7" stroke-dasharray="2 5"/>')      # the step-time SLO
    s.append("</svg>")
    return "".join(s)


def diagnostic_loop(size=300):
    """The book's diagnostic loop around one bottleneck: symptom, evidence, trace across layers,
    root cause, safe change, validate; then go round again with the next bottleneck."""
    c = size / 2
    R, R2, R3 = size * 0.34, size * 0.41, size * 0.49
    steps = ["SYMPTOM", "EVIDENCE", "TRACE", "ROOT CAUSE", "SAFE CHANGE", "VALIDATE"]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-62 -16 {size + 124} {size + 32}">',
         '<defs><radialGradient id="core"><stop offset="0" stop-color="#E6FAFF"/><stop offset=".45" stop-color="'
         f'{CYAN}"/><stop offset="1" stop-color="#1F6FB8"/></radialGradient>'
         f'<radialGradient id="halo"><stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>'
         f'<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient></defs>',
         f'<circle cx="{c}" cy="{c}" r="{R3}" fill="#0C1633" fill-opacity=".72"/>',
         f'<circle cx="{c}" cy="{c}" r="{R2}" fill="none" stroke="{GREEN}" stroke-width="1" stroke-opacity=".55" stroke-dasharray="2 4"/>',
         f'<circle cx="{c}" cy="{c}" r="{R}" fill="none" stroke="#2C5E86" stroke-width="1.1" stroke-opacity=".9"/>']
    for k in range(6):
        a = math.radians(-90 + k * 60)
        x, y = c + R * math.cos(a), c + R * math.sin(a)
        s.append(f'<line x1="{c}" y1="{c}" x2="{x:.1f}" y2="{y:.1f}" stroke="#4A6A9A" stroke-opacity=".45" stroke-dasharray="2 3"/>')
    for k in range(6):
        a0 = -90 + k * 60
        a1, a2 = math.radians(a0 + 12), math.radians(a0 + 48)
        x1, y1 = c + R * math.cos(a1), c + R * math.sin(a1)
        x2, y2 = c + R * math.cos(a2), c + R * math.sin(a2)
        s.append(f'<path d="M{x1:.1f},{y1:.1f} A{R},{R} 0 0 1 {x2:.1f},{y2:.1f}" fill="none" stroke="{GREEN}" '
                 f'stroke-width="2.6" stroke-linecap="round"/>')
        tx, ty, nx, ny = -math.sin(a2), math.cos(a2), math.cos(a2), math.sin(a2)
        tip = (x2 + tx * 7, y2 + ty * 7)
        s.append(f'<path d="M{tip[0]:.1f},{tip[1]:.1f} L{x2 - nx * 4.5:.1f},{y2 - ny * 4.5:.1f} '
                 f'L{x2 + nx * 4.5:.1f},{y2 + ny * 4.5:.1f} Z" fill="{GREEN}"/>')
    for k, label in enumerate(steps):
        a = math.radians(-90 + k * 60)
        x, y = c + R * math.cos(a), c + R * math.sin(a)
        col = CYAN if label == "TRACE" else GREEN
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="#0C1633" stroke="{col}" stroke-width="2"/>'
                 f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.8" fill="{col}"/>')
        lx, ly = c + (R + 20) * math.cos(a), c + (R + 20) * math.sin(a)
        cos = math.cos(a)
        anchor = "middle" if abs(cos) < .1 else ("start" if cos > 0 else "end")
        dy = -3 if k == 0 else (13 if k == 3 else 4)
        s.append(f'<text x="{lx:.1f}" y="{ly + dy:.1f}" text-anchor="{anchor}" font-family="Poppins" font-weight="600" '
                 f'font-size="10.5" letter-spacing="1.4" fill="{PALE}"><tspan fill="{col}">{k + 1}</tspan> {label}</text>')
    # The bottleneck: a GPU die at the center, glowing.
    s.append(f'<circle cx="{c}" cy="{c}" r="36" fill="url(#halo)"/>'
             f'<rect x="{c - 15}" y="{c - 15}" width="30" height="30" rx="3" fill="url(#core)" stroke="{CYAN2}" stroke-width="1"/>')
    for k in range(4):
        o = -10.5 + k * 7
        s.append(f'<line x1="{c + o}" y1="{c - 21}" x2="{c + o}" y2="{c - 15}" stroke="{CYAN2}" stroke-width="1.2"/>'
                 f'<line x1="{c + o}" y1="{c + 15}" x2="{c + o}" y2="{c + 21}" stroke="{CYAN2}" stroke-width="1.2"/>'
                 f'<line x1="{c - 21}" y1="{c + o}" x2="{c - 15}" y2="{c + o}" stroke="{CYAN2}" stroke-width="1.2"/>'
                 f'<line x1="{c + 15}" y1="{c + o}" x2="{c + 21}" y2="{c + o}" stroke="{CYAN2}" stroke-width="1.2"/>')
    s.append(f'<text x="{c}" y="{c + 40}" text-anchor="middle" font-family="Poppins" font-weight="600" font-size="8.6" '
             f'letter-spacing="2" fill="{MUTED}">BOTTLENECK</text>')
    s.append("</svg>")
    return "".join(s)


FRONT = f"""
<div class="kicker">HANDS-ON · GPU CLUSTERS · AI AT SCALE</div>
<div class="title"><span class="l1">AI</span><span class="l2">INFRASTRUCTURE</span><span class="l3">ENGINEERING</span></div>
<div class="sub">Designing, Building, and Operating GPU Clusters, High-Speed Networks, Distributed Training, and LLM Inference at Scale</div>
<div class="tags">
  <div class="tag">{LABS} labs · {EXERCISES} exercises</div>
  <div class="tag">NVLink · RDMA · RoCE · InfiniBand</div>
  <div class="tag">NCCL · Kubernetes · Slurm · LLM serving</div>
</div>
<div class="loop">{diagnostic_loop()}</div>
<div class="author">SRINIVASA RAO BITTLA</div>
"""

BACK = f"""
<div class="kicker small">HANDS-ON · GPU CLUSTERS · AI AT SCALE</div>
<h2>One cluster.<br><span>Every layer.</span></h2>
<p>A training job runs only as fast as its slowest GPU, link or disk. A throttled GPU, a swapped cable, a
lossy switch queue, a misplaced NIC and a bad scheduling decision can all look the same on a dashboard. This
book treats AI infrastructure as <b>one connected system</b>, from accelerators and host topology through
high-speed fabrics, collectives, storage and scheduling to inference serving, operations and cost. Every
chapter follows a workload across those layers with one method: <b>observe, collect evidence, trace the
bottleneck, find the root cause, change safely, and validate with repeatable measurements.</b></p>
<div class="lead">YOU WILL LEARN TO</div>
<ul>
<li>Read GPU, NVLink and PCIe topology and the host signals that predict trouble</li>
<li>Design rail-optimized RoCE and InfiniBand fabrics, from PFC and ECN to optics</li>
<li>Lay out distributed training and tune NCCL collectives and checkpoints</li>
<li>Serve LLMs: KV-cache capacity, batching, time to first token and latency</li>
<li>Run fleets with acceptance tests, Kubernetes and Slurm, SLOs and safe change</li>
<li>Plan power, cooling, capacity and the cost of a useful GPU-hour</li>
<li>Label every number as measured, modeled or illustrative, and mean it</li>
</ul>
<div class="stats">
  <div><b>{CHAPTERS}</b><span>chapters</span></div>
  <div><b>{LABS}</b><span>labs</span></div>
  <div><b>{EXERCISES}</b><span>exercises</span></div>
</div>
<p class="kit">One reference cluster, ORION ({ORION_GPUS} H100-class GPUs), carries the numbers from chapter to
chapter. Most labs run on a laptop; the extensions run on one real GPU. Code, labs and exercises:
<span class="url">github.com/sbittla/network-compute-engineer-ai-infra</span></p>
<div class="bio"><b>SRINIVASA RAO BITTLA</b> has spent over twenty years in AI/ML, performance engineering and
quality assurance, at Adobe, Veeva Systems, LogMeIn and Citrix. He holds patents in AI-enabled predictive
analytics and blockchain security, is a Gatling Master, has mentored more than 10,000 professionals, and is
the author of <i>AI Performance Engineering</i> and <i>AI-Driven Chaos Engineering</i>.
<span class="url">bittla.me</span></div>
<div class="cat">COMPUTERS / ARTIFICIAL INTELLIGENCE / GENERAL<br>
COMPUTERS / NETWORKING / GENERAL</div>
"""

# Fit each title line to the column: INFRASTRUCTURE to the full width, ENGINEERING slightly narrower,
# AI as a short lead-in.
FIT = """
const col = document.querySelector('.title');
const fit = (sel, frac, max) => { const el = document.querySelector(sel); el.style.fontSize = '100px';
  const size = Math.min(max, 100 * col.clientWidth * frac / el.scrollWidth); el.style.fontSize = size + 'px'; };
fit('.l1', .2, 60); fit('.l2', 1, 150); fit('.l3', .8, 100);
"""


def page_html(fmt, front_only=False):
    f = FORMATS[fmt]
    wrap, hinge, spine, H = f["wrap"], f["hinge"], f["spine"], f["height"]
    W = wrap * 2 + TRIM_W * 2 + hinge * 2 + spine
    top = (H - TRIM_H) / 2
    back_x, spine_x = wrap, wrap + TRIM_W + hinge
    front_x = spine_x + spine + hinge
    panel_w = TRIM_W
    inner = 0.75 if fmt == "hardcover" else 0.62          # keep clear of the hinge groove
    outer = 0.62
    loop = LOOP_IN
    if front_only:
        W, H, top, front_x, panel_w, inner, loop = EBOOK_W, TRIM_H, 0, 0, EBOOK_W, outer, 2.95
    ex = front_x + panel_w - LOOP_RIGHT - loop / 2
    ey = top + TRIM_H - LOOP_BOTTOM - loop / 2
    spine_pt = max(9, min(21, spine * 12))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,300;0,400;0,600;0,700;0,800;1,400&display=block" rel="stylesheet">
<style>
@page {{ size: {W}in {H}in; margin: 0 }}
* {{ box-sizing: border-box; margin: 0; padding: 0 }}
html, body {{ width: {W}in; height: {H}in; overflow: hidden }}
body {{ position: relative; font-family: Poppins; color: {PALE};
  background: radial-gradient(ellipse 75% 65% at {'45%' if front_only else '72%'} 30%, {NAVY2} 0%, {NAVY} 55%, {INK} 100%) }}
.sky {{ position: absolute; inset: 0 }} .sky svg {{ width: 100%; height: 100% }}
.panel {{ position: absolute; top: {top}in; width: {panel_w}in; height: {TRIM_H}in }}
.front {{ left: {front_x}in; padding: 0.82in {outer}in 0.62in {inner}in }}
.back {{ left: {back_x}in; padding: 0.7in {inner}in 0.62in {outer}in; font-size: 9.5pt; line-height: 1.5 }}
.kicker {{ display: inline-block; font-weight: 700; font-size: 10.5pt; letter-spacing: 3px; color: {GREEN};
  padding-bottom: 7px; border-bottom: 2.5px solid {GREEN} }}
.kicker.small {{ font-size: 8pt; letter-spacing: 2.6px; padding-bottom: 5px; border-bottom-width: 2px; margin-bottom: 0.24in }}
.title {{ margin-top: 0.36in; font-weight: 800; line-height: .98; letter-spacing: -1px; color: #fff }}
.title span {{ display: block; white-space: nowrap; width: max-content }}
.title .l1 {{ color: {STEEL}; letter-spacing: 2px; margin-bottom: .02in }}
.title .l2 {{ color: {CYAN}; line-height: .95; letter-spacing: -1px;
  text-shadow: -3px 0 rgba(20,184,134,.5), 3px 0 rgba(124,107,255,.35), 0 0 28px rgba(53,201,255,.35) }}
.title .l3 {{ margin-top: .03in }}
.sub {{ margin-top: 0.34in; font-weight: 300; font-size: {15 if front_only else 16}pt; line-height: 1.4; color: #BBD3F0; max-width: 5.6in }}
.tags {{ position: absolute; left: {inner}in; bottom: 1.55in; display: flex; flex-direction: column; gap: 0.1in }}
.tag {{ width: max-content; font-size: {9.5 if front_only else 10.3}pt; color: {GREEN}; border: 1.4px solid {GREEN}; border-radius: 30px;
  padding: 5px 15px; background: rgba(11,21,48,.7) }}
.loop {{ position: absolute; right: {LOOP_RIGHT}in; bottom: {LOOP_BOTTOM}in; width: {loop}in; height: {loop}in }}
.loop svg {{ width: 100%; height: 100%; overflow: visible }}
.author {{ position: absolute; left: {inner}in; right: {outer}in; bottom: 0.62in;
  border-top: 1px solid {GREEN_D}; padding-top: 0.2in; font-weight: 700; font-size: 20pt; letter-spacing: .8px; color: #EEF4FB }}
.back h2 {{ font-weight: 700; font-size: 23pt; line-height: 1.18; color: #fff; margin-bottom: 0.18in }}
.back h2 span {{ color: {CYAN} }}
.back p {{ margin-bottom: 0.15in; color: {PALE} }} .back p b {{ color: #fff }}
.lead {{ font-weight: 700; font-size: 8.4pt; letter-spacing: 2.4px; color: {GREEN}; margin: 0.04in 0 0.07in }}
.back ul {{ list-style: none; margin-bottom: 0.18in }}
.back li {{ position: relative; padding-left: 22px; margin-bottom: 3px }}
.back li:before {{ content: ""; position: absolute; left: 0; top: 3.5px; width: 11px; height: 11px; border-radius: 50%;
  border: 1.4px solid {GREEN} }}
.back li:after {{ content: ""; position: absolute; left: 3.2px; top: 6.2px; width: 4px; height: 2.2px;
  border-left: 1.4px solid {GREEN}; border-bottom: 1.4px solid {GREEN}; transform: rotate(-45deg) }}
.stats {{ display: flex; gap: 0.14in; margin-bottom: 0.16in }}
.stats div {{ flex: 1; border: 1px solid rgba(20,184,134,.35); border-radius: 10px; padding: 7px 12px;
  background: rgba(11,21,48,.6) }}
.stats b {{ display: block; font-size: 19pt; line-height: 1.1; color: #fff }}
.stats span {{ font-size: 8pt; color: {MUTED} }}
.kit {{ font-size: 8.9pt }} .url {{ color: {GREEN}; font-weight: 600 }}
.bio {{ margin-top: 0.04in; padding-top: 0.13in; border-top: 1px solid rgba(159,179,207,.3); font-size: 8.5pt; line-height: 1.5;
  color: #C5D4E8; max-width: 5.75in }} .bio b {{ color: #fff }}
.cat {{ position: absolute; left: {outer}in; bottom: 0.62in; font-size: 6.6pt; letter-spacing: 1.4px; line-height: 1.7; color: {MUTED} }}
.spine {{ position: absolute; top: 0; left: {spine_x}in; width: {spine}in; height: {H}in;
  background: linear-gradient(90deg, rgba(0,0,0,.28), rgba(255,255,255,.04) 50%, rgba(0,0,0,.28)) }}
.spine .t {{ position: absolute; left: 50%; top: {top + 0.55}in; transform-origin: 0 0; transform: rotate(90deg) translateY(-50%);
  white-space: nowrap; font-weight: 800; font-size: {spine_pt:.1f}pt; letter-spacing: 1.2px; color: #fff }}
.spine .t span {{ color: {CYAN} }}
.spine .a {{ position: absolute; left: 50%; bottom: {top + 0.55}in; transform-origin: 0 100%;
  transform: rotate(90deg) translate(-100%, 50%); white-space: nowrap; font-weight: 700; font-size: {spine_pt * 0.6:.1f}pt;
  letter-spacing: 3px; color: {PALE} }}
</style></head><body>
<div class="sky">{background(W * 100, H * 100, ex * 100, ey * 100, top)}</div>
{'' if front_only else f'<div class="panel back">{BACK}</div>'}
{'' if front_only else '<div class="spine"><div class="t">AI <span>INFRASTRUCTURE</span> ENGINEERING</div><div class="a">BITTLA</div></div>'}
<div class="panel front">{FRONT}</div>
</body></html>""", W, H


def exact_size(path, w_in, h_in):
    """Chromium rounds the page size; set the PDF's boxes to KDP's exact dimensions. The
    difference (a few thousandths of an inch) comes off the top and right edges, inside the
    bleed or wrap, and the page is anchored at the bottom left, so nothing on the trim moves."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
    r = PdfReader(str(path)); w = PdfWriter()
    for page in r.pages:
        box = RectangleObject([0, 0, round(w_in * 72, 3), round(h_in * 72, 3)])
        page.mediabox = box; page.cropbox = box; page.trimbox = box; page.bleedbox = box
        w.add_page(page)
    with open(path, "wb") as f:
        w.write(f)


def chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    found = sorted(glob.glob(os.path.expanduser("~/.cache/puppeteer/chrome/win64-*/chrome-win64/chrome.exe")))
    return found[-1] if found else None


async def render(b, html, W, H, scale):
    pg = await b.new_page(viewport={"width": round(W * 96), "height": round(H * 96)}, device_scale_factor=scale)
    await pg.set_content(html, wait_until="networkidle")
    await pg.evaluate("document.fonts.ready")
    await pg.evaluate(FIT)
    return pg


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=chrome())
        for fmt in FORMATS:
            html, W, H = page_html(fmt)
            name = f"{BASE}_{fmt.capitalize()}_7x10_{PAGES}p_cover"
            pg = await render(b, html, W, H, 1.25)
            await pg.pdf(path=str(OUT / f"{name}.pdf"), width=f"{W}in", height=f"{H}in", print_background=True)
            await pg.screenshot(path=str(OUT / f"{name}_preview.png"))
            exact_size(OUT / f"{name}.pdf", W, H)
            print(f"{fmt}: spine {FORMATS[fmt]['spine']:.4f} in, cover {W:.4f} x {H:.3f} in")
        html, W, H = page_html("paperback", front_only=True)
        pg = await render(b, html, W, H, 2560 / (H * 96))
        await pg.screenshot(path=str(OUT / f"{BASE}_Kindle_ebook_cover_1600x2560.jpg"), type="jpeg", quality=95)
        await b.close()
    print(f"interior {PAGES} pages, {EXERCISES} exercises; outputs in {OUT}")


asyncio.run(main())
