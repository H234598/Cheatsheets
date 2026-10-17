#!/usr/bin/env python3
"""Generierten Wissensgraphen gegen Contentindex und HTML-Vertrag prüfen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from build_graph import GraphBuildError, validate_graph_data
from content_index import build_content_index
from io_utils import atomic_write_text, stable_json_dumps


class GraphValidationError(RuntimeError):
    """Der generierte Graph oder seine Seite verletzt den Veröffentlichungsvertrag."""


def _load_graph(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise GraphValidationError(f"Graphdatei fehlt oder ist unsicher: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GraphValidationError(f"Graphdatei ist nicht lesbares JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise GraphValidationError("Graphdatei muss ein JSON-Objekt enthalten")
    return payload


def validate_graph_outputs(root: Path, graph_path: Path, site_dir: Path) -> dict[str, Any]:
    root = root.resolve()
    graph_path = graph_path.resolve()
    site_dir = site_dir.resolve()
    try:
        graph_path.relative_to(root)
        site_dir.relative_to(root)
    except ValueError as exc:
        raise GraphValidationError("Graph- oder Sitepfad verlässt die Repositorywurzel") from exc

    graph = _load_graph(graph_path)
    index = build_content_index(root)
    errors = [issue.format() for issue in index.issues if issue.severity == "error"]
    if errors:
        raise GraphValidationError(
            "Contentindex ist vor der Graphprüfung ungültig:\n" + "\n".join(errors[:25])
        )
    metrics = validate_graph_data(graph, index=index)

    page = site_dir / "wissensgraph" / "index.html"
    if page.is_symlink() or not page.is_file():
        raise GraphValidationError(f"Gerenderte Wissensgraph-Seite fehlt: {page}")
    html = page.read_text(encoding="utf-8")
    required = (
        "data-cheat-knowledge-graph",
        'data-graph-source="../data/knowledge-graph.json"',
        'class="cheat-graph-legend"',
        "<noscript>",
    )
    missing = [needle for needle in required if needle not in html]
    if missing:
        raise GraphValidationError(
            "Gerenderte Wissensgraph-Seite vermisst Vertragsmerkmale: "
            + ", ".join(missing)
        )

    data_copy = site_dir / "data" / "knowledge-graph.json"
    if data_copy.is_symlink() or not data_copy.is_file():
        raise GraphValidationError("Wissensgraph-Datendatei fehlt im Pages-Artefakt")
    if json.loads(data_copy.read_text(encoding="utf-8")) != graph:
        raise GraphValidationError("Pages-Kopie des Wissensgraphen weicht von build/docs ab")

    return {
        **metrics,
        "graph": graph_path.relative_to(root).as_posix(),
        "graph_page": page.relative_to(root).as_posix(),
        "schema_version": 1,
        "source_commit": graph.get("source_commit"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prüft Wissensgraph, Contentabdeckung und gerenderte Graphseite."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--graph", type=Path, default=Path("build/docs/data/knowledge-graph.json")
    )
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    graph = args.graph if args.graph.is_absolute() else root / args.graph
    site_dir = args.site_dir if args.site_dir.is_absolute() else root / args.site_dir
    try:
        report = validate_graph_outputs(root, graph, site_dir)
        if args.report:
            target = args.report if args.report.is_absolute() else root / args.report
            try:
                target.resolve().relative_to((root / "build").resolve())
            except ValueError as exc:
                raise GraphValidationError("Graphbericht muss unter build/ liegen") from exc
            atomic_write_text(target, stable_json_dumps(report))
        print(
            "Wissensgraph erfolgreich geprüft: "
            f"{report['node_count']} Knoten, {report['edge_count']} Kanten."
        )
        return 0
    except (GraphBuildError, GraphValidationError, OSError, ValueError) as exc:
        print(f"Wissensgraph-Prüfung fehlgeschlagen: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
