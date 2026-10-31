#!/usr/bin/env python3
"""Book-wide copyedit lint (release gate G6).

Re-detects the MECHANICAL copyedit issues listed in docs/COPYEDIT_REGISTER.md, plus broken
relative links/anchors and cross-references (Section/Table/Figure/Chapter) that do not resolve.

What is checked is *prose only*: fenced code blocks (``` and ~~~, including mermaid/yaml/json/text),
inline code spans (also when they wrap across lines), HTML comments, link targets and bare URLs are
masked before any term, spelling or unit rule runs. Evidence-label rules look at inline code too,
because labels are written inside backticks by convention.

Usage:
    python scripts/copyedit_lint.py                 # default scope (see DEFAULT_GLOBS)
    python scripts/copyedit_lint.py ch07 ch08       # only files whose path contains a filter
    python scripts/copyedit_lint.py --all           # every .md except review/ and .git/
    python scripts/copyedit_lint.py --only LINK,XREF
    python scripts/copyedit_lint.py --summary       # counts per category/rule only
    python scripts/copyedit_lint.py --format json   # machine-readable findings
    python scripts/copyedit_lint.py --list-rules

Suppressing a finding (only when the register says the text is a deliberate exception):
    put ``<!-- copyedit-lint: ignore -->`` on the line, or
    ``<!-- copyedit-lint: ignore-next-line -->`` on the line before it.

Output: one ``file:line:col: [CATEGORY/RULE] message`` per finding. Exit status 1 if any finding
remains, 0 if clean, 2 on usage error.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GLOBS = [
    "book/part-*/ch*/manuscript.md",
    "book/part-*/ch*/exercises.md",
    "book/part-*/ch*/README.md",
    "book/part-*/ch*/lab/README.md",
    "capstones/README.md",
    "capstones/*/README.md",
    "capstones/*/starter-kit/README.md",
]

# --------------------------------------------------------------------------------------------
# Masking: produce, for every line, a "prose" view in which code/link targets are blanked out
# (same length, so columns stay valid) and a "label" view in which only fenced code is blanked.
# --------------------------------------------------------------------------------------------
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
IGNORE_LINE = "copyedit-lint: ignore"
IGNORE_NEXT = "copyedit-lint: ignore-next-line"


@dataclass
class Line:
    no: int
    raw: str
    prose: str      # code, comments, link targets, URLs masked
    labels: str     # only fenced code masked (inline code kept)
    in_table: bool
    is_heading: bool
    ignored: bool


def _blank(s: str) -> str:
    return re.sub(r"[^\n]", " ", s)


def mask_file(text: str) -> list[Line]:
    raw_lines = text.split("\n")
    fenced = [False] * len(raw_lines)
    fence = None
    for i, ln in enumerate(raw_lines):
        m = FENCE_RE.match(ln)
        if fence:
            fenced[i] = True
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and ln.strip() == m.group(1) + ln.strip()[len(m.group(1)):] and not ln.strip()[len(m.group(1)):].strip():
                fence = None
            continue
        if m:
            fence = m.group(1)
            fenced[i] = True

    # Join non-fenced lines into paragraphs so inline code that wraps lines is handled.
    prose_lines = [""] * len(raw_lines)
    i = 0
    n = len(raw_lines)
    while i < n:
        if fenced[i]:
            prose_lines[i] = _blank(raw_lines[i])
            i += 1
            continue
        j = i
        while j < n and not fenced[j] and raw_lines[j].strip() != "":
            j += 1
        if j == i:  # blank line
            prose_lines[i] = raw_lines[i]
            i += 1
            continue
        block = "\n".join(raw_lines[i:j])
        block = _mask_inline(block)
        for k, part in enumerate(block.split("\n")):
            prose_lines[i + k] = part
        i = j

    out: list[Line] = []
    prev_ignore_next = False
    for idx, ln in enumerate(raw_lines):
        lab = _blank(ln) if fenced[idx] else re.sub(r"<!--.*?-->", lambda m: _blank(m.group(0)), ln)
        ignored = (IGNORE_LINE in ln and IGNORE_NEXT not in ln) or prev_ignore_next
        prev_ignore_next = IGNORE_NEXT in ln
        out.append(Line(
            no=idx + 1,
            raw=ln,
            prose=prose_lines[idx],
            labels=lab,
            in_table=(not fenced[idx]) and ln.lstrip().startswith("|"),
            is_heading=(not fenced[idx]) and bool(re.match(r"^#{1,6}\s", ln)),
            ignored=ignored or fenced[idx],
        ))
    return out


def _mask_inline(block: str) -> str:
    # HTML comments (may span lines)
    block = re.sub(r"<!--.*?-->", lambda m: _blank(m.group(0)), block, flags=re.S)
    # inline code: a backtick run opens, the next run of the same length closes (may span lines)
    res = []
    pos = 0
    for m in re.finditer(r"`+", block):
        if m.start() < pos:
            continue
        run = m.group(0)
        close = re.compile(r"(?<!`)" + re.escape(run) + r"(?!`)")
        c = close.search(block, m.end())
        if not c:
            continue
        res.append(block[pos:m.start()])
        res.append(_blank(block[m.start():c.end()]))
        pos = c.end()
    res.append(block[pos:])
    block = "".join(res)
    # link targets ](...) and autolinks / bare URLs
    block = re.sub(r"\]\(([^)\s]*)(\s+\"[^\"]*\")?\)", lambda m: "]" + _blank(m.group(0)[1:]), block)
    block = re.sub(r"<https?://[^>\s]*>|https?://[^\s)]+", lambda m: _blank(m.group(0)), block)
    return block


# --------------------------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------------------------
@dataclass
class Rule:
    rid: str
    cat: str
    pattern: re.Pattern
    repl: str | Callable[[re.Match], str] | None
    note: str
    where: str = "prose"           # prose | labels
    skip_tables: bool = False
    skip_headings: bool = False
    skip_quoted: bool = False      # skip matches inside "..." / “...” (cited titles)
    exceptions: tuple[str, ...] = ()  # substrings of the raw line that exempt it


def _r(p: str, flags: int = 0) -> re.Pattern:
    return re.compile(p, flags)


def _keepcase(word: str, new: str) -> str:
    return new[0].upper() + new[1:] if word[:1].isupper() else new


CITATION_EXC = (
    "The Datacenter as a Computer", "AI Training Datacenters", "Datacenter Networks",
    "for the Datacenter", "SLURM: Simple Linux Utility", "Fibre optic", "Fibre Channel",
    "Fibre-optic",
)

IZE_STEMS = (
    "optim|util|organ|normal|initial|priorit|minim|maxim|summar|character|recogn|standard|serial|"
    "deserial|synchron|special|general|final|visual|amort|author|capital|custom|emphas|parallel|"
    "virtual|container|categor|random|token|quant|material|local|central|decentral|stabil|"
    "neutral|penal|harmon|sanit|memor|apolog|critic|digit|operational|production|rational|"
    "equal|real|monet|summar|mobil|vectori|crystal|polar|steril|util"
)

RULES: list[Rule] = [
    # ---------------- Terms (vendor / project spelling) ----------------
    Rule("roce", "TERM", _r(r"\bRoCE[ -]v2\b|\bROCEv2\b|\bRoCEV2\b"), "RoCEv2", "RoCEv2 (IBTA Annex A17 spelling, STYLE_GUIDE §6)"),
    Rule("infiniband", "TERM", _r(r"\bInfiniband\b|\bINFINIBAND\b|(?<![/\w-])infiniband(?![/\w-])"), "InfiniBand", "InfiniBand (IBTA trademark spelling)"),
    Rule("allreduce", "TERM", _r(r"\b(?:allreduce|AllReduce|All-Reduce|Allreduce)\b"), "all-reduce", "all-reduce in prose (STYLE_GUIDE §6); API names stay in backticks"),
    Rule("allgather", "TERM", _r(r"\b(?:allgather|AllGather|All-Gather|Allgather)\b"), "all-gather", "all-gather in prose"),
    Rule("reducescatter", "TERM", _r(r"\b(?:reducescatter|ReduceScatter|Reduce-Scatter|Reducescatter)\b"), "reduce-scatter", "reduce-scatter in prose"),
    Rule("alltoall", "TERM", _r(r"\b(?:alltoall|AllToAll|All-To-All|Alltoall)\b"), "all-to-all", "all-to-all in prose"),
    Rule("gpudirect", "TERM", _r(r"\bGPU[ -]Direct\b|\bGPUdirect\b|\bGpuDirect\b"), "GPUDirect", "GPUDirect (NVIDIA spelling)"),
    Rule("nvlink", "TERM", _r(r"\bNVlink\b|\bNvlink\b|\bNvLink\b|\bNVLINK\b"), "NVLink", "NVLink (NVIDIA spelling)"),
    Rule("nvswitch", "TERM", _r(r"\bNVswitch\b|\bNvSwitch\b|\bNVSWITCH\b"), "NVSwitch", "NVSwitch (NVIDIA spelling)"),
    Rule("nvidia", "TERM", _r(r"\bNvidia\b|\bnVidia\b"), "NVIDIA", "NVIDIA (company spelling)"),
    Rule("tensorcore", "TERM", _r(r"\b[Tt]ensor[- ][Cc]ore(s?)\b|\bTensorCores?\b"),
         lambda m: "Tensor Core" + ("s" if m.group(0).endswith("s") else ""),
         "Tensor Core(s) (NVIDIA spelling), also as a modifier: 'Tensor Core GEMM'",
         exceptions=("Tensor Core GPU Architecture",)),
    Rule("connectx", "TERM", _r(r"\bConnect-X\b|\bConnectx\b"), "ConnectX", "ConnectX (NVIDIA spelling)"),
    Rule("bluefield", "TERM", _r(r"\bBluefield\b|\bBlue[Ff]ield-?(?=\d)"), "BlueField", "BlueField (NVIDIA spelling)"),
    Rule("pytorch", "TERM", _r(r"\bPytorch\b|(?<![\w./-])pytorch(?![\w./-])"), "PyTorch", "PyTorch (project spelling)"),
    Rule("deepspeed", "TERM", _r(r"\bDeepspeed\b"), "DeepSpeed", "DeepSpeed (project spelling)"),
    Rule("vllm", "TERM", _r(r"\bVLLM\b|\bVllm\b"), "vLLM", "vLLM (project spelling)"),
    Rule("pcie", "TERM", _r(r"\bPCI-[Ee]\b|\bPCIE\b"), "PCIe", "PCIe (PCI-SIG spelling)"),
    Rule("slurm", "TERM", _r(r"\bSLURM\b"), "Slurm", "Slurm (SchedMD spelling)", exceptions=CITATION_EXC),
    Rule("k8s", "TERM", _r(r"(?<![\w./-])[kK]8s(?![\w./-])"), "Kubernetes", "Kubernetes in prose"),
    Rule("datacentre", "TERM", _r(r"\b([Dd]ata)([ -])centres?\b"),
         lambda m: m.group(1) + m.group(2) + "center" + ("s" if m.group(0).endswith("s") else ""),
         "data center (noun) / data-center (modifier); majority and Ch 2 title", exceptions=CITATION_EXC),
    Rule("datacenter", "TERM", _r(r"(?<![\w/-])datacenters?(?![\w/-])"),
         lambda m: "data center" + ("s" if m.group(0).endswith("s") else ""),
         "data center (two words) in prose", skip_quoted=True, exceptions=CITATION_EXC),
    Rule("railopt", "TERM", _r(r"\b([Rr]ail)[- ]optimi[sz]ed\b|\b([Rr]ail) optimized\b"),
         lambda m: (m.group(1) or m.group(2)) + "-optimized", "rail-optimized (REFERENCE_CLUSTER)"),
    Rule("kvcache", "TERM", _r(r"\bKV-cache\b|\bkv cache\b|\bKV Cache\b(?! [A-Z])"), "KV cache", "KV cache, also as a modifier (STYLE_GUIDE §6)", skip_headings=False),
    Rule("checkpoint", "TERM", _r(r"\b([Cc])heck-points?\b"), lambda m: m.group(1) + "heckpoint" + ("s" if m.group(0).endswith("s") else ""), "checkpoint (one word)"),
    Rule("multitenant", "TERM", _r(r"\b([Mm])ultitenan(t|cy)\b|\b([Mm])ulti tenan(t|cy)\b"),
         lambda m: (m.group(1) or m.group(3)) + "ulti-tenan" + (m.group(2) or m.group(4)), "multi-tenant / multi-tenancy (Ch 19 title)"),
    Rule("tokps", "TERM", _r(r"\btok/s\b|\btokens/sec\b|\btokens/second\b|\btok/sec\b"), "tokens/s", "tokens/s"),
    Rule("percentile", "TERM", _r(r"\bP(50|90|95|99|99\.9)\b"), lambda m: "p" + m.group(1), "lowercase percentiles p50/p95/p99 (STYLE_GUIDE §5)"),
    Rule("parallel-eq", "TERM", _r(r"\b(TP|PP|DP|EP|CP|SP)=(\d+)\b"), lambda m: f"{m.group(1)} = {m.group(2)}", "spaced 'TP = 8' (REFERENCE_CLUSTER)"),
    Rule("precision", "TERM", _r(r"(?<![\w-])(fp8|fp16|fp32|bf16|tf32)(?![\w-])"), lambda m: m.group(1).upper(), "uppercase BF16/FP8/FP16/FP32/TF32 in prose"),
    Rule("section-sign", "XREF-STYLE", _r(r"(?<![Oo]utline )(?<![Oo]utline)§§?\s?(\d+\.\d+(?:\.\d+)*)"),
         lambda m: ("Sections " if m.group(0).startswith("§§") else "Section ") + m.group(1),
         "book sections are 'Section N.M' (STYLE_GUIDE §10); '§N' for other documents' sections is allowed"),
    Rule("ch-abbrev", "XREF-STYLE", _r(r"\bCh\.? ?(\d{1,2})\b"), lambda m: "Chapter " + m.group(1),
         "'Chapter N' in prose (STYLE_GUIDE §10); 'Ch N' is allowed in table cells", skip_tables=True),
    # ---------------- Acronym expansions (canonical wording, register section (b)) ----------------
    Rule("exp-mfu", "ACRONYM", _r(r"\b([Mm])odel FLOP utili[sz]ation\b|\b([Mm])odel FLOPs utilisation\b"),
         lambda m: (m.group(1) or m.group(2)) + "odel FLOPs utilization", "MFU = model FLOPs utilization (PaLM paper term; majority)"),
    Rule("exp-pfc", "ACRONYM", _r(r"\bPriority Flow Control\b"), "priority flow control",
         "PFC = priority flow control (lower case like other generic expansions); 'Priority-based Flow Control' only when naming IEEE 802.1Qbb"),
    Rule("exp-pxn", "ACRONYM", _r(r"\bPCIe ?× ?NVLink\b"), "PCI × NVLink", "PXN = PCI × NVLink (NCCL's own expansion)"),
    Rule("exp-rma", "ACRONYM", _r(r"\b([Rr])eturn[- ]material authori[sz]ation\b|\b([Rr])eturn-merchandise authori[sz]ation\b"),
         lambda m: (m.group(1) or m.group(2)) + "eturn merchandise authorization", "RMA = return merchandise authorization"),
    Rule("exp-ber", "ACRONYM", _r(r"\b([Bb])it[- ]error rate\b|\b([Bb])it-error ratio\b"),
         lambda m: (m.group(1) or m.group(2)) + "it error ratio", "BER = bit error ratio (IEEE 802.3 term)"),
    Rule("vs-period", "STYLE", _r(r"\bvs\.(?=\s)"), "vs", "'vs' without a period (majority form)"),
    Rule("approx-tilde", "UNIT", _r(r"(?<![\w/~$])~ ?(?=\d)"), "≈ ", "approximation sign '≈ ' with a space, not '~'"),
    Rule("ratio-spaced", "UNIT", _r(r"(?<![\d:])(\d+(?:\.\d+)?) : (\d+(?:\.\d+)?)(?![\d:])"), lambda m: f"{m.group(1)}:{m.group(2)}", "ratios as 'N:1' without spaces (majority form)"),
    # ---------------- Spelling (house style: -ize/-yze, -our, -ll-) ----------------
    Rule("ize", "SPELLING", _r(r"\b((?:pre-|re-|de-|un)?(?:" + IZE_STEMS + r")i)s(e|es|ed|ing|ation|ations|er|ers|able)\b", re.I),
         lambda m: m.group(1) + ("Z" if m.group(0)[len(m.group(1))].isupper() else "z") + m.group(2),
         "-ize/-ization (house style; majority of chapters)", skip_quoted=True, exceptions=CITATION_EXC),
    Rule("analyse", "SPELLING", _r(r"\b([Aa])nalys(e|ed|ing)\b"), lambda m: m.group(1) + "nalyz" + m.group(2), "analyze ('analyses' skipped: plural noun is correct; house -yze; lab tools are 'analyzer')", skip_quoted=True),
    Rule("behavior", "SPELLING", _r(r"\b([Bb])ehavior(s|al|ally)?\b"), lambda m: m.group(1) + "ehaviour" + (m.group(2) or ""), "behaviour (only form in use)"),
    Rule("labeled", "SPELLING", _r(r"\b([Ll])abel(ed|ing)\b"), lambda m: m.group(1) + "abell" + m.group(2), "labelled / labelling (majority)",
         exceptions=("ANSI/TIA-606",)),
    Rule("modelled", "SPELLING", _r(r"\b([Mm])odell(ed|ing)\b"), lambda m: m.group(1) + "odel" + m.group(2), "modeled / modeling (majority; matches [MODELED])"),
    Rule("centre", "SPELLING", _r(r"(?<![\w-])([Cc])entre(s?)\b"), lambda m: m.group(1) + "enter" + m.group(2), "center (majority)", skip_quoted=True, exceptions=CITATION_EXC),
    Rule("fibre", "SPELLING", _r(r"\b([Ff])ibre(s?)\b"), lambda m: m.group(1) + "iber" + m.group(2), "fiber (majority)", skip_quoted=True, exceptions=CITATION_EXC),
    Rule("catalog", "SPELLING", _r(r"\b([Cc])atalog(s?)\b"), lambda m: m.group(1) + "atalogue" + m.group(2), "catalogue (majority)"),
    Rule("artefact", "SPELLING", _r(r"\b([Aa])rtefact(s?)\b"), lambda m: m.group(1) + "rtifact" + m.group(2), "artifact (majority)"),
    Rule("queuing", "SPELLING", _r(r"\b([Qq])ueuing\b"), lambda m: m.group(1) + "ueueing", "queueing (majority)"),
    Rule("judgement", "SPELLING", _r(r"\b([Jj])udgement(s?)\b"), lambda m: m.group(1) + "udgment" + m.group(2), "judgment (majority)"),
    Rule("towards", "SPELLING", _r(r"\b([Tt])owards\b"), lambda m: m.group(1) + "oward", "toward (majority)"),
    Rule("signaled", "SPELLING", _r(r"\b([Ss])ignal(ed|ing)\b"), lambda m: m.group(1) + "ignall" + m.group(2), "signalled / signalling (only form in use)"),
    Rule("canceled", "SPELLING", _r(r"\b([Cc])ancel(ed|ing)\b"), lambda m: m.group(1) + "ancell" + m.group(2), "cancelled / cancelling (only form in use)"),
    Rule("favor", "SPELLING", _r(r"\b([Ff])avor(s|ed|ing|able|ite|ites)?\b"), lambda m: m.group(1) + "avour" + (m.group(2) or ""), "favour (only form in use)"),
    Rule("rerun", "SPELLING", _r(r"\b([Rr])e-(run|runs|image|imaged|imaging|test|tested|testing)\b"), lambda m: m.group(1) + "e" + m.group(2), "rerun / reimage / retest (closed compounds)"),
    Rule("microbatch", "SPELLING", _r(r"\b([Mm])icrobatch(es|ing)?\b"), lambda m: m.group(1) + "icro-batch" + (m.group(2) or ""), "micro-batch (majority)"),
    Rule("compounds", "SPELLING", _r(r"\b(speed-up|scaleout|over-subscri\w+|burnin|time-out|data-set|run-book|post-mortem|fail-over|health-check)\b"),
         lambda m: {"speed-up": "speedup", "scaleout": "scale-out", "burnin": "burn-in", "time-out": "timeout",
                    "data-set": "dataset", "run-book": "runbook", "post-mortem": "postmortem", "fail-over": "failover",
                    "health-check": "health check"}.get(m.group(1), m.group(1).replace("over-subscri", "oversubscri")),
         "closed/hyphenated compound as used by the majority"),
    # ---------------- Units and numbers ----------------
    Rule("gbps", "UNIT", _r(r"(?<=\d)( ?)(G|M|T|K|k)bps\b"), lambda m: " " + m.group(2).replace("K", "k") + "b/s", "bit rates as Gb/s, Mb/s, Tb/s (STYLE_GUIDE §5)"),
    Rule("GBps", "UNIT", _r(r"(?<=\d)( ?)(G|M|T|K|k)Bps\b"), lambda m: " " + m.group(2) + "B/s", "byte rates as GB/s, MB/s"),
    Rule("gbit", "UNIT", _r(r"(?<=\d)( ?)(G|M|T)bit/s\b"), lambda m: " " + m.group(2) + "b/s", "bit rates as Gb/s"),
    Rule("per-sec", "UNIT", _r(r"(?<=\d)( ?)([GMTK]i?[Bb])/sec\b"), lambda m: " " + m.group(2) + "/s", "'/s', not '/sec'"),
    Rule("usec", "UNIT", _r(r"(?<=\d)( ?)(us|usec|usecs|μs)\b"), " µs", "microseconds as 'µs' (U+00B5)"),
    Rule("mu-greek", "UNIT", _r(r"μs\b"), "µs", "micro sign U+00B5, not Greek mu U+03BC"),
    Rule("kw", "UNIT", _r(r"(?<=\d)( ?)(KW|kw|Kw)\b"), " kW", "kW"),
    Rule("unit-space", "UNIT", _r(r"(?<![\w.-])(\d+(?:[.,]\d+)?)(Gb/s|GB/s|Tb/s|TB/s|Mb/s|MB/s|GiB|MiB|KiB|TiB|GB|TB|MB|KB|ms|µs|ns|kW|MW|GHz|MHz|kHz|dBm|°C|TFLOP/s|PFLOP/s)(?![\w/])"),
         lambda m: m.group(1) + " " + m.group(2), "space between number and unit (STYLE_GUIDE §5)"),
    Rule("degC", "UNIT", _r(r"(?<=\d)( ?)[º˚]C\b|(?<=\d)°C\b"), " °C", "'N °C' with a space and the degree sign"),
    Rule("times-x", "UNIT", _r(r"(?<![\w.])(\d+(?:\.\d+)?) x (?=\d)|(?<![\w.])([1-9]\d*(?:\.\d+)?)x(?=\d)|(?<![\w.])(\d+(?:\.\d+)?)x(?![\w])"),
         lambda m: (m.group(1) + " × ") if m.group(1) else ((m.group(2) + " × ") if m.group(2) else (m.group(3) + "×")),
         "multiplication sign '×' (spaced between operands, unspaced for a factor: '9×')",
         exceptions=("802.3x",)),
    Rule("pct-space", "UNIT", _r(r"(?<=\d)%"), " %", "'40 %' with a space (house form, REFERENCE_CLUSTER)"),
    Rule("thousands-space", "UNIT", _r(r"(?<![\d,.])(\d{1,3}(?: \d{3})+)(?= ?(?:[kMGT]?(?:b/s|B/s|Hz)|bytes|tokens|B\b))"),
         lambda m: m.group(1).replace(" ", ","), "thousands separator is a comma"),
    Rule("thousands-missing", "UNIT", _r(r"(?<![\w.,/:#-])(\d{5,})(?=(?:\.\d+)? ?(?:B|bytes|tokens|GPUs|nodes|s|ms|µs|ns|W|kW|IOPS|codewords|iterations|steps|h|MiB|KiB|GiB|GB|MB|KB|Mb/s|Gb/s|kHz|MHz)\b)"),
         lambda m: f"{int(m.group(1)):,}", "numbers ≥ 10,000 that carry a unit take comma separators"),
    # ---------------- Evidence labels ----------------
    Rule("label-backticks", "LABEL", _r(r"(?<!`)\[(MEASURED|MODELED|SIMULATED|ILLUSTRATIVE|VENDOR-SPEC|OBSERVED)\b[^\]\n]*\](?!`)"),
         lambda m: "`" + m.group(0) + "`", "evidence labels are written in backticks (house form, 96 % of labels)", where="prose_label"),
    Rule("label-malformed", "LABEL", _r(r"\[(?:VENDOR[ _]SPEC|Vendor[- ]?[Ss]pec|Illustrative|Modell?ed|MODELLED|Measured|Simulated|Observed|ESTIMATED|ASSUMED)\b[^\]\n]*\]"),
         None, "malformed evidence label; use one of STYLE_GUIDE §3 exactly", where="labels"),
    Rule("label-vendor-date", "LABEL", _r(r"\[VENDOR-SPEC(?!, (?:\d{4}-\d{2}|YYYY-MM)\b)[^\]\n]*\]"), None,
         "[VENDOR-SPEC] needs ', YYYY-MM' (month checked) immediately after the tag; the literal template '[VENDOR-SPEC, YYYY-MM]' is allowed when the label itself is being described (STYLE_GUIDE §3)", where="labels"),
    Rule("label-observed-date", "LABEL", _r(r"\[OBSERVED(?!, (?:\d{4}-\d{2}-\d{2}|YYYY-MM-DD)\b)[^\]\n]*\]"), None,
         "[OBSERVED] needs ', YYYY-MM-DD' (STYLE_GUIDE §3)", where="labels"),
]


def _in_quotes(text: str, pos: int) -> bool:
    before = text[:pos]
    if before.count("“") > before.count("”"):
        return True
    return before.count('"') % 2 == 1


def apply_rules(path: Path, lines: list[Line], rules: Iterable[Rule]) -> list[dict]:
    out = []
    for ln in lines:
        if ln.ignored:
            continue
        for r in rules:
            if r.skip_tables and ln.in_table:
                continue
            if r.skip_headings and ln.is_heading:
                continue
            if r.exceptions and any(e in ln.raw for e in r.exceptions):
                continue
            text = ln.labels if r.where in ("labels", "prose_label") else ln.prose
            for m in r.pattern.finditer(text):
                if r.where == "prose_label":
                    # label must sit outside inline code: the prose view keeps it unmasked
                    if ln.prose[m.start():m.start() + 1] != "[":
                        continue
                if r.skip_quoted and _in_quotes(ln.prose, m.start()):
                    continue
                found = ln.raw[m.start():m.end()]
                if r.repl is None:
                    repl = None
                elif callable(r.repl):
                    repl = r.repl(m)
                else:
                    repl = r.repl
                if repl == found:
                    continue
                out.append(dict(file=rel(path), line=ln.no, col=m.start() + 1, end=m.end(), cat=r.cat, rule=r.rid,
                                found=found, replacement=repl, note=r.note))
    return _drop_nested(out)


def _drop_nested(items: list[dict]) -> list[dict]:
    """If one finding's span lies inside another's on the same line, keep only the outer one."""
    keep = []
    for a in items:
        inner = any(b is not a and b["line"] == a["line"] and b["col"] <= a["col"] and b["end"] >= a["end"]
                    and (b["end"] - b["col"]) > (a["end"] - a["col"]) for b in items)
        if not inner:
            keep.append(a)
    return keep


# --------------------------------------------------------------------------------------------
# Links and anchors
# --------------------------------------------------------------------------------------------
LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def gh_slug(heading: str) -> str:
    h = heading.strip().lower()
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", h)
    h = h.replace("`", "")
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")


_anchor_cache: dict[Path, set[str]] = {}


def anchors_of(p: Path) -> set[str]:
    if p in _anchor_cache:
        return _anchor_cache[p]
    seen: collections.Counter = collections.Counter()
    res: set[str] = set()
    try:
        for ln in mask_file(p.read_text(encoding="utf-8")):
            if ln.ignored and FENCE_RE.match(ln.raw) is None and not ln.is_heading:
                pass
            if ln.is_heading and not ln.raw.startswith("#!"):
                m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", ln.raw)
                if m:
                    b = gh_slug(m.group(1))
                    res.add(b if seen[b] == 0 else f"{b}-{seen[b]}")
                    seen[b] += 1
            for m in re.finditer(r"<a\s+(?:name|id)=\"([^\"]+)\"", ln.raw):
                res.add(m.group(1))
    except OSError:
        pass
    _anchor_cache[p] = res
    return res


def check_links(path: Path, lines: list[Line]) -> list[dict]:
    out = []
    for ln in lines:
        if ln.ignored:
            continue
        # links are looked for in the label view (fenced code masked) with inline code masked
        view = ln.labels
        # blank inline code using the prose view (prose blanks code AND link targets, so rebuild)
        for m in LINK_RE.finditer(view):
            if ln.prose[m.start():m.start() + 1] not in ("[", "!"):
                continue  # inside inline code
            target = m.group(2)
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            pth, _, frag = target.partition("#")
            if pth:
                p = (path.parent / pth.replace("%20", " ")).resolve()
                if not p.exists():
                    out.append(dict(file=rel(path), line=ln.no, col=m.start() + 1, cat="LINK", rule="broken-link",
                                    found=target, replacement=None, note="relative link target does not exist"))
                    continue
            else:
                p = path
            if frag and p.is_file() and p.suffix == ".md" and frag.lower() not in anchors_of(p):
                out.append(dict(file=rel(path), line=ln.no, col=m.start() + 1, cat="LINK", rule="broken-anchor",
                                found=target, replacement=None, note=f"anchor #{frag} not found in {p.name}"))
    return out


# --------------------------------------------------------------------------------------------
# Cross-references
# --------------------------------------------------------------------------------------------
class BookIndex:
    def __init__(self) -> None:
        self.chapters: dict[int, Path] = {}
        self.sections: dict[int, set[str]] = collections.defaultdict(set)
        self.tables: dict[int, set[str]] = collections.defaultdict(set)
        self.figures: dict[int, set[str]] = collections.defaultdict(set)
        for d in sorted(ROOT.glob("book/part-*/ch*")):
            m = re.match(r"ch(\d\d)-", d.name)
            if not m or not d.is_dir():
                continue
            n = int(m.group(1))
            self.chapters[n] = d
            ms = d / "manuscript.md"
            files = [p for p in d.glob("*.md")] + [p for p in (d / "lab").glob("README.md")]
            for f in files:
                for ln in mask_file(f.read_text(encoding="utf-8")):
                    if ln.ignored:
                        continue
                    if f == ms:
                        h = re.match(r"^#{2,4}\s+(\d+)\.(\d+(?:\.\d+)*)\.?\s", ln.raw)
                        if h and int(h.group(1)) == n:
                            self.sections[n].add(f"{h.group(1)}.{h.group(2)}")
                    for kind, store in (("Table", self.tables), ("Figure", self.figures)):
                        c = re.match(r"^\s*\*\s*" + kind + r"\s+(\d+)\.(\d+[a-z]?)\s*[—:.–-]", ln.raw)
                        if c:
                            store[int(c.group(1))].add(f"{c.group(1)}.{c.group(2)}")


SEC_REF = re.compile(r"\b(?:Sections?|§§?)\s*(\d+\.\d+(?:\.\d+)*(?:\s*(?:[–-]|,|and|or|&)\s*(?:\d+\.\d+(?:\.\d+)*))*)")


def check_xrefs(path: Path, lines: list[Line], idx: BookIndex) -> list[dict]:
    out = []
    in_book = path.is_relative_to(ROOT / "book") or path.is_relative_to(ROOT / "capstones")
    if not in_book:
        return out

    def add(ln: Line, col: int, found: str, note: str) -> None:
        out.append(dict(file=rel(path), line=ln.no, col=col, cat="XREF", rule="missing-target",
                        found=found, replacement=None, note=note))

    for ln in lines:
        if ln.ignored:
            continue
        s = ln.prose
        for m in SEC_REF.finditer(s):
            if re.search(r"[Oo]utline\s*$", s[:m.start()]):
                continue
            for sid in re.findall(r"\d+\.\d+(?:\.\d+)*", m.group(1)):
                n = int(sid.split(".")[0])
                if n not in idx.chapters:
                    add(ln, m.start() + 1, m.group(0), f"Section {sid}: there is no Chapter {n}")
                elif sid not in idx.sections[n]:
                    add(ln, m.start() + 1, m.group(0), f"Section {sid} has no numbered heading in Chapter {n}")
        for kind, store in (("Table", idx.tables), ("Figure", idx.figures)):
            for m in re.finditer(r"\b" + kind + r"s?\s+(\d+\.\d+[a-z]?(?:\s*(?:[–-]|,|and|or)\s*\d+\.\d+[a-z]?)*)", s):
                if re.match(r"^\s*\*\s*" + kind, ln.raw) and m.start() < 12:
                    continue  # the caption itself
                for tid in re.findall(r"\d+\.\d+[a-z]?", m.group(1)):
                    n = int(tid.split(".")[0])
                    if tid not in store.get(n, set()):
                        add(ln, m.start() + 1, m.group(0), f"{kind} {tid} has no caption '*{kind} {tid} — …*'")
        for m in re.finditer(r"\bChapters?\s+(\d+)(?:\s*[–-]\s*(\d+))?", s):
            for v in (m.group(1), m.group(2)):
                if v and not (1 <= int(v) <= max(idx.chapters)):
                    add(ln, m.start() + 1, m.group(0), f"Chapter {v} does not exist")
        for m in re.finditer(r"\bCapstones?\s+([A-Z])\b", s):
            if not list(ROOT.glob(f"capstones/capstone-{m.group(1).lower()}-*")):
                add(ln, m.start() + 1, m.group(0), f"Capstone {m.group(1)} does not exist")
    return out


# --------------------------------------------------------------------------------------------
def rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def collect_files(all_md: bool, filters: list[str]) -> list[Path]:
    if all_md:
        files = [p for p in ROOT.rglob("*.md") if "review" not in p.parts and ".git" not in p.parts
                 and p.name != "COPYEDIT_REGISTER.md"]  # the register quotes every variant on purpose
    else:
        files = []
        for g in DEFAULT_GLOBS:
            files += [p for p in ROOT.glob(g) if "review" not in p.parts]
    files = sorted(set(files))
    if filters:
        files = [p for p in files if any(f in rel(p) for f in filters)]
    return files


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("filters", nargs="*", help="only files whose repo-relative path contains one of these")
    ap.add_argument("--all", action="store_true", help="lint every .md file except review/, .git/ and this register")
    ap.add_argument("--only", default="", help="comma-separated categories or rule ids to report")
    ap.add_argument("--summary", action="store_true", help="print counts only")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--list-rules", action="store_true")
    args = ap.parse_args(argv)

    if args.list_rules:
        for r in RULES:
            print(f"{r.cat:10s} {r.rid:20s} {r.note}")
        print(f"{'LINK':10s} {'broken-link':20s} relative link target does not exist")
        print(f"{'LINK':10s} {'broken-anchor':20s} #anchor not found in target .md")
        print(f"{'XREF':10s} {'missing-target':20s} Section/Table/Figure/Chapter/Capstone reference does not resolve")
        return 0

    only = {x.strip() for x in args.only.split(",") if x.strip()}
    files = collect_files(args.all, args.filters)
    if not files:
        print("no files matched", file=sys.stderr)
        return 2
    idx = BookIndex()
    findings: list[dict] = []
    for f in files:
        lines = mask_file(f.read_text(encoding="utf-8"))
        findings += apply_rules(f, lines, RULES)
        findings += check_links(f, lines)
        findings += check_xrefs(f, lines, idx)
    if only:
        findings = [x for x in findings if x["cat"] in only or x["rule"] in only]
    findings.sort(key=lambda x: (x["file"], x["line"], x["col"]))

    if args.format == "json":
        json.dump(findings, sys.stdout, ensure_ascii=False, indent=1)
        print()
    elif not args.summary:
        for x in findings:
            rep = f" -> {x['replacement']!r}" if x["replacement"] is not None else ""
            print(f"{x['file']}:{x['line']}:{x['col']}: [{x['cat']}/{x['rule']}] {x['found']!r}{rep}  ({x['note']})")
    if args.format == "text":
        by_cat = collections.Counter(x["cat"] for x in findings)
        by_rule = collections.Counter(f"{x['cat']}/{x['rule']}" for x in findings)
        nfiles = len({x["file"] for x in findings})
        print(f"\n{len(findings)} finding(s) in {nfiles} file(s) of {len(files)} scanned", file=sys.stderr if not args.summary else sys.stdout)
        out = sys.stdout if args.summary else sys.stderr
        for c, n in sorted(by_cat.items()):
            print(f"  {c:11s} {n}", file=out)
        if args.summary:
            for c, n in sorted(by_rule.items()):
                print(f"    {c:32s} {n}", file=out)
    return 1 if findings else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except AttributeError:
        pass
    sys.exit(main())
