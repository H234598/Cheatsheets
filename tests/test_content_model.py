from __future__ import annotations

from pathlib import Path

from conftest import manifest_row, write_manifest, write_page
from content_index import build_content_index, parse_headings
from content_model import advance_fence_state, normalize_posix_path, page_id_from_path


def make_repository(root: Path) -> None:
    first = write_page(
        root,
        "01-Test/Alpha.md",
        title="Alpha",
        aliases=("Erstes Blatt",),
        body="# Alpha\n\nText.\n",
    )
    second = write_page(
        root,
        "01-Test/Beta.md",
        title="Beta",
        body="# Beta\n\nText.\n",
    )
    write_page(
        root,
        "01-Test/INDEX.md",
        title="Test – Kategorienindex",
        page_type="index",
        body=(
            "# Test\n\n"
            "## Seiten\n\n"
            "- [[01-Test/Alpha|Alpha]]\n"
            "- [[01-Test/Beta|Beta]]\n\n"
            "## Verwandte Bereiche\n"
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


def test_fence_state_honours_marker_length() -> None:
    state, fenced = advance_fence_state("````markdown\n", None)
    assert fenced and state == ("`", 4)
    state, fenced = advance_fence_state("```\n", state)
    assert fenced and state == ("`", 4)
    state, fenced = advance_fence_state("````\n", state)
    assert fenced and state is None


def test_headings_ignore_fenced_examples() -> None:
    headings, issues = parse_headings(
        "# Echt\n\n````markdown\n# Beispiel\n````\n\n## Echt zwei\n",
        1,
    )
    assert not issues
    assert [heading.text for heading in headings] == ["Echt", "Echt zwei"]


def test_content_index_discovers_known_roles(tmp_path: Path) -> None:
    make_repository(tmp_path)
    index = build_content_index(tmp_path)
    assert len(index.reference_pages) == 2
    assert len(index.categories) == 1
    assert not index.issues
    assert [page.title for page in index.reference_pages] == ["Alpha", "Beta"]


def test_page_id_is_stable_and_path_sensitive() -> None:
    assert page_id_from_path(Path("01-Test/Alpha.md")) == page_id_from_path(
        Path("01-Test/Alpha.md")
    )
    assert page_id_from_path(Path("01-Test/Alpha.md")) != page_id_from_path(
        Path("01-Test/Beta.md")
    )


def test_normalization_preserves_dot_directories() -> None:
    assert normalize_posix_path(Path(".github/README.md")) == ".github/README.md"


def test_generated_paths_map_landing_and_category_index(tmp_path: Path) -> None:
    make_repository(tmp_path)
    index = build_content_index(tmp_path)
    category = next(
        page for page in index.pages.values() if page.page_type == "category-index"
    )
    assert category.generated_path.as_posix() == "01-Test/index.md"
    alpha = index.page_for_path(tmp_path / "01-Test" / "Alpha.md")
    assert alpha is not None and alpha.title == "Alpha"
