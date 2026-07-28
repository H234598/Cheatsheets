#!/usr/bin/env python3
"""Reproduzierbare Downloadartefakte, Prüfsummen und Provenienz erzeugen.

Die ZIP-, Hash- und Manifestidee stammt aus ``H234598/ADHS-Lernpfad`` am
Commit ``93c8c02d263ec123c1c271caf0d2deaa76760ccb``. Sichere Dateizugriffe und
atomare Ausgaben folgen ``H234598/desinfect`` am Commit
``fbcc6e850fec1f4592ca519fa3e5141b11a95e60``.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
import re
import shutil
import sys
from typing import Sequence
import zipfile

from build_manifest import generate_metadata
from content_index import build_content_index
from content_model import ContentIndex
from download_metadata import (
    ordered_artifacts,
    render_download_checksums,
    render_manifest_csv,
    render_manifest_json,
    render_provenance,
    source_tree_digest,
    write_landing_page,
)
from download_model import (
    ARTIFACT_METADATA,
    DownloadBuildError,
    DownloadBuildResult,
    detect_source_commit,
)
from download_sources import render_combined_markdown, render_source_zip, source_entries
from io_utils import (
    UnsafePathError,
    atomic_write_bytes,
    generated_at_iso,
    sha256_bytes,
    staged_directory,
)


def _validate_index(index: ContentIndex) -> None:
    errors = [issue.format() for issue in index.issues if issue.severity == "error"]
    if errors:
        preview = "\n".join(errors[:25])
        suffix = f"\n… und {len(errors) - 25} weitere" if len(errors) > 25 else ""
        raise DownloadBuildError(f"Contentmodell ist ungültig:\n{preview}{suffix}")


def _merge_extra_payloads(
    payloads: dict[str, bytes], extra_payloads: Mapping[str, bytes] | None
) -> None:
    for name, payload in (extra_payloads or {}).items():
        if name not in ARTIFACT_METADATA:
            raise DownloadBuildError(f"Unbekanntes zusätzliches Downloadartefakt: {name}")
        if name in payloads:
            raise DownloadBuildError(f"Doppeltes zusätzliches Downloadartefakt: {name}")
        if not isinstance(payload, bytes):
            raise DownloadBuildError(f"Downloadartefakt muss Bytes enthalten: {name}")
        payloads[name] = payload


def prepare_payloads(
    root: Path,
    index: ContentIndex,
    *,
    source_commit: str,
    extra_payloads: Mapping[str, bytes] | None = None,
) -> tuple[dict[str, bytes], list[tuple[str, bytes]]]:
    generated = generate_metadata(root)
    entries = source_entries(root, index, generated)
    payloads: dict[str, bytes] = {
        "Cheatsheets-Quellen.zip": render_source_zip(entries),
        "Cheatsheet-Gesamtband.md": render_combined_markdown(
            index, source_commit
        ).encode("utf-8"),
        "MANIFEST.csv": generated["MANIFEST.csv"],
        "MANIFEST.md": generated["MANIFEST.md"],
        "BUILD-REPORT.yaml": generated["BUILD-REPORT.yaml"],
        "SOURCE-SHA256SUMS.txt": dict(entries)["SOURCE-SHA256SUMS.txt"],
        "PROVENANCE.json": render_provenance(index, entries, source_commit),
    }
    _merge_extra_payloads(payloads, extra_payloads)
    listed = ordered_artifacts(payloads)
    payloads["DOWNLOAD-MANIFEST.json"] = render_manifest_json(
        listed, source_commit=source_commit
    ).encode("utf-8")
    payloads["DOWNLOAD-MANIFEST.csv"] = render_manifest_csv(
        listed, source_commit=source_commit
    ).encode("utf-8")
    payloads["DOWNLOAD-SHA256SUMS.txt"] = render_download_checksums(payloads).encode(
        "utf-8"
    )
    return payloads, entries


def build_downloads(
    root: Path,
    output: Path,
    *,
    index: ContentIndex | None = None,
    source_commit: str | None = None,
    strict: bool = True,
    force: bool = False,
    extra_payloads: Mapping[str, bytes] | None = None,
) -> DownloadBuildResult:
    """Erzeuge den vollständigen Downloadsatz atomar unter *output*."""

    root = root.resolve()
    output = output.resolve(strict=False)
    index = index or build_content_index(root)
    _validate_index(index)
    source_commit = (source_commit or detect_source_commit(root)).strip().lower()
    if strict and not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise DownloadBuildError(
            "Ein strenger Downloadbuild benötigt einen vollständigen Quellcommit"
        )
    source_commit = source_commit or "unknown"
    payloads, entries = prepare_payloads(
        root,
        index,
        source_commit=source_commit,
        extra_payloads=extra_payloads,
    )
    artifacts = ordered_artifacts(payloads)

    with staged_directory(output, allowed_root=output.parent.resolve(), force=force) as staging:
        for artifact in artifacts:
            atomic_write_bytes(staging / artifact.name, payloads[artifact.name])

    return DownloadBuildResult(
        output=output,
        artifacts=artifacts,
        source_commit=source_commit,
        generated_at=generated_at_iso(),
        source_files=len(entries),
        source_bytes=sum(len(payload) for _name, payload in entries),
        source_tree_sha256=source_tree_digest(entries),
    )


def copy_downloads_to_site(result: DownloadBuildResult, site_root: Path) -> None:
    target = site_root / "downloads" / "files"
    target.mkdir(parents=True, exist_ok=True)
    for artifact in result.artifacts:
        source = result.output / artifact.name
        destination = target / artifact.name
        if source.is_symlink() or not source.is_file():
            raise DownloadBuildError(f"Downloadquelle ist nicht regulär: {source}")
        shutil.copyfile(source, destination)
        payload = destination.read_bytes()
        if len(payload) != artifact.byte_size or sha256_bytes(payload) != artifact.sha256:
            raise DownloadBuildError(
                f"Downloadartefakt beim Site-Kopieren verändert: {artifact.name}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Erzeugt reproduzierbare Cheatsheet-Downloads und Provenienzdaten."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("build/downloads"))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.check:
            import tempfile

            with tempfile.TemporaryDirectory(prefix="cheatsheets-download-check-") as tmp:
                result = build_downloads(
                    root,
                    Path(tmp) / "downloads",
                    source_commit=args.source_commit,
                    strict=True,
                    force=True,
                )
        else:
            output = args.output if args.output.is_absolute() else root / args.output
            result = build_downloads(
                root,
                output,
                source_commit=args.source_commit,
                strict=args.strict,
                force=args.force,
            )
        print(
            f"Downloadbuild erfolgreich: {len(result.artifacts)} Dateien, "
            f"{result.source_files} Quellen, Quellbaum {result.source_tree_sha256}."
        )
        return 0
    except (DownloadBuildError, UnsafePathError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Downloadbuild fehlgeschlagen: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
