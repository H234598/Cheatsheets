from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import sys
from typing import Iterable

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def write_page(
    root: Path,
    relative: str,
    *,
    title: str,
    page_type: str = "reference",
    status: str = "fertig",
    aliases: Iterable[str] = (),
    tags: Iterable[str] = ("test",),
    body: str = "# Test\n\nInhalt.\n",
    extra: str = "",
) -> Path:
    alias_lines = "\n".join(f"- {value}" for value in aliases)
    tag_lines = "\n".join(f"- {value}" for value in tags)
    text = (
        "---\n"
        f"title: {title}\n"
        "aliases:\n"
        f"{alias_lines}\n"
        "created: '2026-01-01'\n"
        "modified: '2026-01-01'\n"
        f"type: {page_type}\n"
        f"status: {status}\n"
        "tags:\n"
        f"{tag_lines}\n"
        f"{extra}"
        "---\n"
        f"{body}"
    )
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def manifest_row(number: int, area: str, title: str, path: Path, root: Path) -> dict[str, str]:
    payload = path.read_bytes()
    text = payload.decode("utf-8")
    return {
        "nr": str(number),
        "bereich": area,
        "title": title,
        "path": path.relative_to(root).as_posix(),
        "lines": str(len(text.splitlines())),
        "bytes": str(len(payload)),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "origin": "",
        "status": "fertig",
    }


def write_manifest(root: Path, rows: list[dict[str, str]]) -> None:
    with (root / "MANIFEST.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
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
        )
        writer.writeheader()
        writer.writerows(rows)
