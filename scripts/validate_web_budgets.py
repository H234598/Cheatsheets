#!/usr/bin/env python3
"""Statische Größen- und Laufzeitassetbudgets des gebauten Webbaums prüfen."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gzip
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Sequence
from urllib.parse import urlsplit

from io_utils import atomic_write_text, stable_json_dumps

CUSTOM_JAVASCRIPT = (
    "assets/javascripts/site-state.js",
    "assets/javascripts/filters.js",
    "assets/javascripts/mermaid-loader.js",
)
CUSTOM_STYLESHEETS = ("assets/stylesheets/extra.css",)
CUSTOM_JS_GZIP_LIMIT = 30 * 1024
CUSTOM_CSS_GZIP_LIMIT = 35 * 1024
SINGLE_HTML_LIMIT = 2 * 1024 * 1024
RUNTIME_URL_ATTRIBUTES: dict[str, tuple[str, ...]] = {
    "audio": ("src",),
    "embed": ("src",),
    "iframe": ("src",),
    "img": ("src", "srcset"),
    "input": ("src",),
    "link": ("href",),
    "object": ("data",),
    "script": ("src",),
    "source": ("src", "srcset"),
    "track": ("src",),
    "video": ("src", "poster"),
}
CSS_EXTERNAL_URL_RE = re.compile(r"url\(\s*['\"]?(https?://[^)'\"\s]+)", re.I)


@dataclass(frozen=True, slots=True)
class BudgetIssue:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


class RuntimeAssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []

    @staticmethod
    def _srcset_urls(value: str) -> list[str]:
        return [candidate.strip().split()[0] for candidate in value.split(",") if candidate.strip()]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        names = RUNTIME_URL_ATTRIBUTES.get(tag.casefold())
        if not names:
            return
        values = {name.casefold(): value or "" for name, value in attrs}
        if tag.casefold() == "link":
            rel = {part.casefold() for part in values.get("rel", "").split()}
            if not rel.intersection({"stylesheet", "preload", "modulepreload", "icon", "manifest"}):
                return
        for name in names:
            value = values.get(name, "").strip()
            if not value:
                continue
            if name == "srcset":
                self.urls.extend(self._srcset_urls(value))
            else:
                self.urls.append(value)


def gzip_size(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), compresslevel=9, mtime=0))


def _is_external_runtime_url(value: str) -> bool:
    split = urlsplit(value)
    return split.scheme.casefold() in {"http", "https"} and bool(split.netloc)


def analyze_web_budgets(site_dir: Path) -> tuple[list[BudgetIssue], dict[str, object]]:
    site_dir = site_dir.resolve()
    issues: list[BudgetIssue] = []
    javascript: dict[str, dict[str, int]] = {}
    stylesheets: dict[str, dict[str, int]] = {}

    for relative in CUSTOM_JAVASCRIPT:
        path = site_dir / relative
        if not path.is_file() or path.is_symlink():
            issues.append(BudgetIssue("WB001", "Eigenes JavaScript fehlt oder ist unsicher", relative))
            continue
        javascript[relative] = {"bytes": path.stat().st_size, "gzip_bytes": gzip_size(path)}
    for relative in CUSTOM_STYLESHEETS:
        path = site_dir / relative
        if not path.is_file() or path.is_symlink():
            issues.append(BudgetIssue("WB002", "Eigenes Stylesheet fehlt oder ist unsicher", relative))
            continue
        stylesheets[relative] = {"bytes": path.stat().st_size, "gzip_bytes": gzip_size(path)}

    javascript_gzip = sum(item["gzip_bytes"] for item in javascript.values())
    stylesheet_gzip = sum(item["gzip_bytes"] for item in stylesheets.values())
    if javascript_gzip > CUSTOM_JS_GZIP_LIMIT:
        issues.append(
            BudgetIssue(
                "WB010",
                f"Eigenes JavaScript überschreitet {CUSTOM_JS_GZIP_LIMIT} Gzip-Bytes: {javascript_gzip}",
                "assets/javascripts",
            )
        )
    if stylesheet_gzip > CUSTOM_CSS_GZIP_LIMIT:
        issues.append(
            BudgetIssue(
                "WB011",
                f"Eigenes CSS überschreitet {CUSTOM_CSS_GZIP_LIMIT} Gzip-Bytes: {stylesheet_gzip}",
                "assets/stylesheets/extra.css",
            )
        )

    html_files = sorted(site_dir.rglob("*.html"), key=lambda item: item.as_posix().casefold())
    largest_html = {"bytes": 0, "path": ""}
    external_runtime: list[dict[str, str]] = []
    for path in html_files:
        relative = path.relative_to(site_dir).as_posix()
        size = path.stat().st_size
        if size > largest_html["bytes"]:
            largest_html = {"bytes": size, "path": relative}
        if size > SINGLE_HTML_LIMIT:
            issues.append(
                BudgetIssue(
                    "WB012",
                    f"HTML-Datei überschreitet {SINGLE_HTML_LIMIT} Bytes: {size}",
                    relative,
                )
            )
        parser = RuntimeAssetParser()
        parser.feed(path.read_text(encoding="utf-8"))
        for url in parser.urls:
            if _is_external_runtime_url(url):
                external_runtime.append({"path": relative, "url": url})
                issues.append(
                    BudgetIssue("WB020", f"Externes Laufzeitasset: {url}", relative)
                )

    for path in sorted(site_dir.rglob("*.css"), key=lambda item: item.as_posix().casefold()):
        relative = path.relative_to(site_dir).as_posix()
        text = path.read_text(encoding="utf-8")
        for match in CSS_EXTERNAL_URL_RE.finditer(text):
            url = match.group(1)
            external_runtime.append({"path": relative, "url": url})
            issues.append(BudgetIssue("WB021", f"Externes CSS-Laufzeitasset: {url}", relative))

    report: dict[str, object] = {
        "budgets": {
            "custom_css_gzip_bytes": CUSTOM_CSS_GZIP_LIMIT,
            "custom_javascript_gzip_bytes": CUSTOM_JS_GZIP_LIMIT,
            "single_html_bytes": SINGLE_HTML_LIMIT,
        },
        "external_runtime_assets": external_runtime,
        "html_files": len(html_files),
        "issues": [issue.as_dict() for issue in issues],
        "javascript": javascript,
        "largest_html": largest_html,
        "schema_version": 1,
        "stylesheets": stylesheets,
        "summary": {
            "custom_css_gzip_bytes": stylesheet_gzip,
            "custom_javascript_gzip_bytes": javascript_gzip,
            "errors": len(issues),
        },
    }
    return issues, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prüft Größenbudgets und externe Laufzeitassets der gebauten Site."
    )
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    issues, report = analyze_web_budgets(args.site_dir)
    if args.report:
        atomic_write_text(args.report, stable_json_dumps(report))
    if issues:
        print("Webbudgets fehlgeschlagen:")
        for issue in issues:
            print(f"- {issue.path}: {issue.code}: {issue.message}")
        return 1
    summary = report["summary"]
    print(
        "Webbudgets erfolgreich: "
        f"JS {summary['custom_javascript_gzip_bytes']} Gzip-Bytes, "
        f"CSS {summary['custom_css_gzip_bytes']} Gzip-Bytes, "
        f"{report['html_files']} HTML-Dateien, keine externen Laufzeitassets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
