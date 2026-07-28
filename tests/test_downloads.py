from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

import pytest

from build_downloads import build_downloads, copy_downloads_to_site
from conftest import manifest_row, write_manifest, write_page
from content_index import build_content_index
from download_metadata import render_landing_page
from download_model import ARTIFACT_ORDER, DownloadBuildError
from download_sources import canonical_archive_name
from io_utils import BUILD_SENTINEL

COMMIT = "a" * 40
EPOCH = 1767225600


def make_download_repository(root: Path) -> tuple[Path, Path]:
    alpha = write_page(
        root,
        "01-Test/Alpha.md",
        title="Alpha",
        aliases=("Erstes Blatt",),
        body=(
            "# Alpha\n\n"
            "Siehe [[Beta#Details|Details]].\n\n"
            "````markdown\n"
            "[[Beta#Details|Lehrbeispiel]]\n"
            "````\n"
        ),
    )
    beta = write_page(
        root,
        "01-Test/Beta.md",
        title="Beta",
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
    write_manifest(
        root,
        [
            manifest_row(1, "Test", "Alpha", alpha, root),
            manifest_row(2, "Test", "Beta", beta, root),
        ],
    )
    (root / "LICENSE").write_text("CC0 fixture\n", encoding="utf-8")
    (root / "01-Test" / "bild.png").write_bytes(b"fixture-image")
    (root / ".obsidian").mkdir()
    (root / ".obsidian" / "workspace.json").write_text("{}\n", encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "private.yml").write_text("secret: false\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "--all"], cwd=root, check=True)
    return alpha, beta


def file_payloads(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.iterdir(), key=lambda item: item.name.casefold())
        if path.is_file()
    }


def test_download_build_is_deterministic_complete_and_self_describing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_download_repository(tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", str(EPOCH))

    first = build_downloads(
        tmp_path,
        tmp_path / "build" / "first",
        source_commit=COMMIT,
        strict=True,
        force=True,
    )
    second = build_downloads(
        tmp_path,
        tmp_path / "build" / "second",
        source_commit=COMMIT,
        strict=True,
        force=True,
    )

    assert [artifact.name for artifact in first.artifacts] == list(ARTIFACT_ORDER)
    assert file_payloads(first.output) == file_payloads(second.output)
    assert (first.output / BUILD_SENTINEL).is_file()
    assert first.source_tree_sha256 == second.source_tree_sha256

    manifest = json.loads(
        (first.output / "DOWNLOAD-MANIFEST.json").read_text(encoding="utf-8")
    )
    assert {item["name"] for item in manifest["artifacts"]} == set(ARTIFACT_ORDER)
    self_rows = {
        item["name"]: item
        for item in manifest["artifacts"]
        if item["name"].startswith("DOWNLOAD-")
    }
    assert self_rows["DOWNLOAD-MANIFEST.json"]["sha256"] is None
    assert self_rows["DOWNLOAD-MANIFEST.csv"]["sha256"] is None
    assert self_rows["DOWNLOAD-SHA256SUMS.txt"]["sha256"] is None

    with (first.output / "DOWNLOAD-MANIFEST.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        csv_names = {row["name"] for row in csv.DictReader(handle)}
    assert csv_names == set(ARTIFACT_ORDER)

    checksums = {}
    for line in (first.output / "DOWNLOAD-SHA256SUMS.txt").read_text(
        encoding="utf-8"
    ).splitlines():
        digest, name = line.split("  ", 1)
        checksums[name] = digest
    assert set(checksums) == set(ARTIFACT_ORDER) - {"DOWNLOAD-SHA256SUMS.txt"}
    for name, digest in checksums.items():
        assert hashlib.sha256((first.output / name).read_bytes()).hexdigest() == digest

    provenance = json.loads((first.output / "PROVENANCE.json").read_text(encoding="utf-8"))
    assert provenance["source_commit"] == COMMIT
    assert provenance["source_date_epoch"] == EPOCH
    assert provenance["reference_pages"] == 2
    assert provenance["categories"] == 1
    assert provenance["source_tree_sha256"] == first.source_tree_sha256


def test_source_zip_is_safe_sorted_and_excludes_repository_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_download_repository(tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", str(EPOCH))
    result = build_downloads(
        tmp_path,
        tmp_path / "build" / "downloads",
        source_commit=COMMIT,
        strict=True,
        force=True,
    )

    with zipfile.ZipFile(result.output / "Cheatsheets-Quellen.zip") as archive:
        names = archive.namelist()
        assert names == sorted(names, key=str.casefold)
        assert "01-Test/Alpha.md" in names
        assert "01-Test/Beta.md" in names
        assert "01-Test/bild.png" in names
        assert "SOURCE-SHA256SUMS.txt" in names
        assert "LICENSE" in names
        assert not any(name.startswith(".obsidian/") for name in names)
        assert not any(name.startswith(".github/") for name in names)
        assert "Cheatsheet-Gesamtband.md" not in names
        for info in archive.infolist():
            assert info.compress_type == zipfile.ZIP_STORED
            assert (info.external_attr >> 16) & 0o777 == 0o644
            assert info.date_time == (2026, 1, 1, 0, 0, 0)

        source_sums = archive.read("SOURCE-SHA256SUMS.txt").decode("utf-8")
        assert "01-Test/Alpha.md" in source_sums
        assert "SOURCE-SHA256SUMS.txt" not in source_sums


def test_combined_markdown_preserves_fences_and_uses_stable_internal_anchors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alpha, beta = make_download_repository(tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", str(EPOCH))
    result = build_downloads(
        tmp_path,
        tmp_path / "build" / "downloads",
        source_commit=COMMIT,
        strict=True,
        force=True,
    )
    index = build_content_index(tmp_path)
    alpha_record = index.page_for_path(alpha)
    beta_record = index.page_for_path(beta)
    assert alpha_record is not None and beta_record is not None

    combined = (result.output / "Cheatsheet-Gesamtband.md").read_text(
        encoding="utf-8"
    )
    assert f"[]{{#{alpha_record.page_id}}}" in combined
    assert f"[]{{#{beta_record.page_id}}}" in combined
    assert f"](#{beta_record.page_id}--details)" in combined
    assert "[[Beta#Details|Lehrbeispiel]]" in combined
    assert combined.count("````markdown") == 1
    assert f"source_commit: \"{COMMIT}\"" in combined


def test_downloads_are_copied_to_site_and_landing_page_uses_verified_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_download_repository(tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", str(EPOCH))
    result = build_downloads(
        tmp_path,
        tmp_path / "build" / "downloads",
        source_commit=COMMIT,
        strict=True,
        force=True,
    )
    site = tmp_path / "site"
    copy_downloads_to_site(result, site)

    for artifact in result.artifacts:
        copied = site / "downloads" / "files" / artifact.name
        assert copied.is_file()
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == artifact.sha256

    landing = render_landing_page(result)
    for artifact in result.artifacts:
        assert artifact.name in landing
        assert artifact.sha256 in landing
    assert f"Quellcommit | `{COMMIT}`" in landing


def test_untracked_content_asset_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_download_repository(tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", str(EPOCH))
    (tmp_path / "01-Test" / "private.pem").write_text(
        "not-for-publication\n", encoding="utf-8"
    )

    with pytest.raises(DownloadBuildError, match="nicht Git-getracktes Inhaltsasset"):
        build_downloads(
            tmp_path,
            tmp_path / "build" / "downloads",
            source_commit=COMMIT,
            strict=True,
            force=True,
        )


def test_content_asset_symlink_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_download_repository(tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", str(EPOCH))
    external = tmp_path.parent / "external.bin"
    external.write_bytes(b"secret")
    link = tmp_path / "01-Test" / "linked.bin"
    try:
        link.symlink_to(external)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlinks werden nicht unterstützt: {exc}")

    with pytest.raises(DownloadBuildError, match="Inhaltsasset darf kein Symlink"):
        build_downloads(
            tmp_path,
            tmp_path / "build" / "downloads",
            source_commit=COMMIT,
            strict=True,
            force=True,
        )


@pytest.mark.parametrize(
    "name",
    [
        "",
        "/absolute/file.txt",
        "//server/share/file.txt",
        r"\\server\share\file.txt",
        r"C:\temp\file.txt",
        "C:relative.txt",
        "assets/../../startup.bat",
        r"assets/..\..\startup.bat",
        "assets//file.txt",
        "assets/./file.txt",
        "assets/\x00file.txt",
    ],
)
def test_unsafe_archive_names_are_rejected(name: str) -> None:
    with pytest.raises(DownloadBuildError):
        canonical_archive_name(name)


def test_windows_separators_are_canonicalized_before_archive_validation() -> None:
    assert canonical_archive_name(r"assets\icons\cheat.png") == "assets/icons/cheat.png"
