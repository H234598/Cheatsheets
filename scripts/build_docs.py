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
from pathlib import Path
import shutil
from typing import Iterable

from callouts import convert_obsidian_callouts_for_web
from content_index import build_content_index
from content_model import CATEGORY_RE, ContentIndex, FenceState, PageRecord, advance_fence_state
from io_utils import atomic_write_text, mark_generated_root, staged_directory
from link_converters import convert_for_web

PUBLISH_ROLES = {
    "reference",
    "category-index",
    "root-landing",
    "root-index",
    "root-readme",
    "maintenance",
    "download-only",
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


class BuildDocsError(RuntimeError):
    """Die Webquellen konnten nicht vollständig und sicher erzeugt werden."""


@dataclass(frozen=True, slots=True)
class BuildDocsResult:
    output: Path
    pages: int
    assets: int
    source_hashes: dict[str, str]


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


def _transform_page(page: PageRecord, index: ContentIndex) -> str:
    before_fences = fenced_segment_hashes(page.raw_text)
    converted = convert_for_web(
        page.raw_text,
        page.source_path,
        index.root,
        index=index,
        tolerate_issues=False,
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


def _write_generated_support(staging: Path, root: Path) -> None:
    web_assets = root / "web" / "assets"
    if web_assets.is_dir():
        shutil.copytree(web_assets, staging / "assets", dirs_exist_ok=True)
    atomic_write_text(
        staging / "404.md",
        "# Seite nicht gefunden\n\n"
        "Die angeforderte Cheatsheet-Seite ist nicht vorhanden oder wurde verschoben.\n\n"
        "[Zur Startseite](index.md)\n",
    )


def build_docs(
    root: Path,
    output: Path,
    *,
    strict: bool = True,
    force: bool = False,
    max_pages: int | None = None,
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

    index = build_content_index(root)
    errors = _validation_errors(index)
    if errors:
        preview = "\n".join(errors[:25])
        suffix = f"\n… und {len(errors) - 25} weitere" if len(errors) > 25 else ""
        raise BuildDocsError(f"Contentmodell ist ungültig:\n{preview}{suffix}")

    pages = sorted(
        (page for page in index.pages.values() if page.page_type in PUBLISH_ROLES),
        key=lambda page: page.generated_path.as_posix().casefold(),
    )
    if max_pages is not None:
        pages = pages[:max_pages]

    before = source_tree_hashes(root)
    allowed_root = output.parent.resolve()
    asset_count = 0
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

        _write_generated_support(staging, root)
        mark_generated_root(staging)

    after = source_tree_hashes(root)
    if before != after:
        raise BuildDocsError("Der Build hat kanonische Quelldateien verändert")

    return BuildDocsResult(
        output=output,
        pages=len(pages),
        assets=asset_count,
        source_hashes=before,
    )
