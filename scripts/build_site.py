#!/usr/bin/env python3
"""Zentrale CLI für den reproduzierbaren Cheatsheets-Webbuild."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Sequence

import yaml

from build_docs import BuildDocsError, build_docs, source_tree_hashes
from build_downloads import build_downloads, copy_downloads_to_site
from build_navigation import (
    NavigationError,
    build_navigation,
    load_publication_config,
    normalize_site_url,
    validate_publication_config,
)
from content_index import build_content_index
from download_metadata import write_landing_page
from download_model import DownloadBuildError, detect_source_commit
from io_utils import (
    UnsafePathError,
    atomic_write_text,
    mark_generated_root,
    staged_directory,
)


class BuildSiteError(RuntimeError):
    """Die statische Website konnte nicht vollständig erzeugt werden."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validiert und baut die Cheatsheets-Webseite, ohne kanonische "
            "Markdown-Quellen zu verändern."
        )
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("build/docs"))
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    parser.add_argument("--site-url")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-pages", type=int)
    return parser


def validate_cli_combination(args: argparse.Namespace) -> None:
    if args.check and args.dry_run:
        raise ValueError("--check und --dry-run dürfen nicht kombiniert werden")
    if args.max_pages is not None and args.max_pages < 1:
        raise ValueError("--max-pages muss mindestens 1 sein")
    if args.max_pages is not None and args.strict:
        raise ValueError("--max-pages ist mit --strict unvereinbar")
    if args.max_pages is not None and not args.dry_run:
        raise ValueError("--max-pages ist ausschließlich für --dry-run vorgesehen")


def _load_base_config(root: Path) -> dict[str, Any]:
    path = root / "mkdocs.yml"
    if not path.is_file():
        raise BuildSiteError(f"MkDocs-Konfiguration fehlt: {path}")
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BuildSiteError(f"Ungültige mkdocs.yml: {exc}") from exc
    if not isinstance(loaded, dict):
        raise BuildSiteError("mkdocs.yml muss ein YAML-Mapping sein")
    return loaded


def resolve_site_url(root: Path, requested: str | None) -> str:
    """Bestimme die einzige wirksame Site-URL und validiere sie vollständig."""

    config = _load_base_config(root)
    configured = requested or str(config.get("site_url") or "").strip()
    if not configured:
        raise BuildSiteError("Eine vollständige --site-url ist erforderlich")
    try:
        return normalize_site_url(configured)
    except NavigationError as exc:
        raise BuildSiteError(str(exc)) from exc


def write_generated_config(
    root: Path,
    config_path: Path,
    *,
    docs_dir: Path,
    site_dir: Path,
    site_url: str | None,
    nav: list[dict[str, object]] | None = None,
) -> dict[str, Any]:
    """Schreibe eine strukturierte temporäre MkDocs-Konfiguration."""

    config = _load_base_config(root)
    config["site_url"] = resolve_site_url(root, site_url)
    config["docs_dir"] = str(docs_dir.resolve())
    config["site_dir"] = str(site_dir.resolve())
    config["strict"] = True
    if nav is not None:
        config["nav"] = nav

    theme = config.setdefault("theme", {})
    if not isinstance(theme, dict):
        raise BuildSiteError("theme in mkdocs.yml muss ein Mapping sein")
    custom_dir = theme.get("custom_dir")
    if custom_dir:
        custom_path = Path(str(custom_dir))
        if not custom_path.is_absolute():
            custom_path = root / custom_path
        theme["custom_dir"] = str(custom_path.resolve())

    config_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        config_path,
        yaml.safe_dump(
            config,
            allow_unicode=True,
            sort_keys=False,
            width=100,
        ),
    )
    return config


def run_mkdocs(config_path: Path) -> None:
    if importlib.util.find_spec("mkdocs") is None:
        raise BuildSiteError(
            "MkDocs ist nicht installiert. Ausführen: "
            "python -m pip install -r requirements-docs.txt"
        )
    command = [
        sys.executable,
        "-m",
        "mkdocs",
        "build",
        "--config-file",
        str(config_path),
        "--strict",
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise BuildSiteError(f"MkDocs-Build fehlgeschlagen (Exit {exc.returncode})") from exc


def _assert_site(site_dir: Path) -> None:
    required = [site_dir / "index.html", site_dir / "404.html"]
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise BuildSiteError(
            "MkDocs-Ausgabe ist unvollständig; fehlend: " + ", ".join(missing)
        )
    symlinks = [path for path in site_dir.rglob("*") if path.is_symlink()]
    if symlinks:
        raise BuildSiteError(
            "MkDocs-Ausgabe enthält symbolische Links: "
            + ", ".join(path.relative_to(site_dir).as_posix() for path in symlinks[:10])
        )


def _dry_run(root: Path, max_pages: int | None, verbose: bool) -> int:
    index = build_content_index(root)
    errors = [issue for issue in index.issues if issue.severity == "error"]
    publishable = [
        page
        for page in index.pages.values()
        if page.page_type in {
            "reference",
            "category-index",
            "root-landing",
            "root-index",
            "root-readme",
            "maintenance",
        }
    ]
    if max_pages is not None:
        publishable = sorted(
            publishable,
            key=lambda page: page.generated_path.as_posix().casefold(),
        )[:max_pages]
    if not errors:
        publication = load_publication_config(root)
        validate_publication_config(publication, index)
        build_navigation(index)
    if verbose:
        for page in publishable:
            print(f"PLAN {page.relative_path.as_posix()} -> {page.generated_path.as_posix()}")
    print(
        f"Dry-Run: {len(publishable)} HTML-Quellseiten geplant, "
        f"{len(errors)} blockierende Modellfehler."
    )
    return 0 if not errors else 2


def build_site(
    root: Path,
    output: Path,
    site_dir: Path,
    *,
    site_url: str | None,
    strict: bool,
    force: bool,
    config_path: Path | None = None,
) -> tuple[int, int]:
    root = root.resolve()
    output = output if output.is_absolute() else root / output
    site_dir = site_dir if site_dir.is_absolute() else root / site_dir
    config_path = config_path or (root / "build" / "mkdocs.generated.yml")
    config_path = config_path if config_path.is_absolute() else root / config_path

    configured_site_url = resolve_site_url(root, site_url)
    source_commit = detect_source_commit(root)
    before = source_tree_hashes(root)
    index = build_content_index(root)
    download_result = build_downloads(
        root,
        output.parent / "downloads",
        index=index,
        source_commit=source_commit,
        strict=strict,
        force=force,
    )
    docs_result = build_docs(
        root,
        output,
        index=index,
        strict=strict,
        force=force,
        site_url=configured_site_url,
        source_commit=source_commit,
    )
    write_landing_page(docs_result.output / "downloads" / "index.md", download_result)

    with staged_directory(
        site_dir,
        allowed_root=site_dir.parent.resolve(),
        force=force,
    ) as staging_site:
        write_generated_config(
            root,
            config_path,
            docs_dir=docs_result.output,
            site_dir=staging_site,
            site_url=configured_site_url,
            nav=docs_result.navigation,
        )
        run_mkdocs(config_path)
        copy_downloads_to_site(download_result, staging_site)
        _assert_site(staging_site)
        mark_generated_root(staging_site)

    after = source_tree_hashes(root)
    if before != after:
        raise BuildSiteError("Der Gesamtbuild hat kanonische Quelldateien verändert")
    return docs_result.pages, docs_result.assets


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate_cli_combination(args)
        root = args.root.resolve()
        if args.dry_run:
            return _dry_run(root, args.max_pages, args.verbose)

        if args.check:
            with tempfile.TemporaryDirectory(prefix="cheatsheets-check-") as temporary:
                temp = Path(temporary)
                pages, assets = build_site(
                    root,
                    temp / "docs",
                    temp / "site",
                    site_url=args.site_url,
                    strict=True,
                    force=True,
                    config_path=temp / "mkdocs.generated.yml",
                )
        else:
            pages, assets = build_site(
                root,
                args.output,
                args.site_dir,
                site_url=args.site_url,
                strict=args.strict,
                force=args.force,
            )
        print(f"Build erfolgreich: {pages} HTML-Quellseiten und {assets} Assets.")
        return 0
    except (
        BuildDocsError,
        DownloadBuildError,
        BuildSiteError,
        NavigationError,
        UnsafePathError,
        ValueError,
    ) as exc:
        print(f"Build fehlgeschlagen: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
