#!/usr/bin/env python3
"""Das fertige GitHub-Pages-Artefakt fail-closed validieren."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
from typing import Sequence

from io_utils import atomic_write_text, stable_json_dumps

DEFAULT_MAX_BYTES = 1_000_000_000
REQUIRED_FILES = ("index.html", "404.html")


@dataclass(frozen=True, slots=True)
class ArtifactIssue:
    code: str
    message: str
    path: str

    def format(self) -> str:
        return f"{self.path}: {self.code}: {self.message}"

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }


@dataclass(frozen=True, slots=True)
class ArtifactReport:
    site_dir: str
    files: int
    total_bytes: int
    tree_sha256: str
    issues: tuple[ArtifactIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "site_dir": self.site_dir,
            "files": self.files,
            "total_bytes": self.total_bytes,
            "tree_sha256": self.tree_sha256,
            "issues": [issue.as_dict() for issue in self.issues],
            "summary": {"errors": len(self.issues)},
        }


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_pages_artifact(
    site_dir: Path,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> ArtifactReport:
    """Prüfe Struktur, Dateitypen, Linkanzahl, Größe und Baumidentität."""

    if max_bytes < 1:
        raise ValueError("max_bytes muss mindestens 1 sein")

    requested = Path(os.path.abspath(site_dir))
    issues: list[ArtifactIssue] = []
    entries: list[tuple[str, int, str]] = []
    seen_casefold: dict[str, str] = {}
    total_bytes = 0

    try:
        root_stat = requested.lstat()
    except FileNotFoundError:
        return ArtifactReport(
            requested.as_posix(),
            0,
            0,
            hashlib.sha256(b"").hexdigest(),
            (ArtifactIssue("PA001", "Siteverzeichnis fehlt", requested.as_posix()),),
        )

    if stat.S_ISLNK(root_stat.st_mode):
        issues.append(
            ArtifactIssue("PA002", "Siteverzeichnis darf kein Symlink sein", requested.as_posix())
        )
        return ArtifactReport(
            requested.as_posix(),
            0,
            0,
            hashlib.sha256(b"").hexdigest(),
            tuple(issues),
        )
    if not stat.S_ISDIR(root_stat.st_mode):
        issues.append(
            ArtifactIssue("PA003", "Sitepfad ist kein Verzeichnis", requested.as_posix())
        )
        return ArtifactReport(
            requested.as_posix(),
            0,
            0,
            hashlib.sha256(b"").hexdigest(),
            tuple(issues),
        )

    for required in REQUIRED_FILES:
        target = requested / required
        if not target.is_file() or target.is_symlink():
            issues.append(
                ArtifactIssue("PA004", "Erforderliche HTML-Datei fehlt", required)
            )

    for directory, directories, filenames in os.walk(requested, topdown=True, followlinks=False):
        parent = Path(directory)

        safe_directories: list[str] = []
        for name in sorted(directories, key=str.casefold):
            path = parent / name
            relative = _relative(path, requested)
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                issues.append(
                    ArtifactIssue("PA005", "Symbolisches Verzeichnis ist unzulässig", relative)
                )
                continue
            if not stat.S_ISDIR(metadata.st_mode):
                issues.append(
                    ArtifactIssue("PA006", "Unerwarteter Verzeichniseintrag", relative)
                )
                continue
            safe_directories.append(name)
        directories[:] = safe_directories

        for name in sorted(filenames, key=str.casefold):
            path = parent / name
            relative = _relative(path, requested)
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                issues.append(ArtifactIssue("PA007", "Symlink ist unzulässig", relative))
                continue
            if not stat.S_ISREG(metadata.st_mode):
                issues.append(
                    ArtifactIssue("PA008", "Nur reguläre Dateien sind zulässig", relative)
                )
                continue
            if metadata.st_nlink != 1:
                issues.append(
                    ArtifactIssue(
                        "PA009",
                        f"Datei besitzt {metadata.st_nlink} Hardlinks statt genau einem",
                        relative,
                    )
                )

            folded = relative.casefold()
            previous = seen_casefold.get(folded)
            if previous is not None and previous != relative:
                issues.append(
                    ArtifactIssue(
                        "PA010",
                        f"Case-insensitive Pfadkollision mit {previous}",
                        relative,
                    )
                )
            else:
                seen_casefold[folded] = relative

            size = metadata.st_size
            total_bytes += size
            entries.append((relative, size, _hash_file(path)))

    if total_bytes > max_bytes:
        issues.append(
            ArtifactIssue(
                "PA011",
                f"Artefaktgröße {total_bytes} überschreitet das Limit {max_bytes}",
                requested.as_posix(),
            )
        )

    tree_digest = hashlib.sha256()
    for relative, size, digest in sorted(entries, key=lambda item: item[0]):
        tree_digest.update(relative.encode("utf-8"))
        tree_digest.update(b"\0")
        tree_digest.update(str(size).encode("ascii"))
        tree_digest.update(b"\0")
        tree_digest.update(digest.encode("ascii"))
        tree_digest.update(b"\n")

    return ArtifactReport(
        site_dir=requested.as_posix(),
        files=len(entries),
        total_bytes=total_bytes,
        tree_sha256=tree_digest.hexdigest(),
        issues=tuple(sorted(issues, key=lambda issue: (issue.path, issue.code))),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitHub-Pages-Artefakt validieren")
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = validate_pages_artifact(args.site_dir, max_bytes=args.max_bytes)
    except (OSError, ValueError) as exc:
        print(f"Pages-Artefaktvalidierung fehlgeschlagen: {exc}")
        return 2

    if args.report:
        atomic_write_text(args.report, stable_json_dumps(report.as_dict()))

    if not report.ok:
        print("Pages-Artefakt ist ungültig:")
        for issue in report.issues:
            print(f"- {issue.format()}")
        return 1

    print(
        "Pages-Artefakt erfolgreich validiert: "
        f"{report.files} Dateien, {report.total_bytes} Bytes, "
        f"Baum-SHA-256 {report.tree_sha256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
