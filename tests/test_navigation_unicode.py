from __future__ import annotations

from pathlib import Path

from build_navigation import write_navigation_outputs
from conftest import manifest_row, write_manifest, write_page
from content_index import build_content_index


def test_alphabetical_headers_use_same_unicode_normalization_as_sorting(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fullwidth = write_page(
        tmp_path,
        "01-Test/Fullwidth.md",
        title="Ａlpha",
        body="# Ａlpha\n\nInhalt.\n",
    )
    beta = write_page(
        tmp_path,
        "01-Test/Beta.md",
        title="Beta",
        body="# Beta\n\nInhalt.\n",
    )
    write_page(
        tmp_path,
        "01-Test/INDEX.md",
        title="Test – Kategorienindex",
        page_type="index",
        body=(
            "# Test\n\n## Seiten\n\n"
            "- [[01-Test/Fullwidth|Ａlpha]]\n"
            "- [[01-Test/Beta|Beta]]\n"
        ),
        extra="pages: 2\n",
    )
    write_manifest(
        tmp_path,
        [
            manifest_row(1, "Test", "Ａlpha", fullwidth, tmp_path),
            manifest_row(2, "Test", "Beta", beta, tmp_path),
        ],
    )
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1767225600")

    index = build_content_index(tmp_path)
    output = tmp_path / "generated"
    write_navigation_outputs(
        output,
        index,
        site_url="https://example.invalid/Cheatsheets/",
        source_commit="fixture-commit",
    )
    alphabetical = (output / "index" / "alphabetisch.md").read_text(
        encoding="utf-8"
    )

    assert "## A\n\n" in alphabetical
    assert "## Ａ\n\n" not in alphabetical
    assert alphabetical.index("[Ａlpha]") < alphabetical.index("## B")
