#!/usr/bin/env python3
"""Lokale UI-Konfiguration validieren und in den Webbuild übernehmen."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import stat

from content_model import ContentIndex
from io_utils import atomic_write_text, ensure_within, stable_json_dumps

PAGE_ID_RE = re.compile(r"^p_[0-9a-f]{16}$")
ALIASES_FILE = Path("config/page-id-aliases.json")


class UIConfigError(RuntimeError):
    """Die lokale UI-Konfiguration ist unsicher oder inkonsistent."""


def _read_regular_file_no_follow(path: Path, root: Path) -> bytes:
    root = root.resolve()
    path = ensure_within(path, root)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode):
        raise UIConfigError(f"Symbolischer Link ist als UI-Konfiguration unzulässig: {path}")
    if not stat.S_ISREG(before.st_mode):
        raise UIConfigError(f"UI-Konfiguration ist keine reguläre Datei: {path}")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise UIConfigError(f"Geöffnete UI-Konfiguration ist keine reguläre Datei: {path}")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise UIConfigError(
                f"UI-Konfiguration wurde während der Prüfung ausgetauscht: {path}"
            )
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def load_page_id_aliases(root: Path, index: ContentIndex) -> dict[str, object]:
    """Lade und prüfe explizite Migrationen alter auf aktuelle Page-IDs."""

    path = root.resolve() / ALIASES_FILE
    try:
        raw = _read_regular_file_no_follow(path, root)
    except FileNotFoundError as exc:
        raise UIConfigError(f"Page-ID-Migrationsregister fehlt: {ALIASES_FILE}") from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UIConfigError(f"Ungültiges Page-ID-Migrationsregister: {exc}") from exc
    if not isinstance(payload, dict):
        raise UIConfigError("Page-ID-Migrationsregister muss ein JSON-Objekt sein")
    unknown_keys = set(payload) - {"schema_version", "aliases"}
    if unknown_keys:
        raise UIConfigError(
            f"Unbekannte Schlüssel im Page-ID-Migrationsregister: {sorted(unknown_keys)}"
        )
    if payload.get("schema_version") != 1:
        raise UIConfigError(
            "Nicht unterstützte Version des Page-ID-Migrationsregisters: "
            f"{payload.get('schema_version')!r}"
        )

    aliases = payload.get("aliases")
    if not isinstance(aliases, dict):
        raise UIConfigError("aliases muss ein JSON-Objekt sein")

    current_ids = {page.page_id for page in index.reference_pages}
    normalized: dict[str, str] = {}
    for old_id, new_id in aliases.items():
        if not isinstance(old_id, str) or not PAGE_ID_RE.fullmatch(old_id):
            raise UIConfigError(f"Ungültige alte Page-ID: {old_id!r}")
        if not isinstance(new_id, str) or not PAGE_ID_RE.fullmatch(new_id):
            raise UIConfigError(f"Ungültige neue Page-ID für {old_id}: {new_id!r}")
        if old_id == new_id:
            raise UIConfigError(f"Selbstabbildung ist unzulässig: {old_id}")
        if old_id in current_ids:
            raise UIConfigError(
                f"Aktuelle Page-ID darf nicht als veraltet markiert werden: {old_id}"
            )
        if new_id not in current_ids:
            raise UIConfigError(
                f"Migrationsziel existiert nicht im aktuellen Fachseiteninventar: {new_id}"
            )
        normalized[old_id] = new_id

    return {
        "aliases": dict(sorted(normalized.items())),
        "schema_version": 1,
    }


def write_ui_data(staging: Path, root: Path, index: ContentIndex) -> Path:
    """Schreibe die geprüften UI-Migrationsdaten in den generierten Datenbaum."""

    payload = load_page_id_aliases(root, index)
    target = staging / "data" / "page-id-aliases.json"
    atomic_write_text(target, stable_json_dumps(payload))
    return target
