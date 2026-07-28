#!/usr/bin/env python3
"""Markdown, Frontmatter, Kategorien und Manifest strukturiert inventarisieren.

Angepasst aus ``scripts/content_index.py`` des Repositories
``H234598/ADHS-Lernpfad`` am Commit
``93c8c02d263ec123c1c271caf0d2deaa76760ccb``. Die datensatzorientierte
Fehleraggregation folgt zusätzlich Mustern aus ``H234598/desinfect`` am Commit
``fbcc6e850fec1f4592ca519fa3e5141b11a95e60``.
"""

from __future__ import annotations

from collections.abc import Iterable
import csv
from dataclasses import replace
import hashlib
from pathlib import Path, PurePosixPath
import re
from typing import Any

import yaml

from content_model import (
    CATEGORY_RE,
    EXCLUDED_DIRS,
    EXPLICIT_ID_RE,
    FRONTMATTER_RE,
    HEADING_RE,
    BuildIssue,
    CategoryRecord,
    ContentIndex,
    FenceState,
    HeadingRecord,
    ManifestEntry,
    PageRecord,
    advance_fence_state,
    document_url,
    json_compatible,
    normalize_key,
    normalize_posix_path,
    page_id_from_path,
    slugify,
)

WIKILINK_RE = re.compile(r"(?P<embed>!)?\[\[(?P<body>[^\]\n]+)\]\]")
ROOT_ROLES = {
    "00-START-HIER.md": "root-landing",
    "INDEX.md": "root-index",
    "README.md": "root-readme",
    "00-Anforderungsabdeckung.md": "maintenance",
    "MANIFEST.md": "maintenance",
    "QUALITAETSPRUEFUNG.md": "maintenance",
    "CHANGELOG.md": "maintenance",
    "Cheatsheet-Gesamtband.md": "download-only",
}
KNOWN_STATUS = {"fertig", "entwurf", "review", "archiviert"}


def _as_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if isinstance(value, Iterable) and not isinstance(value, (dict, bytes)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),)


def split_frontmatter(
    text: str,
) -> tuple[dict[str, Any], str, int, list[BuildIssue]]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text, 1, []
    issues: list[BuildIssue] = []
    try:
        loaded = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        issues.append(
            BuildIssue(
                "error",
                "FM002",
                f"Ungültiges YAML-Frontmatter: {str(exc).splitlines()[0]}",
                line=1,
            )
        )
        loaded = {}
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        issues.append(
            BuildIssue(
                "error",
                "FM003",
                "YAML-Frontmatter muss ein Mapping sein",
                line=1,
            )
        )
        loaded = {}
    body_start = text[: match.end()].count("\n") + 1
    return json_compatible(loaded), text[match.end() :], body_start, issues


def _strip_heading_markup(value: str) -> tuple[str, str | None]:
    explicit = EXPLICIT_ID_RE.search(value)
    explicit_id = explicit.group(1) if explicit else None
    if explicit:
        value = value[: explicit.start()]
    value = re.sub(r"\s+#+\s*$", "", value).strip()
    return re.sub(r"[`*~]", "", value).strip(), explicit_id


def parse_headings(
    body: str,
    body_start_line: int,
) -> tuple[list[HeadingRecord], list[BuildIssue]]:
    headings: list[HeadingRecord] = []
    issues: list[BuildIssue] = []
    fence: FenceState | None = None
    seen: dict[str, int] = {}
    explicit_seen: dict[str, HeadingRecord] = {}

    for offset, line in enumerate(body.splitlines()):
        fence, is_fenced = advance_fence_state(line, fence)
        if is_fenced:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        level, raw_title = match.groups()
        title, explicit_id = _strip_heading_markup(raw_title)
        base = explicit_id or slugify(title)
        count = seen.get(base, 0)
        anchor = base if count == 0 else f"{base}_{count}"
        seen[base] = count + 1
        heading = HeadingRecord(
            level=len(level),
            text=title,
            anchor=anchor,
            line=body_start_line + offset,
            explicit=explicit_id is not None,
        )
        if explicit_id:
            if explicit_id in explicit_seen:
                issues.append(
                    BuildIssue(
                        "error",
                        "FM004",
                        f"Doppelter expliziter Überschriftenanker #{explicit_id}",
                        line=heading.line,
                        hint=f"Erster Treffer in Zeile {explicit_seen[explicit_id].line}",
                    )
                )
            else:
                explicit_seen[explicit_id] = heading
        headings.append(heading)
    return headings, issues


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*.md")
            if not any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts)
        ),
        key=lambda path: normalize_posix_path(path.relative_to(root)).casefold(),
    )


def classify_document(relative: Path, metadata: dict[str, Any]) -> str:
    parts = relative.parts
    if len(parts) >= 2 and CATEGORY_RE.match(parts[0]):
        if relative.name == "INDEX.md" or metadata.get("type") == "index":
            return "category-index"
        if metadata.get("type") == "reference":
            return "reference"
        return "unknown"
    if len(parts) == 1 and relative.name in ROOT_ROLES:
        return ROOT_ROLES[relative.name]
    if parts and parts[0] in {".github", "config", "docs", "scripts", "tests", "web"}:
        return "technical"
    return "unknown"


def estimate_reading_minutes(body: str) -> int:
    """Deterministische, code- und tabellengewichtete Lesezeitschätzung."""

    fence: FenceState | None = None
    prose_words = 0
    code_lines = 0
    table_rows = 0
    for line in body.splitlines():
        fence, is_fenced = advance_fence_state(line, fence)
        if is_fenced:
            if fence is not None and line.strip() and not FENCE_LINE_RE.match(line):
                code_lines += 1
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|") and stripped.endswith("|") and "|" in stripped[1:-1]:
            if not re.fullmatch(r"\|?[ :\-|]+\|?", stripped):
                table_rows += 1
            continue
        cleaned = re.sub(r"`[^`]*`", " ", line)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", cleaned)
        prose_words += len(re.findall(r"\b[\wÄÖÜäöüß-]+\b", cleaned, flags=re.UNICODE))
    seconds = prose_words / 180 * 60 + code_lines * 12 + table_rows * 6
    return max(1, int((seconds + 59) // 60))


FENCE_LINE_RE = re.compile(r"^ {0,3}(?:`{3,}|~{3,})")


def read_manifest(path: Path) -> tuple[dict[str, ManifestEntry], list[BuildIssue]]:
    issues: list[BuildIssue] = []
    entries: dict[str, ManifestEntry] = {}
    numbers: set[int] = set()
    if not path.is_file():
        return {}, [BuildIssue("error", "MF000", "MANIFEST.csv fehlt", path.name)]
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            expected = {
                "nr",
                "bereich",
                "title",
                "path",
                "lines",
                "bytes",
                "sha256",
                "origin",
                "status",
            }
            if set(reader.fieldnames or ()) != expected:
                issues.append(
                    BuildIssue(
                        "error",
                        "MF003",
                        "MANIFEST.csv besitzt nicht das erwartete Spaltenschema",
                        path.name,
                    )
                )
            for row_number, row in enumerate(reader, start=2):
                try:
                    number = int(row["nr"])
                    relative = normalize_posix_path(row["path"])
                    entry = ManifestEntry(
                        number=number,
                        area=row["bereich"].strip(),
                        title=row["title"].strip(),
                        path=PurePosixPath(relative),
                        lines=int(row["lines"]),
                        bytes=int(row["bytes"]),
                        sha256=row["sha256"].strip().lower(),
                        origin=row["origin"].strip(),
                        status=row["status"].strip(),
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    issues.append(
                        BuildIssue(
                            "error",
                            "MF004",
                            f"Ungültige Manifestzeile: {exc}",
                            path.name,
                            row_number,
                        )
                    )
                    continue
                if relative in entries:
                    issues.append(
                        BuildIssue(
                            "error",
                            "MF005",
                            f"Doppelter Manifestpfad: {relative}",
                            path.name,
                            row_number,
                        )
                    )
                if number in numbers:
                    issues.append(
                        BuildIssue(
                            "error",
                            "MF006",
                            f"Doppelte Manifestnummer: {number}",
                            path.name,
                            row_number,
                        )
                    )
                entries[relative] = entry
                numbers.add(number)
    except OSError as exc:
        issues.append(
            BuildIssue("error", "MF007", f"Manifest kann nicht gelesen werden: {exc}", path.name)
        )
    return entries, issues


def _category_parts(relative: Path) -> tuple[str | None, int | None]:
    if not relative.parts:
        return None, None
    match = CATEGORY_RE.match(relative.parts[0])
    if not match:
        return None, None
    return relative.parts[0], int(match.group("number"))


def _extract_category_index_targets(page: PageRecord) -> list[str]:
    """Lese Wikilinks ausschließlich aus dem Abschnitt ``## Seiten``."""

    _metadata, body, _start, _issues = split_frontmatter(page.raw_text)
    in_pages = False
    fence: FenceState | None = None
    targets: list[str] = []
    for line in body.splitlines(keepends=True):
        fence, is_fenced = advance_fence_state(line, fence)
        if is_fenced:
            continue
        heading = HEADING_RE.match(line.rstrip("\r\n"))
        if heading and len(heading.group(1)) == 2:
            title, _explicit = _strip_heading_markup(heading.group(2))
            if normalize_key(title) == "seiten":
                in_pages = True
                continue
            if in_pages:
                break
        if not in_pages:
            continue
        for match in WIKILINK_RE.finditer(line):
            if match.group("embed"):
                continue
            body_value = match.group("body").split("|", 1)[0].split("#", 1)[0].strip()
            if not body_value:
                continue
            if not body_value.lower().endswith(".md"):
                body_value += ".md"
            targets.append(normalize_posix_path(body_value))
    return targets


def _validate_required_frontmatter(page: PageRecord, issues: list[BuildIssue]) -> None:
    if page.page_type not in {"reference", "category-index"}:
        return
    required = {"title", "type", "status", "tags"}
    if page.page_type == "category-index":
        required.add("pages")
    for key in sorted(required):
        if key not in page.metadata:
            issues.append(
                BuildIssue(
                    "error",
                    "FM001",
                    f"Pflichtfeld im Frontmatter fehlt: {key}",
                    page.relative_path.as_posix(),
                    1,
                )
            )
    if page.status and page.status not in KNOWN_STATUS:
        issues.append(
            BuildIssue(
                "error",
                "FM005",
                f"Unbekannter Status: {page.status}",
                page.relative_path.as_posix(),
                1,
            )
        )


def _collision_issues(pages: dict[str, PageRecord]) -> list[BuildIssue]:
    issues: list[BuildIssue] = []
    paths: dict[str, str] = {}
    urls: dict[str, str] = {}
    keys: dict[str, set[str]] = {}

    for page_id, page in pages.items():
        folded_path = normalize_posix_path(page.relative_path).casefold()
        previous = paths.get(folded_path)
        if previous and previous != page_id:
            issues.append(
                BuildIssue(
                    "error",
                    "FS004",
                    f"Pfadkollision nach Case-Folding mit {pages[previous].relative_path}",
                    page.relative_path.as_posix(),
                )
            )
        paths[folded_path] = page_id

        previous_url = urls.get(page.canonical_url.casefold())
        if previous_url and previous_url != page_id:
            issues.append(
                BuildIssue(
                    "error",
                    "NV001",
                    f"Doppelte kanonische URL mit {pages[previous_url].relative_path}",
                    page.relative_path.as_posix(),
                )
            )
        urls[page.canonical_url.casefold()] = page_id

        if page.page_type not in {"reference", "category-index"}:
            continue
        for value in (page.title, *page.aliases):
            keys.setdefault(normalize_key(value), set()).add(page_id)

    for value, page_ids in sorted(keys.items()):
        if len(page_ids) <= 1:
            continue
        labels = ", ".join(sorted(pages[item].relative_path.as_posix() for item in page_ids))
        issues.append(
            BuildIssue(
                "error",
                "NV002",
                f"Mehrdeutiger Titel oder Alias »{value}«: {labels}",
            )
        )
    return issues


def build_content_index(root: Path) -> ContentIndex:
    root = root.resolve()
    issues: list[BuildIssue] = []
    pages: dict[str, PageRecord] = {}
    manifest, manifest_issues = read_manifest(root / "MANIFEST.csv")
    issues.extend(manifest_issues)

    for path in markdown_files(root):
        relative = path.relative_to(root)
        relative_posix = normalize_posix_path(relative)
        if path.is_symlink():
            issues.append(
                BuildIssue("error", "FS002", "Symbolischer Link im Quellbaum", relative_posix)
            )
            continue
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            issues.append(
                BuildIssue("error", "FS001", "Quelldatei verlässt den Repositoryroot", relative_posix)
            )
            continue
        raw_bytes = path.read_bytes()
        try:
            raw = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            issues.append(
                BuildIssue(
                    "error",
                    "FM006",
                    f"Datei ist nicht gültiges UTF-8: {exc}",
                    relative_posix,
                )
            )
            continue
        metadata, body, body_start, frontmatter_issues = split_frontmatter(raw)
        headings, heading_issues = parse_headings(body, body_start)
        for issue in (*frontmatter_issues, *heading_issues):
            issues.append(replace(issue, source_path=relative_posix))
        role = classify_document(relative, metadata)
        title = str(
            metadata.get("title")
            or next((heading.text for heading in headings if heading.level == 1), None)
            or relative.stem
        ).strip()
        category_id, _category_number = _category_parts(relative)
        manifest_entry = manifest.get(relative_posix)
        category_title = manifest_entry.area if manifest_entry else None
        status = str(metadata.get("status") or "").strip()
        origin = metadata.get("origin")
        reviewed = metadata.get("reviewed")
        page_id = page_id_from_path(relative)
        page = PageRecord(
            source_path=path,
            relative_path=PurePosixPath(relative_posix),
            page_type=role,
            category_id=category_id,
            category_title=category_title,
            title=title,
            aliases=_as_string_tuple(metadata.get("aliases")),
            tags=_as_string_tuple(metadata.get("tags")),
            status=status,
            origin=str(origin).strip() if origin is not None else None,
            reviewed=str(reviewed).strip() if reviewed is not None else None,
            metadata=metadata,
            source_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            line_count=len(raw.splitlines()),
            byte_size=len(raw_bytes),
            headings=tuple(headings),
            canonical_url=document_url(relative, role),
            page_id=page_id,
            estimated_minutes=estimate_reading_minutes(body),
            derived_fields=("estimated_minutes",),
            navigation_position=manifest_entry.number if manifest_entry else None,
            body_start_line=body_start,
            raw_text=raw,
        )
        if page_id in pages:
            issues.append(
                BuildIssue(
                    "error",
                    "NV003",
                    f"Doppelte Page-ID: {page_id}",
                    relative_posix,
                )
            )
        pages[page_id] = page
        if role == "unknown":
            issues.append(
                BuildIssue(
                    "error",
                    "NV004",
                    "Markdown-Datei besitzt keine bekannte Seitenrolle",
                    relative_posix,
                )
            )
        _validate_required_frontmatter(page, issues)

    reference_by_path = {
        page.relative_path.as_posix(): page for page in pages.values() if page.is_reference
    }
    for path_value, page in sorted(reference_by_path.items()):
        entry = manifest.get(path_value)
        if entry is None:
            issues.append(
                BuildIssue("error", "MF001", "Fachseite fehlt im Manifest", path_value)
            )
            continue
        comparisons = {
            "title": (page.title, entry.title),
            "lines": (page.line_count, entry.lines),
            "bytes": (page.byte_size, entry.bytes),
            "sha256": (page.source_sha256, entry.sha256),
            "status": (page.status, entry.status),
            "origin": (page.origin or "", entry.origin),
        }
        for field_name, (actual, expected) in comparisons.items():
            if actual != expected:
                issues.append(
                    BuildIssue(
                        "error",
                        "MF008",
                        f"Manifestabweichung bei {field_name}: Ist={actual!r}, Soll={expected!r}",
                        path_value,
                    )
                )
    for manifest_path in sorted(set(manifest) - set(reference_by_path)):
        issues.append(
            BuildIssue(
                "error",
                "MF002",
                "Manifesteintrag verweist auf keine Fachseite",
                manifest_path,
            )
        )

    category_pages = [page for page in pages.values() if page.page_type == "category-index"]
    references_by_category: dict[str, list[PageRecord]] = {}
    for page in reference_by_path.values():
        if page.category_id:
            references_by_category.setdefault(page.category_id, []).append(page)

    categories: dict[str, CategoryRecord] = {}
    for index_page in sorted(category_pages, key=lambda item: item.relative_path.as_posix()):
        category_id = index_page.category_id
        if category_id is None:
            continue
        match = CATEGORY_RE.match(category_id)
        assert match is not None
        references = references_by_category.get(category_id, [])
        targets = _extract_category_index_targets(index_page)
        actual_paths = {page.relative_path.as_posix() for page in references}
        target_set = set(targets)
        for missing in sorted(actual_paths - target_set):
            issues.append(
                BuildIssue(
                    "error",
                    "NV005",
                    "Fachseite fehlt im Abschnitt »Seiten« des Kategorieindex",
                    missing,
                )
            )
        for extra in sorted(target_set - actual_paths):
            issues.append(
                BuildIssue(
                    "error",
                    "NV006",
                    "Kategorieindex verweist im Abschnitt »Seiten« auf keine Fachseite",
                    index_page.relative_path.as_posix(),
                    hint=extra,
                )
            )
        if len(targets) != len(set(targets)):
            issues.append(
                BuildIssue(
                    "error",
                    "NV007",
                    "Kategorieindex enthält eine Fachseite mehrfach",
                    index_page.relative_path.as_posix(),
                )
            )
        declared_pages = index_page.metadata.get("pages")
        if declared_pages != len(references):
            issues.append(
                BuildIssue(
                    "error",
                    "NV008",
                    f"Frontmatter pages={declared_pages!r}, tatsächlich {len(references)}",
                    index_page.relative_path.as_posix(),
                    1,
                )
            )
        ordered_ids: list[str] = []
        for position, target in enumerate(targets, start=1):
            page = reference_by_path.get(target)
            if page is None:
                continue
            ordered_ids.append(page.page_id)
            pages[page.page_id] = replace(page, navigation_position=position)
        title = next(
            (entry.area for entry in manifest.values() if entry.path.parts[0] == category_id),
            index_page.title.removesuffix(" – Kategorienindex"),
        )
        categories[category_id] = CategoryRecord(
            category_id=category_id,
            number=int(match.group("number")),
            title=title,
            directory=PurePosixPath(category_id),
            index_page_id=index_page.page_id,
            reference_page_ids=tuple(ordered_ids),
        )

    for category_id in sorted(set(references_by_category) - set(categories)):
        issues.append(
            BuildIssue(
                "error",
                "NV009",
                "Kategorie besitzt keinen INDEX.md",
                category_id,
            )
        )

    issues.extend(_collision_issues(pages))
    return ContentIndex(root, pages, categories, manifest, sorted(issues, key=BuildIssue.sort_key))
