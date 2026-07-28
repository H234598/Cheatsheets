from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"

CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_PYTHON = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
CONFIGURE_PAGES = "actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d"
UPLOAD_PAGES = "actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9"
DEPLOY_PAGES = "actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128"


def load_workflow() -> tuple[dict[str, object], str]:
    text = WORKFLOW.read_text(encoding="utf-8")
    payload = yaml.load(text, Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload, text


def steps(job: dict[str, object]) -> list[dict[str, object]]:
    value = job.get("steps")
    assert isinstance(value, list)
    return [item for item in value if isinstance(item, dict)]


def uses(job: dict[str, object]) -> list[str]:
    return [str(item["uses"]) for item in steps(job) if "uses" in item]


def test_pages_workflow_has_only_main_and_manual_triggers() -> None:
    payload, _text = load_workflow()
    triggers = payload["on"]
    assert isinstance(triggers, dict)

    assert set(triggers) == {"push", "workflow_dispatch"}
    assert "pull_request" not in triggers
    push = triggers["push"]
    assert isinstance(push, dict)
    assert push["branches"] == ["main"]


def test_pages_workflow_uses_empty_global_permissions_and_safe_concurrency() -> None:
    payload, _text = load_workflow()

    assert payload["permissions"] == {}
    assert payload["concurrency"] == {
        "group": "github-pages",
        "cancel-in-progress": "false",
    }


def test_build_and_deploy_are_separate_with_minimal_permissions() -> None:
    payload, _text = load_workflow()
    jobs = payload["jobs"]
    assert isinstance(jobs, dict)
    assert set(jobs) == {"build", "deploy"}

    build = jobs["build"]
    deploy = jobs["deploy"]
    assert isinstance(build, dict) and isinstance(deploy, dict)
    assert build["runs-on"] == "ubuntu-24.04"
    assert build["timeout-minutes"] == "55"
    assert build["permissions"] == {"contents": "read", "pages": "write"}

    assert deploy["needs"] == "build"
    assert deploy["runs-on"] == "ubuntu-24.04"
    assert deploy["timeout-minutes"] == "10"
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}
    assert deploy["environment"] == {
        "name": "github-pages",
        "url": "${{ steps.deployment.outputs.page_url }}",
    }
    assert deploy["outputs"] == {
        "page_url": "${{ steps.deployment.outputs.page_url }}"
    }


def test_build_uses_pinned_actions_and_nonpersistent_checkout() -> None:
    payload, _text = load_workflow()
    build = payload["jobs"]["build"]
    assert isinstance(build, dict)
    build_steps = steps(build)
    actions = uses(build)

    assert CHECKOUT in actions
    assert SETUP_PYTHON in actions
    assert CONFIGURE_PAGES in actions
    assert UPLOAD_PAGES in actions

    checkout = next(item for item in build_steps if item.get("uses") == CHECKOUT)
    assert checkout["with"] == {"fetch-depth": "1", "persist-credentials": "false"}
    python = next(item for item in build_steps if item.get("uses") == SETUP_PYTHON)
    assert python["with"]["python-version"] == "3.12"
    configure = next(item for item in build_steps if item.get("uses") == CONFIGURE_PAGES)
    assert configure["id"] == "pages"


def test_site_is_built_once_with_configured_base_url_and_validated() -> None:
    payload, text = load_workflow()
    build = payload["jobs"]["build"]
    assert isinstance(build, dict)

    assert text.count("python scripts/build_site.py") == 1
    assert "${{ steps.pages.outputs.base_url }}" in text
    assert '--site-url "${SITE_URL%/}/"' in text
    assert "python scripts/build_manifest.py --check" in text
    assert "python scripts/validate_pages_artifact.py" in text
    assert "python scripts/validate_offline_archive.py" in text
    assert "--site-dir site" in text

    upload = next(item for item in steps(build) if item.get("uses") == UPLOAD_PAGES)
    assert upload["with"] == {"path": "site"}


def test_deploy_job_uses_only_the_pinned_pages_deployment_action() -> None:
    payload, text = load_workflow()
    deploy = payload["jobs"]["deploy"]
    assert isinstance(deploy, dict)
    deploy_steps = steps(deploy)

    assert uses(deploy) == [DEPLOY_PAGES]
    assert deploy_steps[0]["id"] == "deployment"
    assert "git push" not in text
    assert "secrets." not in text
