#!/usr/bin/env python3
"""Navigation, Indizes und clientseitige Metadaten deterministisch erzeugen.

Die strukturierte Content-Index-Idee stammt aus ``H234598/ADHS-Lernpfad`` am
Commit ``93c8c02d263ec123c1c271caf0d2deaa76760ccb``. Anders als im
Referenzrepository wird die Fachnavigation hier vollständig aus realen
Kategorieindizes erzeugt und niemals als zweite 86-Seiten-Liste gepflegt.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import yaml

from content_model import CategoryRecord, ContentIndex, PageRecord, normalize_key
from io_utils import atomic_write_text, generated_at_iso, stable_json_dumps


class NavigationError(RuntimeError):
    """Navigation oder generierte Indexdaten sind inkonsistent."""


@dataclass(frozen=True, slots=True)
class PublicationConfig:
    schema_version: int
    home: str
    source_index: str
    publish_types: tuple[str, ...]
    maintenance: tuple[str, ...]
    download_only: tuple[str, ...]
    exclude_globs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NavigationResult:
    nav: list[dict[str, object]]
    generated_markdown_pages: int
    data_files: int


def _as_string_tuple(value: Any, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise NavigationError(f"publication.yaml: {field} muss eine Stringliste sein")
    return tuple(value)


def load_publication_config(root: Path) -> PublicationConfig:
    path = root / "config" / "publication.yaml"
    if not path.is_file():
        raise NavigationError(f"Publikationskonfiguration fehlt: {path}")
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise NavigationError(f"Ungültige publication.yaml: {exc}") from exc
    if not isinstance(loaded, dict):
        raise NavigationError("publication.yaml muss ein YAML-Mapping sein")
    schema_version = loaded.get("schema_version")
    if schema_version != 1:
        raise NavigationError(
            f"Nicht unterstützte publication.yaml-Version: {schema_version!r}"
        )
    home = loaded.get("home")
    source_index = loaded.get("source_index")
    if not isinstance(home, str) or not home:
        raise NavigationError("publication.yaml: home fehlt")
    if not isinstance(source_index, str) or not source_index:
        raise NavigationError("publication.yaml: source_index fehlt")
    return PublicationConfig(
        schema_version=1,
        home=home,
        source_index=source_index,
        publish_types=_as_string_tuple(loaded.get("publish_types"), field="publish_types"),
        maintenance=_as_string_tuple(loaded.get("maintenance"), field="maintenance"),
        download_only=_as_string_tuple(loaded.get("download_only"), field="download_only"),
        exclude_globs=_as_string_tuple(loaded.get("exclude_globs"), field="exclude_globs"),
    )


def validate_publication_config(config: PublicationConfig, index: ContentIndex) -> None:
    """Prüfe Root-Sonderrollen, ohne eine zweite Fachseitenliste einzuführen."""

    by_source = {page.relative_path.as_posix(): page for page in index.pages.values()}
    home = by_source.get(config.home)
    if home is None or home.page_type != "root-landing":
        raise NavigationError(
            f"publication.yaml: home verweist nicht auf die Root-Landingpage: {config.home}"
        )
    source_index = by_source.get(config.source_index)
    if source_index is None or source_index.page_type != "root-index":
        raise NavigationError(
            "publication.yaml: source_index verweist nicht auf den Root-Index: "
            f"{config.source_index}"
        )

    configured_maintenance = set(config.maintenance)
    real_maintenance = {
        page.relative_path.as_posix()
        for page in index.pages.values()
        if page.page_type in {"root-readme", "maintenance"}
    }
    if configured_maintenance != real_maintenance:
        raise NavigationError(
            "publication.yaml: maintenance weicht von den erkannten Root-Metadateien ab; "
            f"fehlend={sorted(real_maintenance - configured_maintenance)}, "
            f"zusätzlich={sorted(configured_maintenance - real_maintenance)}"
        )

    configured_downloads = set(config.download_only)
    real_downloads = {
        page.relative_path.as_posix()
        for page in index.pages.values()
        if page.page_type == "download-only"
    }
    if configured_downloads != real_downloads:
        raise NavigationError(
            "publication.yaml: download_only weicht von den erkannten Downloadseiten ab; "
            f"fehlend={sorted(real_downloads - configured_downloads)}, "
            f"zusätzlich={sorted(configured_downloads - real_downloads)}"
        )

    allowed_types = {"reference", "index"}
    unknown = set(config.publish_types) - allowed_types
    if unknown:
        raise NavigationError(
            f"publication.yaml: unbekannte publish_types: {sorted(unknown)}"
        )


def normalize_site_url(value: str) -> str:
    split = urlsplit(value.strip())
    if split.scheme not in {"http", "https"} or not split.netloc:
        raise NavigationError(f"site_url muss eine vollständige HTTP(S)-URL sein: {value!r}")
    if split.query or split.fragment:
        raise NavigationError("site_url darf weder Query noch Fragment enthalten")
    path = split.path or "/"
    if not path.endswith("/"):
        path += "/"
    return urlunsplit((split.scheme, split.netloc, path, "", ""))


def absolute_page_url(site_url: str, page: PageRecord) -> str:
    base = normalize_site_url(site_url)
    return base.rstrip("/") + page.canonical_url


def _relative_link(source: PurePosixPath, target: PurePosixPath) -> str:
    relative = os.path.relpath(target.as_posix(), start=source.parent.as_posix())
    return quote(Path(relative).as_posix(), safe="/._~-@")


def _page(index: ContentIndex, page_id: str) -> PageRecord:
    try:
        return index.pages[page_id]
    except KeyError as exc:
        raise NavigationError(f"Kategorie verweist auf unbekannte Page-ID: {page_id}") from exc


def _category_pages(index: ContentIndex, category: CategoryRecord) -> list[PageRecord]:
    pages = [_page(index, page_id) for page_id in category.reference_page_ids]
    if any(page.category_id != category.category_id for page in pages):
        raise NavigationError(
            f"Kategorie {category.category_id} enthält eine Seite aus einer anderen Kategorie"
        )
    return pages


def build_navigation(index: ContentIndex) -> list[dict[str, object]]:
    """Erzeuge die vollständige MkDocs-Navigation ohne manuelle Fachseitenliste."""

    nav: list[dict[str, object]] = [
        {"Start hier": "index.md"},
        {"Kategorien": "kategorien/index.md"},
    ]
    seen_reference_ids: list[str] = []

    for category in sorted(index.categories.values(), key=lambda item: item.number):
        index_page = _page(index, category.index_page_id)
        pages = _category_pages(index, category)
        seen_reference_ids.extend(page.page_id for page in pages)
        nav.append(
            {
                category.title: [
                    {"Übersicht": index_page.generated_path.as_posix()},
                    *[
                        {page.title: page.generated_path.as_posix()}
                        for page in pages
                    ],
                ]
            }
        )

    expected = [page.page_id for page in index.reference_pages]
    if len(seen_reference_ids) != len(set(seen_reference_ids)):
        raise NavigationError("Eine Fachseite erscheint mehrfach in der Navigation")
    if set(seen_reference_ids) != set(expected):
        missing = sorted(set(expected) - set(seen_reference_ids))
        extra = sorted(set(seen_reference_ids) - set(expected))
        raise NavigationError(
            f"Navigation und Fachseiteninventar weichen ab; fehlend={missing}, zusätzlich={extra}"
        )

    nav.extend(
        [
            {"Gesamtindex": "index/gesamt.md"},
            {"Alphabetisch": "index/alphabetisch.md"},
            {"Tags & Themen": "index/tags.md"},
            {"Downloads & Offline": "downloads/index.md"},
        ]
    )
    return nav


def _frontmatter(title: str, description: str) -> str:
    return (
        "---\n"
        f"title: {title}\n"
        f"description: {description}\n"
        "hide:\n"
        "  - feedback\n"
        "---\n\n"
    )


def _category_overview(index: ContentIndex) -> str:
    target = PurePosixPath("kategorien/index.md")
    lines = [
        _frontmatter("Kategorien", "Alle Cheatsheet-Kategorien im Überblick"),
        "# Kategorien\n\n",
        "Wähle einen klar abgegrenzten Themenbereich. Die Seitenzahlen werden bei jedem Build aus den realen Fachseiten berechnet.\n\n",
    ]
    for category in sorted(index.categories.values(), key=lambda item: item.number):
        index_page = _page(index, category.index_page_id)
        pages = _category_pages(index, category)
        lines.append(
            f"## [{category.title}]({_relative_link(target, index_page.generated_path)})\n\n"
            f"{len(pages)} Fachseiten.\n\n"
        )
    return "".join(lines)


def _grouped_index(index: ContentIndex) -> str:
    target = PurePosixPath("index/gesamt.md")
    lines = [
        _frontmatter("Gesamtindex", "Alle veröffentlichten Cheatsheets nach Kategorie"),
        "# Gesamtindex\n\n",
        f"{len(index.reference_pages)} Fachseiten in {len(index.categories)} Kategorien.\n\n",
    ]
    for category in sorted(index.categories.values(), key=lambda item: item.number):
        lines.append(f"## {category.title}\n\n")
        for page in _category_pages(index, category):
            lines.append(
                f"- [{page.title}]({_relative_link(target, page.generated_path)})"
                f" · ca. {page.estimated_minutes} Min.\n"
            )
        lines.append("\n")
    return "".join(lines)


def _alphabetical_index(index: ContentIndex) -> str:
    target = PurePosixPath("index/alphabetisch.md")
    pages = sorted(
        index.reference_pages,
        key=lambda page: (normalize_key(page.title), page.relative_path.as_posix()),
    )
    lines = [
        _frontmatter("Alphabetischer Index", "Alle Cheatsheets alphabetisch sortiert"),
        "# Alphabetischer Index\n\n",
        "Die Sortierung wird Unicode-normalisiert und ist bei identischem Commit reproduzierbar.\n\n",
    ]
    current = ""
    for page in pages:
        first = page.title[:1].upper() if page.title else "#"
        if first != current:
            current = first
            lines.append(f"## {current}\n\n")
        category = index.categories.get(page.category_id or "")
        category_title = category.title if category else "Ohne Kategorie"
        lines.append(
            f"- [{page.title}]({_relative_link(target, page.generated_path)})"
            f" · {category_title}\n"
        )
    lines.append("\n")
    return "".join(lines)


def _tag_index(index: ContentIndex) -> tuple[str, dict[str, list[PageRecord]]]:
    target = PurePosixPath("index/tags.md")
    tags: dict[str, list[PageRecord]] = {}
    display: dict[str, str] = {}
    for page in index.reference_pages:
        for tag in page.tags:
            key = normalize_key(tag)
            if not key:
                continue
            display.setdefault(key, tag)
            tags.setdefault(key, []).append(page)
    lines = [
        _frontmatter("Tags & Themen", "Cheatsheets nach gepflegten Frontmatter-Tags"),
        "# Tags & Themen\n\n",
        f"{len(tags)} eindeutige Tags aus den Fachseiten.\n\n",
    ]
    for key in sorted(tags):
        pages = sorted(
            tags[key],
            key=lambda page: (normalize_key(page.title), page.relative_path.as_posix()),
        )
        lines.append(f"## {display[key]}\n\n")
        for page in pages:
            lines.append(f"- [{page.title}]({_relative_link(target, page.generated_path)})\n")
        lines.append("\n")
    return "".join(lines), tags


def _downloads_page(index: ContentIndex) -> str:
    target = PurePosixPath("downloads/index.md")
    download_pages = sorted(
        (page for page in index.pages.values() if page.page_type == "download-only"),
        key=lambda page: page.generated_path.as_posix(),
    )
    lines = [
        _frontmatter("Downloads & Offline", "Verfügbare Quell- und Offlineartefakte"),
        "# Downloads & Offline\n\n",
        "Die reproduzierbaren ZIP-, Gesamt-Markdown- und Prüfsummenartefakte folgen in Phase 6. Bereits versionierte Sammeldokumente bleiben erreichbar.\n\n",
    ]
    for page in download_pages:
        lines.append(f"- [{page.title}]({_relative_link(target, page.generated_path)})\n")
    if not download_pages:
        lines.append("Noch kein versioniertes Sammeldokument erkannt.\n")
    lines.append("\n")
    return "".join(lines)


def _build_information(index: ContentIndex, site_url: str, source_commit: str) -> str:
    return _frontmatter(
        "Buildinformationen", "Reproduzierbare technische Metadaten"
    ) + (
        "# Buildinformationen\n\n"
        "| Feld | Wert |\n"
        "|---|---|\n"
        f"| Quellcommit | `{source_commit}` |\n"
        f"| Reproduzierbarer Zeitpunkt | `{generated_at_iso()}` |\n"
        f"| Site-URL | `{normalize_site_url(site_url)}` |\n"
        f"| Fachseiten | {len(index.reference_pages)} |\n"
        f"| Kategorien | {len(index.categories)} |\n"
        f"| Manifest-Einträge | {len(index.manifest)} |\n"
    )


def _page_payload(index: ContentIndex, page: PageRecord, site_url: str) -> dict[str, object]:
    category = index.categories.get(page.category_id or "")
    return {
        "aliases": list(page.aliases),
        "category": page.category_id,
        "category_title": category.title if category else page.category_title,
        "id": page.page_id,
        "minutes": page.estimated_minutes,
        "source_path": page.relative_path.as_posix(),
        "status": page.status,
        "tags": list(page.tags),
        "title": page.title,
        "url": absolute_page_url(site_url, page),
    }


def write_navigation_outputs(
    staging: Path,
    index: ContentIndex,
    *,
    site_url: str,
    source_commit: str,
) -> NavigationResult:
    """Schreibe alle generierten Navigationsseiten und JSON-Daten in *staging*."""

    site_url = normalize_site_url(site_url)
    tag_markdown, tags = _tag_index(index)
    markdown_outputs = {
        PurePosixPath("kategorien/index.md"): _category_overview(index),
        PurePosixPath("index/gesamt.md"): _grouped_index(index),
        PurePosixPath("index/alphabetisch.md"): _alphabetical_index(index),
        PurePosixPath("index/tags.md"): tag_markdown,
        PurePosixPath("downloads/index.md"): _downloads_page(index),
        PurePosixPath("intern/buildinformationen.md"): _build_information(
            index, site_url, source_commit
        ),
    }
    for relative, text in markdown_outputs.items():
        atomic_write_text(staging / relative.as_posix(), text)

    category_payload = [
        {
            "id": category.category_id,
            "number": category.number,
            "page_count": len(category.reference_page_ids),
            "title": category.title,
            "url": absolute_page_url(site_url, _page(index, category.index_page_id)),
        }
        for category in sorted(index.categories.values(), key=lambda item: item.number)
    ]
    page_payload = [
        _page_payload(index, page, site_url)
        for page in index.reference_pages
    ]
    tag_payload = []
    for key, pages in sorted(tags.items()):
        display_name = next(
            tag
            for page in pages
            for tag in page.tags
            if normalize_key(tag) == key
        )
        tag_payload.append(
            {
                "id": key,
                "name": display_name,
                "pages": [
                    page.page_id
                    for page in sorted(pages, key=lambda page: normalize_key(page.title))
                ],
            }
        )
    build_payload = {
        "categories": len(index.categories),
        "generated_at": generated_at_iso(),
        "reference_pages": len(index.reference_pages),
        "schema_version": 1,
        "site_url": site_url,
        "source_commit": source_commit,
    }
    data_outputs = {
        "pages.json": page_payload,
        "categories.json": category_payload,
        "tags.json": tag_payload,
        "build-info.json": build_payload,
    }
    for name, payload in data_outputs.items():
        atomic_write_text(staging / "data" / name, stable_json_dumps(payload))

    nav = build_navigation(index)
    return NavigationResult(
        nav=nav,
        generated_markdown_pages=len(markdown_outputs),
        data_files=len(data_outputs),
    )
