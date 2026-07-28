from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest
import yaml

from conftest import manifest_row, write_manifest, write_page
import build_site as build_site_module
from build_docs import build_docs, fenced_segment_hashes
from build_site import validate_cli_combination, write_generated_config
from io_utils import BUILD_SENTINEL, UnsafePathError


def make_build_repository(root: Path) -> tuple[Path, Path]:
    alpha = write_page(
        root,
        "01-Test/Alpha.md",
        title="Alpha",
        aliases=("Erstes Blatt",),
        body=(
            "# Alpha\n\n"
            "Siehe [[Beta#Details|Details]].\n\n"
            "> [!warning]- Vorsicht\n"
            "> Erst prüfen.\n\n"
            "````markdown\n"
            "[[Beta#Details|Lehrbeispiel]]\n"
            "> [!danger] Nur Syntax\n"
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
    write_manifest(
        root,
        [
            manifest_row(1, "Test", "Alpha", alpha, root),
            manifest_row(2, "Test", "Beta", beta, root),
        ],
    )
    image = root / "01-Test" / "bild.png"
    image.write_bytes(b"fixture-image")
    (root / "MANIFEST.json").write_text("{}\n", encoding="utf-8")
    (root / "web" / "assets" / "stylesheets").mkdir(parents=True)
    (root / "web" / "assets" / "stylesheets" / "extra.css").write_text(
        "body { max-width: 100%; }\n", encoding="utf-8"
    )
    (root / "web" / "overrides").mkdir(parents=True)
    (root / "mkdocs.yml").write_text(
        "site_name: Fixture\n"
        "site_url: https://example.invalid/Cheatsheets/\n"
        "docs_dir: build/docs\n"
        "site_dir: site\n"
        "theme:\n"
        "  name: material\n"
        "  custom_dir: web/overrides\n",
        encoding="utf-8",
    )
    return alpha, image


def test_build_docs_transforms_only_generated_copy(tmp_path: Path) -> None:
    alpha, image = make_build_repository(tmp_path)
    source_before = alpha.read_bytes()
    output = tmp_path / "build" / "docs"

    result = build_docs(tmp_path, output, strict=True)

    assert result.pages == 4
    assert result.assets == 1
    assert (output / BUILD_SENTINEL).is_file()
    assert (output / "index.md").is_file()
    assert (output / "01-Test" / "index.md").is_file()
    assert (output / "01-Test" / "Alpha.md").is_file()
    assert (output / "01-Test" / "bild.png").read_bytes() == image.read_bytes()
    assert not (output / "MANIFEST.json").exists()
    assert (output / "assets" / "stylesheets" / "extra.css").is_file()
    assert (output / "404.md").is_file()

    generated = (output / "01-Test" / "Alpha.md").read_text(encoding="utf-8")
    assert "[Details](Beta.md#details)" in generated
    assert '??? warning "Vorsicht"\n    Erst prüfen.\n' in generated
    assert "[[Beta#Details|Lehrbeispiel]]" in generated
    assert "> [!danger] Nur Syntax" in generated
    assert fenced_segment_hashes(alpha.read_text(encoding="utf-8")) == fenced_segment_hashes(
        generated
    )
    assert alpha.read_bytes() == source_before


def test_existing_unmarked_output_is_never_deleted(tmp_path: Path) -> None:
    make_build_repository(tmp_path)
    output = tmp_path / "build" / "docs"
    output.mkdir(parents=True)
    protected = output / "private.txt"
    protected.write_text("nicht löschen\n", encoding="utf-8")

    with pytest.raises(UnsafePathError):
        build_docs(tmp_path, output, strict=True, force=True)
    assert protected.read_text(encoding="utf-8") == "nicht löschen\n"


def test_generated_config_uses_absolute_paths_and_one_site_url(tmp_path: Path) -> None:
    make_build_repository(tmp_path)
    docs = tmp_path / "build" / "docs"
    site = tmp_path / "site-staging"
    config_path = tmp_path / "build" / "mkdocs.generated.yml"
    config = write_generated_config(
        tmp_path,
        config_path,
        docs_dir=docs,
        site_dir=site,
        site_url="https://docs.example.invalid/cheatsheets",
    )
    parsed = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["site_url"] == "https://docs.example.invalid/cheatsheets/"
    assert parsed["docs_dir"] == str(docs.resolve())
    assert parsed["site_dir"] == str(site.resolve())
    assert Path(parsed["theme"]["custom_dir"]).is_absolute()


def test_build_site_runs_mkdocs_into_atomic_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_build_repository(tmp_path)

    def fake_mkdocs(config_path: Path) -> None:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        site_dir = Path(config["site_dir"])
        site_dir.mkdir(parents=True, exist_ok=True)
        (site_dir / "index.html").write_text("<h1>Fixture</h1>\n", encoding="utf-8")
        (site_dir / "404.html").write_text("<h1>404</h1>\n", encoding="utf-8")

    monkeypatch.setattr(build_site_module, "run_mkdocs", fake_mkdocs)
    pages, assets = build_site_module.build_site(
        tmp_path,
        Path("build/docs"),
        Path("site"),
        site_url="https://example.invalid/Cheatsheets/",
        strict=True,
        force=True,
    )

    assert pages == 4 and assets == 1
    assert (tmp_path / "site" / "index.html").is_file()
    assert (tmp_path / "site" / "404.html").is_file()
    assert (tmp_path / "site" / BUILD_SENTINEL).is_file()


def test_cli_rejects_incomplete_or_conflicting_modes() -> None:
    base = {
        "check": False,
        "dry_run": False,
        "strict": False,
        "max_pages": None,
    }
    validate_cli_combination(Namespace(**base))
    with pytest.raises(ValueError):
        validate_cli_combination(Namespace(**{**base, "check": True, "dry_run": True}))
    with pytest.raises(ValueError):
        validate_cli_combination(Namespace(**{**base, "strict": True, "max_pages": 1}))
    with pytest.raises(ValueError):
        validate_cli_combination(Namespace(**{**base, "max_pages": 1}))
