#!/usr/bin/env python3
"""Build the concise edition (PDF + Word) from concise/chNN.md.

    python scripts/build_concise.py --check          # structure + word-count gate only
    python scripts/build_concise.py                  # check, then build build/concise/*.docx and *.pdf

Pipeline: Markdown chapters -> one assembled Markdown (title and copyright pages, front matter, concise/front/*.md,
parts, chapters, concise/back/*.md appendices, reading list, concise/about-the-author.md) ->
mermaid blocks rendered to PNG with mermaid-cli (npx) using the installed Chrome/Edge ->
pandoc -> DOCX (with a generated table of contents) and pandoc -> HTML -> headless Chrome/Edge -> PDF.
The spec is docs/CONCISE_EDITION_SPEC.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "concise"
OUT = ROOT / "build" / "concise"
TITLE = "AI Infrastructure Engineering"
SUBTITLE = ("Designing, Building, and Operating GPU Clusters, High-Speed Networks, Distributed Training, "
            "and LLM Inference at Scale")
EDITION = "First Edition"
AUTHOR = "Srinivasa Rao Bittla"
ISBNS = [("9798167679542", "paperback"), ("9798167679764", "hardcover")]
REPO_URL = "https://github.com/sbittla/network-compute-engineer-ai-infra"
FRONT_DIR, BACK_DIR = SRC / "front", SRC / "back"
ABOUT_AUTHOR = SRC / "about-the-author.md"
WORDS_MIN, WORDS_MAX = 3000, 4000

PARTS = [("I", "Foundations", range(1, 4)), ("II", "Accelerated Compute", range(4, 7)),
         ("III", "Networking for AI Clusters", range(7, 11)), ("IV", "Distributed AI Systems", range(11, 16)),
         ("V", "Production Operations", range(16, 23)), ("VI", "Applied Engineering", range(23, 25))]

BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"]


def chapter_dirs() -> dict[int, Path]:
    out = {}
    for d in (ROOT / "book").glob("part-*/ch[0-9][0-9]-*"):
        out[int(d.name[2:4])] = d
    return out


def words(text: str) -> int:
    """Words a reader reads: Markdown table syntax (pipes, separator rows) and code fences are not words."""
    text = re.sub(r"^\s*\|?\s*:?-{3,}.*$", " ", text, flags=re.M)   # table separator rows
    text = re.sub(r"^```\w*\s*$", " ", text, flags=re.M)             # fence lines
    return len([t for t in re.findall(r"\S+", text.replace("|", " ")) if re.search(r"\w", t)])


# ------------------------------------------------------------------------------------------- check
def check_chapter(n: int, text: str) -> list[str]:
    errs = []
    w = words(text)
    if not WORDS_MIN <= w <= WORDS_MAX:
        errs.append(f"{w} words (allowed {WORDS_MIN}-{WORDS_MAX})")
    if not re.match(rf"# Chapter {n} — \S", text):
        errs.append(f"first line must be '# Chapter {n} — <title>'")
    for need in ("**What you will learn**", "## Trade-offs", "## Worked example", "## Troubleshooting", "## Operating notes",
                 "## Key takeaways", "> **Hands-on.**"):
        if need not in text:
            errs.append(f"missing '{need}'")
    fences = re.findall(r"^```(\w*)", text, flags=re.M)
    opens = fences[0::2]   # fences alternate open/close
    if len(fences) % 2:
        errs.append("unbalanced code fences")
    mer = sum(1 for f in opens if f == "mermaid")
    code = len(opens) - mer
    if mer > 2:
        errs.append(f"{mer} mermaid diagrams (max 2)")
    if code > 4:
        errs.append(f"{code} code blocks (max 4)")
    if mer and len(re.findall(r"^\*Figure \d+\.\d+ — ", text, flags=re.M)) < mer:
        errs.append("every mermaid diagram needs a '*Figure N.x — …*' caption")
    if re.search(r"\]\((?!https?://|#)[^)]+\)", text):
        errs.append("relative Markdown link (the PDF has no repository)")
    in_code, prev = False, ""
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith("```"):
            in_code = not in_code
        elif not in_code and line.startswith(">") and prev.strip() and not prev.startswith(">"):
            errs.append(f"line {i}: blockquote needs a blank line before it (pandoc merges it into the paragraph)")
        elif not in_code and re.match(r"\*\*Step \d", line) and prev.strip() and not prev.lstrip().startswith(("-", "*", "|")):
            errs.append(f"line {i}: step label needs a blank line before it (it renders inside the previous paragraph)")
        prev = line
    kt = re.search(r"^## Key takeaways\s*$(.*?)(?=^> \*\*Hands-on|^## |\Z)", text, flags=re.M | re.S)
    if kt:
        body = kt.group(1)
        n = len(re.findall(r"^- ", body, flags=re.M))
        if not 5 <= n <= 8:
            errs.append(f"Key takeaways has {n} bullets (5-8)")
        if re.search(r"^- .*\n\s*\n- ", body, flags=re.M):
            errs.append("Key takeaways list is split by a blank line")
    if re.search(r"solutions/", text):
        errs.append("references solutions/ (instructor-only)")
    return errs


def run_check() -> tuple[bool, dict]:
    ok, report = True, {}
    for n in range(1, 25):
        p = SRC / f"ch{n:02d}.md"
        if not p.exists():
            report[n] = {"words": 0, "errors": ["missing file"]}
            ok = False
            continue
        t = p.read_text(encoding="utf-8")
        e = check_chapter(n, t)
        report[n] = {"words": words(t), "errors": e}
        ok &= not e
    total = sum(r["words"] for r in report.values())
    for n, r in report.items():
        print(f"{'OK  ' if not r['errors'] else 'FAIL'} ch{n:02d} {r['words']:5d} words  " + "; ".join(r["errors"]))
    print(f"total {total} words")
    return ok, report


# ------------------------------------------------------------------------------------------- assemble
def reading_list() -> str:
    """Back matter: concise/further-reading.md (edited citations) when present, otherwise the citation part
    of each full chapter's 'Further reading' list."""
    edited = SRC / "further-reading.md"
    if edited.exists():
        return edited.read_text(encoding="utf-8").strip() + "\n"
    lines = ["# Further Reading {.unnumbered}", "",
             "Selected from the full edition's per-chapter reading lists. Vendor documentation changes; "
             "verify version-sensitive details against the release you run.", ""]
    for n, d in sorted(chapter_dirs().items()):
        m = (d / "manuscript.md").read_text(encoding="utf-8")
        sec = re.search(r"^## Further reading\s*$(.*?)(?=^## |\Z)", m, flags=re.M | re.S)
        if not sec:
            continue
        items = re.findall(r"^- (.*?)(?=^- |\Z)", sec.group(1), flags=re.M | re.S)
        title = re.match(r"# Chapter \d+ — (.*)", m).group(1).strip()
        lines += [f"## Chapter {n}: {title} {{.unnumbered}}", ""]
        for it in items:
            it = " ".join(it.split())
            cite = re.match(r"(\*\*.*?\*\*)", it)
            entry = cite.group(1)[2:-2] if cite else it.split(" — ")[0]
            lines.append(f"- {entry}")
        lines.append("")
    return "\n".join(lines)


def build_meta() -> dict:
    """Version stamp printed on the copyright page and written to BUILD_MANIFEST.json."""
    def git(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""
    commit = git("rev-parse", "--short=12", "HEAD") or "unknown"
    dirty = bool(git("status", "--porcelain", "--", "concise", "scripts/build_concise.py"))
    import datetime
    return {"title": TITLE, "subtitle": SUBTITLE, "edition": EDITION, "author": AUTHOR,
            "isbn": {kind: num for num, kind in ISBNS}, "commit": commit, "source_dirty": dirty,
            "build_date": datetime.date.today().isoformat()}


def front_matter(meta: dict) -> str:
    isbn_lines = "\\\n".join(f"ISBN: {num} ({kind})" for num, kind in ISBNS)
    src = f"commit `{meta['commit']}`" + (" with uncommitted changes" if meta["source_dirty"] else "")
    copyright_md = f"""**{TITLE}**\\
*{SUBTITLE}*

{EDITION}

Copyright © 2026 {AUTHOR}. All rights reserved.

{isbn_lines}

Companion code, labs and exercises: <{REPO_URL}>. The companion code, scripts and lab data are
released under the MIT License; the book's text and figures are not.

This printing was built on {meta['build_date']} from {src}.

ORION, the reference cluster used throughout this book, is an illustrative teaching design, not a
measured system or a product recommendation. Product names are trademarks of their owners.
Vendor-specific details are version-sensitive; verify them against the release you run. The
information in this book is provided without warranty; apply changes to production systems only
under your own change-control process."""
    # The copyright page rides in pandoc's 'abstract' slot, which both the HTML and DOCX writers place
    # directly after the title block and before the table of contents.
    abstract = "\n".join("  " + ln if ln else "" for ln in copyright_md.split("\n"))
    return f"""---
title: "{TITLE}"
subtitle: "{SUBTITLE}"
author: "{AUTHOR}"
date: "{EDITION}"
abstract-title: " "
abstract: |
{abstract}
lang: en-US
---

{FRONT_BODY}"""


FRONT_BODY = f"""# About This Edition {{.unnumbered}}

This concise edition of *{TITLE}: {SUBTITLE}* condenses the full edition's 24 chapters to about a
third of their length. It keeps each chapter's core mechanisms, key numbers, worked example, troubleshooting scenario and
operating notes.

**What is in this book, and what is in the companion repository.** This book is complete as a text: you
can read it without anything else. The practice material is not printed here. It is in the free companion
repository named on the copyright page, which holds the full-length text of every chapter, a lab for every
chapter, 484 exercises with expected outputs, worked solutions and marking schemes, single-machine hands-on
labs, and eight capstone projects. "Using the Practice Material" explains how to find and use them. You need
a laptop for the labs; the optional extensions need one GPU host (L2) or a multi-node RDMA lab fabric (L3).

**How to read the numbers.** Every quantitative claim carries an evidence label:

| Label | Meaning |
|----------|-----------------------|
| `[MEASURED]` | Produced by running a stated procedure on stated hardware and software. |
| `[MODELED]` | Computed from a stated formula and stated assumptions. |
| `[SIMULATED]` | Output of a software simulation; the simulator's blind spots are stated. |
| `[ILLUSTRATIVE]` | A plausible value chosen for teaching, not a claim about any product. |
| `[VENDOR-SPEC, YYYY-MM]` | From vendor documentation, checked in the stated month. Re-verify before relying on it. |
| `[OBSERVED, YYYY-MM-DD]` | Counted from public records on the stated date. Goes stale. |

*Table 0.1 — Evidence labels used throughout the book.*

**The running example.** Most chapters use ORION, an illustrative H100-class reference cluster, so numbers
can be traced from one layer to the next. ORION is a teaching device, not a product recommendation.

**The diagnostic loop.** Every chapter applies the book's central method at least once: *observe a
symptom → collect evidence → trace the bottleneck across compute, network, storage and orchestration →
identify the root cause → make a safe change → validate with repeatable measurements.*

**Hands-on work.** Each chapter ends with a *Hands-on* box naming its lab in the companion repository.
Labs come in three tiers. Most run on a laptop (tier L1); the L2 extensions run on one real GPU host, with
a CPU fallback, and the L3 extensions need multi-node remote direct memory access (RDMA) hardware.

**Review status.** The chapters have passed the book's internal editorial review and an AI-assisted
specialist technical review in seven areas: GPU systems, networking and RDMA, distributed training and
storage, inference, operations and security, facilities and economics, and sources. Their findings and
resolutions are published in the companion repository (`docs/reviews/`). Independent review by external
human specialists is recorded there separately. The lab validation matrix (`docs/LAB_VALIDATION_MATRIX.md`)
lists, for every lab, the hardware and software it was tested on, the date and the result; the multi-node
(L3) extensions have not been run by the author. Treat vendor-specific details as version-sensitive.

"""


def extra_pages(d: Path) -> list[str]:
    """Front/back-matter pages (concise/front/*.md, concise/back/*.md), in filename order."""
    return [p.read_text(encoding="utf-8").strip() + "\n" for p in sorted(d.glob("*.md"))] if d.is_dir() else []


def assemble(meta: dict) -> str:
    parts = [front_matter(meta), *extra_pages(FRONT_DIR)]
    for roman, name, rng in PARTS:
        parts.append(f"# Part {roman} — {name} {{.unnumbered .part}}\n")
        for n in rng:
            t = (SRC / f"ch{n:02d}.md").read_text(encoding="utf-8").strip()
            parts.append(t + "\n")
    parts += extra_pages(BACK_DIR)
    parts.append(reading_list())
    if ABOUT_AUTHOR.exists():
        parts.append(ABOUT_AUTHOR.read_text(encoding="utf-8").strip() + "\n")
    return "\n\n".join(parts)


# ------------------------------------------------------------------------------------------- mermaid
def find_browser() -> str | None:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    return shutil.which("chrome") or shutil.which("msedge")


def png_size(p: Path) -> tuple[int, int]:
    import struct
    with open(p, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def normalize(md: str) -> str:
    """Layout fixes that keep the chapter sources simple:
    - a list directly under a paragraph line (e.g. '**What you will learn**') needs a blank line, or pandoc runs
      the bullets inline;
    - table captions go below their table everywhere (some chapters put them above)."""
    out, lines, in_code = [], md.split("\n"), False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and not line.startswith("```"):
            # keep "22 %" and "≈ 5" together across line breaks
            line = re.sub(r"(\d) %", "\\1\u00a0%", line).replace("≈ ", "≈\u00a0")
            if line.startswith("|"):
                # ISO dates in table cells never split at their hyphens
                line = re.sub(r"(?<![\w\[])(\d{4}-\d{2}-\d{2})(?![\w\]])", r"[\1]{.nowrap}", line)
        prev = out[-1] if out else ""
        if (not in_code and re.match(r"- \S", line) and prev.strip() and not re.match(r"\s*([-*+]|\d+\.)\s", prev)
                and not prev.startswith(("|", ">", "#"))):
            out.append("")
        out.append(line)
    md = "\n".join(out)
    cap = r"\*Table [\dA-Z]+\.[\d.]*[a-z]? — (?:[^*\n]|\*[^*\n]+\*|\n(?!\n))*?\*"
    table = r"(?:\|[^\n]*\n)+"

    def move(m: re.Match) -> str:
        # A caption between two tables belongs to the table above it only if that table has no caption of
        # its own above it; otherwise it is the next table's above-caption and moves below that table.
        above = md[:m.start()].rstrip("\n").split("\n")
        if above and above[-1].startswith("|"):
            k = len(above) - 1
            while k >= 0 and above[k].startswith("|"):
                k -= 1
            while k >= 0 and not above[k].strip():
                k -= 1
            prev_table_captioned = k >= 0 and above[k].rstrip().endswith("*") and re.match(r"\*Table ", "\n".join(above[max(0, k - 3):k + 1]).split("\n\n")[-1])
            if not prev_table_captioned:
                return m.group(0)
        return f"{m.group(2)}\n{m.group(1)}\n"

    md = re.sub(rf"^({cap})\n\n?({table})", move, md, flags=re.M)
    # keep the contents to each chapter's teaching sections: the standard closing sections are unlisted
    return re.sub(r"^(## (?:Trade-offs|Worked example|Troubleshooting|Operating notes|Key takeaways)\b[^\n{]*?)[ \t]*$",
                  r"\1 {.unlisted}", md, flags=re.M)


def captions(md: str) -> str:
    """'*Figure|Table|Listing N.x — …*' lines (N may be an appendix letter) become caption blocks (CSS class + Word 'Caption' style)."""
    # a caption may wrap over several source lines; it ends at the closing '*' before a blank line
    return re.sub(r"^\*((?:Figure|Table|Listing) [\dA-Z]+\.[\d.]*[a-z]? — (?:[^*\n]|\*[^*\n]+\*|\n(?!\n))*?)\*[ \t]*$",
                  lambda m: f'::: {{.caption custom-style="Caption"}}\n{m.group(1)}\n:::', md, flags=re.M)


def render_mermaid(md: str, img_dir: Path, browser: str) -> str:
    img_dir.mkdir(parents=True, exist_ok=True)
    pcfg = img_dir / "puppeteer.json"
    pcfg.write_text(json.dumps({"executablePath": browser, "args": ["--no-sandbox"]}), encoding="utf-8")
    npx = shutil.which("npx") or shutil.which("npx.cmd")

    def render(src: str) -> Path:
        h = hashlib.sha1(src.encode()).hexdigest()[:12]
        png = img_dir / f"mmd-{h}.png"
        if not png.exists():
            mmd = img_dir / f"mmd-{h}.mmd"
            mmd.write_text(src, encoding="utf-8")
            r = subprocess.run([npx, "-y", "@mermaid-js/mermaid-cli@11.4.2", "-i", str(mmd), "-o", str(png),
                                "-p", str(pcfg), "-s", "2", "-b", "white"],
                               capture_output=True, text=True, shell=(os.name == "nt"))
            if r.returncode or not png.exists():
                raise SystemExit(f"mermaid render failed for block {h}:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
        return png

    def repl(m: re.Match) -> str:
        src = m.group(1)
        png = render(src)
        w, h = png_size(png)
        # A long left-to-right chain is squeezed into mermaid's 800 px viewport and its text becomes unreadable
        # at page width; lay it out top-to-bottom instead.
        if w > 3.5 * h and re.match(r"\s*(flowchart|graph)\s+LR\b", src):
            png = render(re.sub(r"^(\s*(?:flowchart|graph)\s+)LR\b", r"\1TB", src, count=1))
            w, h = png_size(png)
        size = "height=5.2in" if h > 1.25 * w else "width=100%"   # tall diagrams fit the page height, wide ones its width
        return f"![]({png.as_posix()}){{{size}}}\n"

    return re.sub(r"^```mermaid\n(.*?)^```\n", repl, md, flags=re.M | re.S)


# ------------------------------------------------------------------------------------------- outputs
CSS = """
@page { size: 7in 10in; margin: 0.8in 0.75in 0.85in 0.75in; }
html { font-family: "Charter", "Georgia", "Cambria", serif; font-size: 10.5pt; line-height: 1.45; color: #111; }
body { margin: 0; }
h1, h2, h3, h4 { font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif; line-height: 1.2; break-after: avoid; }
h1 { font-size: 22pt; margin: 0 0 0.6em; break-before: page; }
h1.part { font-size: 28pt; text-align: center; margin-top: 3in; }
h2 { font-size: 14pt; margin: 1.4em 0 0.4em; }
h3 { font-size: 11.5pt; margin: 1.1em 0 0.3em; }
p { margin: 0 0 0.6em; text-align: justify; hyphens: auto; orphans: 3; widows: 3; }
code, pre { font-family: "Cascadia Mono", "Consolas", "DejaVu Sans Mono", monospace; }
code { font-size: 0.86em; overflow-wrap: anywhere; }
pre code { font-size: inherit; }
pre { font-size: 8.2pt; line-height: 1.35; background: #f5f5f4; border-left: 3px solid #a8a29e; padding: 0.45em 0.55em; white-space: pre-wrap;
      word-break: break-word; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; max-width: 100%; font-size: 9pt; line-height: 1.35; margin: 0.6em 0; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
th, td { border-bottom: 1px solid #d6d3d1; padding: 0.25em 0.4em; text-align: left; vertical-align: top;
         overflow-wrap: break-word; hyphens: manual; }
td code, td a { overflow-wrap: anywhere; }
.nowrap { white-space: nowrap; }
a { overflow-wrap: anywhere; }
th { border-bottom: 1.5px solid #57534e; font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif; }
blockquote { margin: 0.8em 0; padding: 0.5em 0.8em; background: #f0f4f8; border-left: 3px solid #4a6fa5; }
blockquote p { text-align: left; }
img { max-width: 100%; max-height: 5.6in; object-fit: contain; display: block; margin: 0.6em auto 0.2em; break-inside: avoid; }
.caption p { font-size: 9pt; color: #44403c; text-align: center; margin: 0.1em 0 1em; }
.caption { break-before: avoid; }
header#title-block-header { text-align: center; padding-top: 2.6in; break-after: page; }
header#title-block-header p { text-align: center; }
header#title-block-header .title { font-size: 30pt; break-before: avoid; margin: 0; }
header#title-block-header .subtitle { font-size: 16pt; color: #57534e; margin: 0.4em 0 2.2em; }
header#title-block-header .author { font-size: 13pt; }
header#title-block-header .date { font-size: 11pt; color: #57534e; margin-top: 0.8em; }
header#title-block-header .abstract { break-before: page; padding-top: 4.2in; font-size: 8.6pt; line-height: 1.4;
      text-align: left; }
header#title-block-header .abstract p { text-align: left; margin: 0 0 0.7em; }
header#title-block-header .abstract-title { display: none; }
nav#TOC { break-after: page; font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif; font-size: 9.5pt; }
nav#TOC::before { content: "Contents"; display: block; font-size: 22pt; font-weight: bold; margin-bottom: 0.6em; }
nav#TOC ul { list-style: none; padding-left: 1em; margin: 0; }
nav#TOC > ul { padding-left: 0; }
nav#TOC > ul > li { margin-top: 0.5em; font-weight: bold; }
nav#TOC > ul > li li { font-weight: normal; }
nav#TOC ul ul ul { display: none; }
nav#TOC a { color: inherit; text-decoration: none; }
a { color: #1d4e89; text-decoration: none; }
"""


def number_pages(pdf: Path) -> None:
    """Folio on every page after the title page (needs PyMuPDF: pip install pymupdf)."""
    try:
        import fitz
    except ImportError:
        print("PyMuPDF not installed: PDF left without page numbers")
        return
    doc = fitz.open(pdf)
    # Folios use an embedded TrueType font: KDP's print checks reject non-embedded fonts such as PyMuPDF's
    # built-in Helvetica. Georgia is the body font, so it is already licensed for embedding in this PDF.
    font_file = next((f for f in (Path("C:/Windows/Fonts/georgia.ttf"), Path("/usr/share/fonts/truetype/msttcorefonts/Georgia.ttf"),
                                  Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")) if f.is_file()), None)
    if font_file is None:
        raise SystemExit("no embeddable folio font found (Georgia or DejaVu Serif)")
    folio_font = fitz.Font(fontfile=str(font_file))
    FOLIO = dict(fontname="folio", fontfile=str(font_file))
    # Contents: Chrome prints the TOC as links without page numbers; add each target's folio at the right margin.
    for i in range(1, min(doc.page_count, 25)):
        page = doc[i]
        links = [ln for ln in page.get_links() if ln.get("kind") in (fitz.LINK_GOTO, fitz.LINK_NAMED) and ln.get("page", -1) > i]
        if len(links) < 5:
            continue
        right = page.rect.width - 0.75 * 72
        seen = set()
        for ln in links:
            r = ln["from"]
            if round(r.y0) in seen:
                continue
            seen.add(round(r.y0))
            text = str(ln["page"] + 1)
            w = folio_font.text_length(text, fontsize=8.5)
            page.insert_text(fitz.Point(right - w, r.y1 - 2.5), text, fontsize=8.5, **FOLIO,
                             color=(0.2, 0.2, 0.2))
    for i, page in enumerate(doc):
        if i == 0:
            continue
        r = page.rect
        page.insert_textbox(fitz.Rect(0, r.height - 40, r.width, r.height - 22), str(i + 1),
                            fontsize=8.5, **FOLIO, color=(0.35, 0.35, 0.35), align=1)
    meta = doc.metadata or {}
    meta.update({"title": f"{TITLE}: {SUBTITLE}", "author": AUTHOR, "subject": f"{TITLE}, {EDITION}",
                 "keywords": "ISBN " + ", ".join(f"{n} ({k})" for n, k in ISBNS) + "; AI infrastructure; GPU clusters; "
                             "RDMA; distributed training; LLM inference",
                 "creator": "scripts/build_concise.py (pandoc, Chrome)"})
    doc.set_metadata(meta)
    tmp = pdf.with_suffix(".tmp.pdf")
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    tmp.replace(pdf)


BODY_PT = 10.5


def check_print_scale(pdf: Path) -> None:
    """Chrome silently shrinks every page when any element is wider than the text block. Fail if the
    dominant body-text size is not the stylesheet's BODY_PT."""
    try:
        import fitz
    except ImportError:
        return
    from collections import Counter
    sizes: Counter = Counter()
    with fitz.open(pdf) as doc:
        for page in doc.pages(10, min(doc.page_count, 120)):
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        sizes[round(span["size"], 1)] += len(span["text"])
    body = sizes.most_common(1)[0][0]
    if abs(body - BODY_PT) > 0.3:
        raise SystemExit(f"PDF body text is {body} pt, expected {BODY_PT} pt: some element overflows the page "
                         "width and Chrome scaled the whole document down")
    print(f"print scale OK (body text {body} pt)")


def reference_docx(path: Path, pandoc: str) -> Path:
    """Pandoc's default reference.docx, patched to the print spec: 7 x 10 in pages with the PDF's margins,
    10.5 pt serif body, 9 pt tables and captions, 8 pt code."""
    import zipfile
    raw = subprocess.run([pandoc, "--print-default-data-file", "reference.docx"], capture_output=True,
                         check=True).stdout
    tmp = path.with_suffix(".src.docx")
    tmp.write_bytes(raw)
    twips = lambda inches: str(round(inches * 1440))  # noqa: E731
    sect = (f'<w:sectPr><w:pgSz w:w="{twips(7)}" w:h="{twips(10)}"/>'
            f'<w:pgMar w:top="{twips(0.8)}" w:right="{twips(0.75)}" w:bottom="{twips(0.85)}" '
            f'w:left="{twips(0.75)}" w:header="{twips(0.4)}" w:footer="{twips(0.4)}" w:gutter="0"/></w:sectPr>')

    def size(styles: str, style_id: str, half_points: int) -> str:
        m = re.search(rf'<w:style [^>]*w:styleId="{style_id}".*?</w:style>', styles, flags=re.S)
        if not m:
            return styles
        block = m.group(0)
        if "<w:sz " in block:
            new = re.sub(r'<w:sz w:val="\d+"\s*/>', f'<w:sz w:val="{half_points}"/>', block)
        elif "<w:rPr>" in block:
            new = block.replace("<w:rPr>", f'<w:rPr><w:sz w:val="{half_points}"/>', 1)
        else:
            new = block.replace("</w:style>", f'<w:rPr><w:sz w:val="{half_points}"/></w:rPr></w:style>')
        return styles.replace(block, new)

    with zipfile.ZipFile(tmp) as zin, zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = re.sub(r"<w:sectPr>.*?</w:sectPr>", sect, data.decode(), flags=re.S).encode()
            elif item.filename == "word/styles.xml":
                s = data.decode()
                s = re.sub(r'(<w:rPrDefault>.*?)<w:sz w:val="\d+"\s*/>(\s*)<w:szCs w:val="\d+"\s*/>',
                           r'\1<w:sz w:val="21" />\2<w:szCs w:val="21" />', s, count=1, flags=re.S)
                s = re.sub(r'<w:rFonts w:asciiTheme="minorHAnsi"[^>]*/>',
                           '<w:rFonts w:ascii="Georgia" w:hAnsi="Georgia" w:eastAsia="Georgia" w:cs="Georgia" />', s, count=1)
                for sid, hp in (("VerbatimChar", 16), ("Compact", 18), ("Caption", 18), ("TableCaption", 18),
                                ("ImageCaption", 18), ("Abstract", 17), ("Heading1", 36), ("Heading2", 28)):
                    s = size(s, sid, hp)
                data = s.encode()
            zout.writestr(item, data)
    tmp.unlink()
    return path


def build(md: str, meta: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    browser = find_browser()
    if not browser:
        raise SystemExit("no Chrome/Edge found for mermaid rendering and PDF printing")
    md = captions(normalize(render_mermaid(md, OUT / "img", browser)))
    src = OUT / "concise.md"
    src.write_text(md, encoding="utf-8")
    base = f"AI_Infrastructure_Engineering_Concise_Edition"
    pandoc = shutil.which("pandoc") or "pandoc"
    common = [pandoc, str(src), "--from", "markdown+pipe_tables+grid_tables-implicit_figures", "--toc",
              "--toc-depth=2", "--syntax-highlighting=none",
              # very wide line budget: pandoc then emits no fixed column widths and each table is sized to
              # its content (otherwise equal "|---|" separators force equal columns and break words)
              "--columns=100000"]

    docx = OUT / f"{base}.docx"
    ref = reference_docx(OUT / "reference.docx", pandoc)
    subprocess.run(common + ["--reference-doc", str(ref), "-o", str(docx)], check=True)

    css = OUT / "print.css"
    css.write_text(CSS, encoding="utf-8")
    html = OUT / f"{base}.html"
    subprocess.run(common + ["-s", "--embed-resources", "--css", str(css), "-o", str(html),
                             "--metadata", f"pagetitle={TITLE}"], check=True)
    pdf = OUT / f"{base}.pdf"
    if pdf.exists():
        pdf.unlink()
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--generate-pdf-document-outline",
                    f"--print-to-pdf={pdf}", html.resolve().as_uri()], check=True, capture_output=True, timeout=600)
    if not pdf.exists():
        raise SystemExit("PDF was not produced")
    number_pages(pdf)
    check_print_scale(pdf)
    meta = dict(meta, files={})
    for f in (docx, pdf):
        meta["files"][f.name] = {"bytes": f.stat().st_size, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
        print(f"wrote {f} ({f.stat().st_size / 1e6:.1f} MB)")
    (OUT / "BUILD_MANIFEST.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'BUILD_MANIFEST.json'} (commit {meta['commit']}, {meta['build_date']})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="structure and word-count gate only")
    ap.add_argument("--force", action="store_true", help="build even if the check fails")
    a = ap.parse_args()
    ok, _ = run_check()
    if a.check:
        return 0 if ok else 1
    if not ok and not a.force:
        print("check failed; fix the chapters or pass --force")
        return 1
    meta = build_meta()
    build(assemble(meta), meta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
