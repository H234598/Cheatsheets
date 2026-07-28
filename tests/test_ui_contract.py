from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
JS_DIR = ROOT / "web" / "assets" / "javascripts"
TEMPLATE_DIR = ROOT / "web" / "overrides"


def test_mkdocs_loads_local_ui_assets_in_stable_order() -> None:
    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))

    assert config["theme"]["font"] is False
    assert config["repo_url"] == "https://github.com/H234598/Cheatsheets"
    assert config["extra_javascript"] == [
        "assets/javascripts/site-state.js",
        "assets/javascripts/filters.js",
        "assets/javascripts/mermaid-loader.js",
    ]
    assert all("//" not in asset for asset in config["extra_javascript"])


def test_templates_keep_progressive_controls_hidden_without_javascript() -> None:
    main = (TEMPLATE_DIR / "main.html").read_text(encoding="utf-8")
    page_meta = (TEMPLATE_DIR / "partials" / "page-meta.html").read_text(
        encoding="utf-8"
    )
    local_state = (TEMPLATE_DIR / "partials" / "local-state.html").read_text(
        encoding="utf-8"
    )
    keyboard = (TEMPLATE_DIR / "partials" / "keyboard-help.html").read_text(
        encoding="utf-8"
    )

    assert 'meta name="cheatsheets-base-url"' in main
    assert 'include "partials/page-meta.html"' in main
    assert 'include "partials/local-state.html"' in main
    assert 'include "partials/keyboard-help.html"' in main
    assert "data-cheatsheet-page-tools" in page_meta
    assert "data-page-id=" in page_meta
    assert "hidden" in page_meta
    assert local_state.count('class="cheat-action-card"') == 3
    assert "data-cheat-keyboard-open" in local_state
    assert "data-cheat-filter-panel" in local_state
    assert "<noscript>" in local_state
    assert "data-cheat-shortcuts-toggle" in keyboard
    assert "<dialog" in keyboard


def test_ui_scripts_do_not_use_html_injection_or_telemetry() -> None:
    scripts = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(JS_DIR.glob("*.js"))
    }
    combined = "\n".join(scripts.values())

    for forbidden in (
        ".innerHTML",
        "insertAdjacentHTML",
        "document.write",
        "sendBeacon",
        "XMLHttpRequest",
        "google-analytics",
        "plausible.io",
    ):
        assert forbidden not in combined
    assert "cheatsheets.ui.v1" in scripts["site-state.js"]
    assert "setShortcutsEnabled" in scripts["site-state.js"]
    assert "localStorage" not in scripts["filters.js"]
    assert "url.origin !== window.location.origin" in scripts["site-state.js"]
    assert "url.origin !== window.location.origin" in scripts["filters.js"]
    assert "Suchbegriffe" not in scripts["site-state.js"]


def test_empty_time_filter_is_unbounded() -> None:
    filters = (JS_DIR / "filters.js").read_text(encoding="utf-8")

    assert "if (timeSelect.value)" in filters
    assert "const maximumMinutes = Number(timeSelect.value)" in filters


def test_css_contains_focus_mobile_and_reduced_motion_contracts() -> None:
    css = (ROOT / "web" / "assets" / "stylesheets" / "extra.css").read_text(
        encoding="utf-8"
    )

    assert ":focus-visible" in css
    assert 'html[data-focus-mode="true"]' in css
    assert "@media (max-width: 44rem)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "overflow-x: auto" in css


def test_page_id_alias_register_has_minimal_schema() -> None:
    payload = json.loads(
        (ROOT / "config" / "page-id-aliases.json").read_text(encoding="utf-8")
    )

    assert payload == {"aliases": {}, "schema_version": 1}


@pytest.mark.parametrize(
    "script_name",
    ["site-state.js", "filters.js", "mermaid-loader.js"],
)
def test_javascript_syntax_when_node_is_available(script_name: str) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js ist nicht installiert; Browserprüfung folgt in Phase 7")
    subprocess.run(
        [node, "--check", str(JS_DIR / script_name)],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
