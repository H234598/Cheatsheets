#!/usr/bin/env python3
"""Interne Linkziele deterministisch und ohne Raten auflösen.

Angepasst aus ``scripts/link_resolution.py`` des Repositories
``H234598/ADHS-Lernpfad`` am Commit
``93c8c02d263ec123c1c271caf0d2deaa76760ccb``.
"""

from __future__ import annotations

from pathlib import Path
import re

from content_model import ContentIndex, PageRecord, normalize_key, normalize_posix_path, slugify
from link_types import IMAGE_SUFFIXES, LinkOccurrence, Resolution

EXTERNAL_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _candidate_relatives(index: ContentIndex, source: Path, target: str) -> list[str]:
    normalized = target.replace("\\", "/").strip()
    if not normalized:
        return []
    target_path = Path(normalized.lstrip("/"))
    try:
        source_relative = source.resolve().relative_to(index.root.resolve())
    except ValueError:
        source_relative = source

    bases = [Path()]
    if not normalized.startswith("/"):
        bases.insert(0, source_relative.parent)

    candidates: list[str] = []
    for base in bases:
        raw = base / target_path
        possible: list[Path]
        if raw.suffix and raw.suffix.lower() != ".md":
            possible = [raw]
        else:
            stem = raw.with_suffix("") if raw.suffix.lower() == ".md" else raw
            possible = [stem, stem.with_suffix(".md"), stem / "INDEX.md", stem / "README.md"]
        for item in possible:
            value = normalize_posix_path(item)
            if value not in candidates:
                candidates.append(value)
    return candidates


def _direct_pages(
    index: ContentIndex,
    occurrence: LinkOccurrence,
) -> tuple[list[PageRecord], list[Path], bool, bool]:
    pages: dict[str, PageRecord] = {}
    assets: dict[str, Path] = {}
    escaped = False
    case_mismatch = False

    for relative in _candidate_relatives(index, occurrence.source, occurrence.target):
        candidate = index.root / relative
        if not _inside_root(candidate, index.root):
            escaped = True
            continue
        exact_page = next(
            (
                page
                for page in index.pages.values()
                if relative in {page.relative_path.as_posix(), page.path_without_suffix}
            ),
            None,
        )
        if exact_page is not None:
            pages[exact_page.page_id] = exact_page
            continue
        folded_page = index.page_for_path(relative)
        if folded_page is not None:
            pages[folded_page.page_id] = folded_page
            case_mismatch = True
            continue
        if candidate.is_file():
            resolved = candidate.resolve()
            if not _inside_root(resolved, index.root) or candidate.is_symlink():
                escaped = True
                continue
            assets[resolved.as_posix()] = resolved
    return list(pages.values()), list(assets.values()), escaped, case_mismatch


def _resolve_heading(page: PageRecord, requested: str) -> tuple[str, str] | Resolution:
    wanted_key = normalize_key(requested)
    wanted_slug = slugify(requested)
    matches = [
        heading
        for heading in page.headings
        if normalize_key(heading.text) == wanted_key
        or heading.anchor == requested
        or heading.anchor == wanted_slug
    ]
    unique = {(item.anchor, item.text): item for item in matches}
    if len(unique) == 1:
        heading = next(iter(unique.values()))
        return heading.text, heading.anchor
    if len(unique) > 1:
        return Resolution(
            "ambiguous-heading",
            page.page_id,
            path=page.source_path,
            page=page,
            candidates=tuple(sorted(f"#{item.anchor}" for item in unique.values())),
            message=(
                f"Überschrift ist in {page.relative_path.as_posix()} mehrdeutig: "
                f"{requested}"
            ),
        )
    return Resolution(
        "missing-heading",
        page.page_id,
        path=page.source_path,
        page=page,
        heading=requested,
        message=(
            f"Überschrift nicht gefunden: {requested} in "
            f"{page.relative_path.as_posix()}"
        ),
    )


def resolve_occurrence(index: ContentIndex, occurrence: LinkOccurrence) -> Resolution:
    target = occurrence.target.strip()
    if target and EXTERNAL_SCHEME_RE.match(target):
        return Resolution(
            "malformed",
            None,
            message=f"Wikilink darf kein externes URL-Ziel enthalten: {occurrence.raw}",
        )

    if not target:
        page = index.page_for_path(occurrence.source)
        if page is None:
            return Resolution(
                "missing-document", None, message="Quelldokument ist nicht indexiert"
            )
        pages, assets, escaped, case_mismatch = [page], [], False, False
    else:
        pages, assets, escaped, case_mismatch = _direct_pages(index, occurrence)
        if not pages and not assets:
            pages = index.lookup_pages(target)

    page_map = {page.page_id: page for page in pages}
    asset_map = {path.resolve().as_posix(): path for path in assets}
    candidates = tuple(
        sorted(
            [page.relative_path.as_posix() for page in page_map.values()]
            + [path.relative_to(index.root).as_posix() for path in asset_map.values()]
        )
    )
    if len(page_map) + len(asset_map) > 1:
        return Resolution(
            "ambiguous",
            None,
            candidates=candidates,
            message=f"Mehrdeutiges Ziel: {occurrence.raw}",
        )

    if asset_map:
        path = next(iter(asset_map.values()))
        if occurrence.heading:
            return Resolution(
                "missing-heading",
                "asset:" + path.relative_to(index.root).as_posix(),
                path=path,
                message=f"Nicht-Markdown-Ziel besitzt keine Überschrift: {occurrence.raw}",
            )
        if occurrence.embed and path.suffix.lower() not in IMAGE_SUFFIXES:
            return Resolution(
                "unsupported-embed",
                "asset:" + path.relative_to(index.root).as_posix(),
                path=path,
                message=f"Nicht unterstützte Einbettung: {occurrence.raw}",
            )
        return Resolution(
            "ok", "asset:" + path.relative_to(index.root).as_posix(), path=path
        )

    if page_map:
        page = next(iter(page_map.values()))
        if case_mismatch:
            return Resolution(
                "case-mismatch",
                page.page_id,
                path=page.source_path,
                page=page,
                candidates=(page.relative_path.as_posix(),),
                message=(
                    f"Groß-/Kleinschreibung des Linkziels stimmt nicht: "
                    f"{occurrence.raw}"
                ),
            )
        if occurrence.embed:
            return Resolution(
                "unsupported-embed",
                page.page_id,
                path=page.source_path,
                page=page,
                message=(
                    "Markdown-Transklusionen werden im Web-MVP nicht automatisch "
                    f"aufgelöst: {occurrence.raw}"
                ),
            )
        if occurrence.heading:
            heading = _resolve_heading(page, occurrence.heading)
            if isinstance(heading, Resolution):
                return heading
            title, anchor = heading
            return Resolution(
                "ok",
                f"section:{page.page_id}#{anchor}",
                path=page.source_path,
                page=page,
                heading=title,
                anchor=anchor,
            )
        return Resolution("ok", page.page_id, path=page.source_path, page=page)

    if escaped:
        return Resolution(
            "malformed",
            None,
            message=f"Linkziel verlässt die Repositorywurzel: {occurrence.raw}",
        )
    return Resolution(
        "missing-document", None, message=f"Ziel nicht gefunden: {occurrence.raw}"
    )
