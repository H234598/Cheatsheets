from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from validate_pages_artifact import main, validate_pages_artifact


def make_site(root: Path) -> Path:
    site = root / "site"
    (site / "assets").mkdir(parents=True)
    (site / "index.html").write_text("<h1>Start</h1>\n", encoding="utf-8")
    (site / "404.html").write_text("<h1>Nicht gefunden</h1>\n", encoding="utf-8")
    (site / "assets" / "app.js").write_text("console.log('ok');\n", encoding="utf-8")
    return site


def test_valid_artifact_reports_stable_tree_hash(tmp_path: Path) -> None:
    site = make_site(tmp_path)

    first = validate_pages_artifact(site)
    second = validate_pages_artifact(site)

    assert first.ok and second.ok
    assert first.files == 3
    assert first.total_bytes > 0
    assert first.tree_sha256 == second.tree_sha256


def test_required_root_pages_are_mandatory(tmp_path: Path) -> None:
    site = make_site(tmp_path)
    (site / "404.html").unlink()

    report = validate_pages_artifact(site)

    assert not report.ok
    assert any(issue.code == "PA004" and issue.path == "404.html" for issue in report.issues)


def test_symlink_is_rejected_without_following_external_target(tmp_path: Path) -> None:
    site = make_site(tmp_path)
    external = tmp_path / "external-secret.txt"
    external.write_text("DO_NOT_PUBLISH\n", encoding="utf-8")
    link = site / "assets" / "linked.txt"
    try:
        link.symlink_to(external)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlinks werden auf dieser Plattform nicht unterstützt: {exc}")

    report = validate_pages_artifact(site)

    assert any(issue.code == "PA007" for issue in report.issues)
    assert all("DO_NOT_PUBLISH" not in issue.message for issue in report.issues)


def test_hardlink_is_rejected(tmp_path: Path) -> None:
    site = make_site(tmp_path)
    source = site / "assets" / "app.js"
    linked = site / "assets" / "app-copy.js"
    try:
        os.link(source, linked)
    except OSError as exc:
        pytest.skip(f"Hardlinks werden auf dieser Plattform nicht unterstützt: {exc}")

    report = validate_pages_artifact(site)

    hardlink_paths = {issue.path for issue in report.issues if issue.code == "PA009"}
    assert {"assets/app.js", "assets/app-copy.js"}.issubset(hardlink_paths)


def test_size_limit_is_enforced(tmp_path: Path) -> None:
    site = make_site(tmp_path)

    report = validate_pages_artifact(site, max_bytes=1)

    assert any(issue.code == "PA011" for issue in report.issues)


def test_cli_writes_machine_readable_report(tmp_path: Path) -> None:
    site = make_site(tmp_path)
    report_path = tmp_path / "reports" / "pages.json"

    exit_code = main(
        [
            "--site-dir",
            str(site),
            "--report",
            str(report_path),
        ]
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["summary"] == {"errors": 0}
    assert payload["files"] == 3
    assert len(payload["tree_sha256"]) == 64
