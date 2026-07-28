#!/usr/bin/env python3
"""Fertiges Offline-HTML-ZIP unabhängig prüfen und sicher entpacken."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from build_offline import inspect_offline_zip, read_regular_file
from download_model import DownloadBuildError
from io_utils import UnsafePathError, atomic_write_text, ensure_within, stable_json_dumps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prüft Manifest, Prüfsummen, ZIP-Metadaten und lokale Referenzen "
            "eines Cheatsheets-Offlinepakets."
        )
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("site/downloads/files/Cheatsheets-Offline-HTML.zip"),
    )
    parser.add_argument("--extract", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        archive = args.archive if args.archive.is_absolute() else root / args.archive
        archive = ensure_within(archive, root)
        payload = read_regular_file(archive, root)

        extract_to: Path | None = None
        if args.extract:
            candidate = args.extract if args.extract.is_absolute() else root / args.extract
            extract_to = ensure_within(candidate, root / "build")

        report = inspect_offline_zip(
            payload,
            extract_to=extract_to,
            force=args.force,
        )
        report["archive"] = archive.relative_to(root).as_posix()
        if extract_to is not None:
            report["extracted_to"] = extract_to.relative_to(root).as_posix()

        if args.report:
            report_path = args.report if args.report.is_absolute() else root / args.report
            report_path = ensure_within(report_path, root / "build")
            atomic_write_text(report_path, stable_json_dumps(report))

        print(
            "Offline-HTML erfolgreich geprüft: "
            f"{report['files']} Dateien, {report['references']} lokale Referenzen, "
            f"Baumhash {report['tree_sha256']}."
        )
        return 0
    except (DownloadBuildError, UnsafePathError, OSError, ValueError) as exc:
        print(f"Offline-HTML-Prüfung fehlgeschlagen: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
