from __future__ import annotations

import io
import json
from pathlib import Path
import zipfile

import pytest
import yaml

from build_offline import (
    OFFLINE_CHECKSUMS_NAME,
    OFFLINE_MANIFEST_NAME,
    OFFLINE_README_NAME,
    OFFLINE_SERVER_NAME,
    OfflineBuildError,
    _augment_integrity_files,
    _copy_and_rewrite_docs,
    render_offline_zip,
    validate_offline_tree,
    validate_offline_zip,
    write_offline_config,
)
from conftest import manifest_row, write_manifest, write_page
from content_index import build_content_index

COMMIT = "b" * 40


def make_index(root: Path):
    alpha = write_page(
        root,
        "01-Test/Alpha.md",
        title="Alpha",
        body="# Alpha\n\nInhalt.\n",
    )
    write_page(
        root,
        "01-Test/INDEX.md",
        title="Test – Kategorienindex",
        page_type="index",
        body="# Test\n\n## Seiten\n\n- [[01-Test/Alpha|Alpha]]\n",
        extra="pages: 1\n",
    )
    write_page(
        root,
        "00-START-HIER.md",
        title="Start hier",
        body="# Start hier\n\n[[01-Test/INDEX|Zur Kategorie]]\n",
    )
    write_page(
        root,
        "INDEX.md",
        title="Quellindex",
        body="# Quellindex\n\n[[01-Test/Alpha|Alpha]]\n",
    )
    write_manifest(root, [manifest_row(1, "Test", "Alpha", alpha, root)])
    return build_content_index(root)


def make_site(root: Path, *, root_relative: bool = False) -> Path:
    site = root / "site"
    (site / "assets").mkdir(parents=True)
    (site / "assets" / "app.css").write_text(
        "body { background-image: url('../image.png'); }\n", encoding="utf-8"
    )
    (site / "image.png").write_bytes(b"image")
    href = "/Alpha.html" if root_relative else "Alpha.html"
    (site / "index.html").write_text(
        f'<!doctype html><html><head><link rel="stylesheet" href="assets/app.css"></head>'
        f'<body><h1>Start</h1><a href="{href}">Alpha</a></body></html>\n',
        encoding="utf-8",
    )
    (site / "Alpha.html").write_text(
        '<!doctype html><html><body><h1 id="alpha">Alpha</h1>'
        '<a href="index.html">Start</a></body></html>\n',
        encoding="utf-8",
    )
    (site / "404.html").write_text(
        '<!doctype html><html><body><h1>404</h1></body></html>\n',
        encoding="utf-8",
    )
    (site / OFFLINE_README_NAME).write_text("Offline\n", encoding="utf-8")
    (site / OFFLINE_SERVER_NAME).write_text("print('server')\n", encoding="utf-8")
    return site


def test_offline_config_uses_file_urls_and_explicit_mode(tmp_path: Path) -> None:
    (tmp_path / "mkdocs.yml").write_text(
        "site_name: Fixture\n"
        "site_url: https://example.invalid/Cheatsheets/\n"
        "docs_dir: build/docs\n"
        "site_dir: site\n"
        "theme:\n"
        "  name: material\n"
        "  custom_dir: web/overrides\n"
        "plugins:\n"
        "  - search:\n"
        "      lang: de\n"
        "extra:\n"
        "  source_repository_url: https://github.com/example/repo\n",
        encoding="utf-8",
    )
    (tmp_path / "web" / "overrides").mkdir(parents=True)
    config_path = tmp_path / "build" / "offline.yml"
    config = write_offline_config(
        tmp_path,
        config_path,
        docs_dir=tmp_path / "docs",
        site_dir=tmp_path / "offline-site",
        site_url="https://example.invalid/Cheatsheets/",
        nav=[{"Start": "index.md"}],
    )
    parsed = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["use_directory_urls"] is False
    assert parsed["strict"] is True
    assert parsed["extra"]["offline_mode"] is True
    assert parsed["extra"]["online_site_url"] == "https://example.invalid/Cheatsheets/"
    assert Path(parsed["theme"]["custom_dir"]).is_absolute()
    assert parsed["nav"] == [{"Start": "index.md"}]


def test_generated_data_is_rewritten_to_relative_html_urls(tmp_path: Path) -> None:
    index = make_index(tmp_path)
    docs = tmp_path / "generated-docs"
    (docs / "data").mkdir(parents=True)
    alpha = index.reference_pages[0]
    category = next(iter(index.categories.values()))
    (docs / "data" / "pages.json").write_text(
        json.dumps([{"id": alpha.page_id, "url": "https://online.invalid/Alpha/"}]),
        encoding="utf-8",
    )
    (docs / "data" / "categories.json").write_text(
        json.dumps([{"id": category.category_id, "url": "https://online.invalid/Test/"}]),
        encoding="utf-8",
    )
    (docs / "data" / "build-info.json").write_text("{}\n", encoding="utf-8")
    (docs / ".cheatsheets-build-root").write_text("generated\n", encoding="utf-8")

    target = tmp_path / "offline-docs"
    _copy_and_rewrite_docs(
        docs,
        target,
        index,
        "https://example.invalid/Cheatsheets/",
    )

    pages = json.loads((target / "data" / "pages.json").read_text(encoding="utf-8"))
    categories = json.loads(
        (target / "data" / "categories.json").read_text(encoding="utf-8")
    )
    build_info = json.loads(
        (target / "data" / "build-info.json").read_text(encoding="utf-8")
    )
    assert pages[0]["url"] == "01-Test/Alpha.html"
    assert categories[0]["url"] == "01-Test/index.html"
    assert build_info["offline"] is True
    assert build_info["url_mode"] == "relative-html"
    assert not (target / ".cheatsheets-build-root").exists()


def test_offline_tree_accepts_relative_links_and_rejects_root_relative(
    tmp_path: Path,
) -> None:
    valid = make_site(tmp_path / "valid")
    report = validate_offline_tree(valid)
    assert report["files"] >= 7
    assert report["references"] >= 3

    invalid = make_site(tmp_path / "invalid", root_relative=True)
    with pytest.raises(OfflineBuildError, match="Root-relativer Link"):
        validate_offline_tree(invalid)


def test_offline_zip_is_deterministic_sorted_and_self_describing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1767225601")
    entries = {
        "index.html": b"<h1>Offline</h1>\n",
        OFFLINE_README_NAME: b"Offline lesen\n",
        OFFLINE_SERVER_NAME: b"print('server')\n",
    }
    augmented, tree_sha = _augment_integrity_files(
        entries,
        source_commit=COMMIT,
        online_site_url="https://example.invalid/Cheatsheets/",
    )
    first = render_offline_zip(augmented)
    second = render_offline_zip(augmented)

    assert first == second
    validate_offline_zip(first, augmented)
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert archive.namelist() == sorted(augmented, key=str.casefold)
        assert OFFLINE_MANIFEST_NAME in archive.namelist()
        assert OFFLINE_CHECKSUMS_NAME in archive.namelist()
        manifest = json.loads(archive.read(OFFLINE_MANIFEST_NAME))
        assert manifest["source_commit"] == COMMIT
        assert manifest["tree_sha256"] == tree_sha
        assert manifest["url_mode"] == "relative-html"
        for info in archive.infolist():
            assert info.compress_type == zipfile.ZIP_STORED
            assert (info.external_attr >> 16) & 0o777 == 0o644
            assert info.date_time[-1] % 2 == 0
