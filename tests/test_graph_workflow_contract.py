from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATE = ROOT / ".github" / "workflows" / "validate.yml"
PAGES = ROOT / ".github" / "workflows" / "pages.yml"


def test_validate_workflow_compiles_and_validates_graph_outputs() -> None:
    text = VALIDATE.read_text(encoding="utf-8")
    assert "node --check web/assets/javascripts/knowledge-graph.js" in text
    assert "node --check tests/web/graph.spec.mjs" in text
    assert text.count("python scripts/validate_graph.py") == 1
    assert "--graph build/docs/data/knowledge-graph.json" in text
    assert "--site-dir site" in text
    assert "--report build/reports/knowledge-graph.json" in text
    assert text.index("python scripts/build_site.py") < text.index(
        "python scripts/validate_graph.py"
    )
    assert text.index("python scripts/validate_graph.py") < text.index(
        "npm run test:web"
    )


def test_pages_workflow_validates_graph_before_upload() -> None:
    text = PAGES.read_text(encoding="utf-8")
    assert text.count("python scripts/validate_graph.py") == 1
    assert "--graph build/docs/data/knowledge-graph.json" in text
    assert "--site-dir site" in text
    assert "--report build/reports/knowledge-graph.json" in text
    assert text.index("python scripts/build_site.py") < text.index(
        "python scripts/validate_graph.py"
    )
    assert text.index("python scripts/validate_graph.py") < text.index(
        "actions/upload-pages-artifact@"
    )
