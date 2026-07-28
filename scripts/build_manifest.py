#!/usr/bin/env python3
"""Kanonische Manifestansichten aus den realen Fachseiten reproduzieren.

Die gestreamte Hash- und Manifestidee ist aus den Exportskripten von
``H234598/ADHS-Lernpfad`` am Commit
``93c8c02d263ec123c1c271caf0d2deaa76760ccb`` abgeleitet. Datensätze,
atomare Schreibvorgänge und vollständige Fehlerzusammenfassungen folgen den
Mustern aus ``H234598/desinfect`` am Commit
``fbcc6e850fec1f4592ca519fa3e5141b11a95e60``.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import difflib
import hashlib
import io
from pathlib import Path
import sys
from typing import Sequence

import yaml

from content_index import build_content_index
from content_model import ContentIndex, PageRecord
from io_utils import atomic_write_bytes, ensure_within

CANONICAL_FILES = (
    "MANIFEST.csv",
    "MANIFEST.md",
    "BUILD-REPORT.yaml",
    "SHA256SUMS.txt",
)


class ManifestBuildError(RuntimeError):
    """Die kanonischen Metadaten konnten nicht sicher erzeugt werden."""


@dataclass(frozen=True, slots=True)
class ManifestRecord:
    number: int
    area: str
    page: PageRecord


def ordered_records(index: ContentIndex) -> list[ManifestRecord]:
    records: list[ManifestRecord] = []
    number = 1
    for category in sorted(index.categories.values(), key=lambda item: item.number):
        for page_id in category.reference_page_ids:
            page = index.pages.get(page_id)
            if page is None or not page.is_reference:
                raise ManifestBuildError(
                    f"Kategorie {category.category_id} enthält keine gültige Fachseite: {page_id}"
                )
            records.append(ManifestRecord(number, category.title, page))
            number += 1
    if {record.page.page_id for record in records} != {
        page.page_id for page in index.reference_pages
    }:
        raise ManifestBuildError("Manifestreihenfolge deckt nicht alle Fachseiten exakt einmal ab")
    return records


def render_manifest_csv(records: list[ManifestRecord]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "nr",
            "bereich",
            "title",
            "path",
            "lines",
            "bytes",
            "sha256",
            "origin",
            "status",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    for record in records:
        page = record.page
        writer.writerow(
            {
                "nr": record.number,
                "bereich": record.area,
                "title": page.title,
                "path": page.relative_path.as_posix(),
                "lines": page.line_count,
                "bytes": page.byte_size,
                "sha256": page.source_sha256,
                "origin": page.origin or "",
                "status": page.status,
            }
        )
    return output.getvalue()


def render_manifest_markdown(records: list[ManifestRecord]) -> str:
    total_lines = sum(record.page.line_count for record in records)
    total_bytes = sum(record.page.byte_size for record in records)
    lines = [
        "---\n",
        "title: Cheatsheets – Manifest\n",
        "type: index\n",
        "status: fertig\n",
        f"pages: {len(records)}\n",
        "---\n\n",
        "# Manifest\n\n",
        "Diese Datei wird deterministisch aus den realen Fachseiten, ihren Kategorieindizes und dem strukturierten Frontmatter erzeugt.\n\n",
        f"- **Fachseiten:** {len(records)}\n",
        f"- **Zeilen:** {total_lines}\n",
        f"- **Bytes:** {total_bytes}\n\n",
        "| Nr. | Bereich | Titel | Pfad | Zeilen | Bytes | Status |\n",
        "|---:|---|---|---|---:|---:|---|\n",
    ]
    for record in records:
        page = record.page
        title = page.title.replace("|", "\\|")
        area = record.area.replace("|", "\\|")
        path = page.relative_path.as_posix().replace("|", "\\|")
        lines.append(
            f"| {record.number} | {area} | {title} | `{path}` | "
            f"{page.line_count} | {page.byte_size} | {page.status} |\n"
        )
    lines.append("\n")
    return "".join(lines)


def _content_date(records: list[ManifestRecord]) -> str | None:
    values: list[str] = []
    for record in records:
        modified = record.page.metadata.get("modified")
        if isinstance(modified, str) and modified.strip():
            values.append(modified.strip())
    return max(values) if values else None


def _content_fingerprint(records: list[ManifestRecord]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(record.page.relative_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(record.page.source_sha256.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def render_build_report(index: ContentIndex, records: list[ManifestRecord]) -> str:
    payload = {
        "schema_version": 1,
        "content_date": _content_date(records),
        "content_fingerprint_sha256": _content_fingerprint(records),
        "categories": len(index.categories),
        "reference_pages": len(records),
        "total_lines": sum(record.page.line_count for record in records),
        "total_bytes": sum(record.page.byte_size for record in records),
        "statuses": {
            status: sum(record.page.status == status for record in records)
            for status in sorted({record.page.status for record in records})
        },
        "category_pages": {
            category.title: len(category.reference_page_ids)
            for category in sorted(index.categories.values(), key=lambda item: item.number)
        },
    }
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=100)


def _checksum_sources(
    index: ContentIndex,
    generated: dict[str, bytes],
) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    excluded = {"MANIFEST.md"}
    published_roles = {
        "reference",
        "category-index",
        "root-landing",
        "root-index",
        "root-readme",
        "maintenance",
        "download-only",
    }
    for page in sorted(index.pages.values(), key=lambda item: item.relative_path.as_posix()):
        relative = page.relative_path.as_posix()
        if page.page_type not in published_roles or relative in excluded:
            continue
        entries.append((relative, page.source_sha256))
    for name in ("MANIFEST.csv", "MANIFEST.md", "BUILD-REPORT.yaml"):
        payload = generated[name]
        entries.append((name, hashlib.sha256(payload).hexdigest()))
    return sorted(entries, key=lambda item: item[0].casefold())


def render_checksums(index: ContentIndex, generated: dict[str, bytes]) -> str:
    return "".join(
        f"{digest}  {path}\n" for path, digest in _checksum_sources(index, generated)
    )


def generate_metadata(root: Path) -> dict[str, bytes]:
    index = build_content_index(root)
    blocking = [
        issue
        for issue in index.issues
        if issue.severity == "error" and not issue.code.startswith("MF")
    ]
    if blocking:
        preview = "\n".join(issue.format() for issue in blocking[:25])
        raise ManifestBuildError(f"Contentmodell ist außerhalb des Manifests ungültig:\n{preview}")
    records = ordered_records(index)
    generated = {
        "MANIFEST.csv": render_manifest_csv(records).encode("utf-8"),
        "MANIFEST.md": render_manifest_markdown(records).encode("utf-8"),
        "BUILD-REPORT.yaml": render_build_report(index, records).encode("utf-8"),
    }
    generated["SHA256SUMS.txt"] = render_checksums(index, generated).encode("utf-8")
    return generated


def write_metadata(output: Path, generated: dict[str, bytes]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name in CANONICAL_FILES:
        atomic_write_bytes(output / name, generated[name])


def _diff_text(name: str, expected: bytes, actual: bytes) -> str:
    try:
        expected_text = expected.decode("utf-8").splitlines(keepends=True)
        actual_text = actual.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return f"{name}: Binärinhalt weicht ab\n"
    return "".join(
        difflib.unified_diff(
            actual_text,
            expected_text,
            fromfile=f"a/{name}",
            tofile=f"b/{name}",
            n=3,
        )
    )


def check_metadata(root: Path, generated: dict[str, bytes]) -> list[str]:
    differences: list[str] = []
    for name in CANONICAL_FILES:
        path = root / name
        if not path.is_file():
            differences.append(f"{name}: Datei fehlt\n")
            continue
        actual = path.read_bytes()
        if actual != generated[name]:
            differences.append(_diff_text(name, generated[name], actual))
    return differences


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Erzeugt oder prüft MANIFEST.*, BUILD-REPORT.yaml und SHA256SUMS.txt."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("build/metadata"))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--update-committed", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check and args.update_committed:
        print("--check und --update-committed sind unvereinbar", file=sys.stderr)
        return 2
    root = args.root.resolve()
    try:
        generated = generate_metadata(root)
        if args.check:
            differences = check_metadata(root, generated)
            if differences:
                print("\n".join(differences), file=sys.stderr)
                return 2
            print("Kanonische Metadaten sind reproduzierbar und aktuell.")
            return 0
        target = root if args.update_committed else (
            args.output if args.output.is_absolute() else root / args.output
        )
        if not args.update_committed:
            target = ensure_within(target, root)
        write_metadata(target, generated)
        mode = "kanonisch aktualisiert" if args.update_committed else f"nach {target} geschrieben"
        print(f"Metadaten {mode}: {', '.join(CANONICAL_FILES)}")
        return 0
    except (ManifestBuildError, OSError, ValueError) as exc:
        print(f"Manifestbuild fehlgeschlagen: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
