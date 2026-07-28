from __future__ import annotations

import json
from pathlib import Path
import shutil
import tarfile
import zipfile

import pytest

from build_downloads import (
    DownloadBuildError,
    FILES_DIRECTORY,
    ROOT_ROLES,
    build_downloads,
    validate_downloads,
)

COMMIT = "a" * 40
EPOCH = 1_700_000_000


def write_source(root: Path) -> None:
    download_name = next(
        name for name, role in ROOT_ROLES.items() if role == "download-only"
    )
    files = {
        "00-START-HIER.md": "# Start hier\n\n[[01-Test/INDEX|Test]]\n",
        "INDEX.md": "# Gesamtindex\n\n[[01-Test/Alpha|Alpha]]\n",
        "README.md": "# Cheatsheets\n\nKanonische Quellen.\n",
        download_name: "# Gesamtband\n\n## Alpha\n\nInhalt.\n",
        "01-Test/INDEX.md": "# Test\n\n- [[01-Test/Alpha|Alpha]]\n",
        "01-Test/Alpha.md": (
            "---\n"
            "title: Alpha\n"
            "type: reference\n"
            "status: fertig\n"
            "tags: [test]\n"
            "---\n"
            "# Alpha\n\nInhalt.\n"
        ),
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def write_site(root: Path) -> Path:
    site = root / "site"
    page = site / "downloads" / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        "<!doctype html><html><body><main><article>"
        "<h1>Downloads</h1></article></main></body></html>\n",
        encoding="utf-8",
    )
    (site / "index.html").write_text("<!doctype html><title>Start</title>\n", encoding="utf-8")
    (site / "404.html").write_text("<!doctype html><title>404</title>\n", encoding="utf-8")
    return site


def public_outputs(site: Path) -> dict[str, bytes]:
    output = site / FILES_DIRECTORY
    return {
        path.name: path.read_bytes()
        for path in sorted(output.iterdir(), key=lambda item: item.name.casefold())
        if not path.name.startswith(".")
    }


def test_download_build_is_byte_reproducible_and_idempotent(tmp_path: Path) -> None:
    write_source(tmp_path)
    site = write_site(tmp_path)

    first = build_downloads(
        tmp_path,
        site,
        source_commit=COMMIT,
        source_date_epoch=EPOCH,
        site_url="https://example.invalid/Cheatsheets/",
    )
    first_outputs = public_outputs(site)
    first_page = (site / "downloads" / "index.html").read_bytes()

    second = build_downloads(
        tmp_path,
        site,
        source_commit=COMMIT,
        source_date_epoch=EPOCH,
        site_url="https://example.invalid/Cheatsheets/",
    )

    assert public_outputs(site) == first_outputs
    assert (site / "downloads" / "index.html").read_bytes() == first_page
    assert first.tree_sha256 == second.tree_sha256
    assert first.source_files == 6
    assert len(first.artifacts) == 3


def test_archives_contain_only_safe_regular_entries(tmp_path: Path) -> None:
    write_source(tmp_path)
    site = write_site(tmp_path)
    build_downloads(
        tmp_path,
        site,
        source_commit=COMMIT,
        source_date_epoch=EPOCH,
    )
    output = site / FILES_DIRECTORY

    with zipfile.ZipFile(output / "cheatsheets-markdown.zip") as archive:
        names = archive.namelist()
        assert names == sorted(names, key=str.casefold)
        assert "Cheatsheets/BUNDLE-MANIFEST.json" in names
        assert "Cheatsheets/BUNDLE-README.txt" in names
        assert all(not Path(name).is_absolute() and ".." not in Path(name).parts for name in names)

    with tarfile.open(output / "cheatsheets-markdown.tar.gz", "r:gz") as archive:
        members = archive.getmembers()
        assert [member.name for member in members] == sorted(
            (member.name for member in members), key=str.casefold
        )
        assert all(member.isfile() for member in members)
        assert all(not Path(member.name).is_absolute() for member in members)


def test_catalog_provenance_checksums_and_html_links_agree(tmp_path: Path) -> None:
    write_source(tmp_path)
    site = write_site(tmp_path)
    report = tmp_path / "build" / "reports" / "downloads.json"

    result = build_downloads(
        tmp_path,
        site,
        source_commit=COMMIT,
        source_date_epoch=EPOCH,
        site_url="https://example.invalid/Cheatsheets/",
        report=report,
    )
    output = site / FILES_DIRECTORY
    catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
    provenance = json.loads(
        (output / "provenance.intoto.json").read_text(encoding="utf-8")
    )
    page = (site / "downloads" / "index.html").read_text(encoding="utf-8")
    report_payload = json.loads(report.read_text(encoding="utf-8"))

    assert catalog["source_commit"] == COMMIT
    assert catalog["source_date_epoch"] == EPOCH
    assert len(catalog["artifacts"]) == 3
    assert provenance["_type"] == "https://in-toto.io/Statement/v1"
    assert provenance["predicateType"] == "https://slsa.dev/provenance/v1"
    assert len(provenance["subject"]) == 4
    assert page.count("<!-- cheatsheets-downloads:start -->") == 1
    assert page.count("<!-- cheatsheets-downloads:end -->") == 1
    assert 'href="files/cheatsheets-markdown.zip"' in page
    assert 'href="files/provenance.intoto.json"' in page
    assert report_payload["downloads_tree_sha256"] == result.tree_sha256


def test_validation_detects_tampered_artifact(tmp_path: Path) -> None:
    write_source(tmp_path)
    site = write_site(tmp_path)
    build_downloads(
        tmp_path,
        site,
        source_commit=COMMIT,
        source_date_epoch=EPOCH,
    )
    artifact = site / FILES_DIRECTORY / "cheatsheets-gesamtband.md"
    artifact.write_text("manipuliert\n", encoding="utf-8")

    with pytest.raises(DownloadBuildError, match="Gesamtband|Prüfsumme"):
        validate_downloads(tmp_path, site, expected_commit=COMMIT)


def test_unmarked_existing_download_directory_is_not_deleted(tmp_path: Path) -> None:
    write_source(tmp_path)
    site = write_site(tmp_path)
    output = site / FILES_DIRECTORY
    output.mkdir(parents=True)
    (output / "fremd.txt").write_text("nicht löschen", encoding="utf-8")

    with pytest.raises(DownloadBuildError, match="keinen sicheren Marker"):
        build_downloads(
            tmp_path,
            site,
            source_commit=COMMIT,
            source_date_epoch=EPOCH,
        )
    assert (output / "fremd.txt").read_text(encoding="utf-8") == "nicht löschen"


def test_symlinked_public_source_is_rejected(tmp_path: Path) -> None:
    write_source(tmp_path)
    external = tmp_path.parent / "external-readme.md"
    external.write_text("extern\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.unlink()
    try:
        readme.symlink_to(external)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlinks werden auf dieser Plattform nicht unterstützt: {exc}")
    site = write_site(tmp_path)

    with pytest.raises(DownloadBuildError, match="Repositorywurzel|nicht regulär"):
        build_downloads(
            tmp_path,
            site,
            source_commit=COMMIT,
            source_date_epoch=EPOCH,
        )


def test_rebuild_replaces_only_its_marked_directory(tmp_path: Path) -> None:
    write_source(tmp_path)
    site = write_site(tmp_path)
    build_downloads(
        tmp_path,
        site,
        source_commit=COMMIT,
        source_date_epoch=EPOCH,
    )
    output = site / FILES_DIRECTORY
    (output / "veraltet.txt").write_text("alt", encoding="utf-8")

    build_downloads(
        tmp_path,
        site,
        source_commit=COMMIT,
        source_date_epoch=EPOCH,
    )

    assert not (output / "veraltet.txt").exists()
    assert (output / "catalog.json").is_file()


def test_fresh_site_can_be_recreated_after_removal(tmp_path: Path) -> None:
    write_source(tmp_path)
    site = write_site(tmp_path)
    build_downloads(
        tmp_path,
        site,
        source_commit=COMMIT,
        source_date_epoch=EPOCH,
    )
    first = public_outputs(site)

    shutil.rmtree(site)
    site = write_site(tmp_path)
    build_downloads(
        tmp_path,
        site,
        source_commit=COMMIT,
        source_date_epoch=EPOCH,
    )

    assert public_outputs(site) == first
