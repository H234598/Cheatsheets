from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_dependabot_updates_actions_and_python_weekly_in_berlin() -> None:
    payload = yaml.safe_load(
        (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    )

    assert payload["version"] == 2
    updates = payload["updates"]
    assert {item["package-ecosystem"] for item in updates} == {
        "github-actions",
        "pip",
    }
    assert all(item["directory"] == "/" for item in updates)
    assert all(item["target-branch"] == "main" for item in updates)
    assert all(item["schedule"]["interval"] == "weekly" for item in updates)
    assert all(item["schedule"]["timezone"] == "Europe/Berlin" for item in updates)
    assert all(item["open-pull-requests-limit"] <= 5 for item in updates)
    assert all(len(item["groups"]) == 1 for item in updates)
