from __future__ import annotations

import csv
from pathlib import Path

from conftest import manifest_row, write_manifest, write_page
from content_index import build_content_index


def make_repository(root: Path) -> Path:
    page = write_page(
        root,
        "01-Test/Alpha.md",
        title="Alpha",
        body="# Alpha\n\nText.\n",
    )
    write_page(
        root,
        "01-Test/INDEX.md",
        title="Test – Kategorienindex",
        page_type="index",
        body="# Test\n\n## Seiten\n\n- [[01-Test/Alpha|Alpha]]\n",
        extra="pages: 1\n",
    )
    write_manifest(root, [manifest_row(1, "Test", "Alpha", page, root)])
    return page


def test_manifest_hash_drift_is_reported(tmp_path: Path) -> None:
    make_repository(tmp_path)
    rows: list[dict[str, str]] = []
    with (tmp_path / "MANIFEST.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["sha256"] = "0" * 64
    write_manifest(tmp_path, rows)

    index = build_content_index(tmp_path)
    assert any(issue.code == "MF008" and "sha256" in issue.message for issue in index.issues)


def test_missing_reference_manifest_entry_is_reported(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write_manifest(tmp_path, [])
    index = build_content_index(tmp_path)
    assert any(issue.code == "MF001" for issue in index.issues)


def test_cross_page_alias_collision_is_reported(tmp_path: Path) -> None:
    first = write_page(
        tmp_path,
        "01-Test/Alpha.md",
        title="Alpha",
        aliases=("Gemeinsam",),
    )
    second = write_page(
        tmp_path,
        "01-Test/Beta.md",
        title="Beta",
        aliases=("Gemeinsam",),
    )
    write_page(
        tmp_path,
        "01-Test/INDEX.md",
        title="Test – Kategorienindex",
        page_type="index",
        body=(
            "# Test\n\n## Seiten\n\n"
            "- [[01-Test/Alpha|Alpha]]\n"
            "- [[01-Test/Beta|Beta]]\n"
        ),
        extra="pages: 2\n",
    )
    write_manifest(
        tmp_path,
        [
            manifest_row(1, "Test", "Alpha", first, tmp_path),
            manifest_row(2, "Test", "Beta", second, tmp_path),
        ],
    )
    index = build_content_index(tmp_path)
    assert any(issue.code == "NV002" for issue in index.issues)
