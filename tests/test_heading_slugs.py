from __future__ import annotations

import pytest

from content_model import slugify


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
