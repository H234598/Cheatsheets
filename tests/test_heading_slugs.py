from __future__ import annotations

import pytest

from content_model import parse_headings, slugify


@pytest.mark.parametrize(
    ("heading", "anchor"),
    [
        ("Konfiguration mit web.config", "konfiguration-mit-webconfig"),
        ("GitLab CI/CD", "gitlab-cicd"),
        ("Hostkeys und known_hosts", "hostkeys-und-known_hosts"),
        ("Java JCA/JCE", "java-jcajce"),
        ("big.LITTLE und DynamIQ", "biglittle-und-dynamiq"),
    ],
)
def test_slugify_matches_python_markdown_toc(heading: str, anchor: str) -> None:
    assert slugify(heading) == anchor


def test_heading_parser_preserves_literal_underscores() -> None:
    headings, issues = parse_headings(
        "## Hostkeys und known_hosts\n\n## wpa_supplicant direkt\n",
        body_start_line=1,
    )

    assert issues == []
    assert [(heading.text, heading.anchor) for heading in headings] == [
        ("Hostkeys und known_hosts", "hostkeys-und-known_hosts"),
        ("wpa_supplicant direkt", "wpa_supplicant-direkt"),
    ]
