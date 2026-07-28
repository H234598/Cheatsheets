#!/usr/bin/env python3
"""Öffentliche Markdownquellen auf aktive HTML- und Secret-Risiken prüfen."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
from typing import Any, Sequence

import yaml

from content_index import markdown_files
from content_model import FRONTMATTER_RE, FenceState, advance_fence_state
from io_utils import atomic_write_text, stable_json_dumps

SECRET_RULES: dict[str, re.Pattern[str]] = {
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"),
    "github-fine-grained-token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,255}\b"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "google-api-key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,200}\b"),
    "credential-url": re.compile(r"https?://[^\s/:@]+:[^\s/@]+@[^\s/]+", re.I),
}
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?P<kind>(?:RSA |EC |OPENSSH )?PRIVATE KEY)-----\s*"
    r"(?P<body>(?:[A-Za-z0-9+/=]{16,}\s*){4,})"
    r"-----END (?P=kind)-----",
    re.M,
)
HTML_TAG_RE = re.compile(
    r"<\s*(?P<closing>/)?\s*(?P<tag>[A-Za-z][A-Za-z0-9:-]*)"
    r"(?P<attrs>[^<>]*?)\s*(?P<selfclosing>/)?\s*>",
)
ATTRIBUTE_RE = re.compile(
    r"(?P<name>[A-Za-z_:][A-Za-z0-9_.:-]*)"
    r"(?:\s*=\s*(?P<value>\"[^\"]*\"|'[^']*'|[^\s>]+))?"
)
INLINE_CODE_RE = re.compile(r"(?P<ticks>`+).*?(?P=ticks)")
MARKDOWN_EXTERNAL_IMAGE_RE = re.compile(r"!\[[^\]\n]*\]\(\s*https?://", re.I)
MARKDOWN_AUTOLINK_RE = re.compile(
    r"<(?:(?:https?://|mailto:)[^<>\s]+|[^<>\s@]+@[^<>\s@]+)>",
    re.I,
)
PRIVATE_IPV4_RE = re.compile(
    r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
    r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
)
INTERNAL_HOST_RE = re.compile(r"\b[A-Za-z0-9.-]+\.(?:internal|corp|lan|local)\b", re.I)
FORBIDDEN_TAGS = {
    "base",
    "button",
    "embed",
    "form",
    "iframe",
    "input",
    "link",
    "math",
    "meta",
    "object",
    "script",
    "style",
    "svg",
}


class SecurityConfigError(RuntimeError):
    """Sicherheitskonfiguration ist ungültig oder unsicher."""


@dataclass(frozen=True, slots=True)
class SecurityIssue:
    severity: str
    code: str
    message: str
    path: str
    line: int
    rule: str | None = None
    fingerprint: str | None = None

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.code}: {self.message}"

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "line": self.line,
        }
        if self.rule:
            payload["rule"] = self.rule
        if self.fingerprint:
            payload["fingerprint"] = self.fingerprint
        return payload


@dataclass(frozen=True, slots=True)
class SecretAllowance:
    rule: str
    path: str
    match_sha256: str
    reason: str


def _read_regular_file_no_follow(path: Path, root: Path) -> bytes:
    root = root.resolve()
    absolute = Path(os.path.abspath(path))
    try:
        absolute.relative_to(root)
        absolute.parent.resolve().relative_to(root)
    except ValueError as exc:
        raise SecurityConfigError(
            f"Konfiguration verlässt die Repositorywurzel: {absolute}"
        ) from exc

    before = absolute.lstat()
    if stat.S_ISLNK(before.st_mode):
        raise SecurityConfigError(f"Konfigurationsdatei darf kein Symlink sein: {absolute}")
    if not stat.S_ISREG(before.st_mode):
        raise SecurityConfigError(f"Konfigurationsdatei ist nicht regulär: {absolute}")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(absolute, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise SecurityConfigError(f"Geöffnete Konfiguration ist nicht regulär: {absolute}")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise SecurityConfigError(
                f"Konfiguration wurde während des Lesens ausgetauscht: {absolute}"
            )
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_yaml_mapping(path: Path, root: Path) -> dict[str, Any]:
    try:
        raw = _read_regular_file_no_follow(path, root)
        loaded = yaml.safe_load(raw.decode("utf-8"))
    except FileNotFoundError as exc:
        raise SecurityConfigError(f"Konfigurationsdatei fehlt: {path}") from exc
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise SecurityConfigError(f"Konfigurationsdatei ist ungültig: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SecurityConfigError(f"Konfigurationsdatei muss ein Mapping sein: {path}")
    if loaded.get("schema_version") != 1:
        raise SecurityConfigError(f"Nicht unterstützte Konfigurationsversion: {path}")
    return loaded


def load_html_policy(root: Path) -> tuple[set[str], set[str]]:
    payload = _read_yaml_mapping(root / "config" / "html-allowlist.yaml", root)
    tags = payload.get("allowed_tags")
    attributes = payload.get("allowed_attributes")
    if not isinstance(tags, list) or any(not isinstance(item, str) for item in tags):
        raise SecurityConfigError("allowed_tags muss eine Stringliste sein")
    if not isinstance(attributes, list) or any(not isinstance(item, str) for item in attributes):
        raise SecurityConfigError("allowed_attributes muss eine Stringliste sein")
    normalized_tags = {item.casefold() for item in tags}
    overlap = normalized_tags & FORBIDDEN_TAGS
    if overlap:
        raise SecurityConfigError(
            f"Gefährliche Tags dürfen nicht freigegeben werden: {sorted(overlap)}"
        )
    return normalized_tags, {item.casefold() for item in attributes}


def load_secret_allowances(root: Path) -> tuple[SecretAllowance, ...]:
    payload = _read_yaml_mapping(root / "config" / "secret-allowlist.yaml", root)
    entries = payload.get("allow")
    if not isinstance(entries, list):
        raise SecurityConfigError("allow muss eine Liste sein")

    allowances: list[SecretAllowance] = []
    valid_rules = {*SECRET_RULES, "private-key-block"}
    for number, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise SecurityConfigError(f"Allowlist-Eintrag {number} muss ein Mapping sein")
        rule = entry.get("rule")
        path = entry.get("path")
        digest = entry.get("match_sha256")
        reason = entry.get("reason")
        values = (rule, path, digest, reason)
        if not all(isinstance(item, str) and item.strip() for item in values):
            raise SecurityConfigError(
                f"Allowlist-Eintrag {number} benötigt rule, path, match_sha256 und reason"
            )
        assert isinstance(rule, str)
        assert isinstance(path, str)
        assert isinstance(digest, str)
        assert isinstance(reason, str)
        if rule not in valid_rules:
            raise SecurityConfigError(
                f"Allowlist-Eintrag {number} nutzt unbekannte Regel: {rule}"
            )
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise SecurityConfigError(f"Allowlist-Eintrag {number} besitzt keinen SHA-256")
        normalized_path = Path(path).as_posix().lstrip("/")
        if normalized_path != path or ".." in Path(path).parts:
            raise SecurityConfigError(
                f"Allowlist-Eintrag {number} besitzt unsicheren Pfad: {path}"
            )
        allowances.append(SecretAllowance(rule, path, digest, reason))
    return tuple(allowances)


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_allowed(
    allowances: tuple[SecretAllowance, ...],
    *,
    rule: str,
    path: str,
    digest: str,
) -> bool:
    return any(
        item.rule == rule and item.path == path and item.match_sha256 == digest
        for item in allowances
    )


def _mask(value: str) -> str:
    return "".join("\n" if char == "\n" else "\r" if char == "\r" else " " for char in value)


def _mask_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    chars = list(line)
    index = 0
    while index < len(chars):
        if in_comment:
            end = line.find("-->", index)
            if end == -1:
                for position in range(index, len(chars)):
                    if chars[position] not in "\r\n":
                        chars[position] = " "
                return "".join(chars), True
            for position in range(index, min(end + 3, len(chars))):
                if chars[position] not in "\r\n":
                    chars[position] = " "
            index = end + 3
            in_comment = False
            continue
        start = line.find("<!--", index)
        if start == -1:
            break
        for position in range(start, min(start + 4, len(chars))):
            chars[position] = " "
        index = start + 4
        in_comment = True
    return "".join(chars), in_comment


def visible_markdown(text: str) -> str:
    """Maskiere Frontmatter, Fences, Kommentare und Inline-Code positionsstabil."""

    frontmatter = FRONTMATTER_RE.match(text)
    frontmatter_end = frontmatter.end() if frontmatter else 0
    fence: FenceState | None = None
    in_comment = False
    output: list[str] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        line_end = offset + len(line)
        if line_end <= frontmatter_end:
            output.append(_mask(line))
            offset = line_end
            continue
        fence, is_fenced = advance_fence_state(line, fence)
        if is_fenced:
            output.append(_mask(line))
            offset = line_end
            continue
        masked, in_comment = _mask_comments(line, in_comment)
        masked = INLINE_CODE_RE.sub(lambda match: _mask(match.group(0)), masked)
        output.append(masked)
        offset = line_end
    return "".join(output)


def _secret_issues(
    text: str,
    relative: str,
    allowances: tuple[SecretAllowance, ...],
) -> list[SecurityIssue]:
    issues: list[SecurityIssue] = []
    for rule, pattern in SECRET_RULES.items():
        for match in pattern.finditer(text):
            digest = fingerprint(match.group(0))
            if _is_allowed(allowances, rule=rule, path=relative, digest=digest):
                continue
            issues.append(
                SecurityIssue(
                    "error",
                    "SC001",
                    f"Mögliche echte Zugangsinformation erkannt ({rule}, Hash {digest[:12]})",
                    relative,
                    text.count("\n", 0, match.start()) + 1,
                    rule,
                    digest,
                )
            )
    for match in PRIVATE_KEY_RE.finditer(text):
        digest = fingerprint(match.group(0))
        rule = "private-key-block"
        if _is_allowed(allowances, rule=rule, path=relative, digest=digest):
            continue
        issues.append(
            SecurityIssue(
                "error",
                "SC002",
                f"Vollständiger privater Schlüsselblock erkannt (Hash {digest[:12]})",
                relative,
                text.count("\n", 0, match.start()) + 1,
                rule,
                digest,
            )
        )
    return issues


def _attribute_value(raw: str | None) -> str:
    if not raw:
        return ""
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
        return raw[1:-1]
    return raw


def _html_issues(
    visible: str,
    relative: str,
    allowed_tags: set[str],
    allowed_attributes: set[str],
) -> list[SecurityIssue]:
    issues: list[SecurityIssue] = []
    for match in MARKDOWN_EXTERNAL_IMAGE_RE.finditer(visible):
        issues.append(
            SecurityIssue(
                "error",
                "SC020",
                "Extern geladenes Markdown-Bild ist unzulässig",
                relative,
                visible.count("\n", 0, match.start()) + 1,
            )
        )

    for match in HTML_TAG_RE.finditer(visible):
        raw = match.group(0)
        if MARKDOWN_AUTOLINK_RE.fullmatch(raw.strip()):
            continue
        tag = match.group("tag").casefold()
        line = visible.count("\n", 0, match.start()) + 1
        if tag in FORBIDDEN_TAGS:
            issues.append(
                SecurityIssue(
                    "error",
                    "SC010",
                    f"Aktives oder gefährliches Raw-HTML-Tag <{tag}> ist unzulässig",
                    relative,
                    line,
                )
            )
        elif tag not in allowed_tags:
            issues.append(
                SecurityIssue(
                    "warning",
                    "SC011",
                    f"Raw-HTML-Tag <{tag}> ist nicht ausdrücklich freigegeben",
                    relative,
                    line,
                )
            )

        if match.group("closing"):
            continue
        for attribute in ATTRIBUTE_RE.finditer(match.group("attrs") or ""):
            name = attribute.group("name").casefold()
            value = _attribute_value(attribute.group("value"))
            if name.startswith("on") or name == "srcdoc":
                issues.append(
                    SecurityIssue(
                        "error",
                        "SC012",
                        f"Aktives HTML-Attribut {name} ist unzulässig",
                        relative,
                        line,
                    )
                )
            elif tag in allowed_tags and name not in allowed_attributes:
                issues.append(
                    SecurityIssue(
                        "warning",
                        "SC013",
                        f"Attribut {name} ist für freigegebenes Raw HTML nicht allowlistet",
                        relative,
                        line,
                    )
                )
            normalized = value.strip().casefold()
            if normalized.startswith("javascript:") or normalized.startswith("data:text/html"):
                issues.append(
                    SecurityIssue(
                        "error",
                        "SC014",
                        f"Gefährliches URL-Schema in Attribut {name}",
                        relative,
                        line,
                    )
                )
            if name in {"src", "poster"} and re.match(r"https?://", value, re.I):
                issues.append(
                    SecurityIssue(
                        "error",
                        "SC015",
                        f"Externes Laufzeitasset in Attribut {name} ist unzulässig",
                        relative,
                        line,
                    )
                )

    for match in PRIVATE_IPV4_RE.finditer(visible):
        issues.append(
            SecurityIssue(
                "info",
                "SC100",
                "Private IPv4-Adresse im sichtbaren Fachtext; Kontext manuell prüfen",
                relative,
                visible.count("\n", 0, match.start()) + 1,
            )
        )
    for match in INTERNAL_HOST_RE.finditer(visible):
        issues.append(
            SecurityIssue(
                "info",
                "SC101",
                "Möglicher interner Hostname im sichtbaren Fachtext; Kontext manuell prüfen",
                relative,
                visible.count("\n", 0, match.start()) + 1,
            )
        )
    return issues


def analyze_security(root: Path) -> list[SecurityIssue]:
    root = root.resolve()
    allowed_tags, allowed_attributes = load_html_policy(root)
    allowances = load_secret_allowances(root)
    issues: list[SecurityIssue] = []
    for path in markdown_files(root):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            issues.append(
                SecurityIssue("error", "SC030", "Markdownquelle darf kein Symlink sein", relative, 1)
            )
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append(
                SecurityIssue("error", "SC031", f"Markdownquelle nicht lesbar: {exc}", relative, 1)
            )
            continue
        issues.extend(_secret_issues(text, relative, allowances))
        issues.extend(
            _html_issues(
                visible_markdown(text),
                relative,
                allowed_tags,
                allowed_attributes,
            )
        )
    return sorted(issues, key=lambda item: (item.path, item.line, item.code))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Secret-, Raw-HTML- und Laufzeitasset-Risiken prüfen"
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        issues = analyze_security(root)
    except SecurityConfigError as exc:
        print(f"Sicherheitsvalidierung fehlgeschlagen: {exc}")
        return 2

    if args.report:
        report = args.report if args.report.is_absolute() else root / args.report
        atomic_write_text(
            report,
            stable_json_dumps(
                {
                    "errors": sum(issue.severity == "error" for issue in issues),
                    "infos": sum(issue.severity == "info" for issue in issues),
                    "issues": [issue.as_dict() for issue in issues],
                    "schema_version": 1,
                    "warnings": sum(issue.severity == "warning" for issue in issues),
                }
            ),
        )

    blocking = [
        issue
        for issue in issues
        if issue.severity == "error" or (args.strict and issue.severity == "warning")
    ]
    if issues:
        print("Sicherheitsbefunde:")
        for issue in issues:
            print(f"- [{issue.severity}] {issue.format()}")
    if blocking:
        print(f"Blockierende Sicherheitsbefunde: {len(blocking)}")
        return 1
    print("Sicherheitsvalidierung erfolgreich: keine blockierenden Befunde.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
