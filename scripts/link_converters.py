#!/usr/bin/env python3
"""Aufgelöste Wikilinks für MkDocs und Gesamt-Markdown konvertieren.

Angepasst aus ``scripts/link_converters.py`` des Repositories
``H234598/ADHS-Lernpfad`` am Commit
``93c8c02d263ec123c1c271caf0d2deaa76760ccb``.
"""

from __future__ import annotations

from collections.abc import Iterable
import html
import os
from pathlib import Path, PurePosixPath
import re
from urllib.parse import quote

from content_index import build_content_index
from content_model import ContentIndex, FenceState, PageRecord, advance_fence_state, slugify
from link_resolution import resolve_occurrence
from link_types import IMAGE_SUFFIXES, LinkError, LinkOccurrence, Resolution, scan_wikilinks


def _relative_posix(source: PurePosixPath, target: PurePosixPath) -> str:
    return Path(os.path.relpath(target.as_posix(), start=source.parent.as_posix())).as_posix()


def _encoded_link(value: str) -> str:
    if "#" in value:
        path, anchor = value.split("#", 1)
        return quote(path, safe="/._~-@") + "#" + quote(anchor, safe="-._~")
    return quote(value, safe="/._~-@")


def _replace_occurrences(
    text: str,
    replacements: Iterable[tuple[LinkOccurrence, str]],
) -> str:
    output = text
    for occurrence, replacement in sorted(
        replacements,
        key=lambda item: item[0].start,
        reverse=True,
    ):
        output = output[: occurrence.start] + replacement + output[occurrence.end :]
    return output


def _target_generated_path(index: ContentIndex, resolution: Resolution) -> PurePosixPath:
    if resolution.page is not None:
        return resolution.page.generated_path
    if resolution.path is None:
        raise LinkError("Aufgelöstes Linkziel besitzt keinen Pfad")
    return PurePosixPath(resolution.path.relative_to(index.root).as_posix())


def _web_replacement(
    index: ContentIndex,
    source_page: PageRecord,
    occurrence: LinkOccurrence,
    resolution: Resolution,
    tolerate: bool,
) -> str:
    if resolution.ok and resolution.path is not None:
        target = _target_generated_path(index, resolution)
        relative = _relative_posix(source_page.generated_path, target)
        if resolution.anchor:
            relative += "#" + resolution.anchor
        relative = _encoded_link(relative)
        if occurrence.embed and resolution.path.suffix.lower() in IMAGE_SUFFIXES:
            return f"![{occurrence.label}]({relative})"
        return f"[{occurrence.label}]({relative})"
    if not tolerate:
        raise LinkError(resolution.message or f"Ungültiges Linkziel: {occurrence.raw}")
    status = re.sub(r"[^a-z0-9_-]", "-", resolution.status.casefold())
    label = html.escape(occurrence.label)
    message = html.escape(resolution.message or resolution.status, quote=True)
    return (
        f'<span class="internal-link internal-link--{status}" '
        f'data-link-status="{status}" title="{message}">'
        f"{label} <small>[{status}]</small></span>"
    )


def convert_for_web(
    text: str,
    source: Path,
    root: Path,
    *,
    index: ContentIndex | None = None,
    tolerate_issues: bool = False,
) -> str:
    index = index or build_content_index(root)
    source_page = index.page_for_path(source)
    if source_page is None:
        raise LinkError(f"Quelldokument ist nicht indexiert: {source}")
    replacements: list[tuple[LinkOccurrence, str]] = []
    for occurrence in scan_wikilinks(text, source):
        resolution = resolve_occurrence(index, occurrence)
        replacements.append(
            (
                occurrence,
                _web_replacement(
                    index,
                    source_page,
                    occurrence,
                    resolution,
                    tolerate_issues,
                ),
            )
        )
    return _replace_occurrences(text, replacements)


def convert_for_combined(
    text: str,
    source: Path,
    root: Path,
    included_paths: set[Path],
    *,
    index: ContentIndex | None = None,
    tolerate_issues: bool = False,
) -> str:
    index = index or build_content_index(root)
    source_page = index.page_for_path(source)
    if source_page is None:
        raise LinkError(f"Quelldokument ist nicht indexiert: {source}")
    included = {path.resolve() for path in included_paths}
    replacements: list[tuple[LinkOccurrence, str]] = []
    for occurrence in scan_wikilinks(text, source):
        resolution = resolve_occurrence(index, occurrence)
        if resolution.ok and resolution.path is not None:
            if occurrence.embed and resolution.path.suffix.lower() in IMAGE_SUFFIXES:
                replacement = (
                    f"![{occurrence.label}]"
                    f"({_encoded_link(resolution.path.relative_to(root).as_posix())})"
                )
            elif resolution.path.resolve() not in included:
                replacement = occurrence.label
            else:
                target_page = resolution.page
                anchor = target_page.page_id if target_page else "asset"
                if resolution.anchor:
                    anchor += "--" + resolution.anchor
                replacement = f"[{occurrence.label}](#{anchor})"
        elif tolerate_issues:
            replacement = f"{occurrence.label} [{resolution.status}]"
        else:
            raise LinkError(resolution.message or f"Ungültiges Linkziel: {occurrence.raw}")
        replacements.append((occurrence, replacement))

    converted = _replace_occurrences(text, replacements)
    anchor_prefix = source_page.page_id
    output = [f"[]{{#{anchor_prefix}}}\n"]
    fence: FenceState | None = None
    for line in converted.splitlines(keepends=True):
        fence, is_fenced = advance_fence_state(line, fence)
        if is_fenced:
            output.append(line)
            continue
        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.rstrip("\r\n"))
        if heading_match:
            level, heading_text = heading_match.groups()
            clean = re.sub(r"\s*\{#[-\w:.]+\}\s*$", "", heading_text)
            heading_id = f"{anchor_prefix}--{slugify(clean)}"
            newline = "\n" if line.endswith("\n") else ""
            output.append(f"{level} {clean} {{#{heading_id}}}{newline}")
        else:
            output.append(line)
    return "".join(output)
