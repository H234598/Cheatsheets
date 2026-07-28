#!/usr/bin/env python3
"""Quellinventar, Gesamt-Markdown und deterministisches ZIP für Downloads."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Mapping, Sequence
import zipfile

from build_manifest import ordered_records
from content_model import (
    CATEGORY_RE,
    FRONTMATTER_RE,
    ContentIndex,
    FenceState,
    PageRecord,
    advance_fence_state,
    normalize_posix_path,
)
from download_model import (
    DownloadBuildError,
    READ_CHUNK_SIZE,
    SOURCE_EXCLUDED_PARTS,
    SOURCE_ROLES,
    ZIP_MIN_EPOCH,
)
from io_utils import sha256_bytes, source_date_epoch, stable_json_dumps, generated_at_iso
from link_converters import convert_for_combined


def _read_regular_source(path: Path, root: Path) -> bytes:
    root = root.resolve()
    absolute = Path(os.path.abspath(path))
    try:
        absolute.relative_to(root)
        absolute.parent.resolve().relative_to(root)
    except ValueError as exc:
        raise DownloadBuildError(f"Quellpfad verlässt die Repositorywurzel: {path}") from exc

    before = absolute.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise DownloadBuildError(f"Quellpfad ist keine reguläre Datei: {path}")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(absolute, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise DownloadBuildError(f"Geöffneter Quellpfad ist nicht regulär: {path}")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise DownloadBuildError(f"Quellpfad wurde während des Lesens ausgetauscht: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, READ_CHUNK_SIZE):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _content_asset_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(
        root.rglob("*"),
        key=lambda item: normalize_posix_path(item.relative_to(root)).casefold(),
    ):
        relative = path.relative_to(root)
        is_content_asset = relative.parts and (
            CATEGORY_RE.match(relative.parts[0])
            or relative.parts[0] in {"assets", "media"}
        )
        if path.is_symlink():
            if is_content_asset:
                raise DownloadBuildError(
                    f"Inhaltsasset darf kein Symlink sein: {relative.as_posix()}"
                )
            continue
        if not path.is_file() or path.suffix.lower() == ".md":
            continue
        if any(part in SOURCE_EXCLUDED_PARTS for part in relative.parts):
            continue
        if is_content_asset:
            paths.append(path)
    return paths


def source_entries(
    root: Path,
    index: ContentIndex,
    generated_metadata: Mapping[str, bytes],
) -> list[tuple[str, bytes]]:
    entries: dict[str, bytes] = {}
    for page in index.pages.values():
        if page.page_type in SOURCE_ROLES:
            entries[page.relative_path.as_posix()] = _read_regular_source(
                page.source_path, root
            )

    for path in _content_asset_paths(root):
        entries[path.relative_to(root).as_posix()] = _read_regular_source(path, root)
    for name in ("MANIFEST.csv", "MANIFEST.md", "BUILD-REPORT.yaml"):
        entries[name] = generated_metadata[name]

    license_path = root / "LICENSE"
    if license_path.exists():
        entries["LICENSE"] = _read_regular_source(license_path, root)

    for name in entries:
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or name.startswith("/"):
            raise DownloadBuildError(f"Unsicherer Archivpfad: {name}")

    ordered = sorted(
        entries.items(), key=lambda item: normalize_posix_path(item[0]).casefold()
    )
    checksum = "".join(
        f"{sha256_bytes(payload)}  {name}\n" for name, payload in ordered
    ).encode("utf-8")
    ordered.append(("SOURCE-SHA256SUMS.txt", checksum))
    return sorted(ordered, key=lambda item: normalize_posix_path(item[0]).casefold())


def render_source_zip(entries: Sequence[tuple[str, bytes]]) -> bytes:
    """Erzeuge ein plattformunabhängiges, unkomprimiertes und stabiles ZIP."""

    epoch = max(source_date_epoch(), ZIP_MIN_EPOCH)
    value = datetime.fromtimestamp(epoch, tz=timezone.utc)
    date_time = (value.year, value.month, value.day, value.hour, value.minute, value.second)
    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=zipfile.ZIP_STORED,
        allowZip64=True,
        strict_timestamps=False,
    ) as archive:
        for name, payload in entries:
            info = zipfile.ZipInfo(filename=name, date_time=date_time)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.extra = b""
            info.comment = b""
            archive.writestr(info, payload)
    return buffer.getvalue()


def _fenced_segment_hashes(text: str) -> tuple[str, ...]:
    fence: FenceState | None = None
    current: list[str] = []
    hashes: list[str] = []
    for line in text.splitlines(keepends=True):
        previous = fence
        fence, is_fenced = advance_fence_state(line, fence)
        if not is_fenced:
            continue
        current.append(line)
        if previous is not None and fence is None:
            hashes.append(hashlib.sha256("".join(current).encode("utf-8")).hexdigest())
            current = []
    if current:
        hashes.append(hashlib.sha256("".join(current).encode("utf-8")).hexdigest())
    return tuple(hashes)


def _body_without_title(page: PageRecord) -> str:
    match = FRONTMATTER_RE.match(page.raw_text)
    text = page.raw_text[match.end() :] if match else page.raw_text
    fence: FenceState | None = None
    output: list[str] = []
    removed = False
    for line in text.splitlines(keepends=True):
        fence, is_fenced = advance_fence_state(line, fence)
        heading = re.match(r"^ {0,3}#\s+(.+?)\s*(?:\r?\n)?$", line)
        if not removed and not is_fenced and heading:
            if heading.group(1).strip() == page.title.strip():
                removed = True
                continue
        output.append(line)
    return "".join(output)


def render_combined_markdown(index: ContentIndex, source_commit: str) -> str:
    records = ordered_records(index)
    included = {record.page.source_path.resolve() for record in records}
    lines = [
        "---\n",
        'title: "Cheatsheet-Gesamtband"\n',
        "type: reference\n",
        "status: generated\n",
        f"pages: {len(records)}\n",
        f"source_commit: {stable_json_dumps(source_commit).strip()}\n",
        f"generated_at: {stable_json_dumps(generated_at_iso()).strip()}\n",
        "---\n\n# Cheatsheet-Gesamtband\n\n",
        "> [!abstract] Reproduzierbares Gesamtband\n",
        "> Aus den kanonischen Fachseiten desselben Commits erzeugt.\n\n",
        "## Inhaltsverzeichnis\n\n",
    ]
    current_area = ""
    for record in records:
        if record.area != current_area:
            current_area = record.area
            lines.append(f"### {current_area}\n\n")
        lines.append(f"- [{record.number}. {record.page.title}](#{record.page.page_id})\n")

    for record in records:
        page = record.page
        converted = convert_for_combined(
            _body_without_title(page),
            page.source_path,
            index.root,
            included,
            index=index,
        )
        if _fenced_segment_hashes(page.raw_text) != _fenced_segment_hashes(converted):
            raise DownloadBuildError(
                "Geschützte Codefences wurden im Gesamtband verändert: "
                f"{page.relative_path.as_posix()}"
            )
        anchor, separator, remainder = converted.partition("\n")
        if not separator or anchor != f"[]{{#{page.page_id}}}":
            raise DownloadBuildError(
                f"Gesamtbandanker fehlt: {page.relative_path.as_posix()}"
            )
        lines.extend(
            [
                "\n---\n\n",
                f"{anchor}\n## {record.number}. {page.title}\n\n",
                f"- **Kategorie:** {record.area}\n",
                f"- **Quellpfad:** `{page.relative_path.as_posix()}`\n",
                f"- **Quell-SHA-256:** `{page.source_sha256}`\n\n",
                remainder,
            ]
        )
        if not remainder.endswith("\n"):
            lines.append("\n")
    return "".join(lines)
