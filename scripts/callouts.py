#!/usr/bin/env python3
"""Obsidian-Callouts fence-sicher in Material-Admonitions umwandeln.

Erweitert aus ``scripts/callouts.py`` des Repositories
``H234598/ADHS-Lernpfad`` am Commit
``93c8c02d263ec123c1c271caf0d2deaa76760ccb``.
"""

from __future__ import annotations

import re

from content_model import FenceState, advance_fence_state

CALLOUT_START_RE = re.compile(
    r"^(?P<indent>[ \t]*)>\s*\[!(?P<kind>[A-Za-z0-9_-]+)\]"
    r"(?P<fold>[+-])?\s*(?P<title>.*?)[ \t]*(?P<newline>\r?\n)?$"
)
CALLOUT_BODY_RE = re.compile(
    r"^(?P<indent>[ \t]*)>\s?(?P<body>.*?)(?P<newline>\r?\n)?$"
)

CALLOUT_TYPES = {
    "abstract": "abstract",
    "summary": "abstract",
    "tldr": "abstract",
    "info": "info",
    "todo": "info",
    "tip": "tip",
    "hint": "tip",
    "important": "important",
    "success": "success",
    "check": "success",
    "done": "success",
    "question": "question",
    "help": "question",
    "faq": "question",
    "warning": "warning",
    "caution": "warning",
    "attention": "warning",
    "failure": "failure",
    "fail": "failure",
    "missing": "failure",
    "danger": "danger",
    "error": "danger",
    "bug": "bug",
    "example": "example",
    "quote": "quote",
    "cite": "quote",
    "note": "note",
    "evidence": "evidence",
}

DEFAULT_TITLES = {
    "abstract": "Zusammenfassung",
    "info": "Hinweis",
    "tip": "Tipp",
    "important": "Wichtig",
    "success": "Erfolg",
    "question": "Frage",
    "warning": "Warnung",
    "failure": "Fehler",
    "danger": "Gefahr",
    "bug": "Fehlerbild",
    "example": "Beispiel",
    "quote": "Zitat",
    "note": "Hinweis",
    "evidence": "Evidenz",
}


def _quoted_title(title: str) -> str:
    return title.replace("\\", "\\\\").replace('"', '\\"')


def convert_obsidian_callouts_for_web(text: str) -> str:
    """Konvertiere unterstützte Callout-Blockquotes außerhalb von Codefences."""

    lines = text.splitlines(keepends=True)
    output: list[str] = []
    fence: FenceState | None = None
    index = 0

    while index < len(lines):
        line = lines[index]
        fence, is_fenced = advance_fence_state(line, fence)
        if is_fenced:
            output.append(line)
            index += 1
            continue

        match = CALLOUT_START_RE.match(line)
        if not match:
            output.append(line)
            index += 1
            continue

        source_kind = match.group("kind").casefold()
        target_kind = CALLOUT_TYPES.get(source_kind)
        if target_kind is None:
            output.append(line)
            index += 1
            continue

        indent = match.group("indent")
        title = match.group("title").strip() or DEFAULT_TITLES[target_kind]
        fold = match.group("fold")
        directive = "???+" if fold == "+" else ("???" if fold == "-" else "!!!")
        newline = match.group("newline") or "\n"

        body: list[tuple[str, str]] = []
        index += 1
        while index < len(lines):
            body_match = CALLOUT_BODY_RE.match(lines[index])
            if not body_match or body_match.group("indent") != indent:
                break
            body.append(
                (
                    body_match.group("body"),
                    body_match.group("newline") or ("\n" if lines[index].endswith("\n") else ""),
                )
            )
            index += 1

        output.append(
            f'{indent}{directive} {target_kind} "{_quoted_title(title)}"{newline}'
        )
        if body:
            for body_line, body_newline in body:
                output.append(f"{indent}    {body_line}{body_newline}")
        else:
            output.append(newline)

    return "".join(output)
