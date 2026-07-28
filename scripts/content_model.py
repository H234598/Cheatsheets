#!/usr/bin/env python3
"""Kanonische Datentypen und stabile Identifikatoren für Cheatsheets.

Angepasst aus ``scripts/content_model.py`` des Repositories
``H234598/ADHS-Lernpfad`` am Commit
``93c8c02d263ec123c1c271caf0d2deaa76760ccb``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
import hashlib
from pathlib import Path, PurePosixPath
import re
import unicodedata
from typing import Any, Literal

EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "htmlcov",
    "node_modules",
    "playwright-report",
    "site",
    "test-results",
}
CATEGORY_RE = re.compile(r"^(?P<number>\d{2})-(?P<slug>[^/]+)$")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*$")
FENCE_RE = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})(?P<info>[^\r\n]*)(?:\r?\n)?$")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})[ \t]*(?:\r?\n)?$")
EXPLICIT_ID_RE = re.compile(r"\s*\{#([-\w:.]+)\}\s*$")
ATTR_LIST_RE = re.compile(r"\s*\{[^{}]+\}\s*$")

FenceState = tuple[str, int]
Severity = Literal["info", "warning", "error"]


def advance_fence_state(
    line: str,
    state: FenceState | None,
) -> tuple[FenceState | None, bool]:
    """Aktualisiere einen CommonMark-kompatiblen Fence-Zustand.

    Der boolesche Rückgabewert ist für Öffnungs-, Inhalts- und Schließzeilen
    wahr. Schließer müssen dasselbe Zeichen und mindestens die Öffnungslänge
    verwenden.
    """

    if state is not None:
        match = FENCE_CLOSE_RE.match(line)
        if match:
            marker = match.group("marker")
            if marker[0] == state[0] and len(marker) >= state[1]:
                return None, True
        return state, True

    match = FENCE_RE.match(line)
    if match is None:
        return None, False
    marker = match.group("marker")
    info = match.group("info")
    if marker[0] == "`" and "`" in info:
        return None, False
    return (marker[0], len(marker)), True


def normalize_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def normalize_posix_path(path: str | Path | PurePosixPath) -> str:
    value = unicodedata.normalize("NFC", PurePosixPath(path).as_posix())
    while value.startswith("./"):
        value = value[2:]
    return value.lstrip("/")


def slugify(value: str) -> str:
    """Erzeuge einen stabilen, MkDocs-nahen ASCII-Anker."""

    value = ATTR_LIST_RE.sub("", value)
    value = re.sub(r"[`*_~]", "", value)
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-") or "section"


def page_id_from_path(relative_path: Path) -> str:
    normalized = normalize_posix_path(relative_path)
    payload = f"cheatsheets-page-v1\0{normalized}".encode("utf-8")
    return "p_" + hashlib.sha256(payload).hexdigest()[:16]


def canonical_document_path(relative_path: Path) -> str:
    path = normalize_posix_path(relative_path)
    return path[:-3] if path.lower().endswith(".md") else path


def document_url(relative_path: Path, role: str) -> str:
    if role == "root-landing":
        return "/"
    if role == "category-index":
        return f"/{relative_path.parent.as_posix().strip('/')}/"
    return "/" + canonical_document_path(relative_path).strip("/") + "/"


def json_compatible(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (Path, PurePosixPath)):
        return value.as_posix()
    if isinstance(value, dict):
        return {
            str(key): json_compatible(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set)):
        return [json_compatible(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


@dataclass(frozen=True, slots=True)
class HeadingRecord:
    level: int
    text: str
    anchor: str
    line: int
    explicit: bool = False


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    number: int
    area: str
    title: str
    path: PurePosixPath
    lines: int
    bytes: int
    sha256: str
    origin: str
    status: str


@dataclass(frozen=True, slots=True)
class PageRecord:
    source_path: Path
    relative_path: PurePosixPath
    page_type: str
    category_id: str | None
    category_title: str | None
    title: str
    aliases: tuple[str, ...]
    tags: tuple[str, ...]
    status: str
    origin: str | None
    reviewed: str | None
    metadata: dict[str, Any] = field(repr=False)
    source_sha256: str = ""
    line_count: int = 0
    byte_size: int = 0
    headings: tuple[HeadingRecord, ...] = field(default_factory=tuple)
    canonical_url: str = ""
    page_id: str = ""
    estimated_minutes: int = 1
    derived_fields: tuple[str, ...] = field(default_factory=tuple)
    navigation_position: int | None = None
    body_start_line: int = 1
    raw_text: str = field(default="", repr=False)

    @property
    def is_reference(self) -> bool:
        return self.page_type == "reference"

    @property
    def generated_path(self) -> PurePosixPath:
        if self.page_type == "root-landing":
            return PurePosixPath("index.md")
        if self.page_type == "category-index":
            return self.relative_path.parent / "index.md"
        if self.page_type == "root-index":
            return PurePosixPath("index/quelle.md")
        if self.page_type in {"root-readme", "maintenance"}:
            return PurePosixPath("intern") / self.relative_path.name
        if self.page_type == "download-only":
            return PurePosixPath("downloads") / self.relative_path.name
        return self.relative_path

    @property
    def path_without_suffix(self) -> str:
        return canonical_document_path(Path(self.relative_path.as_posix()))


@dataclass(frozen=True, slots=True)
class CategoryRecord:
    category_id: str
    number: int
    title: str
    directory: PurePosixPath
    index_page_id: str
    reference_page_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BuildIssue:
    severity: Severity
    code: str
    message: str
    source_path: str | None = None
    line: int | None = None
    column: int | None = None
    hint: str | None = None

    def sort_key(self) -> tuple[str, int, int, str, str]:
        return (
            self.source_path or "",
            self.line or 0,
            self.column or 0,
            self.code,
            self.message,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            key: value
            for key, value in {
                "severity": self.severity,
                "code": self.code,
                "message": self.message,
                "source_path": self.source_path,
                "line": self.line,
                "column": self.column,
                "hint": self.hint,
            }.items()
            if value is not None
        }

    def format(self) -> str:
        location = self.source_path or "<repository>"
        if self.line is not None:
            location += f":{self.line}"
        if self.column is not None:
            location += f":{self.column}"
        suffix = f" Hinweis: {self.hint}" if self.hint else ""
        return f"{location}: {self.severity.upper()} {self.code}: {self.message}{suffix}"


@dataclass(slots=True)
class ContentIndex:
    root: Path
    pages: dict[str, PageRecord]
    categories: dict[str, CategoryRecord]
    manifest: dict[str, ManifestEntry]
    issues: list[BuildIssue]
    by_relative_path: dict[str, str] = field(default_factory=dict)
    lookup: dict[str, set[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.by_relative_path or self.lookup:
            return
        for page_id, page in self.pages.items():
            relative = normalize_posix_path(page.relative_path)
            without_suffix = canonical_document_path(Path(relative))
            self.by_relative_path[relative.casefold()] = page_id
            self.by_relative_path[without_suffix.casefold()] = page_id
            keys = {
                page.title,
                page.relative_path.stem,
                relative,
                without_suffix,
                page_id,
                *page.aliases,
            }
            for key in keys:
                self.lookup.setdefault(normalize_key(key), set()).add(page_id)

    @property
    def reference_pages(self) -> list[PageRecord]:
        return sorted(
            (page for page in self.pages.values() if page.is_reference),
            key=lambda page: (
                page.navigation_position if page.navigation_position is not None else 10**9,
                normalize_key(page.title),
                page.relative_path.as_posix(),
            ),
        )

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)

    def lookup_pages(self, key: str) -> list[PageRecord]:
        return [
            self.pages[page_id]
            for page_id in sorted(self.lookup.get(normalize_key(key), set()))
        ]

    def page_for_path(self, value: str | Path | PurePosixPath) -> PageRecord | None:
        path = Path(value)
        if path.is_absolute():
            try:
                path = path.resolve().relative_to(self.root.resolve())
            except ValueError:
                return None
        normalized = normalize_posix_path(path).casefold()
        page_id = self.by_relative_path.get(normalized)
        return self.pages.get(page_id) if page_id else None
