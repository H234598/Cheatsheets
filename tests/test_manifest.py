from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import pytest

from build_manifest import (
    CANONICAL_FILES,
    ManifestBuildError,
    check_metadata,
    ordered_records,
)
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


def test_ordered_records_rejects_duplicate_page_ids(tmp_path: Path) -> None:
    make_repository(tmp_path)
    index = build_content_index(tmp_path)
    category_id, category = next(iter(index.categories.items()))
    duplicate_id = category.reference_page_ids[0]
    index.categories[category_id] = replace(
        category,
        reference_page_ids=category.reference_page_ids + (duplicate_id,),
    )

    with pytest.raises(ManifestBuildError, match="exakt einmal"):
        ordered_records(index)


def test_check_metadata_rejects_symlink_without_reading_target(
    tmp_path: Path,
) -> None:
    generated = {
        name: f"expected {name}\n".encode("utf-8") for name in CANONICAL_FILES
    }
    for name, payload in generated.items():
        (tmp_path / name).write_bytes(payload)

    external = tmp_path.parent / "external-sensitive-metadata.txt"
    external.write_text("DO_NOT_LEAK_THIS_SECRET\n", encoding="utf-8")
    link = tmp_path / "BUILD-REPORT.yaml"
    link.unlink()
    try:
        link.symlink_to(external)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlinks werden auf dieser Plattform nicht unterstützt: {exc}")

    differences = check_metadata(tmp_path, generated)
    report = "".join(differences)

    assert "BUILD-REPORT.yaml" in report
    assert "symbolischer Link" in report
    assert "DO_NOT_LEAK_THIS_SECRET" not in report
