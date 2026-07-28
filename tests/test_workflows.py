from __future__ import annotations

from pathlib import Path

from validate_workflows import validate_workflows

ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
PYTHON_SHA = "5fda3b95a4ea91299a34e894583c3862153e4b97"
NODE_SHA = "820762786026740c76f36085b0efc47a31fe5020"
ARTIFACT_SHA = "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"


def valid_workflow() -> str:
    return f"""name: Validate

on:
  pull_request:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: validate-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:
  validate:
    runs-on: ubuntu-24.04
    timeout-minutes: 40
    steps:
      - name: Checkout
        uses: actions/checkout@{CHECKOUT_SHA} # v7.0.1
        with:
          persist-credentials: false
      - name: Python
        uses: actions/setup-python@{PYTHON_SHA} # v7.0.0
        with:
          python-version: "3.12"
      - name: Node
        uses: actions/setup-node@{NODE_SHA} # v7.0.0
        with:
          node-version: "24"
      - name: Dependencies
        run: |
          npm ci --ignore-scripts
          npx --no-install playwright install --with-deps chromium
      - name: Test
        run: |
          python -m pytest -q
          python scripts/validate_web_budgets.py --site-dir site
          python scripts/validate_offline_archive.py \
            --archive site/downloads/files/Cheatsheets-Offline-HTML.zip \
            --extract build/offline-site \
            --report build/reports/offline.json
          node --check tests/web/offline.spec.mjs
          npm run test:web
      - name: Reports
        if: always()
        uses: actions/upload-artifact@{ARTIFACT_SHA} # v7.0.1
        with:
          path: build/reports
"""


def write_workflow(root: Path, content: str) -> Path:
    path = root / ".github" / "workflows" / "validate.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_repository_workflows_follow_policy() -> None:
    assert validate_workflows(ROOT) == []


def test_valid_fixture_passes(tmp_path: Path) -> None:
    write_workflow(tmp_path, valid_workflow())
    assert validate_workflows(tmp_path) == []


def test_unpinned_action_and_write_permissions_are_rejected(tmp_path: Path) -> None:
    content = valid_workflow().replace(
        f"actions/checkout@{CHECKOUT_SHA} # v7.0.1",
        "actions/checkout@v7",
    ).replace("contents: read", "contents: write")
    write_workflow(tmp_path, content)

    codes = {issue.code for issue in validate_workflows(tmp_path)}

    assert "WF002" in codes
    assert "WF020" in codes
    assert "WF041" in codes


def test_pull_request_target_and_persistent_credentials_are_rejected(
    tmp_path: Path,
) -> None:
    content = valid_workflow().replace(
        "  pull_request:\n",
        "  pull_request_target:\n",
    ).replace("persist-credentials: false", "persist-credentials: true")
    write_workflow(tmp_path, content)

    codes = {issue.code for issue in validate_workflows(tmp_path)}

    assert "WF001" in codes
    assert "WF004" in codes
    assert "WF040" in codes
    assert "WF047" in codes


def test_validate_job_requires_timeout_runner_and_always_upload(tmp_path: Path) -> None:
    content = (
        valid_workflow()
        .replace("    runs-on: ubuntu-24.04", "    runs-on: ubuntu-latest")
        .replace("    timeout-minutes: 40\n", "")
        .replace("        if: always()\n", "")
    )
    write_workflow(tmp_path, content)

    codes = {issue.code for issue in validate_workflows(tmp_path)}

    assert "WF031" in codes
    assert "WF032" in codes
    assert "WF049" in codes


def test_validate_workflow_rejects_deployment_actions(tmp_path: Path) -> None:
    deployment = (
        "      - name: Deploy\n"
        "        uses: actions/deploy-pages@"
        + "a" * 40
        + " # v5.0.0\n"
    )
    content = valid_workflow().replace(
        "      - name: Reports\n",
        deployment + "      - name: Reports\n",
    )
    write_workflow(tmp_path, content)

    codes = {issue.code for issue in validate_workflows(tmp_path)}

    assert "WF044" in codes


def test_node_24_and_browser_gates_are_required(tmp_path: Path) -> None:
    content = (
        valid_workflow()
        .replace(
            f"      - name: Node\n        uses: actions/setup-node@{NODE_SHA} # v7.0.0\n"
            "        with:\n          node-version: \"24\"\n",
            "",
        )
        .replace("          npm ci --ignore-scripts\n", "")
        .replace("          npx --no-install playwright install --with-deps chromium\n", "")
        .replace("          python scripts/validate_web_budgets.py --site-dir site\n", "")
        .replace("          npm run test:web\n", "")
    )
    write_workflow(tmp_path, content)

    codes = {issue.code for issue in validate_workflows(tmp_path)}

    assert {"WF053", "WF055", "WF056", "WF057", "WF058"}.issubset(codes)


def test_offline_archive_report_extraction_and_browser_syntax_are_required(
    tmp_path: Path,
) -> None:
    content = (
        valid_workflow()
        .replace("          python scripts/validate_offline_archive.py \\\n", "")
        .replace(
            "            --archive site/downloads/files/Cheatsheets-Offline-HTML.zip \\\n",
            "",
        )
        .replace("            --extract build/offline-site \\\n", "")
        .replace("            --report build/reports/offline.json\n", "")
        .replace("          node --check tests/web/offline.spec.mjs\n", "")
    )
    write_workflow(tmp_path, content)

    codes = {issue.code for issue in validate_workflows(tmp_path)}

    assert {"WF059", "WF060", "WF061", "WF062"}.issubset(codes)


def test_wrong_node_version_and_remote_npx_are_rejected(tmp_path: Path) -> None:
    content = valid_workflow().replace('node-version: "24"', 'node-version: "22"').replace(
        "npx --no-install playwright install --with-deps chromium",
        "npx playwright install --with-deps chromium",
    )
    write_workflow(tmp_path, content)

    codes = {issue.code for issue in validate_workflows(tmp_path)}

    assert "WF006" in codes
    assert "WF054" in codes
    assert "WF056" in codes
