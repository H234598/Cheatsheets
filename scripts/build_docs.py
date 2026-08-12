#!/usr/bin/env python3
"""Deterministische Webquellen unter ``build/docs`` erzeugen.

Die grundlegende Trennung zwischen kanonischen Quellen und generiertem
``build/docs`` ist aus ``H234598/ADHS-Lernpfad`` am Commit
``93c8c02d263ec123c1c271caf0d2deaa76760ccb`` abgeleitet. Atomarer Austausch
und fail-closed Dateibehandlung folgen den Mustern aus ``H234598/desinfect``
am Commit ``fbcc6e850fec1f4592ca519fa3e5141b11a95e60``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
from typing import Iterable

from build_graph import GraphBuildError, GraphBuildResult, write_graph_outputs
from build_navigation import (
    NavigationResult,
    load_publication_config,
    normalize_site_url,
    validate_publication_config,
    write_navigation_outputs,
)
from callouts import convert_obsidian_callouts_for_web
from content_index import build_content_index
from content_model import (
    CATEGORY_RE,
    FRONTMATTER_RE,
    ContentIndex,
    FenceState,
    PageRecord,
    advance_fence_state,
)
from io_utils import atomic_write_text, mark_generated_root, staged_directory
from link_converters import convert_for_web
from ui_config import UIConfigError, write_ui_data

PUBLISH_ROLES = {
    "reference",
    "category-index",
    "root-landing",
    "root-index",
    "root-readme",
    "maintenance",
}
SOURCE_EXCLUDED_PARTS = {
    ".git",
    ".github",
    ".obsidian",
    ".venv",
    "__pycache__",
    "build",
    "node_modules",
    "site",
    "tests",
}
RESERVED_WEB_METADATA = {
    "web_category_id",
    "web_category_title",
    "web_minutes",
    "web_page_id",
    "web_page_type",
    "web_source_path",
}


class BuildDocsError(RuntimeError):
    """Die Webquellen konnten nicht vollständig und sicher erzeugt werden."""


@dataclass(frozen=True, slots=True)
class BuildDocsResult:
    output: Path
    pages: int
    assets: int
    source_hashes: dict[str, str]
    navigation: list[dict[str, object]]
    generated_markdown_pages: int
    data_files: int


def fenced_segment_hashes(text: str) -> tuple[str, ...]:
    """Hashwerte aller vollständigen Fence-Segmente in Quellreihenfolge."""

    fence: FenceState | None = None
    current: list[str] = []
    hashes: list[str] = []
    for line in text.splitlines(keepends=True):
        previous = fence
        fence, is_fenced = advance_fence_state(line, fence)
        if is_fenced:
            current.append(line)
            if previous is not None and fence is None:
                hashes.append(hashlib.sha256("".join(current).encode("utf-8")).hexdigest())
                current = []
    if current:
        # Ein ungeschlossener Fence wird trotzdem geschützt; MkDocs strict wird
        # ihn später zusätzlich als Markdownproblem behandeln.
        hashes.append(hashlib.sha256("".join(current).encode("utf-8")).hexdigest())
    return tuple(hashes)


def source_tree_hashes(root: Path, *, include_technical: bool = False) -> dict[str, str]:
    """Berechne einen stabil sortierten Hash-Snapshot relevanter Quelldateien."""

    result: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part in SOURCE_EXCLUDED_PARTS for part in relative.parts):
            continue
        if not include_technical and relative.parts and relative.parts[0] in {
            "config",
            "docs",
            "scripts",
            "web",
        }:
            continue
        payload = path.read_bytes()
        result[relative.as_posix()] = hashlib.sha256(payload).hexdigest()
    return result


def _validation_errors(index: ContentIndex) -> list[str]:
    return [issue.format() for issue in index.issues if issue.severity == "error"]


def _web_metadata_lines(page: PageRecord) -> list[str]:
    values: list[tuple[str, str | int]] = [
        ("web_page_id", page.page_id),
        ("web_page_type", page.page_type),
        ("web_minutes", page.estimated_minutes),
        ("web_source_path", page.relative_path.as_posix()),
    ]
    if page.category_id:
        values.append(("web_category_id", page.category_id))
    if page.category_title:
        values.append(("web_category_title", page.category_title))

    lines: list[str] = []
    for key, value in values:
        encoded = str(value) if isinstance(value, int) else json.dumps(value, ensure_ascii=False)
        lines.append(f"{key}: {encoded}")
    return lines


def inject_web_metadata(text: str, page: PageRecord) -> str:
    """Ergänze ausschließlich die generierte Kopie um stabile UI-Metadaten."""

    collisions = RESERVED_WEB_METADATA.intersection(page.metadata)
    if collisions:
        raise BuildDocsError(
            "Reservierte Web-Metadaten sind bereits in der kanonischen Quelle belegt: "
            f"{page.relative_path.as_posix()} ({', '.join(sorted(collisions))})"
        )

    match = FRONTMATTER_RE.match(text)
    lines = _web_metadata_lines(page)
    if match is None:
        return "---\n" + "\n".join(lines) + "\n---\n" + text

    newline = "\r\n" if "\r\n" in match.group(0) else "\n"
    insertion = newline + newline.join(lines)
    return text[: match.end(1)] + insertion + text[match.end(1) :]


def _transform_page(page: PageRecord, index: ContentIndex) -> str:
    before_fences = fenced_segment_hashes(page.raw_text)
    generated_source = inject_web_metadata(page.raw_text, page)
    converted = convert_for_web(
        generated_source,
        page.source_path,
        index.root,
        index=index,
    )
    converted = convert_obsidian_callouts_for_web(converted)
    after_fences = fenced_segment_hashes(converted)
    if before_fences != after_fences:
        raise BuildDocsError(
            "Geschützte Codefences wurden bei der Webtransformation verändert: "
            f"{page.relative_path.as_posix()}"
        )
    return converted


def _asset_paths(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part in SOURCE_EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() == ".md":
            continue
        if not relative.parts:
            continue
        first = relative.parts[0]
        if not (CATEGORY_RE.match(first) or first in {"assets", "media"}):
            continue
        yield path


def _write_generated_support(staging: Path, root: Path, site_url: str) -> None:
    web_assets = root / "web" / "assets"
    if web_assets.is_dir():
        shutil.copytree(web_assets, staging / "assets", dirs_exist_ok=True)
    home_url = normalize_site_url(site_url)
    atomic_write_text(
        staging / "404.md",
        "# Seite nicht gefunden\n\n"
        "Die angeforderte Cheatsheet-Seite ist nicht vorhanden oder wurde verschoben.\n\n"
        f"[Zur Startseite]({home_url})\n",
    )


def build_docs(
    root: Path,
    output: Path,
    *,
    index: ContentIndex | None = None,
    strict: bool = True,
    force: bool = False,
    max_pages: int | None = None,
    site_url: str = "https://example.invalid/Cheatsheets/",
    source_commit: str = "unknown",
) -> BuildDocsResult:
    """Erzeuge die vollständige Webquellkopie atomar.

    ``max_pages`` ist ausschließlich für lokale Fixture-/Entwicklungsbuilds
    gedacht. Ein strenger vollständiger Build lehnt eine Begrenzung ab.
    """

    root = root.resolve()
    output = output.resolve(strict=False)
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages muss mindestens 1 sein")
    if strict and max_pages is not None:
        raise ValueError("Ein strenger Build darf nicht mit max_pages begrenzt werden")

    index = index or build_content_index(root)
    errors = _validation_errors(index)
    if errors:
        preview = "\n".join(errors[:25])
        suffix = f"\n… und {len(errors) - 25} weitere" if len(errors) > 25 else ""
        raise BuildDocsError(f"Contentmodell ist ungültig:\n{preview}{suffix}")

    publication = load_publication_config(root)
    validate_publication_config(publication, index)

    pages = sorted(
        (page for page in index.pages.values() if page.page_type in PUBLISH_ROLES),
        key=lambda page: page.generated_path.as_posix().casefold(),
    )
    if max_pages is not None:
        pages = pages[:max_pages]

    before = source_tree_hashes(root)
    allowed_root = output.parent.resolve()
    asset_count = 0
    navigation_result: NavigationResult | None = None
    graph_result: GraphBuildResult | None = None
    with staged_directory(output, allowed_root=allowed_root, force=force) as staging:
        for page in pages:
            target = staging / page.generated_path.as_posix()
            atomic_write_text(target, _transform_page(page, index))
        for asset in _asset_paths(root):
            relative = asset.relative_to(root)
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(asset, target)
            asset_count += 1

        _write_generated_support(staging, root, site_url)
        navigation_result = write_navigation_outputs(
            staging,
            index,
            site_url=site_url,
            source_commit=source_commit,
        )
        try:
            graph_result = write_graph_outputs(
                staging,
                index,
                site_url=site_url,
                source_commit=source_commit,
            )
            write_ui_data(staging, root, index)
        except (GraphBuildError, UIConfigError) as exc:
            raise BuildDocsError(f"Generierte Webdaten sind ungültig: {exc}") from exc
        mark_generated_root(staging)

    after = source_tree_hashes(root)
    if before != after:
        raise BuildDocsError("Der Build hat kanonische Quelldateien verändert")
    if navigation_result is None or graph_result is None:
        raise BuildDocsError("Navigation, Graph und Suchmetadaten wurden nicht erzeugt")

    return BuildDocsResult(
        output=output,
        pages=len(pages),
        assets=asset_count,
        source_hashes=before,
        navigation=navigation_result.nav,
        generated_markdown_pages=(
            navigation_result.generated_markdown_pages + graph_result.markdown_pages
        ),
        data_files=navigation_result.data_files + graph_result.data_files + 1,
    )
