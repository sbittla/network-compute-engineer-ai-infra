#!/usr/bin/env python3
"""Build the concise edition (PDF + Word) from concise/chNN.md.

    python scripts/build_concise.py --check          # structure + word-count gate only
    python scripts/build_concise.py                  # check, then build build/concise/*.docx and *.pdf

Pipeline: Markdown chapters -> one assembled Markdown (front matter, parts, chapters, reading list) ->
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
SUBTITLE = "Concise Edition"
TAGLINE = ("From GPU Compute and High-Speed Networking to Distributed Training, LLM Inference, "
           "and Production-Scale AI Systems")
AUTHOR = "Srinivasa Rao Bittla"
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
    """Back matter: the citation part of each full chapter's 'Further reading' list."""
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


FRONT = f"""---
title: "{TITLE}"
subtitle: "{SUBTITLE}"
author: "{AUTHOR}"
lang: en-US
---

# About This Edition {{.unnumbered}}

This concise edition condenses the 24 chapters of *{TITLE}: {TAGLINE}* to about a third of their
length. It keeps each chapter's core mechanisms, key numbers, worked example, troubleshooting scenario and
operating notes. The full edition, with its labs, exercises, capstones and answer keys, remains the
reference.

**How to read the numbers.** Every quantitative claim carries an evidence label:

| Label | Meaning |
|---|---|
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
Most labs run on a laptop (Level 1); the L2 extensions run on one real GPU host with a CPU fallback, and
the L3 extensions need multi-node RDMA hardware.

**Review status.** The chapters passed the book's internal editorial review. External technical review
and hardware validation of every lab are tracked separately; treat vendor-specific details as
version-sensitive.

"""


def assemble() -> str:
    parts = [FRONT]
    for roman, name, rng in PARTS:
        parts.append(f"# Part {roman} — {name} {{.unnumbered .part}}\n")
        for n in rng:
            t = (SRC / f"ch{n:02d}.md").read_text(encoding="utf-8").strip()
            parts.append(t + "\n")
    parts.append(reading_list())
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
        prev = out[-1] if out else ""
        if (not in_code and re.match(r"- \S", line) and prev.strip() and not re.match(r"\s*([-*+]|\d+\.)\s", prev)
                and not prev.startswith(("|", ">", "#"))):
            out.append("")
        out.append(line)
    md = "\n".join(out)
    cap = r"\*Table [\d.]+ — (?:[^*\n]|\*[^*\n]+\*|\n(?!\n))*?\*"
    table = r"(?:\|[^\n]*\n)+"
    return re.sub(rf"^({cap})\n\n?({table})", lambda m: f"{m.group(2)}\n{m.group(1)}\n", md, flags=re.M)


def captions(md: str) -> str:
    """'*Figure N.x — …*' / '*Table N.x — …*' lines become caption blocks (CSS class + Word 'Caption' style)."""
    # a caption may wrap over several source lines; it ends at the closing '*' before a blank line
    return re.sub(r"^\*((?:Figure|Table) [\d.]+ — (?:[^*\n]|\*[^*\n]+\*|\n(?!\n))*?)\*[ \t]*$",
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
        size = "height=6.6in" if h > 1.25 * w else "width=100%"   # tall diagrams fit the page height, wide ones its width
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
code, pre { font-family: "Cascadia Mono", "Consolas", "DejaVu Sans Mono", monospace; font-size: 8.6pt; }
pre { background: #f5f5f4; border-left: 3px solid #a8a29e; padding: 0.5em 0.7em; white-space: pre-wrap;
      word-break: break-word; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; font-size: 8.8pt; margin: 0.6em 0; break-inside: avoid; }
th, td { border-bottom: 1px solid #d6d3d1; padding: 0.25em 0.4em; text-align: left; vertical-align: top; }
th { border-bottom: 1.5px solid #57534e; font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif; }
blockquote { margin: 0.8em 0; padding: 0.5em 0.8em; background: #f0f4f8; border-left: 3px solid #4a6fa5; }
blockquote p { text-align: left; }
img { max-width: 100%; max-height: 6.6in; object-fit: contain; display: block; margin: 0.6em auto 0.2em; break-inside: avoid; }
.caption p { font-size: 8.8pt; color: #44403c; text-align: center; margin: 0.1em 0 1em; }
.caption { break-before: avoid; }
header#title-block-header { text-align: center; padding-top: 2.6in; break-after: page; }
header#title-block-header p { text-align: center; }
header#title-block-header .title { font-size: 30pt; break-before: avoid; margin: 0; }
header#title-block-header .subtitle { font-size: 16pt; color: #57534e; margin: 0.4em 0 2.2em; }
header#title-block-header .author { font-size: 13pt; }
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
    for i, page in enumerate(doc):
        if i == 0:
            continue
        r = page.rect
        page.insert_textbox(fitz.Rect(0, r.height - 40, r.width, r.height - 22), str(i + 1),
                            fontsize=8.5, fontname="helv", color=(0.35, 0.35, 0.35), align=1)
    tmp = pdf.with_suffix(".tmp.pdf")
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    tmp.replace(pdf)


def build(md: str) -> None:
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
              "--toc-depth=2", "--syntax-highlighting=none"]

    docx = OUT / f"{base}.docx"
    subprocess.run(common + ["-o", str(docx)], check=True)

    css = OUT / "print.css"
    css.write_text(CSS, encoding="utf-8")
    html = OUT / f"{base}.html"
    subprocess.run(common + ["-s", "--embed-resources", "--css", str(css), "-o", str(html),
                             "--metadata", f"pagetitle={TITLE} — {SUBTITLE}"], check=True)
    pdf = OUT / f"{base}.pdf"
    if pdf.exists():
        pdf.unlink()
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--generate-pdf-document-outline",
                    f"--print-to-pdf={pdf}", html.resolve().as_uri()], check=True, capture_output=True, timeout=600)
    if not pdf.exists():
        raise SystemExit("PDF was not produced")
    number_pages(pdf)
    for f in (docx, pdf):
        print(f"wrote {f} ({f.stat().st_size / 1e6:.1f} MB)")


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
    build(assemble())
    return 0


if __name__ == "__main__":
    sys.exit(main())
