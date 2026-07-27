#!/usr/bin/env python3
"""CLI für die vollständige, schreibgeschützte Inhaltsinventur."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from content_index import build_content_index
from content_model import BuildIssue
from io_utils import atomic_write_text, stable_json_dumps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validiert Frontmatter, Kategorien, Rollen und MANIFEST.csv."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--expected-reference-pages", type=int, default=86)
    parser.add_argument("--expected-categories", type=int, default=12)
    return parser


def _strictify(issues: list[BuildIssue], strict: bool) -> list[BuildIssue]:
    if not strict:
        return issues
    return [
        BuildIssue(
            "error" if issue.severity == "warning" else issue.severity,
            issue.code,
            issue.message,
            issue.source_path,
            issue.line,
            issue.column,
            issue.hint,
        )
        for issue in issues
    ]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    index = build_content_index(args.root)
    issues = list(index.issues)

    references = len(index.reference_pages)
    categories = len(index.categories)
    if references != args.expected_reference_pages:
        issues.append(
            BuildIssue(
                "error",
                "BL001",
                f"Erwartet {args.expected_reference_pages} Fachseiten, gefunden {references}",
            )
        )
    if categories != args.expected_categories:
        issues.append(
            BuildIssue(
                "error",
                "BL002",
                f"Erwartet {args.expected_categories} Kategorien, gefunden {categories}",
            )
        )

    issues = sorted(_strictify(issues, args.strict), key=BuildIssue.sort_key)
    errors = sum(issue.severity == "error" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)

    for issue in issues:
        print(issue.format(), file=sys.stderr if issue.severity == "error" else sys.stdout)

    payload = {
        "schema_version": 1,
        "reference_pages": references,
        "categories": categories,
        "markdown_pages": len(index.pages),
        "manifest_entries": len(index.manifest),
        "issues": [issue.as_dict() for issue in issues],
        "summary": {"errors": errors, "warnings": warnings},
    }
    if args.report:
        atomic_write_text(args.report, stable_json_dumps(payload))

    print(
        f"Inhaltsinventur: {references} Fachseiten, {categories} Kategorien, "
        f"{errors} Fehler, {warnings} Warnungen."
    )
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
