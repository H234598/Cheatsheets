#!/usr/bin/env python3
"""Öffentliche API für die gemeinsame Linkverarbeitung."""

from callouts import convert_obsidian_callouts_for_web
from content_index import build_content_index, markdown_files
from content_model import ContentIndex, slugify
from link_converters import convert_for_combined, convert_for_web
from link_resolution import resolve_occurrence
from link_validation import analyze_all, issue_for, resolve_target, validate_all
from link_types import (
    IMAGE_SUFFIXES,
    LinkError,
    LinkIssue,
    LinkOccurrence,
    LinkTarget,
    Resolution,
    scan_wikilinks,
    split_link,
)

__all__ = [
    "ContentIndex",
    "IMAGE_SUFFIXES",
    "LinkError",
    "LinkIssue",
    "LinkOccurrence",
    "LinkTarget",
    "Resolution",
    "analyze_all",
    "build_content_index",
    "convert_for_combined",
    "convert_for_web",
    "convert_obsidian_callouts_for_web",
    "issue_for",
    "markdown_files",
    "resolve_occurrence",
    "resolve_target",
    "scan_wikilinks",
    "slugify",
    "split_link",
    "validate_all",
]
