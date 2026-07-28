#!/usr/bin/env python3
"""MkDocs-Hook für den optionalen, vollständig generierten Wissensgraphen."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from build_graph import GraphBuildError, write_graph_outputs
from content_index import build_content_index
from download_model import detect_source_commit

ROOT = Path(__file__).resolve().parents[1]


def build_graph_for_config(config: dict[str, Any], *, root: Path = ROOT) -> None:
    """Schreibe Graphseite und -daten vor der MkDocs-Dateiinventur."""

    docs_value = config.get("docs_dir")
    site_url = str(config.get("site_url") or "").strip()
    if not docs_value:
        raise GraphBuildError("MkDocs-Konfiguration besitzt kein docs_dir")
    if not site_url:
        raise GraphBuildError("MkDocs-Konfiguration besitzt keine site_url")

    docs_dir = Path(str(docs_value)).resolve()
    if docs_dir.is_symlink() or not docs_dir.is_dir():
        raise GraphBuildError(f"Generiertes MkDocs-docs_dir fehlt oder ist unsicher: {docs_dir}")

    index = build_content_index(root.resolve())
    write_graph_outputs(
        docs_dir,
        index,
        site_url=site_url,
        source_commit=detect_source_commit(root.resolve()),
    )


def on_config(config: Any, **_kwargs: Any) -> Any:
    build_graph_for_config(config)
    return config
