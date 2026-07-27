#!/usr/bin/env python3
"""Typisierte Obsidian-Linkvorkommen und fence-sicherer Quellscanner.

Angepasst aus ``scripts/link_types.py`` des Repositories
``H234598/ADHS-Lernpfad`` am Commit
``93c8c02d263ec123c1c271caf0d2deaa76760ccb``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from content_model import FenceState, PageRecord, advance_fence_state

WIKILINK_RE = re.compile(r"(?P<embed>!)?\[\[(?P<body>[^\]\n]+)\]\]")
ATX_HEADING_RE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+|$)")
BLOCK_PREFIX_RE = re.compile(
    r"^ {0,3}(?:>|(?:[-+*]|\d{1,9}[.)])[ \t]+|<!--)"
)
SETEXT_OR_RULE_RE = re.compile(r"^ {0,3}(?:=+[ \t]*|-{3,}[ \t]*)\r?\n?$")
IMAGE_SUFFIXES = {
    ".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp",
}


class LinkError(ValueError):
    """Ein interner Link ist nicht eindeutig und sicher auflösbar."""


@dataclass(frozen=True, slots=True)
class LinkTarget:
    path: Path
    heading: str | None = None


@dataclass(frozen=True, slots=True)
class LinkOccurrence:
    source: Path
    raw: str
    target: str
    heading: str | None
    label: str
    embed: bool
    line: int
    column: int
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Resolution:
    status: str
    target_id: str | None
    path: Path | None = None
    page: PageRecord | None = None
    heading: str | None = None
    anchor: str | None = None
    candidates: tuple[str, ...] = ()
    message: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"


@dataclass(frozen=True, slots=True)
class LinkIssue:
    code: str
    severity: str
    message: str
    path: str
    line: int
    column: int
    raw: str
    requested_target: str
    candidates: tuple[str, ...] = ()

    def format(self) -> str:
        candidates = (
            f"; Kandidaten: {', '.join(self.candidates)}" if self.candidates else ""
        )
        return (
            f"{self.path}:{self.line}:{self.column}: "
            f"{self.severity.upper()} {self.code}: {self.message}{candidates}"
        )

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "raw": self.raw,
            "requested_target": self.requested_target,
        }
        if self.candidates:
            payload["candidates"] = list(self.candidates)
        return payload


def split_link(raw: str) -> tuple[str, str | None, str]:
    """Zerlege ``Ziel#Überschrift|Label`` genau einmal je Trennzeichen."""

    if "|" in raw:
        target_raw, label_raw = raw.split("|", 1)
        label = label_raw.strip()
    else:
        target_raw, label = raw, ""
    target_raw = target_raw.strip()
    if "#" in target_raw:
        target, heading_raw = target_raw.split("#", 1)
        heading = heading_raw.strip() or None
    else:
        target, heading = target_raw, None
    target = target.strip()
    if not label:
        label = heading or Path(target).stem or target or "Link"
    return target, heading, label


def _mask_comments_and_inline_code(
    line: str,
    in_comment: bool,
    inline_ticks: int,
    following_text: str,
) -> tuple[str, bool, int]:
    """Maskiere Kommentare und Inline-Code bei stabilen Quelloffsets."""

    chars = list(line)
    index = 0
    while index < len(chars):
        if in_comment:
            end = line.find("-->", index)
            if end == -1:
                for position in range(index, len(chars)):
                    if chars[position] != "\n":
                        chars[position] = " "
                return "".join(chars), True, inline_ticks
            for position in range(index, end + 3):
                if chars[position] != "\n":
                    chars[position] = " "
            index = end + 3
            in_comment = False
            continue
        if inline_ticks:
            if chars[index] == "`":
                run = 1
                while index + run < len(chars) and chars[index + run] == "`":
                    run += 1
                for position in range(index, index + run):
                    chars[position] = " "
                if run == inline_ticks:
                    inline_ticks = 0
                index += run
                continue
            if chars[index] != "\n":
                chars[index] = " "
            index += 1
            continue
        if line.startswith("<!--", index):
            in_comment = True
            continue
        if chars[index] == "`":
            run = 1
            while index + run < len(chars) and chars[index + run] == "`":
                run += 1
            future = line[index + run :] + following_text
            if any(len(match.group(0)) == run for match in re.finditer(r"`+", future)):
                for position in range(index, index + run):
                    chars[position] = " "
                inline_ticks = run
                index += run
                continue
            index += run
            continue
        index += 1
    return "".join(chars), in_comment, inline_ticks


def _inline_block_boundary(line: str) -> bool:
    if not line.strip():
        return True
    if line.startswith("    ") or line.startswith("\t"):
        return True
    if ATX_HEADING_RE.match(line) or BLOCK_PREFIX_RE.match(line):
        return True
    if SETEXT_OR_RULE_RE.match(line):
        return True
    _state, is_fenced = advance_fence_state(line, None)
    return is_fenced


def _inline_block_tail(lines: list[str], index: int) -> str:
    if _inline_block_boundary(lines[index]):
        return ""
    tail: list[str] = []
    for line in lines[index + 1 :]:
        if _inline_block_boundary(line):
            break
        tail.append(line)
    return "".join(tail)


def scan_wikilinks(text: str, source: Path) -> list[LinkOccurrence]:
    """Finde Wikilinks außerhalb von Frontmatter, Code und Kommentaren."""

    frontmatter = re.match(
        r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S
    )
    frontmatter_end = frontmatter.end() if frontmatter else 0
    occurrences: list[LinkOccurrence] = []
    lines = text.splitlines(keepends=True)
    fence: FenceState | None = None
    in_comment = False
    inline_ticks = 0
    offset = 0

    for line_index, line in enumerate(lines):
        line_number = line_index + 1
        line_end = offset + len(line)
        if line_end <= frontmatter_end:
            offset = line_end
            continue

        if in_comment or inline_ticks:
            masked, in_comment, inline_ticks = _mask_comments_and_inline_code(
                line,
                in_comment,
                inline_ticks,
                _inline_block_tail(lines, line_index),
            )
            if in_comment or inline_ticks or line.startswith(("    ", "\t")):
                offset = line_end
                continue
            _append_occurrences(occurrences, masked, source, line_number, offset)
            offset = line_end
            continue

        fence, is_fenced = advance_fence_state(line, fence)
        if is_fenced:
            offset = line_end
            continue
        if line.startswith(("    ", "\t")):
            offset = line_end
            continue
        masked, in_comment, inline_ticks = _mask_comments_and_inline_code(
            line,
            False,
            0,
            _inline_block_tail(lines, line_index),
        )
        _append_occurrences(occurrences, masked, source, line_number, offset)
        offset = line_end
    return occurrences


def _append_occurrences(
    output: list[LinkOccurrence],
    masked: str,
    source: Path,
    line_number: int,
    offset: int,
) -> None:
    for match in WIKILINK_RE.finditer(masked):
        target, heading, label = split_link(match.group("body"))
        output.append(
            LinkOccurrence(
                source=source,
                raw=match.group(0),
                target=target,
                heading=heading,
                label=label,
                embed=bool(match.group("embed")),
                line=line_number,
                column=match.start() + 1,
                start=offset + match.start(),
                end=offset + match.end(),
            )
        )
