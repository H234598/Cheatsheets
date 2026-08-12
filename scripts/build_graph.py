#!/usr/bin/env python3
"""Deterministischen Cheatsheet-Wissensgraphen und seine Webansicht erzeugen.

Die GraphBuilder-, Edge-Aggregations- und Statistikmuster sind aus
``H234598/ADHS-Lernpfad`` übernommen und auf Kategorien, Fachseiten, Tags und
reale interne Links des Cheatsheets-Repositories reduziert. Referenzstand:
``93c8c02d263ec123c1c271caf0d2deaa76760ccb``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

from content_model import ContentIndex, PageRecord, json_compatible, normalize_key, slugify
from io_utils import atomic_write_text, generated_at_iso, stable_json_dumps
from link_resolution import resolve_occurrence
from link_types import scan_wikilinks

GRAPH_SCHEMA_VERSION = 1
GRAPH_DATA_PATH = PurePosixPath("data/knowledge-graph.json")
GRAPH_PAGE_PATH = PurePosixPath("wissensgraph/index.md")
GRAPH_VIEWBOX = {"width": 1200, "height": 900}
NODE_TYPES = {"category", "page", "tag"}
EDGE_TYPES = {"contains", "tagged", "links"}


class GraphBuildError(RuntimeError):
    """Der Wissensgraph ist unvollständig oder widersprüchlich."""


def normalize_site_url(value: str) -> str:
    split = urlsplit(value.strip())
    if split.scheme not in {"http", "https"} or not split.netloc:
        raise GraphBuildError(f"site_url muss eine vollständige HTTP(S)-URL sein: {value!r}")
    if split.query or split.fragment:
        raise GraphBuildError("site_url darf weder Query noch Fragment enthalten")
    path = split.path or "/"
    if not path.endswith("/"):
        path += "/"
    return urlunsplit((split.scheme, split.netloc, path, "", ""))


def absolute_page_url(site_url: str, page: PageRecord) -> str:
    return normalize_site_url(site_url).rstrip("/") + page.canonical_url


@dataclass(frozen=True, slots=True)
class GraphBuildResult:
    graph: dict[str, Any]
    markdown_pages: int = 1
    data_files: int = 1


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _edge_id(edge_type: str, source: str, target: str) -> str:
    return _stable_id("edge", f"{edge_type}\0{source}\0{target}")


def _category_node_id(category_id: str) -> str:
    return f"category:{category_id}"


def _tag_node_id(tag: str) -> str:
    return _stable_id("tag", normalize_key(tag))


def _tag_url(site_url: str, tag: str) -> str:
    base = normalize_site_url(site_url).rstrip("/")
    return f"{base}/index/tags/#{quote(slugify(tag), safe='-._~')}"


def _offline_page_url(page: PageRecord) -> str:
    return page.generated_path.with_suffix(".html").as_posix()


def _offline_tag_url(tag: str) -> str:
    return f"index/tags.html#{quote(slugify(tag), safe='-._~')}"


def _category_positions(index: ContentIndex) -> dict[str, tuple[float, float]]:
    categories = sorted(index.categories.values(), key=lambda item: item.number)
    center_x = GRAPH_VIEWBOX["width"] / 2
    center_y = GRAPH_VIEWBOX["height"] / 2
    radius = 220.0
    result: dict[str, tuple[float, float]] = {}
    for position, category in enumerate(categories):
        angle = -math.pi / 2 + (2 * math.pi * position / max(1, len(categories)))
        result[category.category_id] = (
            round(center_x + radius * math.cos(angle), 3),
            round(center_y + radius * math.sin(angle), 3),
        )
    return result


def _page_positions(index: ContentIndex) -> dict[str, tuple[float, float]]:
    categories = sorted(index.categories.values(), key=lambda item: item.number)
    result: dict[str, tuple[float, float]] = {}
    category_count = max(1, len(categories))
    sector_width = 2 * math.pi / category_count
    center_x = GRAPH_VIEWBOX["width"] / 2
    center_y = GRAPH_VIEWBOX["height"] / 2

    for category_position, category in enumerate(categories):
        pages = [index.pages[page_id] for page_id in category.reference_page_ids]
        center_angle = -math.pi / 2 + sector_width * category_position
        for page_position, page in enumerate(pages):
            band = page_position // 8
            slot = page_position % 8
            remaining = max(1, min(8, len(pages) - band * 8))
            spread = sector_width * 0.72
            angle = center_angle if remaining == 1 else (
                center_angle - spread / 2 + spread * slot / (remaining - 1)
            )
            radius = 335.0 + 62.0 * band
            result[page.page_id] = (
                round(center_x + radius * math.cos(angle), 3),
                round(center_y + radius * math.sin(angle), 3),
            )
    return result


def _tag_positions(tags: list[str]) -> dict[str, tuple[float, float]]:
    center_x = GRAPH_VIEWBOX["width"] / 2
    center_y = GRAPH_VIEWBOX["height"] / 2
    golden_angle = math.pi * (3 - math.sqrt(5))
    result: dict[str, tuple[float, float]] = {}
    for position, tag in enumerate(tags):
        radius = 18.0 + 13.5 * math.sqrt(position)
        angle = position * golden_angle
        result[_tag_node_id(tag)] = (
            round(center_x + radius * math.cos(angle), 3),
            round(center_y + radius * math.sin(angle), 3),
        )
    return result


def _display_tags(index: ContentIndex) -> list[str]:
    display: dict[str, str] = {}
    for page in index.reference_pages:
        for tag in page.tags:
            key = normalize_key(tag)
            if key:
                display.setdefault(key, tag)
    return [display[key] for key in sorted(display)]


def _add_edge(
    edges: dict[tuple[str, str, str], dict[str, Any]],
    edge_type: str,
    source: str,
    target: str,
    *,
    occurrence: dict[str, Any] | None = None,
) -> None:
    key = (edge_type, source, target)
    edge = edges.setdefault(
        key,
        {
            "id": _edge_id(edge_type, source, target),
            "type": edge_type,
            "source": source,
            "target": target,
            "count": 0,
            "occurrences": [],
        },
    )
    edge["count"] += 1
    if occurrence is not None and occurrence not in edge["occurrences"]:
        edge["occurrences"].append(occurrence)


def _page_link_edges(
    index: ContentIndex,
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    for page in index.reference_pages:
        for occurrence in scan_wikilinks(page.raw_text, page.source_path):
            resolution = resolve_occurrence(index, occurrence)
            target = resolution.page
            if not resolution.ok or target is None or not target.is_reference:
                continue
            _add_edge(
                edges,
                "links",
                page.page_id,
                target.page_id,
                occurrence={
                    "column": occurrence.column,
                    "label": occurrence.label,
                    "line": occurrence.line,
                    "path": page.relative_path.as_posix(),
                },
            )


def build_graph(
    index: ContentIndex,
    *,
    site_url: str,
    source_commit: str,
) -> dict[str, Any]:
    """Baue den vollständigen, deterministisch positionierten Wissensgraphen."""

    if index.error_count:
        raise GraphBuildError("Contentindex enthält blockierende Fehler")

    site_url = normalize_site_url(site_url)
    category_positions = _category_positions(index)
    page_positions = _page_positions(index)
    tags = _display_tags(index)
    tag_positions = _tag_positions(tags)
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}

    for category in sorted(index.categories.values(), key=lambda item: item.number):
        category_page = index.pages.get(category.index_page_id)
        if category_page is None:
            raise GraphBuildError(
                f"Kategorie {category.category_id} besitzt keine indexierte Landingpage"
            )
        x, y = category_positions[category.category_id]
        node_id = _category_node_id(category.category_id)
        nodes[node_id] = {
            "category_id": category.category_id,
            "id": node_id,
            "label": category.title,
            "page_count": len(category.reference_page_ids),
            "search": normalize_key(category.title),
            "type": "category",
            "offline_url": _offline_page_url(category_page),
            "url": absolute_page_url(site_url, category_page),
            "x": x,
            "y": y,
        }
        for page_id in category.reference_page_ids:
            _add_edge(edges, "contains", node_id, page_id)

    tag_pages: dict[str, list[str]] = {}
    tag_labels: dict[str, str] = {}
    for page in index.reference_pages:
        x, y = page_positions[page.page_id]
        nodes[page.page_id] = {
            "aliases": list(page.aliases),
            "category_id": page.category_id,
            "id": page.page_id,
            "label": page.title,
            "minutes": page.estimated_minutes,
            "search": normalize_key(" ".join((page.title, *page.aliases, *page.tags))),
            "source_path": page.relative_path.as_posix(),
            "tags": list(page.tags),
            "type": "page",
            "offline_url": _offline_page_url(page),
            "url": absolute_page_url(site_url, page),
            "x": x,
            "y": y,
        }
        for tag in page.tags:
            key = normalize_key(tag)
            if not key:
                continue
            tag_id = _tag_node_id(tag)
            tag_labels.setdefault(tag_id, tag)
            tag_pages.setdefault(tag_id, []).append(page.page_id)
            _add_edge(edges, "tagged", page.page_id, tag_id)

    for tag_id in sorted(tag_labels, key=lambda item: normalize_key(tag_labels[item])):
        label = tag_labels[tag_id]
        x, y = tag_positions[tag_id]
        pages = sorted(set(tag_pages[tag_id]))
        nodes[tag_id] = {
            "id": tag_id,
            "label": label,
            "page_count": len(pages),
            "pages": pages,
            "search": normalize_key(label),
            "type": "tag",
            "offline_url": _offline_tag_url(label),
            "url": _tag_url(site_url, label),
            "x": x,
            "y": y,
        }

    _page_link_edges(index, edges)

    for edge in edges.values():
        edge["occurrences"] = sorted(
            edge["occurrences"],
            key=lambda item: (
                str(item.get("path", "")),
                int(item.get("line", 0)),
                int(item.get("column", 0)),
                str(item.get("label", "")),
            ),
        )

    node_list = [nodes[node_id] for node_id in sorted(nodes)]
    edge_list = [edges[key] for key in sorted(edges)]
    graph: dict[str, Any] = {
        "edges": edge_list,
        "generated_at": generated_at_iso(),
        "nodes": node_list,
        "schema_version": GRAPH_SCHEMA_VERSION,
        "site_url": site_url,
        "source_commit": source_commit,
        "stats": {
            "edge_count": len(edge_list),
            "edges_by_type": dict(
                sorted(Counter(str(edge["type"]) for edge in edge_list).items())
            ),
            "node_count": len(node_list),
            "nodes_by_type": dict(
                sorted(Counter(str(node["type"]) for node in node_list).items())
            ),
        },
        "viewbox": GRAPH_VIEWBOX,
    }
    validate_graph_data(graph, index=index)
    return json_compatible(graph)


def validate_graph_data(
    graph: dict[str, Any],
    *,
    index: ContentIndex | None = None,
) -> dict[str, Any]:
    """Prüfe Schema, Endpunkte und Contentabdeckung des Graphen fail-closed."""

    if graph.get("schema_version") != GRAPH_SCHEMA_VERSION:
        raise GraphBuildError("Nicht unterstützte Wissensgraph-Schemaversion")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise GraphBuildError("Wissensgraph benötigt Knoten- und Kantenlisten")

    node_ids: set[str] = set()
    node_types: Counter[str] = Counter()
    for node in nodes:
        if not isinstance(node, dict):
            raise GraphBuildError("Wissensgraph enthält einen ungültigen Knoten")
        node_id = str(node.get("id") or "")
        node_type = str(node.get("type") or "")
        if not node_id or node_id in node_ids:
            raise GraphBuildError(f"Doppelte oder leere Knoten-ID: {node_id!r}")
        if node_type not in NODE_TYPES:
            raise GraphBuildError(f"Unbekannter Knotentyp: {node_type!r}")
        if not isinstance(node.get("x"), (int, float)) or not isinstance(
            node.get("y"), (int, float)
        ):
            raise GraphBuildError(f"Knoten besitzt keine numerische Position: {node_id}")
        node_ids.add(node_id)
        node_types[node_type] += 1

    edge_ids: set[str] = set()
    edge_types: Counter[str] = Counter()
    contains_by_page: Counter[str] = Counter()
    for edge in edges:
        if not isinstance(edge, dict):
            raise GraphBuildError("Wissensgraph enthält eine ungültige Kante")
        edge_id = str(edge.get("id") or "")
        edge_type = str(edge.get("type") or "")
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not edge_id or edge_id in edge_ids:
            raise GraphBuildError(f"Doppelte oder leere Kanten-ID: {edge_id!r}")
        if edge_type not in EDGE_TYPES:
            raise GraphBuildError(f"Unbekannter Kantentyp: {edge_type!r}")
        if source not in node_ids or target not in node_ids:
            raise GraphBuildError(
                f"Kante verweist auf unbekannten Endpunkt: {edge_id} ({source} → {target})"
            )
        if edge_type == "contains":
            contains_by_page[target] += 1
        edge_ids.add(edge_id)
        edge_types[edge_type] += 1

    if index is not None:
        expected_pages = {page.page_id for page in index.reference_pages}
        actual_pages = {
            str(node["id"]) for node in nodes if str(node.get("type")) == "page"
        }
        if actual_pages != expected_pages:
            raise GraphBuildError(
                "Wissensgraph und Fachseiteninventar weichen ab; "
                f"fehlend={sorted(expected_pages - actual_pages)}, "
                f"zusätzlich={sorted(actual_pages - expected_pages)}"
            )
        expected_categories = len(index.categories)
        if node_types["category"] != expected_categories:
            raise GraphBuildError(
                f"Wissensgraph enthält {node_types['category']} statt "
                f"{expected_categories} Kategorien"
            )
        wrong_membership = sorted(
            page_id for page_id in expected_pages if contains_by_page[page_id] != 1
        )
        if wrong_membership:
            raise GraphBuildError(
                "Fachseiten benötigen genau eine Kategoriezuordnung im Graphen: "
                + ", ".join(wrong_membership)
            )

    return {
        "edge_count": len(edges),
        "edges_by_type": dict(sorted(edge_types.items())),
        "node_count": len(nodes),
        "nodes_by_type": dict(sorted(node_types.items())),
    }


def _legend_html() -> str:
    return (
        '<section class="cheat-graph-legend" aria-labelledby="cheat-graph-legend-title">\n'
        '  <h2 id="cheat-graph-legend-title">Legende</h2>\n'
        '  <ul>\n'
        '    <li><span class="cheat-graph-symbol cheat-graph-symbol--category" aria-hidden="true"></span> Kategorie</li>\n'
        '    <li><span class="cheat-graph-symbol cheat-graph-symbol--page" aria-hidden="true"></span> Fachseite</li>\n'
        '    <li><span class="cheat-graph-symbol cheat-graph-symbol--tag" aria-hidden="true"></span> Tag</li>\n'
        '    <li><span class="cheat-graph-line cheat-graph-line--contains" aria-hidden="true"></span> gehört zu Kategorie</li>\n'
        '    <li><span class="cheat-graph-line cheat-graph-line--tagged" aria-hidden="true"></span> besitzt Tag</li>\n'
        '    <li><span class="cheat-graph-line cheat-graph-line--links" aria-hidden="true"></span> interner Querverweis</li>\n'
        '  </ul>\n'
        '</section>\n'
    )


def render_graph_page(graph: dict[str, Any], index: ContentIndex) -> str:
    stats = graph["stats"]
    lines = [
        "---\n",
        "title: Wissensgraph\n",
        "description: Kategorien, Fachseiten, Tags und Querverweise interaktiv erkunden\n",
        "hide:\n  - feedback\n",
        "---\n\n",
        "# Wissensgraph\n\n",
        "Der Graph wird bei jedem Build ausschließlich aus den veröffentlichten Cheatsheets erzeugt. Suche oder wähle einen Knoten, um seine direkten Beziehungen hervorzuheben.\n\n",
        '<div class="cheat-knowledge-graph" data-cheat-knowledge-graph '
        'data-graph-source="../data/knowledge-graph.json" aria-busy="true">\n',
        '  <p class="cheat-graph-status" data-cheat-graph-status role="status" aria-live="polite">Wissensgraph wird geladen …</p>\n',
        '  <div data-cheat-graph-controls hidden></div>\n',
        '  <div class="cheat-graph-stage" data-cheat-graph-stage tabindex="0" '
        'aria-label="Interaktiver Wissensgraph" hidden></div>\n',
        '  <section class="cheat-graph-details" data-cheat-graph-details '
        'aria-labelledby="cheat-graph-details-title" hidden>\n',
        '    <h2 id="cheat-graph-details-title">Ausgewählter Knoten</h2>\n',
        '    <div data-cheat-graph-details-body></div>\n',
        '  </section>\n',
        _legend_html(),
        '</div>\n\n',
        '<noscript>\n',
        '  <section class="cheat-graph-noscript" aria-labelledby="cheat-graph-noscript-title">\n',
        '    <h2 id="cheat-graph-noscript-title">Ohne JavaScript</h2>\n',
        '    <p>Die interaktive Darstellung benötigt JavaScript. Alle Fachseiten bleiben über die folgenden Kategorien erreichbar.</p>\n',
        '    <ul>\n',
    ]
    for category in sorted(index.categories.values(), key=lambda item: item.number):
        category_page = index.pages[category.index_page_id]
        lines.append(
            f'      <li><a href="../{category_page.generated_path.with_suffix(".html").as_posix()}">'
            f"{category.title}</a> ({len(category.reference_page_ids)} Fachseiten)</li>\n"
        )
    lines.extend(
        [
            '    </ul>\n',
            '  </section>\n',
            '</noscript>\n\n',
            f"{stats['nodes_by_type']['page']} Fachseiten, "
            f"{stats['nodes_by_type']['category']} Kategorien und "
            f"{stats['nodes_by_type'].get('tag', 0)} Tags werden dargestellt.\n",
        ]
    )
    return "".join(lines)


def write_graph_outputs(
    staging: Path,
    index: ContentIndex,
    *,
    site_url: str,
    source_commit: str,
) -> GraphBuildResult:
    graph = build_graph(index, site_url=site_url, source_commit=source_commit)
    atomic_write_text(staging / GRAPH_DATA_PATH, stable_json_dumps(graph))
    atomic_write_text(staging / GRAPH_PAGE_PATH, render_graph_page(graph, index))
    return GraphBuildResult(graph=graph)
