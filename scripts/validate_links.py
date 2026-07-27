#!/usr/bin/env python3
"""CLI für interne Wikilinks, Embeds, Anker und Callouts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from callouts import convert_obsidian_callouts_for_web
from link_validation import analyze_all
from io_utils import atomic_write_text, stable_json_dumps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validiert interne Wikilinks und die Callout-Konvertierung."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    index, link_issues = analyze_all(args.root)
    model_issues = list(index.issues)
    errors = sum(issue.severity == "error" for issue in model_issues) + sum(
        issue.severity == "error" for issue in link_issues
    )
    warnings = sum(issue.severity == "warning" for issue in model_issues) + sum(
        issue.severity == "warning" for issue in link_issues
    )
    if args.strict:
        errors += warnings
        warnings = 0

    for issue in model_issues:
        print(issue.format(), file=sys.stderr if issue.severity == "error" else sys.stdout)
    for issue in link_issues:
        print(issue.format(), file=sys.stderr if issue.severity == "error" else sys.stdout)

    sample = "> [!danger]- Löschen\n> Nur nach Backup.\n"
    expected = '??? danger "Löschen"\n    Nur nach Backup.\n'
    if convert_obsidian_callouts_for_web(sample) != expected:
        errors += 1
        print("Interner Callout-Konvertierungstest ist fehlgeschlagen", file=sys.stderr)

    payload = {
        "schema_version": 1,
        "model_issues": [issue.as_dict() for issue in model_issues],
        "link_issues": [issue.as_dict() for issue in link_issues],
        "summary": {"errors": errors, "warnings": warnings},
    }
    if args.report:
        atomic_write_text(args.report, stable_json_dumps(payload))

    print(f"Linkvalidierung: {errors} Fehler, {warnings} Warnungen.")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
