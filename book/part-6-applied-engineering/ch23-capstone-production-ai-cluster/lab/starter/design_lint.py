#!/usr/bin/env python3
"""Capstone design-review linter -- STARTER (learner version).

Implement every function marked TODO. Run ``python ../check.py`` to see progress.

Checks a capstone design bundle (design.md, assumptions.yaml, bom.yaml, topology.yaml,
failure_domains.yaml, slos.yaml, benchmarks.md) for completeness and internal consistency before
a human design review spends time on it. See lab/README.md for the rule catalogue.

Usage:
    python design_lint.py ../data/bundle_kestrel_capA [--out report.md]
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
# Rule implementations -- TODO
# ------------------------------------------------------------------------------------------

def _is_empty(v: Any) -> bool:
    """True for None or a blank string (provided helper)."""
    return v is None or (isinstance(v, str) and not v.strip())


def check_completeness(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """COMP-001 and COMP-002.

    TODO:
      * COMP-001 for every file in BUNDLE_FILES that is None (location: the file name), and for
        every REQUIRED_SECTIONS entry with no ``## <Section>`` heading in design.md
        (location: ``design.md:<Section>``).
      * COMP-002 for every row in assumptions.yaml["assumptions"], failure_domains.yaml["domains"]
        and slos.yaml["slos"] that lacks a REQUIRED_FIELDS field or has it empty
        (location: ``<file>:<row id>.<field>``).
        Exception: a *present but empty* ``mitigation`` in failure_domains.yaml is left to FD-001.
    """
    raise NotImplementedError("TODO: check_completeness")


def check_capacity(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """GPU-001, GPU-002, GPU-003 (count arithmetic).

    TODO:
      * GPU-001 ``bom.yaml:gpu_nodes``: (count - spares) x gpus_per_node != total_gpus.
      * GPU-002 ``assumptions.yaml:workload.parallelism``: tp x pp x dp != workload.total_gpus.
      * GPU-003 ``bom.yaml:racks.gpu_racks``: sum of nodes per rack != gpu_nodes.count.
    """
    raise NotImplementedError("TODO: check_capacity")


def check_fabric(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """PORT-001..004 and CABLE-001 (backend fabric arithmetic).

    TODO (all fields under topology.yaml["backend"]):
      * PORT-001 ``topology.yaml:rail_leaf``: downlinks + uplinks > radix.
      * PORT-002 ``topology.yaml:claimed_oversubscription``: |parse_ratio(claim) - down/up| > 0.01.
      * PORT-003 ``topology.yaml:spine``: rail_leaf.count x uplinks_per_spine > spine.radix.
      * PORT-004 ``topology.yaml:rail_leaf``: downlinks != bom gpu_nodes.count
        (one NIC per node lands on each rail leaf).
      * CABLE-001 ``bom.yaml:cables.backend_400g``: != rail_leaf.count x (downlinks + uplinks).
    """
    raise NotImplementedError("TODO: check_fabric")


def check_power(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """POWER-001 per rack (location ``bom.yaml:racks.<rack>``).

    TODO: nodes_in_rack x node_power_kw.max > racks.budget_kw. Use *max*, not sustained, power:
    a rack budget must survive the worst case, not the average. Compare with a small
    tolerance (e.g. 1e-9 kW) so that a rack exactly at budget passes despite float rounding.
    """
    raise NotImplementedError("TODO: check_power")


def check_evidence(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """EVID-001..004 over the benchmarks.md table (location ``benchmarks.md:<row id>``).

    TODO: use parse_markdown_table. Emit at most ONE finding per row, testing in this order:
      * EVID-001 label empty;
      * EVID-002 label does not match LABEL_RE;
      * EVID-003 label MEASURED and manifest in ("", "-", "n/a");
      * EVID-004 label MEASURED, tier "L1" and unit in PHYSICAL_UNITS.
    """
    raise NotImplementedError("TODO: check_evidence")


def check_unlabeled_numbers(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """NUM-001 (location ``design.md:L<1-based line number>``).

    TODO: flag each non-heading line of design.md that matches NUMBER_WITH_UNIT_RE but matches
    neither INLINE_LABEL_RE nor ID_REF_RE.
    """
    raise NotImplementedError("TODO: check_unlabeled_numbers")


def defined_ids(bundle: dict[str, Any]) -> set[str]:
    """TODO: return every ID defined in assumptions, failure domains, SLOs and benchmark rows."""
    raise NotImplementedError("TODO: defined_ids")


def check_cross_refs(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """XREF-001 (location ``design.md:<ID>``), one finding per distinct undefined ID.

    TODO: find ID_REF_RE references in design.md that are not in defined_ids(bundle).
    """
    raise NotImplementedError("TODO: check_cross_refs")


def check_failure_domains(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """FD-001 and FD-002.

    TODO:
      * FD-001 ``failure_domains.yaml:<id>``: redundancy == "none" (case-insensitive) and empty
        mitigation.
      * FD-002 ``failure_domains.yaml:<class>``: a REQUIRED_FD_CLASSES class with no domain.
    """
    raise NotImplementedError("TODO: check_failure_domains")


def check_slos(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """SLO-001 (location ``slos.yaml:<id>.target``).

    TODO: flag a present, non-empty target that does not match TARGET_RE (e.g. "low").
    """
    raise NotImplementedError("TODO: check_slos")


CHECKS = [check_completeness, check_capacity, check_fabric, check_power, check_evidence,
          check_unlabeled_numbers, check_cross_refs, check_failure_domains, check_slos]


def run_lint(bundle: dict[str, Any]) -> dict[str, Any]:
    """Run every check and summarise.

    TODO: return ``{"findings": [...], "counts": {"blocker": n, "major": n, "minor": n},
    "gate": "PASS" | "FAIL"}``. Sort findings by (SEVERITY_ORDER, rule, location). The gate is
    PASS only when there are zero blocker and zero major findings.
    """
    raise NotImplementedError("TODO: run_lint")


def render_report(result: dict[str, Any], bundle_name: str) -> str:
    """TODO: Markdown report containing the line ``Gate: PASS`` or ``Gate: FAIL`` and one table
    row per finding showing severity, rule, location and message."""
    raise NotImplementedError("TODO: render_report")


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
