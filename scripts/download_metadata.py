#!/usr/bin/env python3
"""Downloadmanifeste, Provenienz und öffentliche Landingpage rendern."""

from __future__ import annotations

import csv
import hashlib
import html
import io
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import quote

from content_model import ContentIndex
from download_model import (
    ARTIFACT_METADATA,
    ARTIFACT_ORDER,
    OPTIONAL_ARTIFACTS,
    PRIMARY_ARTIFACTS,
    SOURCE_REPOSITORY,
    DownloadArtifact,
    DownloadBuildError,
    DownloadBuildResult,
)
from io_utils import atomic_write_text, generated_at_iso, sha256_bytes, source_date_epoch
from io_utils import stable_json_dumps


def source_tree_digest(entries: Sequence[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, payload in entries:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).hexdigest().encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def artifact_from_payload(name: str, payload: bytes) -> DownloadArtifact:
    try:
        kind, media_type, description = ARTIFACT_METADATA[name]
    except KeyError as exc:
        raise DownloadBuildError(f"Unbekannte Downloaddatei: {name}") from exc
    return DownloadArtifact(
        name=name,
        kind=kind,
        media_type=media_type,
        description=description,
        byte_size=len(payload),
        sha256=sha256_bytes(payload),
        primary=name in PRIMARY_ARTIFACTS,
    )


def ordered_artifacts(payloads: Mapping[str, bytes]) -> tuple[DownloadArtifact, ...]:
    order = {name: number for number, name in enumerate(ARTIFACT_ORDER)}
    return tuple(
        artifact_from_payload(name, payloads[name])
        for name in sorted(payloads, key=lambda item: (order.get(item, len(order)), item))
    )


def _manifest_rows(artifacts: Sequence[DownloadArtifact]) -> list[dict[str, object]]:
    actual = {artifact.name: artifact for artifact in artifacts}
    rows: list[dict[str, object]] = []
    for name in ARTIFACT_ORDER:
        if name in OPTIONAL_ARTIFACTS and name not in actual:
            continue
        kind, media_type, description = ARTIFACT_METADATA[name]
        artifact = actual.get(name)
        rows.append(
            {
                "bytes": artifact.byte_size if artifact else None,
                "description": description,
                "integrity": "embedded" if artifact else "DOWNLOAD-SHA256SUMS.txt",
                "kind": kind,
                "media_type": media_type,
                "name": name,
                "primary": name in PRIMARY_ARTIFACTS,
                "sha256": artifact.sha256 if artifact else None,
            }
        )
    return rows


def render_manifest_json(
    artifacts: Sequence[DownloadArtifact], *, source_commit: str
) -> str:
    return stable_json_dumps(
        {
            "artifacts": _manifest_rows(artifacts),
            "generated_at": generated_at_iso(),
            "integrity_note": (
                "Die Manifest- und Prüfsummendateien tragen ihren Hash nicht im "
                "eigenen Inhalt. DOWNLOAD-SHA256SUMS.txt deckt beide Manifeste und "
                "alle übrigen Artefakte ab."
            ),
            "schema_version": 1,
            "source_commit": source_commit,
            "source_repository": SOURCE_REPOSITORY,
        }
    )


def render_manifest_csv(
    artifacts: Sequence[DownloadArtifact], *, source_commit: str
) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "name",
            "kind",
            "media_type",
            "bytes",
            "sha256",
            "integrity",
            "primary",
            "source_commit",
            "generated_at",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    generated_at = generated_at_iso()
    for row in _manifest_rows(artifacts):
        writer.writerow(
            {
                "name": row["name"],
                "kind": row["kind"],
                "media_type": row["media_type"],
                "bytes": row["bytes"] if row["bytes"] is not None else "",
                "sha256": row["sha256"] or "",
                "integrity": row["integrity"],
                "primary": str(row["primary"]).lower(),
                "source_commit": source_commit,
                "generated_at": generated_at,
            }
        )
    return output.getvalue()


def render_download_checksums(payloads: Mapping[str, bytes]) -> str:
    return "".join(
        f"{sha256_bytes(payloads[name])}  {name}\n"
        for name in sorted(payloads, key=str.casefold)
        if name != "DOWNLOAD-SHA256SUMS.txt"
    )


def render_provenance(
    index: ContentIndex,
    entries: Sequence[tuple[str, bytes]],
    source_commit: str,
) -> bytes:
    return stable_json_dumps(
        {
            "categories": len(index.categories),
            "generated_at": generated_at_iso(),
            "reference_pages": len(index.reference_pages),
            "schema_version": 1,
            "source_bytes": sum(len(payload) for _name, payload in entries),
            "source_commit": source_commit,
            "source_date_epoch": source_date_epoch(),
            "source_files": len(entries),
            "source_repository": SOURCE_REPOSITORY,
            "source_tree_sha256": source_tree_digest(entries),
            "zip_compression": "stored",
        }
    ).encode("utf-8")


def _human_size(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def render_landing_page(result: DownloadBuildResult) -> str:
    lines = [
        "---\n",
        "title: Downloads & Offline\n",
        "description: Reproduzierbare Downloads mit Prüfsummen und Provenienz\n",
        "hide:\n  - feedback\n---\n\n",
        "# Downloads & Offline\n\n",
        "Alle Dateien stammen aus demselben Quellcommit und Build. Das Projekt "
        "erfasst beim Download keine zusätzlichen Nutzerdaten.\n\n",
        "## Primäre Downloads\n\n",
    ]
    for artifact in result.artifacts:
        if not artifact.primary:
            continue
        href = "files/" + quote(artifact.name, safe="._~-")
        name = html.escape(artifact.name)
        lines.extend(
            [
                f"### {name}\n\n{html.escape(artifact.description)}\n\n",
                f'<a class="md-button md-button--primary" href="{href}" download>'
                f"{name} herunterladen</a>\n\n",
                f"- **Größe:** {_human_size(artifact.byte_size)}\n",
                f"- **SHA-256:** `{artifact.sha256}`\n",
            ]
        )
        if artifact.kind == "offline-html":
            lines.extend(
                [
                    "- **Direkt:** ZIP entpacken und `index.html` öffnen.\n",
                    "- **Mit Suche und lokalen Werkzeugen:** im entpackten Ordner "
                    "`python offline-server.py` starten.\n",
                ]
            )
        lines.append("\n")

    lines.extend(
        [
            "## Manifeste, Prüfsummen und Provenienz\n\n",
            "| Datei | Zweck | Größe | SHA-256 |\n",
            "|---|---|---:|---|\n",
        ]
    )
    for artifact in result.artifacts:
        if artifact.primary:
            continue
        href = "files/" + quote(artifact.name, safe="._~-")
        lines.append(
            f'| <a href="{href}" download>{html.escape(artifact.name)}</a> | '
            f"{html.escape(artifact.description)} | {_human_size(artifact.byte_size)} | "
            f"`{artifact.sha256}` |\n"
        )

    lines.extend(
        [
            "\n## Provenienznachweis\n\n| Feld | Wert |\n|---|---|\n",
            f"| Repository | `{SOURCE_REPOSITORY}` |\n",
            f"| Quellcommit | `{result.source_commit}` |\n",
            f"| Reproduzierbarer Zeitpunkt | `{result.generated_at}` |\n",
            f"| Quelldateien im Archiv | {result.source_files} |\n",
            f"| Quellbytes im Archiv | {result.source_bytes} |\n",
            f"| Quellbaum-SHA-256 | `{result.source_tree_sha256}` |\n",
            "\n## Prüfen\n\n```bash\nsha256sum -c DOWNLOAD-SHA256SUMS.txt\n```\n\n",
            "```powershell\n",
            "Get-FileHash .\\Cheatsheets-Quellen.zip -Algorithm SHA256\n",
            "```\n\n",
            "> [!note] Selbstreferenzielle Metadaten\n",
            f"> JSON und CSV führen alle {len(result.artifacts)} Downloaddateien auf. "
            "Ihre eigenen Hashfelder bleiben leer; `DOWNLOAD-SHA256SUMS.txt` "
            "enthält die Hashwerte beider Manifeste und aller übrigen Dateien.\n",
        ]
    )
    return "".join(lines)


def write_landing_page(path: Path, result: DownloadBuildResult) -> None:
    atomic_write_text(path, render_landing_page(result))
