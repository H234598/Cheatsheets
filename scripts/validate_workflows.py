#!/usr/bin/env python3
"""GitHub-Actions-Workflows gegen die Repository-Sicherheitsregeln prüfen."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Sequence

import yaml

from io_utils import atomic_write_text, stable_json_dumps

ACTION_LINE_RE = re.compile(
    r"^(?P<indent>\s*)uses:\s*(?P<action>[^@\s]+)@(?P<sha>[0-9a-f]{40})"
    r"\s+#\s+(?P<version>v[0-9]+(?:\.[0-9]+){1,2}(?:[-+][0-9A-Za-z.-]+)?)\s*$"
)
EXTERNAL_USES_RE = re.compile(r"^\s*uses:\s*(?P<action>[^@\s]+)@(?P<ref>[^\s#]+)")
BANNED_TEXT_PATTERNS = {
    "WF001": (re.compile(r"\bpull_request_target\s*:"), "pull_request_target ist unzulässig"),
    "WF002": (re.compile(r"\bcontents\s*:\s*write\b"), "contents: write ist unzulässig"),
    "WF003": (re.compile(r"\bgit\s+push\b"), "Workflows dürfen nicht direkt pushen"),
    "WF004": (
        re.compile(r"\bpersist-credentials\s*:\s*(?:true|yes|on|1)\b", re.I),
        "Checkout-Credentials dürfen nicht persistent bleiben",
    ),
    "WF005": (re.compile(r"\$\{\{\s*secrets\."), "Validierung darf keine Secrets verwenden"),
    "WF006": (
        re.compile(r"\bnpx\s+(?!--no-install\b)"),
        "npx darf keine nicht lokal installierten Pakete nachladen",
    ),
}
REQUIRED_VALIDATE_TRIGGERS = {"pull_request", "push", "workflow_dispatch"}
ALLOWED_VALIDATE_PERMISSIONS = {"contents": "read"}
DEPLOY_ACTIONS = {
    "actions/configure-pages",
    "actions/upload-pages-artifact",
    "actions/deploy-pages",
}
REQUIRED_VALIDATE_COMMANDS = {
    "WF055": ("npm ci --ignore-scripts", "npm ci --ignore-scripts fehlt"),
    "WF056": (
        "npx --no-install playwright install --with-deps chromium",
        "reproduzierbare Chromium-Installation fehlt",
    ),
    "WF057": (
        "python scripts/validate_web_budgets.py",
        "Webbudget- und Laufzeitassetprüfung fehlt",
    ),
    "WF058": ("npm run test:web", "blockierende Browser- und Accessibility-Tests fehlen"),
}


@dataclass(frozen=True, slots=True)
class WorkflowIssue:
    severity: str
    code: str
    message: str
    path: str
    line: int | None = None

    def format(self) -> str:
        position = f":{self.line}" if self.line is not None else ""
        return f"{self.path}{position}: {self.code}: {self.message}"

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }
        if self.line is not None:
            payload["line"] = self.line
        return payload


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item).casefold() for key, item in value.items()}


def _steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    value = job.get("steps")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _load_workflow(path: Path, relative: str) -> tuple[dict[str, Any], str, list[WorkflowIssue]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {}, "", [
            WorkflowIssue("error", "WF010", f"Datei nicht lesbar: {exc}", relative)
        ]
    try:
        loaded = yaml.load(text, Loader=yaml.BaseLoader)
    except yaml.YAMLError as exc:
        return {}, text, [
            WorkflowIssue("error", "WF011", f"Ungültiges YAML: {exc}", relative)
        ]
    if not isinstance(loaded, dict):
        return {}, text, [
            WorkflowIssue("error", "WF012", "Workflow muss ein Mapping sein", relative)
        ]
    return loaded, text, []


def _line_for_pattern(text: str, pattern: re.Pattern[str]) -> int | None:
    for number, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            return number
    return None


def _validate_action_pins(relative: str, text: str) -> list[WorkflowIssue]:
    issues: list[WorkflowIssue] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = EXTERNAL_USES_RE.match(line)
        if match is None:
            continue
        action = match.group("action")
        if action.startswith("./") or action.startswith("docker://"):
            continue
        if ACTION_LINE_RE.match(line) is None:
            issues.append(
                WorkflowIssue(
                    "error",
                    "WF020",
                    "Externe Action benötigt vollständigen 40-stelligen SHA und Versionskommentar",
                    relative,
                    number,
                )
            )
    return issues


def _validate_common(relative: str, text: str, payload: dict[str, Any]) -> list[WorkflowIssue]:
    issues: list[WorkflowIssue] = []
    for code, (pattern, message) in BANNED_TEXT_PATTERNS.items():
        line = _line_for_pattern(text, pattern)
        if line is not None:
            issues.append(WorkflowIssue("error", code, message, relative, line))

    issues.extend(_validate_action_pins(relative, text))
    jobs = _mapping(payload.get("jobs"))
    if not jobs:
        issues.append(WorkflowIssue("error", "WF030", "Workflow enthält keine Jobs", relative))
        return issues

    for job_name, raw_job in jobs.items():
        job = _mapping(raw_job)
        try:
            timeout_value = int(str(job.get("timeout-minutes", "")))
        except ValueError:
            timeout_value = 0
        if timeout_value < 1 or timeout_value > 60:
            issues.append(
                WorkflowIssue(
                    "error",
                    "WF031",
                    f"Job {job_name} benötigt timeout-minutes zwischen 1 und 60",
                    relative,
                )
            )
        if str(job.get("runs-on", "")) != "ubuntu-24.04":
            issues.append(
                WorkflowIssue(
                    "error",
                    "WF032",
                    f"Job {job_name} muss reproduzierbar auf ubuntu-24.04 laufen",
                    relative,
                )
            )
        if _string_mapping(job.get("permissions")).get("contents") == "write":
            issues.append(
                WorkflowIssue(
                    "error",
                    "WF033",
                    f"Job {job_name} besitzt contents: write",
                    relative,
                )
            )
    return issues


def _validate_validate_workflow(relative: str, payload: dict[str, Any]) -> list[WorkflowIssue]:
    issues: list[WorkflowIssue] = []
    if str(payload.get("name", "")) != "Validate":
        issues.append(
            WorkflowIssue("error", "WF039", "Workflowname muss Validate lauten", relative)
        )

    triggers = _mapping(payload.get("on"))
    missing = REQUIRED_VALIDATE_TRIGGERS - set(triggers)
    if missing:
        issues.append(
            WorkflowIssue(
                "error",
                "WF040",
                f"Validate-Workflow vermisst Trigger: {sorted(missing)}",
                relative,
            )
        )
    push = _mapping(triggers.get("push"))
    branches = push.get("branches")
    if not isinstance(branches, list) or [str(item) for item in branches] != ["main"]:
        issues.append(
            WorkflowIssue(
                "error",
                "WF045",
                "Push-Validierung muss ausschließlich main beobachten",
                relative,
            )
        )

    permissions = _string_mapping(payload.get("permissions"))
    if permissions != ALLOWED_VALIDATE_PERMISSIONS:
        issues.append(
            WorkflowIssue(
                "error",
                "WF041",
                f"Validate-Workflow benötigt exakt {ALLOWED_VALIDATE_PERMISSIONS}, gefunden {permissions}",
                relative,
            )
        )

    concurrency = _mapping(payload.get("concurrency"))
    if str(concurrency.get("cancel-in-progress", "")).casefold() != "true":
        issues.append(
            WorkflowIssue(
                "error",
                "WF042",
                "Validate-Workflow muss ältere Läufe abbrechen",
                relative,
            )
        )

    checkout_seen = False
    python_seen = False
    node_seen = False
    upload_seen = False
    run_commands: list[str] = []
    for job_name, raw_job in _mapping(payload.get("jobs")).items():
        job = _mapping(raw_job)
        if job.get("environment") is not None:
            issues.append(
                WorkflowIssue(
                    "error",
                    "WF043",
                    f"PR-Job {job_name} darf kein Environment verwenden",
                    relative,
                )
            )
        job_permissions = _string_mapping(job.get("permissions"))
        if job_permissions and job_permissions != ALLOWED_VALIDATE_PERMISSIONS:
            issues.append(
                WorkflowIssue(
                    "error",
                    "WF046",
                    f"PR-Job {job_name} darf globale Leserechte nicht erweitern",
                    relative,
                )
            )

        for step in _steps(job):
            uses = str(step.get("uses", ""))
            action = uses.split("@", 1)[0]
            values = _string_mapping(step.get("with"))
            run_commands.append(str(step.get("run", "")))
            if action == "actions/checkout":
                checkout_seen = True
                if values.get("persist-credentials") != "false":
                    issues.append(
                        WorkflowIssue(
                            "error",
                            "WF047",
                            "Checkout muss persist-credentials: false setzen",
                            relative,
                        )
                    )
            elif action == "actions/setup-python":
                python_seen = True
                if values.get("python-version") != "3.12":
                    issues.append(
                        WorkflowIssue(
                            "error",
                            "WF048",
                            "CI muss Python 3.12 verwenden",
                            relative,
                        )
                    )
            elif action == "actions/setup-node":
                node_seen = True
                if values.get("node-version") != "24":
                    issues.append(
                        WorkflowIssue(
                            "error",
                            "WF054",
                            "Browser-CI muss Node.js 24 verwenden",
                            relative,
                        )
                    )
            elif action == "actions/upload-artifact":
                upload_seen = True
                condition = str(step.get("if", "")).replace("${{", "").replace("}}", "").strip()
                if condition != "always()":
                    issues.append(
                        WorkflowIssue(
                            "error",
                            "WF049",
                            "Diagnostikartefakte müssen auch nach Fehlern hochgeladen werden",
                            relative,
                        )
                    )
            if action in DEPLOY_ACTIONS:
                issues.append(
                    WorkflowIssue(
                        "error",
                        "WF044",
                        f"Validate-Workflow darf {action} nicht verwenden",
                        relative,
                    )
                )

    if not checkout_seen:
        issues.append(WorkflowIssue("error", "WF050", "Checkout-Schritt fehlt", relative))
    if not python_seen:
        issues.append(WorkflowIssue("error", "WF051", "Python-Setup fehlt", relative))
    if not node_seen:
        issues.append(WorkflowIssue("error", "WF053", "Node.js-Setup fehlt", relative))
    if not upload_seen:
        issues.append(WorkflowIssue("error", "WF052", "Diagnostik-Upload fehlt", relative))

    combined_commands = "\n".join(run_commands)
    for code, (needle, message) in REQUIRED_VALIDATE_COMMANDS.items():
        if needle not in combined_commands:
            issues.append(WorkflowIssue("error", code, message, relative))
    return issues


def validate_workflows(root: Path) -> list[WorkflowIssue]:
    workflow_root = root / ".github" / "workflows"
    if not workflow_root.is_dir():
        return [
            WorkflowIssue(
                "error",
                "WF000",
                "Workflowverzeichnis fehlt",
                ".github/workflows",
            )
        ]

    paths = sorted(
        [*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml")],
        key=lambda item: item.name.casefold(),
    )
    if not paths:
        return [
            WorkflowIssue("error", "WF000", "Keine Workflows gefunden", ".github/workflows")
        ]

    issues: list[WorkflowIssue] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            issues.append(
                WorkflowIssue(
                    "error",
                    "WF013",
                    "Workflow darf kein Symlink sein",
                    relative,
                )
            )
            continue
        payload, text, load_issues = _load_workflow(path, relative)
        issues.extend(load_issues)
        if load_issues:
            continue
        issues.extend(_validate_common(relative, text, payload))
        if relative == ".github/workflows/validate.yml":
            issues.extend(_validate_validate_workflow(relative, payload))

    return sorted(issues, key=lambda issue: (issue.path, issue.line or 0, issue.code))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitHub-Actions-Sicherheitsregeln prüfen")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    issues = validate_workflows(root)
    if args.report:
        report = args.report if args.report.is_absolute() else root / args.report
        atomic_write_text(
            report,
            stable_json_dumps(
                {
                    "errors": sum(issue.severity == "error" for issue in issues),
                    "issues": [issue.as_dict() for issue in issues],
                    "schema_version": 1,
                }
            ),
        )
    if issues:
        print("Workflowvalidierung fehlgeschlagen:")
        for issue in issues:
            print(f"- {issue.format()}")
        return 1
    print(
        "Workflowvalidierung erfolgreich: minimale Rechte, unveränderliche Action-Pins "
        "und reproduzierbare Browsergates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
