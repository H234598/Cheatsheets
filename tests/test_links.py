from __future__ import annotations

from pathlib import Path

import pytest

from conftest import manifest_row, write_manifest, write_page
from content_index import ROOT_ROLES, build_content_index
from link_converters import convert_for_web
from link_resolution import resolve_occurrence
from link_types import LinkError, LinkOccurrence, scan_wikilinks, split_link


def make_link_repository(root: Path, *, duplicate_alias: bool = False) -> tuple[Path, Path]:
    first = write_page(
        root,
        "01-Test/Alpha.md",
        title="Alpha",
        aliases=("Gemeinsam",) if duplicate_alias else ("Erstes Blatt",),
        body=(
            "# Alpha\n\n"
            "## Diagnose\n\n"
            "Siehe [[Beta#Details|Details von Beta]].\n"
        ),
    )
    second = write_page(
        root,
        "01-Test/Beta.md",
        title="Beta",
        aliases=("Gemeinsam",) if duplicate_alias else ("Zweites Blatt",),
        body="# Beta\n\n## Details\n\nText.\n",
    )
    write_page(
        root,
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
        root,
        [
            manifest_row(1, "Test", "Alpha", first, root),
            manifest_row(2, "Test", "Beta", second, root),
        ],
    )
    return first, second


def occurrence(
    source: Path,
    target: str,
    *,
    heading: str | None = None,
    embed: bool = False,
) -> LinkOccurrence:
    raw = f"{'!' if embed else ''}[[{target}{'#' + heading if heading else ''}]]"
    return LinkOccurrence(
        source=source,
        raw=raw,
        target=target,
        heading=heading,
        label=heading or Path(target).stem or "Link",
        embed=embed,
        line=1,
        column=1,
        start=0,
        end=len(raw),
    )


def test_split_link_supports_heading_alias_and_local_anchor() -> None:
    assert split_link("Beta#Details|Mehr") == ("Beta", "Details", "Mehr")
    assert split_link("#Diagnose") == ("", "Diagnose", "Diagnose")


def test_scanner_ignores_protected_markdown_regions() -> None:
    text = (
        "---\nalias: '[[Frontmatter]]'\n---\n"
        "[[Echt]]\n"
        "`[[Inline]]`\n"
        "<!-- [[Kommentar]] -->\n"
        "    [[Eingerueckt]]\n"
        "````markdown\n[[Fence]]\n```\n````\n"
        "[[Auch echt|Label]]\n"
    )
    found = scan_wikilinks(text, Path("Quelle.md"))
    assert [(item.target, item.label) for item in found] == [
        ("Echt", "Echt"),
        ("Auch echt", "Label"),
    ]


def test_resolves_relative_alias_heading_and_local_anchor(tmp_path: Path) -> None:
    alpha, beta = make_link_repository(tmp_path)
    index = build_content_index(tmp_path)

    direct = resolve_occurrence(index, occurrence(alpha, "Beta"))
    assert direct.ok and direct.page and direct.page.source_path == beta

    alias = resolve_occurrence(index, occurrence(alpha, "Zweites Blatt"))
    assert alias.ok and alias.page and alias.page.source_path == beta

    heading = resolve_occurrence(index, occurrence(alpha, "Beta", heading="Details"))
    assert heading.ok and heading.anchor == "details"

    local = resolve_occurrence(index, occurrence(alpha, "", heading="Diagnose"))
    assert local.ok and local.page and local.page.source_path == alpha
    assert local.anchor == "diagnose"


def test_case_mismatch_and_missing_targets_are_errors(tmp_path: Path) -> None:
    alpha, _beta = make_link_repository(tmp_path)
    index = build_content_index(tmp_path)
    mismatch = resolve_occurrence(index, occurrence(alpha, "beta"))
    assert mismatch.status == "case-mismatch"
    missing = resolve_occurrence(index, occurrence(alpha, "Nicht da"))
    assert missing.status == "missing-document"


def test_ambiguous_alias_and_path_escape_are_rejected(tmp_path: Path) -> None:
    alpha, _beta = make_link_repository(tmp_path, duplicate_alias=True)
    index = build_content_index(tmp_path)
    ambiguous = resolve_occurrence(index, occurrence(alpha, "Gemeinsam"))
    assert ambiguous.status == "ambiguous"
    escaped = resolve_occurrence(index, occurrence(alpha, "../../../etc/passwd"))
    assert escaped.status == "malformed"


def test_images_are_embeddable_but_markdown_transclusion_is_not(tmp_path: Path) -> None:
    alpha, _beta = make_link_repository(tmp_path)
    image = tmp_path / "01-Test" / "bild.png"
    image.write_bytes(b"not-a-real-image")
    index = build_content_index(tmp_path)

    image_resolution = resolve_occurrence(
        index, occurrence(alpha, "bild.png", embed=True)
    )
    assert image_resolution.ok and image_resolution.path == image

    page_resolution = resolve_occurrence(index, occurrence(alpha, "Beta", embed=True))
    assert page_resolution.status == "unsupported-embed"


def test_web_conversion_uses_generated_relative_paths_and_preserves_fences(
    tmp_path: Path,
) -> None:
    alpha, _beta = make_link_repository(tmp_path)
    index = build_content_index(tmp_path)
    text = (
        "Siehe [[Beta#Details|Details]].\n\n"
        "````markdown\n[[Beta#Details|Lehrbeispiel]]\n````\n"
    )
    converted = convert_for_web(text, alpha, tmp_path, index=index)
    assert "[Details](Beta.md#details)" in converted
    assert "````markdown\n[[Beta#Details|Lehrbeispiel]]\n````" in converted


def test_download_only_link_targets_raw_artifact_instead_of_html(tmp_path: Path) -> None:
    alpha, _beta = make_link_repository(tmp_path)
    download_name = next(
        name for name, role in ROOT_ROLES.items() if role == "download-only"
    )
    write_page(
        tmp_path,
        download_name,
        title="Gesamtband",
        body="# Gesamtband\n\nDownloadinhalt.\n",
    )
    index = build_content_index(tmp_path)

    converted = convert_for_web(
        f"[[{download_name}|Gesamtband herunterladen]]\n",
        alpha,
        tmp_path,
        index=index,
    )

    assert converted == (
        f'<a href="../downloads/files/{download_name}" download>'
        "Gesamtband herunterladen</a>\n"
    )


def test_web_conversion_fails_closed_on_invalid_link(tmp_path: Path) -> None:
    alpha, _beta = make_link_repository(tmp_path)
    index = build_content_index(tmp_path)
    with pytest.raises(LinkError):
        convert_for_web("[[Fehlt]]\n", alpha, tmp_path, index=index)
