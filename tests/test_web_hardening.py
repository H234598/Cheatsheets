from __future__ import annotations

from pathlib import Path

import pytest

from serve_site import SiteServerError, normalize_base_path
from validate_web_budgets import analyze_web_budgets


def write_minimal_site(root: Path, *, html: str | None = None) -> Path:
    site = root / "site"
    (site / "assets" / "javascripts").mkdir(parents=True)
    (site / "assets" / "stylesheets").mkdir(parents=True)
    for name in (
        "site-state.js",
        "filters.js",
        "accessibility.js",
        "mermaid-loader.js",
    ):
        (site / "assets" / "javascripts" / name).write_text(
            'console.log("fixture");\n', encoding="utf-8"
        )
    for name in ("extra.css", "accessibility.css"):
        (site / "assets" / "stylesheets" / name).write_text(
            "body { max-width: 100%; }\n", encoding="utf-8"
        )
    payload = html or (
        "<!doctype html><html lang=\"de\"><head>"
        '<link rel="stylesheet" href="assets/stylesheets/extra.css">'
        '<link rel="stylesheet" href="assets/stylesheets/accessibility.css">'
        '<script src="assets/javascripts/site-state.js"></script>'
        '<script src="assets/javascripts/accessibility.js"></script>'
        "</head><body><h1>Fixture</h1></body></html>\n"
    )
    (site / "index.html").write_text(payload, encoding="utf-8")
    (site / "404.html").write_text(
        "<!doctype html><html lang=\"de\"><body><h1>404</h1></body></html>\n",
        encoding="utf-8",
    )
    return site


def test_base_path_is_canonicalized_and_rejects_unsafe_values() -> None:
    assert normalize_base_path("/Cheatsheets") == "/Cheatsheets/"
    assert normalize_base_path("//Cheatsheets//") == "/Cheatsheets/"

    for value in (
        "Cheatsheets",
        "/Cheatsheets/../private/",
        "/Cheatsheets/?debug=1",
        "/Cheatsheets/#fragment",
        "\\Cheatsheets\\",
    ):
        with pytest.raises(SiteServerError):
            normalize_base_path(value)


def test_local_runtime_assets_and_small_custom_bundle_pass(tmp_path: Path) -> None:
    site = write_minimal_site(tmp_path)
    issues, report = analyze_web_budgets(site)

    assert issues == []
    assert report["summary"]["errors"] == 0
    assert report["summary"]["custom_javascript_gzip_bytes"] > 0
    assert report["summary"]["custom_css_gzip_bytes"] > 0
    assert report["external_runtime_assets"] == []
    assert report["html_files"] == 2


def test_external_runtime_asset_is_blocking(tmp_path: Path) -> None:
    site = write_minimal_site(
        tmp_path,
        html=(
            "<!doctype html><html><head>"
            '<script src="https://cdn.example.invalid/tracker.js"></script>'
            "</head><body><h1>Fixture</h1></body></html>\n"
        ),
    )
    issues, report = analyze_web_budgets(site)

    assert {issue.code for issue in issues} == {"WB020"}
    assert report["external_runtime_assets"] == [
        {
            "path": "index.html",
            "url": "https://cdn.example.invalid/tracker.js",
        }
    ]


def test_missing_custom_asset_is_blocking(tmp_path: Path) -> None:
    site = write_minimal_site(tmp_path)
    (site / "assets" / "javascripts" / "filters.js").unlink()

    issues, _ = analyze_web_budgets(site)

    assert "WB001" in {issue.code for issue in issues}
