#!/usr/bin/env python3
"""Capstone design-review linter -- REFERENCE SOLUTION (instructor only).

Checks a capstone design bundle (design.md, assumptions.yaml, bom.yaml, topology.yaml,
failure_domains.yaml, slos.yaml, benchmarks.md) for completeness and internal consistency before
a human design review spends time on it. See lab/README.md for the rule catalogue.

Usage:
    python design_lint.py ../../lab/data/bundle_kestrel_capA [--out report.md]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

# ------------------------------------------------------------------------------------------
# Provided scaffolding (identical in starter/ and solutions/)
# ------------------------------------------------------------------------------------------

BUNDLE_FILES = ["design.md", "assumptions.yaml", "bom.yaml", "topology.yaml",
                "failure_domains.yaml", "slos.yaml", "benchmarks.md"]

REQUIRED_SECTIONS = ["Problem statement", "Assumptions", "Architecture", "Failure domains",
                     "Benchmark evidence", "Failure exercise", "Next-step backlog"]

REQUIRED_FIELDS = {
    "assumptions.yaml": ["id", "statement", "value", "unit", "label", "owner", "validation"],
    "failure_domains.yaml": ["id", "class", "scope", "redundancy", "mitigation", "detection"],
    "slos.yaml": ["id", "name", "sli", "target", "unit", "window", "source"],
}

REQUIRED_FD_CLASSES = ["gpu", "node", "nic", "rail_leaf", "spine", "rack_power", "storage",
                       "scheduler"]

LABEL_RE = re.compile(r"^(MEASURED|MODELED|SIMULATED|ILLUSTRATIVE|VENDOR-SPEC, \d{4}-\d{2})$")
INLINE_LABEL_RE = re.compile(
    r"\[(MEASURED|MODELED|SIMULATED|ILLUSTRATIVE|VENDOR-SPEC, \d{4}-\d{2})\]")
ID_REF_RE = re.compile(r"\b(?:A|B|FD|SLO)-\d{2}\b")
NUMBER_WITH_UNIT_RE = re.compile(
    r"(?<![\w.])\d+(?:\.\d+)?\s?(?:Gb/s|GB/s|TB/s|TFLOP/s|kW|W|ms|µs|us|GB|TB|%)(?![\w/])")
PHYSICAL_UNITS = {"Gb/s", "GB/s", "TB/s", "TFLOP/s", "µs", "us", "ms", "kW", "W"}
TARGET_RE = re.compile(r"^\s*(?:>=|<=|>|<)?\s*\d+(?:\.\d+)?\s*$")

RULES: dict[str, tuple[str, str]] = {
    "COMP-001": ("blocker", "design.md is missing a required section"),
    "COMP-002": ("major", "required field missing or empty"),
    "GPU-001": ("blocker", "(nodes - spares) x GPUs/node != total GPUs"),
    "GPU-002": ("blocker", "TP x PP x DP != workload GPU count"),
    "GPU-003": ("major", "nodes placed in racks != BOM node count"),
    "PORT-001": ("blocker", "leaf downlinks + uplinks exceed leaf radix"),
    "PORT-002": ("major", "claimed oversubscription != downlinks:uplinks"),
    "PORT-003": ("blocker", "leaf count x uplinks per spine exceeds spine radix"),
    "PORT-004": ("major", "rail-leaf downlinks != GPU node count"),
    "CABLE-001": ("major", "BOM backend cable count != links implied by topology"),
    "POWER-001": ("blocker", "rack nodes x node max power exceeds rack budget"),
    "EVID-001": ("major", "benchmark row has no evidence label"),
    "EVID-002": ("major", "benchmark label not in the evidence vocabulary"),
    "EVID-003": ("major", "MEASURED row without an environment manifest"),
    "EVID-004": ("major", "MEASURED physical-performance claim from an L1 environment"),
    "NUM-001": ("major", "number with a unit in design.md has no label or ID reference"),
    "XREF-001": ("major", "design.md references an ID that is not defined in the bundle"),
    "FD-001": ("major", "failure domain with no redundancy and no mitigation"),
    "FD-002": ("major", "required failure-domain class not analysed"),
    "SLO-001": ("major", "SLO target is not a measurable numeric threshold"),
}

SEVERITY_ORDER = {"blocker": 0, "major": 1, "minor": 2}


def make_finding(rule: str, location: str, message: str) -> dict[str, str]:
    """Build a finding dict. ``location`` follows the conventions in lab/README.md."""
    return {"rule": rule, "severity": RULES[rule][0], "location": location, "message": message}


def parse_markdown_table(text: str) -> list[dict[str, str]]:
    """Parse the first pipe table in ``text`` into a list of row dicts (cells stripped)."""
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if header is not None and rows:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = cells
        elif all(set(c) <= set("-: ") for c in cells):
            continue
        else:
            rows.append(dict(zip(header, cells)))
    return rows


def load_bundle(path: str | Path) -> dict[str, Any]:
    """Load a bundle directory. YAML files become dicts; Markdown files stay strings.

    Missing files are stored as ``None`` so that completeness checks can report them.
    """
    root = Path(path)
    bundle: dict[str, Any] = {}
    for name in BUNDLE_FILES:
        p = root / name
        if not p.exists():
            bundle[name] = None
        elif name.endswith(".yaml"):
            bundle[name] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        else:
            bundle[name] = p.read_text(encoding="utf-8")
    return bundle


def parse_ratio(text: str) -> float:
    """Parse an oversubscription string such as ``"3:1"`` into 3.0."""
    a, b = str(text).split(":")
    return float(a) / float(b)


# ------------------------------------------------------------------------------------------
# Rule implementations
# ------------------------------------------------------------------------------------------

def _is_empty(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def check_completeness(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """COMP-001 (missing design.md section / missing file) and COMP-002 (missing field).

    Locations: ``design.md:<Section>``; ``<file>`` for a missing file;
    ``<file>:<row id>.<field>`` for a missing or empty field.
    """
    out: list[dict[str, str]] = []
    for name in BUNDLE_FILES:
        if bundle.get(name) is None:
            out.append(make_finding("COMP-001", name, f"{name} is missing from the bundle"))
    design = bundle.get("design.md") or ""
    headings = {m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", design, re.M)}
    for sec in REQUIRED_SECTIONS:
        if bundle.get("design.md") is not None and sec not in headings:
            out.append(make_finding("COMP-001", f"design.md:{sec}",
                                    f"section '## {sec}' not found"))
    list_key = {"assumptions.yaml": "assumptions", "failure_domains.yaml": "domains",
                "slos.yaml": "slos"}
    for fname, fields in REQUIRED_FIELDS.items():
        doc = bundle.get(fname) or {}
        for row in doc.get(list_key[fname], []) or []:
            rid = row.get("id", "?")
            for f in fields:
                if f == "id":
                    continue
                # An empty mitigation on a no-redundancy domain is FD-001's job, not COMP-002's.
                if fname == "failure_domains.yaml" and f == "mitigation" and f in row:
                    continue
                if f not in row or _is_empty(row[f]):
                    out.append(make_finding("COMP-002", f"{fname}:{rid}.{f}",
                                            f"{rid} has no '{f}'"))
    return out


def check_capacity(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """GPU-001, GPU-002, GPU-003.

    Locations: ``bom.yaml:gpu_nodes``, ``assumptions.yaml:workload.parallelism``,
    ``bom.yaml:racks.gpu_racks``.
    """
    out: list[dict[str, str]] = []
    bom = bundle.get("bom.yaml") or {}
    gn = bom.get("gpu_nodes", {})
    nodes, gpn, spares = int(gn.get("count", 0)), int(gn.get("gpus_per_node", 0)), int(
        gn.get("spares", 0) or 0)
    total = int(bom.get("total_gpus", 0))
    if (nodes - spares) * gpn != total:
        out.append(make_finding(
            "GPU-001", "bom.yaml:gpu_nodes",
            f"({nodes} - {spares}) x {gpn} = {(nodes - spares) * gpn} but total_gpus = {total}"))
    wl = (bundle.get("assumptions.yaml") or {}).get("workload", {})
    par = wl.get("parallelism", {})
    if par:
        prod = int(par.get("tp", 1)) * int(par.get("pp", 1)) * int(par.get("dp", 1))
        target = int(wl.get("total_gpus", total))
        if prod != target:
            out.append(make_finding(
                "GPU-002", "assumptions.yaml:workload.parallelism",
                f"TP x PP x DP = {prod} but the workload uses {target} GPUs"))
    racks = (bom.get("racks") or {}).get("gpu_racks") or {}
    if racks and sum(int(v) for v in racks.values()) != nodes:
        out.append(make_finding(
            "GPU-003", "bom.yaml:racks.gpu_racks",
            f"racks hold {sum(int(v) for v in racks.values())} nodes but BOM lists {nodes}"))
    return out


def check_fabric(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """PORT-001..004 and CABLE-001.

    Locations: ``topology.yaml:rail_leaf`` (PORT-001, PORT-004),
    ``topology.yaml:claimed_oversubscription`` (PORT-002), ``topology.yaml:spine`` (PORT-003),
    ``bom.yaml:cables.backend_400g`` (CABLE-001).
    Backend links implied by topology = leaf count x (downlinks + uplinks).
    """
    out: list[dict[str, str]] = []
    be = (bundle.get("topology.yaml") or {}).get("backend", {})
    leaf, spine = be.get("rail_leaf", {}), be.get("spine", {})
    down, up, radix = int(leaf.get("downlinks", 0)), int(leaf.get("uplinks", 0)), int(
        leaf.get("radix", 0))
    if down + up > radix:
        out.append(make_finding("PORT-001", "topology.yaml:rail_leaf",
                                f"{down} down + {up} up = {down + up} > radix {radix}"))
    claimed = be.get("claimed_oversubscription")
    if claimed and up:
        computed = down / up
        if abs(parse_ratio(claimed) - computed) > 0.01:
            out.append(make_finding("PORT-002", "topology.yaml:claimed_oversubscription",
                                    f"claimed {claimed} but {down}:{up} = {computed:.4f}:1"))
    n_leaf, ups = int(leaf.get("count", 0)), int(leaf.get("uplinks_per_spine", 0))
    if spine and n_leaf * ups > int(spine.get("radix", 0)):
        out.append(make_finding("PORT-003", "topology.yaml:spine",
                                f"{n_leaf} leaves x {ups} = {n_leaf * ups} > spine radix "
                                f"{spine.get('radix')}"))
    nodes = int(((bundle.get("bom.yaml") or {}).get("gpu_nodes") or {}).get("count", 0))
    if down != nodes:
        out.append(make_finding("PORT-004", "topology.yaml:rail_leaf",
                                f"{down} downlinks per rail leaf but {nodes} GPU nodes"))
    links = n_leaf * (down + up)
    cables = ((bundle.get("bom.yaml") or {}).get("cables") or {}).get("backend_400g")
    if cables is not None and int(cables) != links:
        out.append(make_finding("CABLE-001", "bom.yaml:cables.backend_400g",
                                f"BOM has {cables} backend links; topology implies "
                                f"{n_leaf} x ({down} + {up}) = {links}"))
    return out


def check_power(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """POWER-001 per rack. Location: ``bom.yaml:racks.<rack>``. Uses node *max* power."""
    out: list[dict[str, str]] = []
    bom = bundle.get("bom.yaml") or {}
    pmax = float((bom.get("node_power_kw") or {}).get("max", 0))
    racks = bom.get("racks") or {}
    budget = float(racks.get("budget_kw", 0))
    for rack, n in (racks.get("gpu_racks") or {}).items():
        need = int(n) * pmax
        if need > budget + 1e-9:
            out.append(make_finding("POWER-001", f"bom.yaml:racks.{rack}",
                                    f"{n} x {pmax} kW = {need:.1f} kW > budget {budget} kW"))
    return out


def check_evidence(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """EVID-001..004 over benchmarks.md. Location: ``benchmarks.md:<row id>``.

    One finding per row (the first rule that fires, in order 001, 002, 003, 004).
    """
    out: list[dict[str, str]] = []
    for row in parse_markdown_table(bundle.get("benchmarks.md") or ""):
        rid, label = row.get("id", "?"), row.get("label", "").strip()
        manifest, tier = row.get("manifest", "").strip(), row.get("tier", "").strip()
        loc = f"benchmarks.md:{rid}"
        if not label:
            out.append(make_finding("EVID-001", loc, "no evidence label"))
        elif not LABEL_RE.match(label):
            out.append(make_finding("EVID-002", loc, f"label '{label}' not in vocabulary"))
        elif label == "MEASURED" and manifest in ("", "-", "n/a"):
            out.append(make_finding("EVID-003", loc, "MEASURED with no manifest"))
        elif label == "MEASURED" and tier == "L1" and row.get("unit", "").strip() in PHYSICAL_UNITS:
            out.append(make_finding("EVID-004", loc,
                                    f"physical metric '{row.get('metric')}' MEASURED at L1"))
    return out


def check_unlabeled_numbers(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """NUM-001. Location: ``design.md:L<line number, 1-based>``.

    A line is flagged when it contains a number with a unit from NUMBER_WITH_UNIT_RE, is not a
    heading, and carries neither an inline evidence label nor an ID reference (A-/B-/FD-/SLO-).
    """
    out: list[dict[str, str]] = []
    for i, line in enumerate((bundle.get("design.md") or "").splitlines(), start=1):
        if line.lstrip().startswith("#"):
            continue
        if NUMBER_WITH_UNIT_RE.search(line) and not INLINE_LABEL_RE.search(line) \
                and not ID_REF_RE.search(line):
            out.append(make_finding("NUM-001", f"design.md:L{i}", line.strip()[:80]))
    return out


def defined_ids(bundle: dict[str, Any]) -> set[str]:
    """All IDs defined in the bundle (assumptions, failure domains, SLOs, benchmark rows)."""
    ids: set[str] = set()
    for fname, key in (("assumptions.yaml", "assumptions"), ("failure_domains.yaml", "domains"),
                       ("slos.yaml", "slos")):
        ids |= {str(r.get("id")) for r in ((bundle.get(fname) or {}).get(key) or [])}
    ids |= {r.get("id", "") for r in parse_markdown_table(bundle.get("benchmarks.md") or "")}
    return ids


def check_cross_refs(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """XREF-001. Location: ``design.md:<ID>`` (one finding per distinct undefined ID)."""
    known = defined_ids(bundle)
    seen: list[str] = []
    for ref in ID_REF_RE.findall(bundle.get("design.md") or ""):
        if ref not in known and ref not in seen:
            seen.append(ref)
    return [make_finding("XREF-001", f"design.md:{r}", f"{r} is not defined") for r in seen]


def check_failure_domains(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """FD-001 (``failure_domains.yaml:<id>``) and FD-002 (``failure_domains.yaml:<class>``)."""
    out: list[dict[str, str]] = []
    domains = (bundle.get("failure_domains.yaml") or {}).get("domains") or []
    for d in domains:
        if str(d.get("redundancy", "")).strip().lower() == "none" and _is_empty(
                d.get("mitigation")):
            out.append(make_finding("FD-001", f"failure_domains.yaml:{d.get('id')}",
                                    f"{d.get('class')} has no redundancy and no mitigation"))
    present = {d.get("class") for d in domains}
    for cls in REQUIRED_FD_CLASSES:
        if cls not in present:
            out.append(make_finding("FD-002", f"failure_domains.yaml:{cls}",
                                    f"no failure domain of class '{cls}'"))
    return out


def check_slos(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """SLO-001. Location: ``slos.yaml:<id>.target``. Missing targets are COMP-002's job."""
    out: list[dict[str, str]] = []
    for s in (bundle.get("slos.yaml") or {}).get("slos") or []:
        t = s.get("target")
        if t is not None and not _is_empty(t) and not TARGET_RE.match(str(t)):
            out.append(make_finding("SLO-001", f"slos.yaml:{s.get('id')}.target",
                                    f"target '{t}' is not a numeric threshold"))
    return out


CHECKS = [check_completeness, check_capacity, check_fabric, check_power, check_evidence,
          check_unlabeled_numbers, check_cross_refs, check_failure_domains, check_slos]


def run_lint(bundle: dict[str, Any]) -> dict[str, Any]:
    """Run every check. Returns ``{"findings": [...sorted...], "counts": {...}, "gate": str}``.

    Findings are sorted by (severity order, rule, location). The gate is ``"PASS"`` when there are
    no blocker or major findings, else ``"FAIL"``.
    """
    findings: list[dict[str, str]] = []
    for chk in CHECKS:
        findings.extend(chk(bundle))
    findings.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["rule"], f["location"]))
    counts = {sev: sum(f["severity"] == sev for f in findings) for sev in SEVERITY_ORDER}
    gate = "PASS" if counts["blocker"] == 0 and counts["major"] == 0 else "FAIL"
    return {"findings": findings, "counts": counts, "gate": gate}


def render_report(result: dict[str, Any], bundle_name: str) -> str:
    """Render a Markdown report: title, gate line ``Gate: PASS|FAIL``, counts, findings table."""
    c = result["counts"]
    lines = [f"# Design-review lint report -- {bundle_name}", "",
             f"Gate: {result['gate']}  (blocker={c['blocker']}, major={c['major']}, "
             f"minor={c['minor']})", "",
             "| # | Severity | Rule | Location | Finding |", "|---|---|---|---|---|"]
    for i, f in enumerate(result["findings"], 1):
        lines.append(f"| {i} | {f['severity']} | {f['rule']} | `{f['location']}` | "
                     f"{f['message'].replace('|', '/')} |")
    if not result["findings"]:
        lines.append("| - | - | - | - | no findings |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    result = run_lint(load_bundle(args.bundle))
    report = render_report(result, args.bundle.name)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
