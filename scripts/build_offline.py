#!/usr/bin/env python3
"""Reproduzierbares, selbstenthaltendes Offline-HTML-Paket erzeugen."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import Callable, Iterable
from urllib.parse import unquote, urlsplit
import zipfile

import yaml

from content_model import ContentIndex
from download_model import DownloadBuildError, DownloadBuildResult, READ_CHUNK_SIZE, ZIP_MIN_EPOCH
from download_sources import canonical_archive_name
from io_utils import (
    atomic_write_bytes,
    atomic_write_text,
    generated_at_iso,
    sha256_bytes,
    source_date_epoch,
    stable_json_dumps,
    staged_directory,
)

OFFLINE_ARCHIVE_NAME = "Cheatsheets-Offline-HTML.zip"
OFFLINE_MANIFEST_NAME = "OFFLINE-MANIFEST.json"
OFFLINE_CHECKSUMS_NAME = "OFFLINE-SHA256SUMS.txt"
OFFLINE_README_NAME = "OFFLINE-LESEN.txt"
OFFLINE_SERVER_NAME = "offline-server.py"
BUILD_SENTINEL = ".cheatsheets-build-root"
RUNTIME_URL_ATTRIBUTES: dict[str, tuple[str, ...]] = {
    "audio": ("src",),
    "base": ("href",),
    "embed": ("src",),
    "iframe": ("src",),
    "img": ("src", "srcset"),
    "input": ("src",),
    "object": ("data",),
    "script": ("src",),
    "source": ("src", "srcset"),
    "track": ("src",),
    "video": ("src", "poster"),
}
RUNTIME_LINK_RELS = {
    "apple-touch-icon",
    "icon",
    "manifest",
    "modulepreload",
    "preconnect",
    "prefetch",
    "dns-prefetch",
    "preload",
    "stylesheet",
}
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)
CSS_IMPORT_RE = re.compile(
    r"@import\s+(?:url\(\s*)?['\"]?(?P<url>[^'\"\s;)]+)", re.I
)
CHECKSUM_LINE_RE = re.compile(r"^(?P<sha>[0-9a-f]{64})  (?P<name>[^\r\n]+)$")
SOURCE_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class OfflineBuildError(DownloadBuildError):
    """Das Offlinepaket konnte nicht vollständig oder sicher erzeugt werden."""


@dataclass(frozen=True, slots=True)
class OfflineBuildResult:
    payload: bytes
    files: int
    uncompressed_bytes: int
    tree_sha256: str


@dataclass(frozen=True, slots=True)
class OfflineReference:
    tag: str
    attribute: str
    value: str
    runtime: bool


@dataclass(frozen=True, slots=True)
class ParsedHtml:
    references: tuple[OfflineReference, ...]
    ids: frozenset[str]


class ReferenceParser(HTMLParser):
    """Sammle IDs sowie lokale, externe und laufzeitwirksame URL-Attribute."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[OfflineReference] = []
        self.ids: set[str] = set()
        self._style_depth = 0

    @staticmethod
    def _srcset(value: str) -> Iterable[str]:
        for candidate in value.split(","):
            candidate = candidate.strip()
            if candidate:
                yield candidate.split()[0]

    def _add_reference(
        self,
        *,
        tag: str,
        attribute: str,
        value: str,
        runtime: bool,
    ) -> None:
        value = value.strip()
        if not value:
            return
        if attribute == "srcset":
            for item in self._srcset(value):
                self.references.append(OfflineReference(tag, attribute, item, runtime))
            return
        self.references.append(OfflineReference(tag, attribute, value, runtime))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        values = {name.casefold(): value or "" for name, value in attrs}
        identifier = values.get("id", "").strip()
        if identifier:
            self.ids.add(identifier)

        style = values.get("style", "")
        for match in CSS_URL_RE.finditer(style):
            self._add_reference(
                tag=tag,
                attribute="style",
                value=match.group(2),
                runtime=True,
            )

        if tag == "base":
            raise OfflineBuildError("Offline-HTML darf kein <base>-Element enthalten")
        if tag == "style":
            self._style_depth += 1
        if tag == "meta" and values.get("http-equiv", "").casefold() == "refresh":
            raise OfflineBuildError("Offline-HTML darf keinen Meta-Refresh enthalten")

        if tag == "a":
            self._add_reference(
                tag=tag,
                attribute="href",
                value=values.get("href", ""),
                runtime=False,
            )
            return

        if tag == "link":
            relations = {item.casefold() for item in values.get("rel", "").split()}
            self._add_reference(
                tag=tag,
                attribute="href",
                value=values.get("href", ""),
                runtime=bool(relations & RUNTIME_LINK_RELS),
            )
            return

        for attribute in RUNTIME_URL_ATTRIBUTES.get(tag, ()):
            self._add_reference(
                tag=tag,
                attribute=attribute,
                value=values.get(attribute, ""),
                runtime=True,
            )

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "style" and self._style_depth:
            self._style_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._style_depth:
            return
        for match in CSS_URL_RE.finditer(data):
            self._add_reference(
                tag="style",
                attribute="url",
                value=match.group(2),
                runtime=True,
            )
        for match in CSS_IMPORT_RE.finditer(data):
            self._add_reference(
                tag="style",
                attribute="import",
                value=match.group("url"),
                runtime=True,
            )

    def result(self) -> ParsedHtml:
        return ParsedHtml(tuple(self.references), frozenset(self.ids))


def _load_base_config(root: Path) -> dict[str, object]:
    path = root / "mkdocs.yml"
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise OfflineBuildError(
            f"Offline-Konfiguration kann mkdocs.yml nicht lesen: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise OfflineBuildError("mkdocs.yml muss ein YAML-Mapping sein")
    return payload


def write_offline_config(
    root: Path,
    path: Path,
    *,
    docs_dir: Path,
    site_dir: Path,
    site_url: str,
    nav: list[dict[str, object]],
) -> dict[str, object]:
    """Schreibe eine separate MkDocs-Konfiguration mit dateibasierten URLs."""

    config = _load_base_config(root)
    config["site_name"] = f"{config.get('site_name', 'Cheatsheets')} – Offline"
    config["site_url"] = site_url
    config["docs_dir"] = str(docs_dir.resolve())
    config["site_dir"] = str(site_dir.resolve())
    config["strict"] = True
    config["use_directory_urls"] = False
    config["nav"] = nav

    theme = config.setdefault("theme", {})
    if not isinstance(theme, dict):
        raise OfflineBuildError("theme in mkdocs.yml muss ein Mapping sein")
    custom_dir = theme.get("custom_dir")
    if custom_dir:
        custom_path = Path(str(custom_dir))
        if not custom_path.is_absolute():
            custom_path = root / custom_path
        theme["custom_dir"] = str(custom_path.resolve())

    extra = config.setdefault("extra", {})
    if not isinstance(extra, dict):
        raise OfflineBuildError("extra in mkdocs.yml muss ein Mapping sein")
    extra["offline_mode"] = True
    extra["online_site_url"] = site_url

    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        path,
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False, width=100),
    )
    return config


def _offline_url_for_generated_path(path: PurePosixPath) -> str:
    if path.suffix.casefold() != ".md":
        raise OfflineBuildError(f"Unerwarteter generierter Markdownpfad: {path}")
    return path.with_suffix(".html").as_posix()


def _assert_no_symlinks(root: Path) -> None:
    if root.is_symlink():
        raise OfflineBuildError(f"Offline-Quellbaum darf kein Symlink sein: {root}")
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        for name in [*dirnames, *filenames]:
            path = Path(directory) / name
            if path.is_symlink():
                raise OfflineBuildError(
                    f"Offline-Quellbaum enthält Symlink: {path.relative_to(root)}"
                )


def read_regular_file(path: Path, root: Path) -> bytes:
    """Lese eine reguläre Datei positionsstabil und ohne Symlinkfolge."""

    root = root.resolve()
    absolute = Path(os.path.abspath(path))
    try:
        absolute.relative_to(root)
        absolute.parent.resolve().relative_to(root)
    except ValueError as exc:
        raise OfflineBuildError(f"Dateipfad verlässt den erlaubten Root: {path}") from exc

    before = absolute.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise OfflineBuildError(f"Dateipfad ist keine reguläre Datei: {path}")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(absolute, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OfflineBuildError(f"Geöffneter Dateipfad ist nicht regulär: {path}")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise OfflineBuildError(f"Dateipfad wurde während des Lesens ausgetauscht: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, READ_CHUNK_SIZE):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _regular_files(root: Path) -> list[Path]:
    _assert_no_symlinks(root)
    files: list[Path] = []
    casefolded: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        relative = path.relative_to(root).as_posix()
        if not path.is_file():
            continue
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise OfflineBuildError(
                f"Offlinebaum enthält keine einfache reguläre Datei: {relative}"
            )
        key = relative.casefold()
        previous = casefolded.get(key)
        if previous is not None and previous != relative:
            raise OfflineBuildError(
                f"Case-insensitive Pfadkollision im Offlinebaum: {previous} / {relative}"
            )
        casefolded[key] = relative
        files.append(path)
    return files


def _copy_regular_tree(source: Path, target: Path) -> None:
    if target.exists():
        raise OfflineBuildError(f"Temporäres Offline-Docs-Ziel existiert bereits: {target}")
    target.mkdir(parents=True)
    for path in _regular_files(source):
        relative = path.relative_to(source)
        atomic_write_bytes(target / relative, read_regular_file(path, source))


def _copy_and_rewrite_docs(
    source: Path,
    target: Path,
    index: ContentIndex,
    online_site_url: str,
) -> None:
    _copy_regular_tree(source, target)
    (target / BUILD_SENTINEL).unlink(missing_ok=True)

    pages_path = target / "data" / "pages.json"
    categories_path = target / "data" / "categories.json"
    build_info_path = target / "data" / "build-info.json"
    try:
        pages = json.loads(pages_path.read_text(encoding="utf-8"))
        categories = json.loads(categories_path.read_text(encoding="utf-8"))
        build_info = json.loads(build_info_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OfflineBuildError(f"Generierte Webdaten sind nicht offlinefähig: {exc}") from exc

    if not isinstance(pages, list) or not isinstance(categories, list) or not isinstance(
        build_info, dict
    ):
        raise OfflineBuildError("Generierte Webdaten besitzen unerwartete JSON-Strukturen")

    for item in pages:
        if not isinstance(item, dict):
            raise OfflineBuildError("pages.json enthält keinen Objektdatensatz")
        page_id = str(item.get("id") or "")
        page = index.pages.get(page_id)
        if page is None:
            raise OfflineBuildError(f"pages.json verweist auf unbekannte Page-ID: {page_id}")
        item["url"] = _offline_url_for_generated_path(page.generated_path)

    for item in categories:
        if not isinstance(item, dict):
            raise OfflineBuildError("categories.json enthält keinen Objektdatensatz")
        category_id = str(item.get("id") or "")
        category = index.categories.get(category_id)
        if category is None:
            raise OfflineBuildError(
                f"categories.json verweist auf unbekannte Kategorie: {category_id}"
            )
        page = index.pages.get(category.index_page_id)
        if page is None:
            raise OfflineBuildError(
                f"Kategorie {category_id} besitzt keine indexierte Landingpage"
            )
        item["url"] = _offline_url_for_generated_path(page.generated_path)

    build_info["offline"] = True
    build_info["online_site_url"] = online_site_url
    build_info["url_mode"] = "relative-html"
    atomic_write_text(pages_path, stable_json_dumps(pages))
    atomic_write_text(categories_path, stable_json_dumps(categories))
    atomic_write_text(build_info_path, stable_json_dumps(build_info))


def _support_readme(online_site_url: str, source_commit: str) -> str:
    return (
        "CHEATSHEETS – OFFLINE-HTML\n"
        "==========================\n\n"
        "Schnellstart ohne Installation:\n"
        "  1. Dieses ZIP vollständig entpacken.\n"
        "  2. index.html im Browser öffnen.\n\n"
        "Dabei bleiben Inhalte, Kategorien, Indizes und normale Links verfügbar. "
        "Einige Browser beschränken Suche, Favoriten und Filter bei file://.\n\n"
        "Vollständige lokale Funktionen:\n"
        "  python offline-server.py\n"
        "  Danach http://127.0.0.1:8765/index.html öffnen.\n\n"
        "Der Server bindet ausschließlich an 127.0.0.1 und benötigt keinen "
        "Internetzugang. Externe Quelllinks werden nur beim bewussten Anklicken geöffnet.\n\n"
        f"Quellcommit: {source_commit}\n"
        f"Online-Ausgabe: {online_site_url}\n"
        f"Reproduzierbarer Zeitpunkt: {generated_at_iso()}\n"
    )


def _support_server() -> str:
    return '''#!/usr/bin/env python3
"""Das entpackte Cheatsheets-Offlinepaket nur lokal ausliefern."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8765

handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
server = ThreadingHTTPServer((HOST, PORT), handler)
print(f"Cheatsheets offline: http://{HOST}:{PORT}/index.html", flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
'''


def _parse_html(path: Path) -> ParsedHtml:
    parser = ReferenceParser()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeError) as exc:
        raise OfflineBuildError(f"Offline-HTML ist nicht lesbar: {path}: {exc}") from exc
    return parser.result()


def _reference_target(
    root: Path,
    source: Path,
    reference: OfflineReference,
) -> tuple[Path | None, str]:
    value = reference.value.strip()
    if not value:
        return None, ""
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise OfflineBuildError(
            f"Steuerzeichen in Offline-Link {source.relative_to(root)}: {value!r}"
        )
    if value.startswith("//") or value.startswith("\\\\"):
        raise OfflineBuildError(
            f"Protokollrelativer oder UNC-Link in {source.relative_to(root)}: {value}"
        )

    split = urlsplit(value)
    scheme = split.scheme.casefold()
    if scheme in {"http", "https", "mailto", "tel"}:
        if reference.runtime:
            raise OfflineBuildError(
                f"Externes Laufzeitasset in {source.relative_to(root)} "
                f"({reference.tag}/{reference.attribute}): {value}"
            )
        return None, ""
    if scheme == "data":
        if reference.runtime:
            return None, ""
        raise OfflineBuildError(
            f"Data-URL ist als anklickbarer Offline-Link unzulässig in "
            f"{source.relative_to(root)}: {value}"
        )
    if scheme:
        raise OfflineBuildError(
            f"Nicht unterstütztes URL-Schema in {source.relative_to(root)}: {value}"
        )

    decoded = unquote(split.path)
    fragment = unquote(split.fragment)
    if "\\" in decoded:
        raise OfflineBuildError(
            f"Backslash ist in Offline-Links nicht portabel in "
            f"{source.relative_to(root)}: {value}"
        )
    if not decoded:
        return source, fragment
    if decoded.startswith("/"):
        raise OfflineBuildError(
            f"Root-relativer Link ist offline nicht portabel in "
            f"{source.relative_to(root)}: {value}"
        )

    candidate = (source.parent / decoded).resolve(strict=False)
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise OfflineBuildError(
            f"Offline-Link verlässt den Paketroot in {source.relative_to(root)}: {value}"
        ) from exc
    if decoded.endswith("/"):
        candidate /= "index.html"
    return candidate, fragment


def validate_offline_tree(root: Path) -> dict[str, object]:
    """Prüfe Dateitypen sowie jede lokale HTML-/CSS-Referenz fail-closed."""

    root = root.resolve()
    required = [
        root / "index.html",
        root / "404.html",
        root / OFFLINE_README_NAME,
        root / OFFLINE_SERVER_NAME,
    ]
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise OfflineBuildError(
            "Offlinebaum ist unvollständig; fehlend: " + ", ".join(missing)
        )

    files = _regular_files(root)
    html_documents = {
        path.resolve(): _parse_html(path)
        for path in files
        if path.suffix.casefold() == ".html"
    }
    checked_references = 0
    external_links = 0

    for path in files:
        references: list[OfflineReference] = []
        if path.suffix.casefold() == ".html":
            references.extend(html_documents[path.resolve()].references)
        elif path.suffix.casefold() == ".css":
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise OfflineBuildError(f"Offline-CSS ist nicht lesbar: {path}: {exc}") from exc
            references.extend(
                OfflineReference("css", "url", match.group(2).strip(), True)
                for match in CSS_URL_RE.finditer(text)
            )
            references.extend(
                OfflineReference("css", "import", match.group("url"), True)
                for match in CSS_IMPORT_RE.finditer(text)
            )

        for reference in references:
            target, fragment = _reference_target(root, path, reference)
            if target is None:
                if urlsplit(reference.value).scheme.casefold() in {
                    "http",
                    "https",
                    "mailto",
                    "tel",
                }:
                    external_links += 1
                continue
            checked_references += 1
            if not target.is_file() or target.is_symlink():
                raise OfflineBuildError(
                    f"Fehlendes lokales Offlineziel in {path.relative_to(root)}: "
                    f"{reference.value}"
                )
            if fragment and target.suffix.casefold() == ".html":
                document = html_documents.get(target.resolve())
                if document is None or fragment not in document.ids:
                    raise OfflineBuildError(
                        f"Fehlender Offlineanker in {path.relative_to(root)}: "
                        f"{reference.value}"
                    )

    return {
        "bytes": sum(path.stat().st_size for path in files),
        "external_links": external_links,
        "files": len(files),
        "references": checked_references,
    }


def _entry_payloads(root: Path) -> dict[str, bytes]:
    entries: dict[str, bytes] = {}
    for path in _regular_files(root):
        relative = path.relative_to(root).as_posix()
        if relative == BUILD_SENTINEL:
            continue
        name = canonical_archive_name(relative)
        if name in entries:
            raise OfflineBuildError(f"Doppelter Offline-Archiveintrag: {name}")
        entries[name] = read_regular_file(path, root)
    return entries


def _tree_digest(entries: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name in sorted(entries, key=str.casefold):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_bytes(entries[name]).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _augment_integrity_files(
    entries: dict[str, bytes], *, source_commit: str, online_site_url: str
) -> tuple[dict[str, bytes], str]:
    if OFFLINE_CHECKSUMS_NAME in entries or OFFLINE_MANIFEST_NAME in entries:
        raise OfflineBuildError("Offlinebaum kollidiert mit reservierten Integritätsdateien")
    checksum_text = "".join(
        f"{sha256_bytes(entries[name])}  {name}\n"
        for name in sorted(entries, key=str.casefold)
    )
    entries = dict(entries)
    entries[OFFLINE_CHECKSUMS_NAME] = checksum_text.encode("utf-8")
    tree_sha256 = _tree_digest(entries)
    manifest = {
        "files": [
            {
                "bytes": len(entries[name]),
                "name": name,
                "sha256": sha256_bytes(entries[name]),
            }
            for name in sorted(entries, key=str.casefold)
        ],
        "generated_at": generated_at_iso(),
        "online_site_url": online_site_url,
        "schema_version": 1,
        "source_commit": source_commit,
        "source_date_epoch": source_date_epoch(),
        "tree_sha256": tree_sha256,
        "url_mode": "relative-html",
    }
    entries[OFFLINE_MANIFEST_NAME] = stable_json_dumps(manifest).encode("utf-8")
    return entries, tree_sha256


def _zip_timestamp_for_epoch(epoch: int) -> tuple[int, int, int, int, int, int]:
    normalized = max(epoch, ZIP_MIN_EPOCH)
    normalized -= normalized % 2
    value = datetime.fromtimestamp(normalized, tz=timezone.utc)
    return value.year, value.month, value.day, value.hour, value.minute, value.second


def _zip_timestamp() -> tuple[int, int, int, int, int, int]:
    return _zip_timestamp_for_epoch(source_date_epoch())


def render_offline_zip(entries: dict[str, bytes]) -> bytes:
    """Erzeuge ein bytegleich reproduzierbares ZIP ohne Kompressionsdrift."""

    buffer = io.BytesIO()
    seen: set[str] = set()
    timestamp = _zip_timestamp()
    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=zipfile.ZIP_STORED,
        allowZip64=True,
        strict_timestamps=False,
    ) as archive:
        for raw_name in sorted(entries, key=str.casefold):
            name = canonical_archive_name(raw_name)
            if name in seen:
                raise OfflineBuildError(f"Doppelter ZIP-Eintrag: {name}")
            seen.add(name)
            info = zipfile.ZipInfo(name, date_time=timestamp)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.extra = b""
            info.comment = b""
            archive.writestr(info, entries[raw_name])
    return buffer.getvalue()


def validate_offline_zip(payload: bytes, expected: dict[str, bytes]) -> None:
    """Lese das fertige Archiv erneut ein und vergleiche alle Bytes und Metadaten."""

    if len(payload) > 900 * 1024 * 1024:
        raise OfflineBuildError("Offline-ZIP überschreitet das Sicherheitslimit")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = archive.namelist()
            if len(names) > 20_000:
                raise OfflineBuildError("Offline-ZIP enthält zu viele Einträge")
            if names != sorted(expected, key=str.casefold):
                raise OfflineBuildError("Offline-ZIP-Reihenfolge oder Dateimenge ist instabil")
            if len(names) != len(set(names)):
                raise OfflineBuildError("Offline-ZIP enthält doppelte Einträge")
            normalized_names: set[str] = set()
            for info in archive.infolist():
                name = canonical_archive_name(info.filename)
                if name in normalized_names:
                    raise OfflineBuildError(
                        f"Offline-ZIP kollidiert nach Pfadnormalisierung: {name}"
                    )
                normalized_names.add(name)
                if info.file_size > 100 * 1024 * 1024:
                    raise OfflineBuildError(f"Offline-ZIP-Eintrag ist zu groß: {name}")
                mode = info.external_attr >> 16
                if not stat.S_ISREG(mode):
                    raise OfflineBuildError(f"Offline-ZIP enthält keinen regulären Eintrag: {name}")
                if info.compress_type != zipfile.ZIP_STORED:
                    raise OfflineBuildError(f"Offline-ZIP komprimiert unerwartet: {name}")
                if mode & 0o777 != 0o644:
                    raise OfflineBuildError(f"Offline-ZIP besitzt instabile Rechte: {name}")
                if info.date_time != _zip_timestamp():
                    raise OfflineBuildError(f"Offline-ZIP besitzt instabilen Zeitstempel: {name}")
                if archive.read(name) != expected[name]:
                    raise OfflineBuildError(f"Offline-ZIP-Inhalt weicht ab: {name}")
    except zipfile.BadZipFile as exc:
        raise OfflineBuildError("Offline-ZIP ist beschädigt") from exc


def _parse_checksum_file(payload: bytes) -> dict[str, str]:
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise OfflineBuildError("Offline-Prüfsummen sind kein gültiges UTF-8") from exc
    checksums: dict[str, str] = {}
    for line in lines:
        match = CHECKSUM_LINE_RE.fullmatch(line)
        if match is None:
            raise OfflineBuildError(f"Ungültige Offline-Prüfsummenzeile: {line!r}")
        name = canonical_archive_name(match.group("name"))
        if name in checksums:
            raise OfflineBuildError(f"Doppelte Offline-Prüfsumme: {name}")
        checksums[name] = match.group("sha")
    return checksums


def _parse_manifest(payload: bytes) -> dict[str, object]:
    try:
        manifest = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OfflineBuildError(f"Offline-Manifest ist ungültig: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise OfflineBuildError("Offline-Manifest besitzt keine unterstützte Schema-Version")
    source_commit = manifest.get("source_commit")
    if not isinstance(source_commit, str) or not (
        SOURCE_COMMIT_RE.fullmatch(source_commit) or source_commit == "unknown"
    ):
        raise OfflineBuildError("Offline-Manifest besitzt keinen gültigen Quellcommit")
    epoch = manifest.get("source_date_epoch")
    if not isinstance(epoch, int) or epoch < 0:
        raise OfflineBuildError("Offline-Manifest besitzt keinen gültigen Quellzeitpunkt")
    if manifest.get("url_mode") != "relative-html":
        raise OfflineBuildError("Offline-Manifest besitzt einen unerwarteten URL-Modus")
    return manifest


def _read_zip_entries(
    payload: bytes,
) -> tuple[dict[str, bytes], dict[str, zipfile.ZipInfo]]:
    if len(payload) > 900 * 1024 * 1024:
        raise OfflineBuildError("Offline-ZIP überschreitet das Sicherheitslimit")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = archive.namelist()
            if len(names) > 20_000:
                raise OfflineBuildError("Offline-ZIP enthält zu viele Einträge")
            if names != sorted(names, key=str.casefold) or len(names) != len(set(names)):
                raise OfflineBuildError("Offline-ZIP ist nicht eindeutig sortiert")
            entries: dict[str, bytes] = {}
            infos: dict[str, zipfile.ZipInfo] = {}
            for info in archive.infolist():
                name = canonical_archive_name(info.filename)
                if name in entries:
                    raise OfflineBuildError(
                        f"Offline-ZIP kollidiert nach Pfadnormalisierung: {name}"
                    )
                if info.file_size > 100 * 1024 * 1024:
                    raise OfflineBuildError(f"Offline-ZIP-Eintrag ist zu groß: {name}")
                mode = info.external_attr >> 16
                if not stat.S_ISREG(mode) or mode & 0o777 != 0o644:
                    raise OfflineBuildError(f"Unsicherer Offline-ZIP-Eintrag: {name}")
                if info.compress_type != zipfile.ZIP_STORED:
                    raise OfflineBuildError(f"Offline-ZIP-Eintrag ist nicht reproduzierbar: {name}")
                entries[name] = archive.read(info)
                infos[name] = info
            return entries, infos
    except zipfile.BadZipFile as exc:
        raise OfflineBuildError("Offline-ZIP ist beschädigt") from exc


def _materialize_entries(entries: dict[str, bytes], target: Path) -> dict[str, object]:
    target.mkdir(parents=True, exist_ok=False)
    for name, payload in entries.items():
        destination = target / canonical_archive_name(name)
        atomic_write_bytes(destination, payload)
    return validate_offline_tree(target)


def inspect_offline_zip(
    payload: bytes,
    *,
    extract_to: Path | None = None,
    force: bool = False,
) -> dict[str, object]:
    """Validiere ein fertiges Offline-ZIP unabhängig vom Buildprozess."""

    entries, infos = _read_zip_entries(payload)
    required = {
        "index.html",
        "404.html",
        OFFLINE_README_NAME,
        OFFLINE_SERVER_NAME,
        OFFLINE_MANIFEST_NAME,
        OFFLINE_CHECKSUMS_NAME,
    }
    missing = sorted(required - set(entries))
    if missing:
        raise OfflineBuildError("Offline-ZIP ist unvollständig; fehlend: " + ", ".join(missing))

    manifest = _parse_manifest(entries[OFFLINE_MANIFEST_NAME])
    rows = manifest.get("files")
    if not isinstance(rows, list):
        raise OfflineBuildError("Offline-Manifest besitzt keine Dateiliste")
    manifest_files: dict[str, tuple[int, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise OfflineBuildError("Offline-Manifest enthält keinen Objektdatensatz")
        name = canonical_archive_name(str(row.get("name") or ""))
        size = row.get("bytes")
        digest = row.get("sha256")
        if (
            name in manifest_files
            or not isinstance(size, int)
            or size < 0
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise OfflineBuildError(f"Ungültiger Offline-Manifestdatensatz: {name}")
        manifest_files[name] = (size, digest)

    expected_manifest_names = set(entries) - {OFFLINE_MANIFEST_NAME}
    if set(manifest_files) != expected_manifest_names:
        raise OfflineBuildError("Offline-Manifest und ZIP-Dateimenge weichen ab")
    for name, (size, digest) in manifest_files.items():
        if len(entries[name]) != size or sha256_bytes(entries[name]) != digest:
            raise OfflineBuildError(f"Offline-Manifest stimmt nicht mit ZIP-Inhalt überein: {name}")

    checksums = _parse_checksum_file(entries[OFFLINE_CHECKSUMS_NAME])
    expected_checksum_names = set(entries) - {
        OFFLINE_MANIFEST_NAME,
        OFFLINE_CHECKSUMS_NAME,
    }
    if set(checksums) != expected_checksum_names:
        raise OfflineBuildError("Offline-Prüfsummen und ZIP-Dateimenge weichen ab")
    for name, digest in checksums.items():
        if sha256_bytes(entries[name]) != digest:
            raise OfflineBuildError(f"Offline-Prüfsumme ist falsch: {name}")

    digest_entries = {
        name: content
        for name, content in entries.items()
        if name != OFFLINE_MANIFEST_NAME
    }
    tree_sha256 = _tree_digest(digest_entries)
    if manifest.get("tree_sha256") != tree_sha256:
        raise OfflineBuildError("Offline-Baumhash stimmt nicht mit dem Manifest überein")

    expected_timestamp = _zip_timestamp_for_epoch(int(manifest["source_date_epoch"]))
    for name, info in infos.items():
        if info.date_time != expected_timestamp:
            raise OfflineBuildError(f"Offline-ZIP besitzt falschen Zeitstempel: {name}")

    if extract_to is None:
        with tempfile.TemporaryDirectory(prefix="cheatsheets-offline-inspect-") as tmp:
            tree_report = _materialize_entries(entries, Path(tmp) / "site")
    else:
        extract_to = extract_to.resolve(strict=False)
        with staged_directory(
            extract_to,
            allowed_root=extract_to.parent.resolve(),
            force=force,
        ) as staging:
            for name, content in entries.items():
                atomic_write_bytes(staging / canonical_archive_name(name), content)
            tree_report = validate_offline_tree(staging)

    return {
        "archive_bytes": len(payload),
        "archive_sha256": sha256_bytes(payload),
        "files": len(entries),
        "references": tree_report["references"],
        "external_links": tree_report["external_links"],
        "schema_version": 1,
        "source_commit": manifest["source_commit"],
        "source_date_epoch": manifest["source_date_epoch"],
        "tree_sha256": tree_sha256,
        "uncompressed_bytes": sum(len(content) for content in entries.values()),
    }


def build_offline_archive(
    root: Path,
    docs_dir: Path,
    *,
    index: ContentIndex,
    nav: list[dict[str, object]],
    base_downloads: DownloadBuildResult,
    site_url: str,
    source_commit: str,
    run_mkdocs: Callable[[Path], None],
) -> OfflineBuildResult:
    """Baue Offline-HTML, kopiere Basisdownloads und liefere ZIP-Bytes zurück."""

    root = root.resolve()
    build_root = root / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cheatsheets-offline-", dir=build_root) as tmp:
        temporary = Path(tmp)
        offline_docs = temporary / "docs"
        offline_site = temporary / "site"
        config_path = temporary / "mkdocs.offline.generated.yml"
        _copy_and_rewrite_docs(docs_dir, offline_docs, index, site_url)
        write_offline_config(
            root,
            config_path,
            docs_dir=offline_docs,
            site_dir=offline_site,
            site_url=site_url,
            nav=nav,
        )
        run_mkdocs(config_path)

        from build_downloads import copy_downloads_to_site

        copy_downloads_to_site(base_downloads, offline_site)
        atomic_write_text(
            offline_site / OFFLINE_README_NAME,
            _support_readme(site_url, source_commit),
        )
        atomic_write_text(offline_site / OFFLINE_SERVER_NAME, _support_server())
        validate_offline_tree(offline_site)
        entries = _entry_payloads(offline_site)
        entries, tree_sha256 = _augment_integrity_files(
            entries,
            source_commit=source_commit,
            online_site_url=site_url,
        )
        payload = render_offline_zip(entries)
        validate_offline_zip(payload, entries)
        inspect_offline_zip(payload)
        return OfflineBuildResult(
            payload=payload,
            files=len(entries),
            uncompressed_bytes=sum(len(item) for item in entries.values()),
            tree_sha256=tree_sha256,
        )
