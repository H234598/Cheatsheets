from __future__ import annotations

import json
from pathlib import Path

from conftest import manifest_row, write_manifest, write_page
from build_navigation import (
    absolute_page_url,
    build_navigation,
    load_publication_config,
    validate_publication_config,
    write_navigation_outputs,
)
from content_index import build_content_index


def _write_publication_config(root: Path) -> None:
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
        "download_only: []\n\n"
        "exclude_globs:\n"
        "  - build/**\n"
        "  - site/**\n"
        "  - .git/**\n"
        "  - .github/**\n"
        "  - .obsidian/**\n",
        encoding="utf-8",
    )


def _write_category_index(root: Path, names: tuple[str, ...]) -> None:
    links = "".join(f"- [[01-Test/{name}|{name}]]\n" for name in names)
    write_page(
        root,
        "01-Test/INDEX.md",
        title="Test – Kategorienindex",
        page_type="index",
        body=f"# Test\n\n## Seiten\n\n{links}",
        extra=f"pages: {len(names)}\n",
    )


def make_navigation_repository(root: Path) -> dict[str, Path]:
    pages = {
        "Alpha": write_page(
            root,
            "01-Test/Alpha.md",
            title="Alpha",
            aliases=("Erstes Blatt",),
            tags=("test", "alpha"),
            body="# Alpha\n\nInhalt.\n",
        ),
        "Beta": write_page(
            root,
            "01-Test/Beta.md",
            title="Beta",
            tags=("test", "beta"),
            body="# Beta\n\nInhalt.\n",
        ),
    }
    _write_category_index(root, ("Alpha", "Beta"))
    write_page(
        root,
        "00-START-HIER.md",
        title="Start hier",
        body="# Start hier\n\n[[01-Test/INDEX|Kategorie]]\n",
    )
    write_page(
        root,
        "INDEX.md",
        title="Quellindex",
        body="# Quellindex\n\n[[01-Test/Alpha|Alpha]]\n",
    )
    write_manifest(
        root,
        [
            manifest_row(1, "Test", "Alpha", pages["Alpha"], root),
            manifest_row(2, "Test", "Beta", pages["Beta"], root),
        ],
    )
    _write_publication_config(root)
    (root / "mkdocs.yml").write_text(
        "site_name: Fixture\n"
        "site_url: https://example.invalid/Cheatsheets/\n"
        "docs_dir: build/docs\n"
        "site_dir: site\n"
        "theme:\n"
        "  name: material\n",
        encoding="utf-8",
    )
    return pages


def test_navigation_contains_every_reference_exactly_once(tmp_path: Path) -> None:
    make_navigation_repository(tmp_path)
    index = build_content_index(tmp_path)
    nav = build_navigation(index)
    serialized = json.dumps(nav, ensure_ascii=False)

    assert serialized.count("01-Test/Alpha.md") == 1
    assert serialized.count("01-Test/Beta.md") == 1
    assert nav[0] == {"Start hier": "index.md"}
    assert nav[1] == {"Kategorien": "kategorien/index.md"}
    assert nav[-1] == {"Downloads & Offline": "downloads/index.md"}


def test_generated_indexes_and_json_data_are_complete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    make_navigation_repository(tmp_path)
    index = build_content_index(tmp_path)
    staging = tmp_path / "staging"
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1767225600")

    result = write_navigation_outputs(
        staging,
        index,
        site_url="https://example.invalid/Cheatsheets",
        source_commit="fixture-commit",
    )

    assert result.generated_markdown_pages == 6
    assert result.data_files == 4
    for relative in (
        "kategorien/index.md",
        "index/gesamt.md",
        "index/alphabetisch.md",
        "index/tags.md",
        "downloads/index.md",
        "intern/buildinformationen.md",
        "data/pages.json",
        "data/categories.json",
        "data/tags.json",
        "data/build-info.json",
    ):
        assert (staging / relative).is_file(), relative

    pages = json.loads((staging / "data" / "pages.json").read_text(encoding="utf-8"))
    alpha = next(page for page in pages if page["title"] == "Alpha")
    assert alpha["aliases"] == ["Erstes Blatt"]
    assert alpha["tags"] == ["test", "alpha"]
    assert alpha["url"] == "https://example.invalid/Cheatsheets/01-Test/Alpha/"

    build_info = json.loads(
        (staging / "data" / "build-info.json").read_text(encoding="utf-8")
    )
    assert build_info["generated_at"] == "2026-01-01T00:00:00Z"
    assert build_info["source_commit"] == "fixture-commit"
    assert build_info["reference_pages"] == 2


def test_project_page_and_custom_domain_need_no_markdown_change(tmp_path: Path) -> None:
    make_navigation_repository(tmp_path)
    index = build_content_index(tmp_path)
    alpha = next(page for page in index.reference_pages if page.title == "Alpha")

    assert absolute_page_url(
        "https://h234598.github.io/Cheatsheets/", alpha
    ) == "https://h234598.github.io/Cheatsheets/01-Test/Alpha/"
    assert absolute_page_url(
        "https://cheatsheets.example.org/", alpha
    ) == "https://cheatsheets.example.org/01-Test/Alpha/"


def test_publication_config_contains_roles_but_no_reference_inventory(
    tmp_path: Path,
) -> None:
    make_navigation_repository(tmp_path)
    index = build_content_index(tmp_path)
    config = load_publication_config(tmp_path)
    validate_publication_config(config, index)

    raw = (tmp_path / "config" / "publication.yaml").read_text(encoding="utf-8")
    assert "Alpha.md" not in raw
    assert "Beta.md" not in raw
    assert config.home == "00-START-HIER.md"
    assert config.source_index == "INDEX.md"


def test_new_reference_appears_without_editing_mkdocs_config(tmp_path: Path) -> None:
    pages = make_navigation_repository(tmp_path)
    mkdocs_before = (tmp_path / "mkdocs.yml").read_bytes()
    pages["Gamma"] = write_page(
        tmp_path,
        "01-Test/Gamma.md",
        title="Gamma",
        tags=("test", "gamma"),
        body="# Gamma\n\nInhalt.\n",
    )
    _write_category_index(tmp_path, ("Alpha", "Beta", "Gamma"))
    write_manifest(
        tmp_path,
        [
            manifest_row(1, "Test", "Alpha", pages["Alpha"], tmp_path),
            manifest_row(2, "Test", "Beta", pages["Beta"], tmp_path),
            manifest_row(3, "Test", "Gamma", pages["Gamma"], tmp_path),
        ],
    )

    index = build_content_index(tmp_path)
    nav = build_navigation(index)
    assert "01-Test/Gamma.md" in json.dumps(nav)
    assert (tmp_path / "mkdocs.yml").read_bytes() == mkdocs_before


def test_reference_and_category_urls_are_unique(tmp_path: Path) -> None:
    make_navigation_repository(tmp_path)
    index = build_content_index(tmp_path)
    pages = list(index.reference_pages) + [
        index.pages[category.index_page_id]
        for category in index.categories.values()
    ]
    urls = [absolute_page_url("https://example.invalid/Cheatsheets/", page) for page in pages]
    assert len(urls) == len(set(urls))
