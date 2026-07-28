#!/usr/bin/env python3
"""Datentypen und feste Verträge der reproduzierbaren Downloadpipeline."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

SOURCE_REPOSITORY = "H234598/Cheatsheets"
SOURCE_ROLES = {
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
READ_CHUNK_SIZE = 1024 * 1024
ZIP_MIN_EPOCH = 315532800  # 1980-01-01T00:00:00Z, frühestes ZIP-Datum.
PRIMARY_ARTIFACTS = {
    "Cheatsheets-Quellen.zip",
    "Cheatsheets-Offline-HTML.zip",
    "Cheatsheet-Gesamtband.md",
}
OPTIONAL_ARTIFACTS = {"Cheatsheets-Offline-HTML.zip"}
ARTIFACT_METADATA: dict[str, tuple[str, str, str]] = {
    "Cheatsheets-Quellen.zip": (
        "source-archive",
        "application/zip",
        "Obsidian-taugliches Archiv der kanonischen Inhaltsquellen und Inhaltsassets.",
    ),
    "Cheatsheets-Offline-HTML.zip": (
        "offline-html",
        "application/zip",
        "Selbstenthaltende HTML-Ausgabe mit relativen Links, lokaler Suche und file://-Fallback.",
    ),
    "Cheatsheet-Gesamtband.md": (
        "combined-markdown",
        "text/markdown; charset=utf-8",
        "Aus allen Fachseiten in kanonischer Kategorienreihenfolge erzeugtes Gesamt-Markdown.",
    ),
    "MANIFEST.csv": (
        "source-metadata",
        "text/csv; charset=utf-8",
        "Maschinenlesbares Fachseitenmanifest.",
    ),
    "MANIFEST.md": (
        "source-metadata",
        "text/markdown; charset=utf-8",
        "Menschenlesbare Manifestansicht.",
    ),
    "BUILD-REPORT.yaml": (
        "source-metadata",
        "application/yaml; charset=utf-8",
        "Reproduzierbarer Bericht über Umfang und Inhaltsfingerabdruck.",
    ),
    "SOURCE-SHA256SUMS.txt": (
        "source-integrity",
        "text/plain; charset=utf-8",
        "SHA-256-Prüfsummen der veröffentlichten kanonischen Quellen.",
    ),
    "PROVENANCE.json": (
        "provenance",
        "application/json; charset=utf-8",
        "Quellcommit, Buildzeitpunkt und Inhaltsumfang dieses Artefaktsatzes.",
    ),
    "DOWNLOAD-MANIFEST.json": (
        "download-metadata",
        "application/json; charset=utf-8",
        "JSON-Manifest der primären und abgeleiteten Downloadartefakte.",
    ),
    "DOWNLOAD-MANIFEST.csv": (
        "download-metadata",
        "text/csv; charset=utf-8",
        "CSV-Manifest der primären und abgeleiteten Downloadartefakte.",
    ),
    "DOWNLOAD-SHA256SUMS.txt": (
        "download-integrity",
        "text/plain; charset=utf-8",
        "SHA-256-Prüfsummen aller Downloaddateien außer dieser Prüfsummendatei.",
    ),
}
ARTIFACT_ORDER = tuple(ARTIFACT_METADATA)


class DownloadBuildError(RuntimeError):
    """Downloadartefakte konnten nicht vollständig oder sicher erzeugt werden."""


@dataclass(frozen=True, slots=True)
class DownloadArtifact:
    name: str
    kind: str
    media_type: str
    description: str
    byte_size: int
    sha256: str
    primary: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "bytes": self.byte_size,
            "description": self.description,
            "kind": self.kind,
            "media_type": self.media_type,
            "name": self.name,
            "primary": self.primary,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class DownloadBuildResult:
    output: Path
    artifacts: tuple[DownloadArtifact, ...]
    source_commit: str
    generated_at: str
    source_files: int
    source_bytes: int
    source_tree_sha256: str


def detect_source_commit(root: Path) -> str:
    """Ermittle den Quellcommit aus CI oder dem lokalen Git-Checkout."""

    github_sha = os.environ.get("GITHUB_SHA", "").strip()
    if re.fullmatch(r"[0-9a-fA-F]{40}", github_sha):
        return github_sha.lower()
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unknown"
    candidate = completed.stdout.strip()
    return candidate.lower() if re.fullmatch(r"[0-9a-fA-F]{40}", candidate) else "unknown"
