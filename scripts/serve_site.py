#!/usr/bin/env python3
"""Gebauten Pages-Baum lokal unter einem Project-Page-Basispfad ausliefern."""

from __future__ import annotations

import argparse
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Sequence
from urllib.parse import urlsplit, urlunsplit


class SiteServerError(RuntimeError):
    """Lokaler Browsertestserver kann nicht sicher gestartet werden."""


def normalize_base_path(value: str) -> str:
    candidate = value.strip()
    if not candidate.startswith("/"):
        raise SiteServerError("base-path muss mit / beginnen")
    if "?" in candidate or "#" in candidate or "\\" in candidate:
        raise SiteServerError("base-path darf weder Query, Fragment noch Backslash enthalten")
    parts = candidate.split("/")
    if any(part in {".", ".."} for part in parts):
        raise SiteServerError("base-path darf keine Punktsegmente enthalten")
    if not candidate.endswith("/"):
        candidate += "/"
    while "//" in candidate:
        candidate = candidate.replace("//", "/")
    return candidate


def translate_mounted_request(
    request_target: str,
    base_path: str,
) -> tuple[str | None, str | None, HTTPStatus | None]:
    """Übersetze einen Request in den gemounteten Sitebaum oder eine Weiterleitung."""

    base_path = normalize_base_path(base_path)
    split = urlsplit(request_target)
    path = split.path

    if base_path != "/":
        if path == "/":
            return None, base_path, HTTPStatus.FOUND
        if path == base_path.rstrip("/"):
            return None, base_path, HTTPStatus.MOVED_PERMANENTLY
        if not path.startswith(base_path):
            return None, None, None
        relative = "/" + path[len(base_path) :]
    else:
        if not path.startswith("/"):
            return None, None, None
        relative = path or "/"

    translated = urlunsplit(("", "", relative, split.query, ""))
    return translated, None, None


class MountedSiteHandler(SimpleHTTPRequestHandler):
    """Mountet genau ein reguläres Siteverzeichnis unter ``base_path``."""

    base_path = "/"
    site_root = Path(".")
    verbose = False

    def _mounted_path(self) -> bool:
        translated, redirect, status = translate_mounted_request(
            self.path,
            self.base_path,
        )
        if redirect is not None and status is not None:
            self.send_response(status)
            self.send_header("Location", redirect)
            self.end_headers()
            return False
        if translated is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return False
        self.path = translated
        return True

    def do_GET(self) -> None:  # noqa: N802 - API der Standardbibliothek
        if self._mounted_path():
            super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802 - API der Standardbibliothek
        if self._mounted_path():
            super().do_HEAD()

    def send_error(
        self,
        code: int,
        message: str | None = None,
        explain: str | None = None,
    ) -> None:
        if code == HTTPStatus.NOT_FOUND:
            page = self.site_root / "404.html"
            if page.is_file() and not page.is_symlink():
                payload = page.read_bytes()
                self.send_response(HTTPStatus.NOT_FOUND, message)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(payload)
                return
        super().send_error(code, message, explain)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        if self.verbose:
            super().log_message(format, *args)


def configured_handler(
    *,
    site_root: Path,
    base_path: str,
    verbose: bool,
):
    class ConfiguredMountedSiteHandler(MountedSiteHandler):
        pass

    ConfiguredMountedSiteHandler.site_root = site_root
    ConfiguredMountedSiteHandler.base_path = base_path
    ConfiguredMountedSiteHandler.verbose = verbose
    return partial(ConfiguredMountedSiteHandler, directory=str(site_root))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Liefert site/ für Playwright unter einem Pages-Basispfad aus."
    )
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    parser.add_argument("--base-path", default="/Cheatsheets/")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    site_root = args.site_dir.resolve()
    if not site_root.is_dir() or site_root.is_symlink():
        raise SiteServerError(f"Siteverzeichnis fehlt oder ist unsicher: {site_root}")
    if not (site_root / "index.html").is_file():
        raise SiteServerError(f"index.html fehlt unter {site_root}")
    if args.port < 1 or args.port > 65535:
        raise SiteServerError("port muss zwischen 1 und 65535 liegen")

    base_path = normalize_base_path(args.base_path)
    handler = configured_handler(
        site_root=site_root,
        base_path=base_path,
        verbose=args.verbose,
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        f"Cheatsheets-Testserver: http://{args.host}:{args.port}{base_path}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
