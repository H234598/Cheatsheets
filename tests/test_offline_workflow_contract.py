from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_workflow(name: str) -> dict[str, Any]:
    path = ROOT / ".github" / "workflows" / name
    payload = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def run_commands(payload: dict[str, Any]) -> str:
    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    commands: list[str] = []
    for raw_job in jobs.values():
        assert isinstance(raw_job, dict)
        steps = raw_job.get("steps", [])
        assert isinstance(steps, list)
        for step in steps:
            if isinstance(step, dict):
                commands.append(str(step.get("run", "")))
    return "\n".join(commands)


def test_validate_workflow_independently_extracts_and_tests_offline_archive() -> None:
    payload = load_workflow("validate.yml")
    commands = run_commands(payload)

    assert "python scripts/validate_offline_archive.py" in commands
    assert "--archive site/downloads/files/Cheatsheets-Offline-HTML.zip" in commands
    assert "--extract build/offline-site" in commands
    assert "--report build/reports/offline.json" in commands
    assert "node --check tests/web/offline.spec.mjs" in commands
    assert "npm run test:web" in commands

    jobs = payload["jobs"]
    validate = jobs["validate"]
    browser_step = next(
        step
        for step in validate["steps"]
        if isinstance(step, dict)
        and step.get("name") == "Browser-, Accessibility- und Mobiltests"
    )
    environment = browser_step.get("env")
    assert environment == {
        "CI": "true",
        "SITE_DIR": "site",
        "WEB_TEST_BASE_PATH": "/Cheatsheets/",
        "WEB_TEST_PORT": "4173",
        "OFFLINE_SITE_DIR": "build/offline-site",
        "OFFLINE_TEST_PORT": "4174",
    }


def test_pages_workflow_validates_offline_archive_without_rebuilding_in_deploy() -> None:
    payload = load_workflow("pages.yml")
    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    build = jobs["build"]
    deploy = jobs["deploy"]
    assert isinstance(build, dict) and isinstance(deploy, dict)

    build_commands = "\n".join(
        str(step.get("run", ""))
        for step in build.get("steps", [])
        if isinstance(step, dict)
    )
    deploy_commands = "\n".join(
        str(step.get("run", ""))
        for step in deploy.get("steps", [])
        if isinstance(step, dict)
    )

    assert "python scripts/build_site.py" in build_commands
    assert "python scripts/validate_offline_archive.py" in build_commands
    assert "--report build/reports/offline.json" in build_commands
    assert "--extract" not in build_commands
    assert "build_site.py" not in deploy_commands
    assert "validate_offline_archive.py" not in deploy_commands
    assert deploy.get("needs") == "build"
