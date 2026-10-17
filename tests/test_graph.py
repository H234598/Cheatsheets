from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from build_graph import (
    GraphBuildError,
    build_graph,
    validate_graph_data,
    write_graph_outputs,
)
from conftest import manifest_row, write_manifest, write_page
from content_index import build_content_index

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "c" * 40
SITE_URL = "https://example.invalid/Cheatsheets/"


def make_graph_repository(root: Path):
    alpha = write_page(
        root,
        "01-Test/Alpha.md",
        title="Alpha",
        aliases=("Erstes Blatt",),
        tags=("test", "gemeinsam"),
        body=(
            "# Alpha\n\n"
            "Siehe [[Beta|Beta]].\n\n"
            "```markdown\n"
            "[[Nicht vorhanden|reines Lehrbeispiel]]\n"
            "```\n"
        ),
    )
    beta = write_page(
        root,
        "01-Test/Beta.md",
        title="Beta",
        tags=("gemeinsam", "netzwerk"),
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
    return build_content_index(root), alpha, beta


def test_graph_is_deterministic_complete_and_fence_safe(tmp_path: Path) -> None:
    index, alpha_path, beta_path = make_graph_repository(tmp_path)
    first = build_graph(index, site_url=SITE_URL, source_commit=COMMIT)
    second = build_graph(index, site_url=SITE_URL, source_commit=COMMIT)

    assert first == second
    assert first["source_commit"] == COMMIT
    assert first["stats"]["nodes_by_type"] == {
        "category": 1,
        "page": 2,
        "tag": 3,
    }
    assert first["stats"]["edges_by_type"]["contains"] == 2
    assert first["stats"]["edges_by_type"]["tagged"] == 4

    alpha = index.page_for_path(alpha_path)
    beta = index.page_for_path(beta_path)
    assert alpha is not None and beta is not None
    link_edges = [edge for edge in first["edges"] if edge["type"] == "links"]
    assert [(edge["source"], edge["target"]) for edge in link_edges] == [
        (alpha.page_id, beta.page_id)
    ]
    assert link_edges[0]["count"] == 1
    assert "Nicht vorhanden" not in json.dumps(first, ensure_ascii=False)

    page_nodes = {node["id"]: node for node in first["nodes"] if node["type"] == "page"}
    assert page_nodes[alpha.page_id]["url"].startswith(SITE_URL)
    assert page_nodes[alpha.page_id]["offline_url"] == "01-Test/Alpha.html"
    assert page_nodes[alpha.page_id]["aliases"] == ["Erstes Blatt"]


def test_graph_validator_rejects_unknown_edge_endpoint(tmp_path: Path) -> None:
    index, _alpha, _beta = make_graph_repository(tmp_path)
    graph = build_graph(index, site_url=SITE_URL, source_commit=COMMIT)
    invalid = deepcopy(graph)
    invalid["edges"][0]["target"] = "p_0000000000000000"

    with pytest.raises(GraphBuildError, match="unbekannten Endpunkt"):
        validate_graph_data(invalid, index=index)


def test_graph_outputs_include_interactive_page_and_no_js_fallback(tmp_path: Path) -> None:
    index, _alpha, _beta = make_graph_repository(tmp_path)
    staging = tmp_path / "build" / "docs"
    result = write_graph_outputs(
        staging,
        index,
        site_url=SITE_URL,
        source_commit=COMMIT,
    )

    graph = json.loads(
        (staging / "data" / "knowledge-graph.json").read_text(encoding="utf-8")
    )
    page = (staging / "wissensgraph" / "index.md").read_text(encoding="utf-8")
    assert result.graph == graph
    assert 'data-cheat-knowledge-graph' in page
    assert 'data-graph-source="../data/knowledge-graph.json"' in page
    assert 'class="cheat-graph-legend"' in page
    assert "<noscript>" in page
    assert "01-Test/index.html" in page


def test_mkdocs_and_ui_wire_graph_as_secondary_optional_feature() -> None:
    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    assert "/wissensgraph/**" in config["not_in_nav"]
    assert "assets/stylesheets/knowledge-graph.css" in config["extra_css"]
    assert "assets/javascripts/graph-shortcut.js" in config["extra_javascript"]
    assert "assets/javascripts/knowledge-graph.js" in config["extra_javascript"]

    local_state = (
        ROOT / "web" / "overrides" / "partials" / "local-state.html"
    ).read_text(encoding="utf-8")
    keyboard = (
        ROOT / "web" / "overrides" / "partials" / "keyboard-help.html"
    ).read_text(encoding="utf-8")
    shortcut = (
        ROOT / "web" / "assets" / "javascripts" / "graph-shortcut.js"
    ).read_text(encoding="utf-8")

    assert "Wissensgraph erkunden" in local_state
    assert "wissensgraph/index.html" in local_state
    assert "wissensgraph/" in local_state
    assert "g</kbd>, dann <kbd>w" in keyboard
    assert 'return offline ? "wissensgraph/index.html" : "wissensgraph/";' in shortcut
    assert 'key !== "w"' in shortcut
    assert (ROOT / "web" / "assets" / "stylesheets" / "knowledge-graph.css").is_file()
