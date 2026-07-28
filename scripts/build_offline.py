#!/usr/bin/env python3
"""Reproduzierbares, selbstenthaltendes Offline-HTML-Paket erzeugen."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
from typing import Callable, Iterable
from urllib.parse import unquote, urlsplit
import zipfile

import yaml

from content_model import ContentIndex
from download_model import DownloadBuildError, DownloadBuildResult, ZIP_MIN_EPOCH
from download_sources import canonical_archive_name
from io_utils import (
    atomic_write_text,
    generated_at_iso,
    sha256_bytes,
    source_date_epoch,
    stable_json_dumps,
)

OFFLINE_ARCHIVE_NAME = "Cheatsheets-Offline-HTML.zip"
OFFLINE_MANIFEST_NAME = "OFFLINE-MANIFEST.json"
OFFLINE_CHECKSUMS_NAME = "OFFLINE-SHA256SUMS.txt"
OFFLINE_README_NAME = "OFFLINE-LESEN.txt"
OFFLINE_SERVER_NAME = "offline-server.py"
BUILD_SENTINEL = ".cheatsheets-build-root"
URL_ATTRIBUTES: dict[str, tuple[str, ...]] = {
    "a": ("href",),
    "audio": ("src",),
    "embed": ("src",),
    "iframe": ("src",),
    "img": ("src", "srcset"),
    "input": ("src",),
    "link": ("href",),
    "object": ("data",),
    "script": ("src",),
    "source": ("src", "srcset"),
    "track": ("src",),
    "video": ("src", "poster"),
}
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)


class OfflineBuildError(DownloadBuildError):
    """Das Offlinepaket konnte nicht vollständig oder sicher erzeugt werden."""


@dataclass(frozen=True, slots=True)
class OfflineBuildResult:
    payload: bytes
    files: int
    uncompressed_bytes: int
    tree_sha256: str


class ReferenceParser(HTMLParser):
    """Sammle lokale und externe URL-Attribute ohne HTML umzuschreiben."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[str] = []

    @staticmethod
    def _srcset(value: str) -> Iterable[str]:
        for candidate in value.split(","):
            candidate = candidate.strip()
            if candidate:
                yield candidate.split()[0]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        names = URL_ATTRIBUTES.get(tag.casefold())
        if not names:
            return
        values = {name.casefold(): value or "" for name, value in attrs}
        for name in names:
            value = values.get(name, "").strip()
            if not value:
                continue
            if name == "srcset":
                self.references.extend(self._srcset(value))
            else:
                self.references.append(value)


def _load_base_config(root: Path) -> dict[str, object]:
    path = root / "mkdocs.yml"
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise OfflineBuildError(f"Offline-Konfiguration kann mkdocs.yml nicht lesen: {exc}") from exc
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


def _copy_and_rewrite_docs(
    source: Path,
    target: Path,
    index: ContentIndex,
    online_site_url: str,
) -> None:
    if target.exists():
        raise OfflineBuildError(f"Temporäres Offline-Docs-Ziel existiert bereits: {target}")
    shutil.copytree(source, target, symlinks=False)
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

    if not isinstance(pages, list) or not isinstance(categories, list) or not isinstance(build_info, dict):
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


def _regular_files(root: Path) -> list[Path]:
    files: list[Path] = []
    casefolded: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise OfflineBuildError(f"Offlinebaum enthält Symlink: {relative}")
        if not path.is_file():
            continue
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise OfflineBuildError(f"Offlinebaum enthält keine einfache reguläre Datei: {relative}")
        key = relative.casefold()
        previous = casefolded.get(key)
        if previous is not None and previous != relative:
            raise OfflineBuildError(
                f"Case-insensitive Pfadkollision im Offlinebaum: {previous} / {relative}"
            )
        casefolded[key] = relative
        files.append(path)
    return files


def _resolve_local_reference(root: Path, source: Path, value: str) -> Path | None:
    value = value.strip()
    if not value or value.startswith("#"):
        return None
    if value.startswith("//") or value.startswith("\\\\"):
        raise OfflineBuildError(
            f"Protokollrelativer oder UNC-Link in {source.relative_to(root)}: {value}"
        )
    split = urlsplit(value)
    scheme = split.scheme.casefold()
    if scheme in {"http", "https", "mailto", "tel"}:
        return None
    if scheme == "data":
        return None
    if scheme:
        raise OfflineBuildError(
            f"Nicht unterstütztes URL-Schema in {source.relative_to(root)}: {value}"
        )
    decoded = unquote(split.path)
    if not decoded:
        return None
    if decoded.startswith(("/", "\\")):
        raise OfflineBuildError(
            f"Root-relativer Link ist offline nicht portabel in {source.relative_to(root)}: {value}"
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
    return candidate


def validate_offline_tree(root: Path) -> dict[str, object]:
    """Prüfe Dateitypen und jede lokale HTML-/CSS-Referenz fail-closed."""

    root = root.resolve()
    required = [root / "index.html", root / "404.html", root / OFFLINE_README_NAME]
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise OfflineBuildError("Offlinebaum ist unvollständig; fehlend: " + ", ".join(missing))

    files = _regular_files(root)
    checked_references = 0
    for path in files:
        suffix = path.suffix.casefold()
        references: list[str] = []
        if suffix == ".html":
            parser = ReferenceParser()
            try:
                parser.feed(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as exc:
                raise OfflineBuildError(f"Offline-HTML ist nicht lesbar: {path}: {exc}") from exc
            references.extend(parser.references)
        elif suffix == ".css":
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise OfflineBuildError(f"Offline-CSS ist nicht lesbar: {path}: {exc}") from exc
            references.extend(match.group(2).strip() for match in CSS_URL_RE.finditer(text))

        for value in references:
            target = _resolve_local_reference(root, path, value)
            if target is None:
                continue
            checked_references += 1
            if not target.is_file() or target.is_symlink():
                raise OfflineBuildError(
                    f"Fehlendes lokales Offlineziel in {path.relative_to(root)}: {value}"
                )

    return {
        "files": len(files),
        "references": checked_references,
        "bytes": sum(path.stat().st_size for path in files),
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
        entries[name] = path.read_bytes()
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


def _zip_timestamp() -> tuple[int, int, int, int, int, int]:
    value = datetime.fromtimestamp(max(source_date_epoch(), ZIP_MIN_EPOCH), tz=timezone.utc)
    return value.year, value.month, value.day, value.hour, value.minute, value.second


def render_offline_zip(entries: dict[str, bytes]) -> bytes:
    """Erzeuge ein bytegleich reproduzierbares ZIP ohne Kompressionsdrift."""

    import io

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

    import io

    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = archive.namelist()
            if names != sorted(expected, key=str.casefold):
                raise OfflineBuildError("Offline-ZIP-Reihenfolge oder Dateimenge ist instabil")
            if len(names) != len(set(names)):
                raise OfflineBuildError("Offline-ZIP enthält doppelte Einträge")
            for info in archive.infolist():
                name = canonical_archive_name(info.filename)
                if info.compress_type != zipfile.ZIP_STORED:
                    raise OfflineBuildError(f"Offline-ZIP komprimiert unerwartet: {name}")
                if (info.external_attr >> 16) & 0o777 != 0o644:
                    raise OfflineBuildError(f"Offline-ZIP besitzt instabile Rechte: {name}")
                if info.date_time != _zip_timestamp():
                    raise OfflineBuildError(f"Offline-ZIP besitzt instabilen Zeitstempel: {name}")
                if archive.read(name) != expected[name]:
                    raise OfflineBuildError(f"Offline-ZIP-Inhalt weicht ab: {name}")
    except zipfile.BadZipFile as exc:
        raise OfflineBuildError("Offline-ZIP ist beschädigt") from exc


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
    """Baue Offline-HTML, kopiere Basisk Downloads und liefere ZIP-Bytes zurück."""

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
        return OfflineBuildResult(
            payload=payload,
            files=len(entries),
            uncompressed_bytes=sum(len(item) for item in entries.values()),
            tree_sha256=tree_sha256,
        )
