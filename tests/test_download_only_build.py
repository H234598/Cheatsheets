from __future__ import annotations

from pathlib import Path

from conftest import manifest_row, write_manifest, write_page
from build_docs import build_docs
from content_index import ROOT_ROLES


def _write_publication_config(root: Path, download_name: str) -> None:
    path = root / "config" / "publication.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "schema_version: 1\n\n"
        "home: 00-START-HIER.md\n"
        "source_index: INDEX.md\n\n"
        "publish_types:\n"
        "  - reference\n"
        "  - index\n\n"
        "maintenance: []\n"
        "download_only:\n"
        f"  - {download_name}\n\n"
        "exclude_globs:\n"
        "  - build/**\n"
        "  - site/**\n"
        "  - .git/**\n"
        "  - .github/**\n"
        "  - .obsidian/**\n",
        encoding="utf-8",
    )


def test_download_only_page_tolerates_ambiguous_combined_headings(tmp_path: Path) -> None:
    alpha = write_page(
        tmp_path,
        "01-Test/Alpha.md",
        title="Alpha",
        body="# Alpha\n\nInhalt.\n",
    )
    write_page(
        tmp_path,
        "01-Test/INDEX.md",
        title="Test – Kategorienindex",
        page_type="index",
        body="# Test\n\n## Seiten\n\n- [[01-Test/Alpha|Alpha]]\n",
        extra="pages: 1\n",
    )
    write_page(
        tmp_path,
        "00-START-HIER.md",
        title="Start hier",
        body="# Start hier\n\n[[01-Test/INDEX|Zur Kategorie]]\n",
    )
    write_page(
        tmp_path,
        "INDEX.md",
        title="Quellindex",
        body="# Quellindex\n\n[[01-Test/Alpha|Alpha]]\n",
    )
    write_manifest(tmp_path, [manifest_row(1, "Test", "Alpha", alpha, tmp_path)])

    download_name = next(
        name for name, role in ROOT_ROLES.items() if role == "download-only"
    )
    write_page(
        tmp_path,
        download_name,
        title="Gesamtband",
        body=(
            "# Gesamtband\n\n"
            "- [[#Tastenkürzel]]\n\n"
            "## Tastenkürzel\n\nErster Teil.\n\n"
            "## Tastenkürzel\n\nZweiter Teil.\n"
        ),
    )
    _write_publication_config(tmp_path, download_name)

    output = tmp_path / "build" / "docs"
    result = build_docs(
        tmp_path,
        output,
        strict=True,
        site_url="https://example.invalid/Cheatsheets/",
        source_commit="fixture-commit",
    )

    generated = (output / "downloads" / download_name).read_text(encoding="utf-8")
    assert result.pages == 5
    assert 'data-link-status="ambiguous-heading"' in generated
    assert "Tastenkürzel <small>[ambiguous-heading]</small>" in generated
