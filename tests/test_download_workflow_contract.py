from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"


def workflow_text(name: str) -> str:
    return (WORKFLOW_DIR / name).read_text(encoding="utf-8")


def test_validate_and_pages_build_downloads_exactly_once_after_site_build() -> None:
    for name in ("validate.yml", "pages.yml"):
        text = workflow_text(name)
        assert text.count("python scripts/build_site.py") == 1
        assert text.count("python scripts/build_downloads.py") == 1
        assert text.count("python scripts/validate_pages_artifact.py") == 1
        assert text.index("python scripts/build_site.py") < text.index(
            "python scripts/build_downloads.py"
        )
        assert text.index("python scripts/build_downloads.py") < text.index(
            "python scripts/validate_pages_artifact.py"
        )
        assert "--report build/reports/downloads.json" in text


def test_pages_deploy_job_never_builds_or_reads_sources() -> None:
    text = workflow_text("pages.yml")
    deploy = text.split("\n  deploy:\n", 1)[1]

    assert "scripts/build_downloads.py" not in deploy
    assert "scripts/build_site.py" not in deploy
    assert "actions/checkout" not in deploy
    assert "secrets." not in deploy


def test_download_generation_receives_the_same_site_url_as_mkdocs() -> None:
    pages = workflow_text("pages.yml")
    validate = workflow_text("validate.yml")

    assert pages.count('${SITE_URL%/}/') >= 2
    assert "--site-url https://example.invalid/Cheatsheets/" in validate
    assert validate.count("https://example.invalid/Cheatsheets/") >= 2


def test_download_report_is_inside_the_existing_diagnostic_artifact() -> None:
    validate = workflow_text("validate.yml")

    assert "--report build/reports/downloads.json" in validate
    assert "path: build/reports" in validate
    assert "if: always()" in validate
