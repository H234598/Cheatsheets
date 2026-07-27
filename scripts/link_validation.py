#!/usr/bin/env python3
"""Alle Linkauflösungsprobleme strukturiert berichten."""

from __future__ import annotations

from pathlib import Path

from content_index import build_content_index
from content_model import ContentIndex
from link_resolution import resolve_occurrence
from link_types import LinkError, LinkIssue, LinkOccurrence, LinkTarget, Resolution, scan_wikilinks

LINK_VALIDATED_ROLES = {
    "reference",
    "category-index",
    "root-landing",
    "root-index",
    "root-readme",
    "maintenance",
}

STATUS_CODES = {
    "missing-document": "LK001",
    "ambiguous": "LK002",
    "missing-heading": "LK003",
    "case-mismatch": "LK004",
    "malformed": "LK005",
    "ambiguous-heading": "LK006",
    "unsupported-embed": "EM001",
}


def issue_for(
    index: ContentIndex,
    occurrence: LinkOccurrence,
    resolution: Resolution,
) -> LinkIssue | None:
    if resolution.ok:
        return None
    try:
        path = occurrence.source.resolve().relative_to(index.root).as_posix()
    except ValueError:
        path = occurrence.source.as_posix()
    return LinkIssue(
        code=STATUS_CODES.get(resolution.status, "LK999"),
        severity="error",
        message=resolution.message or resolution.status,
        path=path,
        line=occurrence.line,
        column=occurrence.column,
        raw=occurrence.raw,
        requested_target=occurrence.target,
        candidates=resolution.candidates,
    )


def analyze_all(
    root: Path,
    index: ContentIndex | None = None,
) -> tuple[ContentIndex, list[LinkIssue]]:
    index = index or build_content_index(root)
    issues: list[LinkIssue] = []
    pages = sorted(index.pages.values(), key=lambda item: item.relative_path.as_posix())
    for page in pages:
        if page.page_type not in LINK_VALIDATED_ROLES:
            continue
        for occurrence in scan_wikilinks(page.raw_text, page.source_path):
            issue = issue_for(index, occurrence, resolve_occurrence(index, occurrence))
            if issue is not None:
                issues.append(issue)
    return index, sorted(
        issues,
        key=lambda item: (item.path, item.line, item.column, item.code),
    )


def validate_all(root: Path) -> list[str]:
    index, link_issues = analyze_all(root)
    errors = [issue.format() for issue in index.issues if issue.severity == "error"]
    errors.extend(issue.format() for issue in link_issues if issue.severity == "error")
    return errors


def resolve_target(
    root: Path,
    source: Path,
    target: str,
    heading: str | None = None,
    *,
    index: ContentIndex | None = None,
) -> LinkTarget:
    index = index or build_content_index(root)
    occurrence = LinkOccurrence(
        source=source,
        raw=f"[[{target}{'#' + heading if heading else ''}]]",
        target=target,
        heading=heading,
        label=heading or Path(target).stem or target,
        embed=False,
        line=1,
        column=1,
        start=0,
        end=0,
    )
    resolution = resolve_occurrence(index, occurrence)
    if not resolution.ok or resolution.path is None:
        raise LinkError(resolution.message or f"Ungültiges Linkziel: {occurrence.raw}")
    return LinkTarget(resolution.path, resolution.anchor)
